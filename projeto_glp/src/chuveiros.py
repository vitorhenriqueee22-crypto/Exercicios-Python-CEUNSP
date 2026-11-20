# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Experimentação e Análise de Dados
# Aluno: Vitor Henrique Santos Das Virgens
# Projeto: Monitoramento e otimização do consumo de GLP
# Módulo: chuveiros — aquecimento de água, demanda térmica e perdas
# ============================================================
"""Análise do aquecimento de água para chuveiros (seção 2.7 do relatório).

Quantidade de usuários, duração do banho, vazão, temperaturas e rendimento
NÃO são presumidos: entram como parâmetros (medidos ou hipóteses).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .constantes import CALOR_ESPECIFICO_AGUA_KJ_KGK, CHUVEIROS, PCI_KJ_KG


def calor_aquecimento_kj(volume_l, delta_t_k, massa_especifica_kg_l: float = 1.0,
                         calor_especifico: float = CALOR_ESPECIFICO_AGUA_KJ_KGK):
    """Equação 10: Q = ρ·V·c·(Ts − Te), em kJ."""
    return massa_especifica_kg_l * volume_l * calor_especifico * delta_t_k


def glp_para_calor_kg(calor_kj, rendimento: float):
    """Equação 11: m_GLP = Q / (η·PCI)."""
    if not 0 < rendimento <= 1:
        raise ValueError("O rendimento deve estar entre 0 e 1.")
    return calor_kj / (rendimento * PCI_KJ_KG)


def volume_diario_l(n_banhos, duracao_min, vazao_l_min):
    """Equação 12: V = N_b · t_b · q_v, em litros."""
    return n_banhos * duracao_min * vazao_l_min


def glp_por_banho_kg(duracao_min, vazao_l_min, delta_t_k, rendimento):
    """GLP necessário para um banho, pelas Equações 10 a 12."""
    q = calor_aquecimento_kj(volume_diario_l(1, duracao_min, vazao_l_min), delta_t_k)
    return glp_para_calor_kg(q, rendimento)


def perda_termica_w(coef_global_w_m2k, area_m2, temp_agua_c, temp_ambiente_c):
    """Equação 13: q = U·A·(Ta − Tamb), em W."""
    return coef_global_w_m2k * area_m2 * (temp_agua_c - temp_ambiente_c)


def registros(df: pd.DataFrame) -> pd.DataFrame:
    c = df[df["setor"] == CHUVEIROS].copy()
    c["data"] = pd.to_datetime(c["data"])
    return c


def diario(df: pd.DataFrame, preco: float) -> pd.DataFrame:
    """kg/dia, usuários, kg/usuário, temperatura média de entrada e consumo em
    horas sem usuários (perdas em espera ou aquecedor ligado fora de uso)."""
    c = registros(df)
    sem_uso = c["atividade_valor"].fillna(0) == 0
    d = c.groupby("data").agg(consumo_kg=("consumo_kg", "sum"),
                              usuarios=("atividade_valor", "sum"),
                              temp_entrada_c=("temperatura_c", "mean"))
    d["kg_sem_uso"] = c[sem_uso & c["hora"].notna()].groupby("data")["consumo_kg"].sum()
    d["kg_sem_uso"] = d["kg_sem_uso"].fillna(0.0)
    d = d.reset_index()
    d["kg_por_usuario"] = np.where(d["usuarios"] > 0, d["consumo_kg"] / d["usuarios"], np.nan)
    d["custo_r"] = d["consumo_kg"] * preco
    d["fracao_sem_uso_pct"] = np.where(d["consumo_kg"] > 0, d["kg_sem_uso"] / d["consumo_kg"] * 100, np.nan)
    return d


def perfil_horario(df: pd.DataFrame) -> pd.DataFrame:
    c = registros(df)
    c = c[c["hora"].notna()]
    if c.empty:
        return pd.DataFrame(columns=["hora", "kg_medio", "usuarios_medios"])
    c = c.assign(h=c["hora"].str.slice(0, 2).astype(int))
    dias = c["data"].nunique()
    tab = c.groupby("h").agg(kg=("consumo_kg", "sum"), usuarios=("atividade_valor", "sum"))
    tab = tab.reindex(range(24), fill_value=0.0)
    return pd.DataFrame({"hora": tab.index, "kg_medio": tab["kg"] / dias,
                         "usuarios_medios": tab["usuarios"] / dias})


def demanda_termica_estimada(diario_ch: pd.DataFrame, parametros: dict) -> pd.DataFrame:
    """Demanda térmica útil estimada (kWh/dia) e GLP teórico, a partir dos
    usuários registrados e das hipóteses de duração, vazão e temperatura de
    saída. O resultado é HIPOTÉTICO enquanto esses parâmetros não forem medidos."""
    d = diario_ch.copy()
    delta_t = parametros["temperatura_saida_c"] - d["temp_entrada_c"]
    volume = volume_diario_l(d["usuarios"], parametros["duracao_banho_min"], parametros["vazao_l_min"])
    q_kj = calor_aquecimento_kj(volume, delta_t)
    d["demanda_util_kwh"] = q_kj / 3600
    d["glp_teorico_kg"] = glp_para_calor_kg(q_kj, parametros["rendimento_aquecedor"])
    d["glp_excedente_kg"] = d["consumo_kg"] - d["glp_teorico_kg"]
    return d
