# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Experimentação e Análise de Dados
# Aluno: Vitor Henrique Santos Das Virgens
# Projeto: Monitoramento e otimização do consumo de GLP
# Módulo: relatorios — avaliação de intervenções e exportação
# ============================================================
"""Avaliação estatística de intervenções e relatórios exportáveis."""

from __future__ import annotations

import io
from datetime import datetime

import numpy as np
import pandas as pd

from . import chuveiros, estatistica, fundicao, indicadores, restaurante
from .constantes import CHUVEIROS, FUNDICAO, NOME_SETOR, RESTAURANTE

METRICA_PADRAO = {
    FUNDICAO: "kg de GLP por tonelada (dias com produção)",
    RESTAURANTE: "kg de GLP por refeição (dias úteis)",
    CHUVEIROS: "kg de GLP em horas sem uso, por dia",
}


def serie_metrica(df: pd.DataFrame, setor: str, equipamento: str | None,
                  preco: float = 0.0) -> pd.Series:
    """Série diária do indicador usado para avaliar intervenções no setor."""
    if setor == FUNDICAO:
        d = fundicao.diario_fornos(df)
        if equipamento:
            d = d[d["equipamento_id"] == equipamento]
        d = d[d["metal_t"].fillna(0) > 0]
        return pd.Series((d["consumo_kg"] / d["metal_t"]).to_numpy(), index=d["data"]).sort_index()
    if setor == RESTAURANTE:
        d = restaurante.diario(df, preco)
        d = d[(d["refeicoes"] > 0) & (d["data"].dt.dayofweek < 5)]
        return pd.Series(d["kg_por_refeicao"].to_numpy(), index=d["data"]).sort_index()
    if setor == CHUVEIROS:
        d = chuveiros.diario(df, preco)
        return pd.Series(d["kg_sem_uso"].to_numpy(), index=d["data"]).sort_index()
    raise ValueError(f"Setor sem métrica definida: {setor}")


def avaliar_intervencao(df: pd.DataFrame, intervencao: dict, janela_dias: int = 90,
                        alfa: float = 0.05) -> dict:
    """Compara a métrica do setor nos ``janela_dias`` antes e depois da data
    de início da intervenção (amostras independentes)."""
    serie = serie_metrica(df, intervencao["setor"], intervencao.get("equipamento_id"))
    inicio = pd.Timestamp(intervencao["data_inicio"])
    antes = serie[(serie.index < inicio) & (serie.index >= inicio - pd.Timedelta(days=janela_dias))]
    depois = serie[(serie.index >= inicio) & (serie.index < inicio + pd.Timedelta(days=janela_dias))]
    resultado = estatistica.comparar_antes_depois(antes, depois, pareado=False, alfa=alfa)
    return {"intervencao": intervencao, "metrica": METRICA_PADRAO[intervencao["setor"]],
            "resultado": resultado, "antes": antes, "depois": depois}


def tabela_intervencoes(df: pd.DataFrame, intervencoes: pd.DataFrame,
                        janela_dias: int = 90) -> pd.DataFrame:
    linhas = []
    for _, i in intervencoes.iterrows():
        try:
            av = avaliar_intervencao(df, i.to_dict(), janela_dias)
        except ValueError as erro:
            linhas.append({"id": i["id"], "descricao": i["descricao"], "erro": str(erro)})
            continue
        r = av["resultado"]
        linhas.append({
            "id": i["id"], "setor": NOME_SETOR.get(i["setor"], i["setor"]),
            "equipamento": i["equipamento_id"], "descricao": i["descricao"],
            "inicio": i["data_inicio"], "metrica": av["metrica"],
            "n_antes": r.n_antes, "n_depois": r.n_depois,
            "media_antes": r.media_antes, "media_depois": r.media_depois,
            "reducao_pct": r.reducao_percentual,
            "ic95_inf_pct": r.ic95_reducao_percentual[0], "ic95_sup_pct": r.ic95_reducao_percentual[1],
            "teste": r.teste, "p_valor": r.p_valor, "significativo": r.significativo,
        })
    return pd.DataFrame(linhas)


