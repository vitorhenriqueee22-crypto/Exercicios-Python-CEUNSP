# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Experimentação e Análise de Dados
# Aluno: Vitor Henrique Santos Das Virgens
# Projeto: Monitoramento e otimização do consumo de GLP
# Módulo: anomalias — detecção de consumo fora do padrão (Quadro 9)
# ============================================================
"""Detecção de anomalias.

Toda anomalia é um ALERTA para investigação, não uma conclusão automática de
desperdício. Consumo inesperado com atividade nula pode indicar vazamento: a
verificação cabe a profissional habilitado.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

D2_AMPLITUDE_MOVEL = 1.128      # constante d2 para amplitude móvel de 2 pontos


def cercas_tukey(valores, fator: float = 1.5) -> pd.DataFrame:
    """Cercas de Tukey (Tukey, 1977): fora de [Q1 − k·IQR; Q3 + k·IQR]."""
    x = pd.Series(valores, dtype=float)
    q1, q3 = x.quantile(0.25), x.quantile(0.75)
    iqr = q3 - q1
    inf, sup = q1 - fator * iqr, q3 + fator * iqr
    return pd.DataFrame({"valor": x, "limite_inf": inf, "limite_sup": sup,
                         "anomalia": (x < inf) | (x > sup)})


def escore_z_robusto(valores, limite: float = 3.5) -> pd.DataFrame:
    """Escore z modificado (Iglewicz; Hoaglin, 1993):
    M = 0,6745 · (x − mediana) / MAD; anomalia se |M| > limite."""
    x = pd.Series(valores, dtype=float)
    mediana = x.median()
    mad = (x - mediana).abs().median()
    if mad == 0 or np.isnan(mad):
        m = pd.Series(0.0, index=x.index)
    else:
        m = 0.6745 * (x - mediana) / mad
    return pd.DataFrame({"valor": x, "escore_m": m, "anomalia": m.abs() > limite})


@dataclass
class CartaIMR:
    linha_central: float
    lsc: float
    lic: float
    mr_medio: float
    lsc_mr: float
    dados: pd.DataFrame


def carta_imr(valores) -> CartaIMR:
    """Gráfico de controle de valores individuais e amplitude móvel
    (Montgomery, 2013): limites x̄ ± 2,66·MR̄ (= 3·MR̄/d2)."""
    x = pd.Series(valores, dtype=float)
    mr = x.diff().abs()
    mr_medio = mr.mean()
    centro = x.mean()
    lsc = centro + 3 * mr_medio / D2_AMPLITUDE_MOVEL
    lic = centro - 3 * mr_medio / D2_AMPLITUDE_MOVEL
    dados = pd.DataFrame({"valor": x, "amplitude_movel": mr,
                          "anomalia": (x > lsc) | (x < lic)})
    return CartaIMR(centro, lsc, lic, mr_medio, 3.267 * mr_medio, dados)


def cusum(residuos) -> pd.Series:
    """Soma acumulada dos resíduos em relação à linha de base (Page, 1954).
    Inclinação persistente indica mudança de desempenho: para cima, consumo
    acima do esperado; para baixo, economia em relação à linha de base."""
    return pd.Series(residuos, dtype=float).cumsum()


def consumo_sem_atividade(df: pd.DataFrame, coluna_consumo: str = "consumo_kg",
                          coluna_atividade: str = "atividade_valor",
                          minimo_kg: float = 0.0) -> pd.DataFrame:
    """Registros com consumo acima de ``minimo_kg`` e atividade igual a zero."""
    atividade = df[coluna_atividade].fillna(0)
    return df[(df[coluna_consumo] > minimo_kg) & (atividade == 0)]


def detectar(valores, metodo: str = "z_robusto", **kw) -> pd.Series:
    """Atalho: retorna a máscara booleana de anomalias pelo método escolhido."""
    if metodo == "tukey":
        return cercas_tukey(valores, kw.get("fator", 1.5))["anomalia"]
    if metodo == "z_robusto":
        return escore_z_robusto(valores, kw.get("limite", 3.5))["anomalia"]
    if metodo == "imr":
        return carta_imr(valores).dados["anomalia"]
    raise ValueError(f"Método desconhecido: {metodo}")
