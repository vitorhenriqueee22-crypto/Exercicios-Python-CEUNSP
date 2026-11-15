# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Experimentação e Análise de Dados
# Aluno: Vitor Henrique Santos Das Virgens
# Projeto: Monitoramento e otimização do consumo de GLP
# Módulo: indicadores — consumo, custo, participação e consumo específico
# ============================================================
"""Indicadores gerais (seção 5 do escopo; Equações 1 a 3 do relatório).

Atenção: comparar somente quilogramas entre setores pode enganar. Sempre que
houver atividade registrada, use o consumo específico (kg por unidade).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .constantes import NOME_SETOR, PCI_KWH_KG

UNIDADE_ESPECIFICA = {
    "FUNDICAO": "kg/t",
    "RESTAURANTE": "kg/refeição",
    "CHUVEIROS": "kg/usuário",
}


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    """Garante tipos e cria a coluna de data como datetime."""
    df = df.copy()
    df["data"] = pd.to_datetime(df["data"])
    if "consumo_kg" not in df.columns:
        df["consumo_kg"] = df["consumo_valor"]
    return df


def diario(df: pd.DataFrame, por_equipamento: bool = False) -> pd.DataFrame:
    """Agrega os registros (horários ou diários) em totais diários."""
    df = preparar(df)
    chaves = ["data", "setor"] + (["equipamento_id"] if por_equipamento else [])
    agregado = df.groupby(chaves, dropna=False).agg(
        consumo_kg=("consumo_kg", "sum"),
        atividade=("atividade_valor", lambda s: s.sum(min_count=1)),
        horas=("tempo_funcionamento_h", lambda s: s.sum(min_count=1)),
        horas_sem_carga=("tempo_sem_carga_h", lambda s: s.sum(min_count=1)),
        ciclos=("ciclos", lambda s: s.sum(min_count=1)),
        temperatura_c=("temperatura_c", "mean"),
        registros=("consumo_kg", "size"),
    ).reset_index()
    return agregado


def por_periodo(df: pd.DataFrame, freq: str = "MS") -> pd.DataFrame:
    """Consumo (kg) por período e setor. freq: 'D' dia, 'W-MON' semana,
    'MS' mês."""
    df = preparar(df)
    tabela = (df.groupby([pd.Grouper(key="data", freq=freq), "setor"])["consumo_kg"]
              .sum().unstack("setor").fillna(0.0))
    return tabela


def participacao(df: pd.DataFrame, preco: float) -> pd.DataFrame:
    """Consumo, energia, custo e participação percentual por setor."""
    df = preparar(df)
    tab = df.groupby("setor")["consumo_kg"].sum().rename("consumo_kg").to_frame()
    total = tab["consumo_kg"].sum()
    tab["participacao_pct"] = tab["consumo_kg"] / total * 100 if total else np.nan
    tab["energia_mwh"] = tab["consumo_kg"] * PCI_KWH_KG / 1000
    tab["custo_r"] = tab["consumo_kg"] * preco
    tab["nome"] = [NOME_SETOR.get(s, s) for s in tab.index]
    return tab.sort_values("consumo_kg", ascending=False)


def consumo_especifico(diario_setor: pd.DataFrame) -> pd.Series:
    """Equação 3: CE = m_GLP / A, somente para dias com atividade > 0."""
    validos = diario_setor["atividade"].fillna(0) > 0
    return (diario_setor.loc[validos, "consumo_kg"] / diario_setor.loc[validos, "atividade"])


def especifico_por_setor(df: pd.DataFrame, preco: float,
                         equipamentos: pd.DataFrame | None = None) -> pd.DataFrame:
    """Consumo específico médio do período, por setor (razão das somas).

    Na fundição, o mesmo metal pode passar por vários fornos (fusão, espera,
    tratamento térmico). Para não contar a mesma tonelada várias vezes, o
    denominador do setor usa só as toneladas dos fornos de função "Fusão"
    quando o cadastro de equipamentos é informado; o numerador inclui o
    consumo de todos os fornos."""
    d = diario(df)
    fusao = None
    if equipamentos is not None and len(equipamentos) and "funcao" in equipamentos.columns:
        fusao = set(equipamentos.loc[equipamentos["funcao"].astype(str).str.lower() == "fusão",
                                     "equipamento_id"])
    linhas = []
    for setor, grupo in d.groupby("setor"):
        com_atividade = grupo[grupo["atividade"].fillna(0) > 0]
        kg, ativ = com_atividade["consumo_kg"].sum(), com_atividade["atividade"].sum()
        if setor == "FUNDICAO" and fusao:
            f = preparar(df)
            f = f[(f["setor"] == "FUNDICAO")]
            dias_producao = f.loc[f["equipamento_id"].isin(fusao) & (f["atividade_valor"] > 0), "data"]
            ativ = f.loc[f["equipamento_id"].isin(fusao), "atividade_valor"].sum()
            kg = f.loc[f["data"].isin(dias_producao), "consumo_kg"].sum()
            com_atividade = dias_producao.drop_duplicates()
        ce = kg / ativ if ativ else np.nan
        linhas.append({"setor": setor, "nome": NOME_SETOR.get(setor, setor),
                       "unidade": UNIDADE_ESPECIFICA.get(setor, "kg/unid."),
                       "consumo_especifico": ce, "custo_especifico_r": ce * preco,
                       "dias_com_atividade": len(com_atividade)})
    return pd.DataFrame(linhas).set_index("setor")


def resumo_geral(df: pd.DataFrame, preco: float) -> dict:
    """Números da visão geral."""
    df = preparar(df)
    total = df["consumo_kg"].sum()
    dias = df["data"].dt.normalize().nunique()
    part = participacao(df, preco)
    return {
        "consumo_total_kg": total,
        "custo_total_r": total * preco,
        "energia_total_mwh": total * PCI_KWH_KG / 1000,
        "dias": dias,
        "consumo_medio_diario_kg": total / dias if dias else np.nan,
        "setor_maior_consumo": part.index[0] if len(part) else None,
        "participacao_maior_pct": part["participacao_pct"].iloc[0] if len(part) else np.nan,
        "inicio": df["data"].min(),
        "fim": df["data"].max(),
    }


def comparar_periodos(df: pd.DataFrame, periodo_a: tuple, periodo_b: tuple) -> pd.DataFrame:
    """Consumo médio diário por setor em dois períodos e variação percentual.
    Use apenas como descrição; a prova de redução exige a seção 2.9.3."""
    d = diario(df)
    def media(periodo):
        ini, fim = pd.Timestamp(periodo[0]), pd.Timestamp(periodo[1])
        sel = d[(d["data"] >= ini) & (d["data"] <= fim)]
        dias = (fim - ini).days + 1
        return sel.groupby("setor")["consumo_kg"].sum() / dias
    a, b = media(periodo_a), media(periodo_b)
    tab = pd.DataFrame({"media_diaria_a_kg": a, "media_diaria_b_kg": b}).fillna(0.0)
    tab["variacao_pct"] = np.where(tab["media_diaria_a_kg"] > 0,
                                   (tab["media_diaria_b_kg"] / tab["media_diaria_a_kg"] - 1) * 100,
                                   np.nan)
    return tab


def indice_base_100(tabela_periodos: pd.DataFrame) -> pd.DataFrame:
    """Converte séries de escalas diferentes em índice (primeiro período = 100),
    para compará-las em um único eixo."""
    base = tabela_periodos.iloc[0].replace(0, np.nan)
    return tabela_periodos.divide(base) * 100
