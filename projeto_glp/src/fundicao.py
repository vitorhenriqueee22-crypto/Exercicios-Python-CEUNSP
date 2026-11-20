# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Experimentação e Análise de Dados
# Aluno: Vitor Henrique Santos Das Virgens
# Projeto: Monitoramento e otimização do consumo de GLP
# Módulo: fundicao — fornos, balanço térmico e indicadores
# ============================================================
"""Análise da fundição (seção 2.5 do relatório).

Cada forno é tratado individualmente, conforme o cadastro de equipamentos:
fornos de fusão, de espera e de tratamento térmico têm funcionamento distinto.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .constantes import FUNDICAO, PCI_KJ_KG
from . import estatistica
from .indicadores import diario


def calor_util_kj(massa_metal_kg, cs, cl, calor_latente, t_inicial, t_fusao, t_vazamento):
    """Equação 5: Q_útil = m·[cs·(Tf − T0) + Lf + cl·(Tv − Tf)], em kJ."""
    return massa_metal_kg * (cs * (t_fusao - t_inicial) + calor_latente
                             + cl * (t_vazamento - t_fusao))


def eficiencia_forno(q_util_kj, massa_glp_kg):
    """Equação 6: η = Q_útil / (m_GLP · PCI)."""
    energia = np.asarray(massa_glp_kg, dtype=float) * PCI_KJ_KG
    return np.divide(q_util_kj, energia, out=np.full_like(energia, np.nan), where=energia > 0)


def diario_fornos(df: pd.DataFrame) -> pd.DataFrame:
    """Totais diários por forno, com indicadores do Quadro 5."""
    d = diario(df[df["setor"] == FUNDICAO], por_equipamento=True)
    d = d.rename(columns={"atividade": "metal_t"})
    operou = d["horas"].fillna(0) > 0
    d["kg_por_h"] = np.where(operou, d["consumo_kg"] / d["horas"], np.nan)
    d["kg_por_t"] = np.where(d["metal_t"].fillna(0) > 0, d["consumo_kg"] / d["metal_t"], np.nan)
    d["kg_por_ciclo"] = np.where(d["ciclos"].fillna(0) > 0, d["consumo_kg"] / d["ciclos"], np.nan)
    d["fracao_sem_carga"] = np.where(operou, d["horas_sem_carga"] / d["horas"], np.nan)
    return d


def indicadores_por_forno(df: pd.DataFrame, preco: float,
                          equipamentos: pd.DataFrame | None = None) -> pd.DataFrame:
    """Indicadores do período por forno (razão das somas, não média das razões)."""
    d = diario_fornos(df)
    linhas = []
    for forno, g in d.groupby("equipamento_id"):
        kg, t, h = g["consumo_kg"].sum(), g["metal_t"].sum(), g["horas"].sum()
        ciclos, sem_carga = g["ciclos"].sum(), g["horas_sem_carga"].sum()
        sem_atividade = g[(g["metal_t"].fillna(0) == 0) & (g["consumo_kg"] > 0)]
        linhas.append({
            "equipamento_id": forno,
            "dias_operacao": int((g["consumo_kg"] > 0).sum()),
            "consumo_kg": kg,
            "metal_t": t,
            "horas": h,
            "ciclos": ciclos,
            "kg_por_h": kg / h if h else np.nan,
            "kg_por_t": kg / t if t else np.nan,
            "kg_por_ciclo": kg / ciclos if ciclos else np.nan,
            "custo_r": kg * preco,
            "r_por_t": kg * preco / t if t else np.nan,
            "fracao_sem_carga_pct": sem_carga / h * 100 if h else np.nan,
            "kg_dias_sem_producao": sem_atividade["consumo_kg"].sum(),
        })
    tab = pd.DataFrame(linhas).set_index("equipamento_id")
    if equipamentos is not None and len(equipamentos):
        cad = equipamentos.set_index("equipamento_id")
        for col in ("nome", "tipo", "funcao"):
            if col in cad.columns:
                tab[col] = cad[col].reindex(tab.index)
    return tab


def modelo_consumo(diario_forno: pd.DataFrame) -> estatistica.ResultadoRegressao:
    """Equação 7: G_dia = β0 + β1·h_lig + β2·M_metal + ε (dias de operação)."""
    dados = diario_forno[(diario_forno["horas"].fillna(0) > 0)].copy()
    variaveis = [v for v in ("horas", "metal_t")
                 if dados[v].notna().all() and dados[v].nunique() > 1]
    if not variaveis:
        raise ValueError("Sem variação em horas ou massa para ajustar o modelo.")
    return estatistica.regressao_linear(dados, "consumo_kg", variaveis)


def eficiencia_estimada(diario_forno: pd.DataFrame, liga: dict) -> pd.Series:
    """Eficiência térmica diária estimada (Equação 6) para fornos de fusão.
    Usa a temperatura registrada como temperatura de vazamento. O resultado
    herda a origem das propriedades da liga (HIPOTESE, enquanto não houver
    ficha técnica)."""
    d = diario_forno[(diario_forno["metal_t"].fillna(0) > 0)
                     & diario_forno["temperatura_c"].notna()]
    q = calor_util_kj(d["metal_t"] * 1000, liga["calor_especifico_solido_kj_kgk"],
                      liga["calor_especifico_liquido_kj_kgk"], liga["calor_latente_fusao_kj_kg"],
                      liga["temperatura_inicial_c"], liga["temperatura_fusao_c"],
                      d["temperatura_c"])
    return pd.Series(eficiencia_forno(q.to_numpy(), d["consumo_kg"].to_numpy()), index=d.index)