def tabelas_resumo(df: pd.DataFrame, preco: float, equipamentos: pd.DataFrame | None,
                   alertas: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    resumo = indicadores.resumo_geral(df, preco)
    tab_resumo = pd.DataFrame({
        "indicador": ["Período", "Consumo total (kg)", "Custo total (R$)", "Energia (MWh)",
                      "Consumo médio diário (kg/dia)", "Setor de maior consumo"],
        "valor": [f"{resumo['inicio']:%d/%m/%Y} a {resumo['fim']:%d/%m/%Y}",
                  round(resumo["consumo_total_kg"], 1), round(resumo["custo_total_r"], 2),
                  round(resumo["energia_total_mwh"], 2), round(resumo["consumo_medio_diario_kg"], 1),
                  NOME_SETOR.get(resumo["setor_maior_consumo"], resumo["setor_maior_consumo"])],
    })
    tabelas = {
        "resumo": tab_resumo,
        "setores": indicadores.participacao(df, preco).reset_index(),
        "consumo_especifico": indicadores.especifico_por_setor(df, preco, equipamentos).reset_index(),
        "mensal": indicadores.por_periodo(df, "MS").reset_index(),
        "fornos": fundicao.indicadores_por_forno(df, preco, equipamentos).reset_index(),
        "restaurante_diario": restaurante.diario(df, preco),
        "chuveiros_diario": chuveiros.diario(df, preco),
    }
    if alertas is not None:
        tabelas["alertas"] = alertas
    return tabelas


def exportar_excel(tabelas: dict[str, pd.DataFrame], origem: str) -> bytes:
    """Planilha com uma aba por tabela e uma aba de identificação da origem."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as escritor:
        pd.DataFrame({"campo": ["Origem dos dados", "Gerado em", "Aviso"],
                      "valor": [origem, datetime.now().strftime("%d/%m/%Y %H:%M"),
                                "Dados SIMULADOS não descrevem a empresa." if origem == "SIMULADO"
                                else "Dados medidos pela empresa."]}
                     ).to_excel(escritor, sheet_name="origem", index=False)
        for nome, tabela in tabelas.items():
            saida = tabela.copy()
            for coluna in saida.columns:
                if isinstance(saida[coluna].dtype, pd.CategoricalDtype):
                    saida[coluna] = saida[coluna].astype(str)
            saida.to_excel(escritor, sheet_name=nome[:31], index=False)
    return buffer.getvalue()


def relatorio_markdown(df: pd.DataFrame, preco: float, origem: str,
                       intervencoes: pd.DataFrame | None, alertas: pd.DataFrame | None,
                       equipamentos: pd.DataFrame | None = None) -> str:
    r = indicadores.resumo_geral(df, preco)
    part = indicadores.participacao(df, preco)
    esp = indicadores.especifico_por_setor(df, preco, equipamentos)

    def n(x, c=0):
        return f"{x:,.{c}f}".replace(",", "X").replace(".", ",").replace("X", ".")

    linhas = [
        "# Relatório de consumo de GLP",
        "",
        f"- **Origem dos dados:** {origem}"
        + (" — dados sintéticos; NÃO descrevem a empresa." if origem == "SIMULADO" else ""),
        f"- **Período:** {r['inicio']:%d/%m/%Y} a {r['fim']:%d/%m/%Y} ({r['dias']} dias)",
        f"- **Preço considerado:** R$ {n(preco, 2)}/kg",
        "",
        "## Visão geral",
        "",
        f"- Consumo total: {n(r['consumo_total_kg'])} kg ({n(r['energia_total_mwh'], 1)} MWh)",
        f"- Custo total: R$ {n(r['custo_total_r'], 2)}",
        f"- Consumo médio diário: {n(r['consumo_medio_diario_kg'], 1)} kg/dia",
        "",
        "| Setor | Consumo (kg) | Participação | Custo (R$) | Consumo específico |",
        "|---|---:|---:|---:|---:|",
    ]
    for setor, linha in part.iterrows():
        ce = esp.loc[setor] if setor in esp.index else None
        txt_ce = f"{n(ce['consumo_especifico'], 3)} {ce['unidade']}" if ce is not None and \
            not np.isnan(ce["consumo_especifico"]) else "—"
        linhas.append(f"| {linha['nome']} | {n(linha['consumo_kg'])} | {n(linha['participacao_pct'], 1)} % "
                      f"| {n(linha['custo_r'], 2)} | {txt_ce} |")
    linhas += ["", "> Maior consumo absoluto não é, sozinho, evidência de ineficiência: compare o "
               "consumo específico de cada setor ao longo do tempo.", ""]
    if intervencoes is not None and len(intervencoes):
        tab = tabela_intervencoes(df, intervencoes)
        linhas += ["## Avaliação de intervenções (90 dias antes × 90 dias depois)", ""]
        for _, t in tab.iterrows():
            if "erro" in t and isinstance(t.get("erro"), str):
                linhas.append(f"- {t['id']}: não avaliada ({t['erro']})")
                continue
            conclusao = "redução estatisticamente significativa" if t["significativo"] else \
                "sem evidência estatística de redução"
            linhas.append(f"- **{t['id']}** — {t['descricao']} ({t['equipamento']}, desde {t['inicio']}): "
                          f"{t['metrica']}: {n(t['media_antes'], 3)} → {n(t['media_depois'], 3)} "
                          f"({n(t['reducao_pct'], 1)} %; IC 95 % {n(t['ic95_inf_pct'], 1)} a "
                          f"{n(t['ic95_sup_pct'], 1)} %); {t['teste']}, p = {t['p_valor']:.2g}: {conclusao}.")
        linhas += ["", "> Amostras independentes: confirme que produção, mix e estação são comparáveis "
                   "entre os períodos antes de atribuir a diferença à intervenção.", ""]
    if alertas is not None and len(alertas):
        linhas += ["## Alertas para investigação", ""]
        for _, a in alertas.head(30).iterrows():
            rotulo = {"critico": "Crítico", "serio": "Sério", "atencao": "Atenção"}.get(a["nivel"], a["nivel"])
            linhas.append(f"- **{rotulo}** — {a['data']:%d/%m/%Y} — {a['setor']}: {a['mensagem']}")
        linhas += ["", "> Alertas são indícios para investigação, não conclusões. Ajustes em "
                   "equipamentos de GLP devem ser avaliados por profissionais habilitados.", ""]
    return "\n".join(linhas)


# Variáveis diárias disponíveis para análise estatística, por setor
VARIAVEIS = {
    FUNDICAO: {"consumo_kg": "Consumo diário (kg)", "kg_por_t": "kg por tonelada",
               "kg_por_h": "kg por hora ligado", "metal_t": "Toneladas processadas",
               "horas": "Horas ligado", "horas_sem_carga": "Horas sem carga",
               "ciclos": "Ciclos", "temperatura_c": "Temperatura de vazamento (°C)"},
    RESTAURANTE: {"consumo_kg": "Consumo diário (kg)", "kg_por_refeicao": "kg por refeição",
                  "refeicoes": "Refeições"},
    CHUVEIROS: {"consumo_kg": "Consumo diário (kg)", "kg_por_usuario": "kg por usuário",
                "kg_sem_uso": "kg em horas sem uso", "usuarios": "Usuários",
                "temp_entrada_c": "Temperatura da água de entrada (°C)"},
}


def tabela_diaria(df: pd.DataFrame, setor: str, equipamento: str | None = None,
                  preco: float = 0.0) -> pd.DataFrame:
    """Tabela diária com o consumo e as variáveis explicativas do setor."""
    if setor == FUNDICAO:
        d = fundicao.diario_fornos(df)
        if equipamento:
            d = d[d["equipamento_id"] == equipamento]
        d = d.groupby("data", as_index=False).agg(
            consumo_kg=("consumo_kg", "sum"), metal_t=("metal_t", "sum"), horas=("horas", "sum"),
            horas_sem_carga=("horas_sem_carga", "sum"), ciclos=("ciclos", "sum"),
            temperatura_c=("temperatura_c", "mean"))
        d["kg_por_t"] = np.where(d["metal_t"] > 0, d["consumo_kg"] / d["metal_t"], np.nan)
        d["kg_por_h"] = np.where(d["horas"] > 0, d["consumo_kg"] / d["horas"], np.nan)
    elif setor == RESTAURANTE:
        d = restaurante.diario(df, preco)[["data", "consumo_kg", "refeicoes", "kg_por_refeicao"]]
    elif setor == CHUVEIROS:
        d = chuveiros.diario(df, preco)[["data", "consumo_kg", "usuarios", "kg_por_usuario",
                                         "kg_sem_uso", "temp_entrada_c"]]
    else:
        raise ValueError(f"Setor sem tabela diária: {setor}")
    return d.sort_values("data").reset_index(drop=True)
