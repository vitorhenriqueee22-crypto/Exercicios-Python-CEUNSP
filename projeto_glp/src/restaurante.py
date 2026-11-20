# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Experimentação e Análise de Dados
# Aluno: Vitor Henrique Santos Das Virgens
# Projeto: Monitoramento e otimização do consumo de GLP
# Módulo: restaurante — consumo por refeição e perfis de uso
# ============================================================
"""Análise do restaurante industrial (seção 2.6 do relatório).

O consumo diário tem uma parcela fixa (β0) e uma proporcional às refeições
(β1·N). Por isso kg/refeição cai quando N sobe (Equação 9): compare dias de
volume semelhante (faixas) ou use os resíduos do modelo.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .constantes import RESTAURANTE
from . import estatistica

DIAS_SEMANA = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]


def registros(df: pd.DataFrame) -> pd.DataFrame:
    r = df[df["setor"] == RESTAURANTE].copy()
    r["data"] = pd.to_datetime(r["data"])
    return r


def diario(df: pd.DataFrame, preco: float) -> pd.DataFrame:
    r = registros(df)
    d = r.groupby("data").agg(consumo_kg=("consumo_kg", "sum"),
                              refeicoes=("atividade_valor", "sum")).reset_index()
    d["kg_por_refeicao"] = np.where(d["refeicoes"] > 0, d["consumo_kg"] / d["refeicoes"], np.nan)
    d["custo_r"] = d["consumo_kg"] * preco
    d["custo_por_refeicao_r"] = d["kg_por_refeicao"] * preco
    d["dia_semana"] = d["data"].dt.dayofweek.map(dict(enumerate(DIAS_SEMANA)))
    return d


def modelo_consumo(diario_rest: pd.DataFrame) -> estatistica.ResultadoRegressao:
    """Equação 8: G_dia = β0 + β1·N_ref + ε (dias com refeições)."""
    dados = diario_rest[diario_rest["refeicoes"] > 0]
    return estatistica.regressao_linear(dados, "consumo_kg", ["refeicoes"])


def por_faixa(diario_rest: pd.DataFrame, faixas: list[float]) -> pd.DataFrame:
    """kg/refeição comparado entre dias de volume semelhante."""
    dados = diario_rest[diario_rest["refeicoes"] > 0].copy()
    dados["faixa"] = pd.cut(dados["refeicoes"], bins=faixas, right=False)
    tab = dados.groupby("faixa", observed=True).agg(
        dias=("consumo_kg", "size"),
        refeicoes_media=("refeicoes", "mean"),
        kg_dia_medio=("consumo_kg", "mean"),
        kg_por_refeicao_medio=("kg_por_refeicao", "mean"),
        kg_por_refeicao_dp=("kg_por_refeicao", "std"),
    )
    tab.index = [f"{int(i.left)} a {int(i.right) - 1}" for i in tab.index]
    return tab


def por_dia_semana(diario_rest: pd.DataFrame) -> pd.DataFrame:
    tab = diario_rest.groupby("dia_semana").agg(
        dias=("consumo_kg", "size"), kg_dia_medio=("consumo_kg", "mean"),
        refeicoes_media=("refeicoes", "mean"))
    return tab.reindex([d for d in DIAS_SEMANA if d in tab.index])


def perfil_horario(df: pd.DataFrame) -> pd.DataFrame:
    """Consumo médio por hora do dia, nos dias com registro horário."""
    r = registros(df)
    r = r[r["hora"].notna()]
    if r.empty:
        return pd.DataFrame(columns=["hora", "kg_medio", "refeicoes_medias"])
    r["h"] = r["hora"].str.slice(0, 2).astype(int)
    dias = r["data"].nunique()
    tab = r.groupby("h").agg(kg=("consumo_kg", "sum"), refeicoes=("atividade_valor", "sum"))
    tab = tab.reindex(range(24), fill_value=0.0)
    return pd.DataFrame({"hora": tab.index, "kg_medio": tab["kg"] / dias,
                         "refeicoes_medias": tab["refeicoes"] / dias})


def fora_do_horario(df: pd.DataFrame, abertura: int, fechamento: int) -> pd.DataFrame:
    """Consumo registrado fora do horário de funcionamento da cozinha."""
    r = registros(df)
    r = r[r["hora"].notna()].copy()
    h = r["hora"].str.slice(0, 2).astype(int)
    fora = r[((h < abertura) | (h >= fechamento)) & (r["consumo_kg"] > 0)]
    return fora.groupby("data")["consumo_kg"].sum().rename("kg_fora_horario").reset_index()
