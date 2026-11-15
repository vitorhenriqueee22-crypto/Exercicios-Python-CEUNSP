"""Página: Comparação entre setores."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402
from plotly.subplots import make_subplots  # noqa: E402

from src import indicadores, painel  # noqa: E402
from src.constantes import CHUVEIROS, FUNDICAO, RESTAURANTE, SETORES  # noqa: E402

ctx = painel.contexto()
painel.cabecalho("Comparação entre setores", ctx,
                 "Consumo absoluto, custo e, principalmente, consumo específico de cada setor.")
df = ctx.dados
if df.empty:
    painel.sem_dados()
    st.stop()

part = indicadores.participacao(df, ctx.preco)
esp = indicadores.especifico_por_setor(df, ctx.preco, ctx.equipamentos)
tabela = part.join(esp[["unidade", "consumo_especifico", "custo_especifico_r"]], how="left")
st.dataframe(tabela.reset_index()[["nome", "consumo_kg", "participacao_pct", "energia_mwh", "custo_r",
                                   "consumo_especifico", "unidade", "custo_especifico_r"]],
             hide_index=True, width="stretch", column_config={
                 "nome": "Setor",
                 "consumo_kg": st.column_config.NumberColumn("Consumo (kg)", format="%.0f"),
                 "participacao_pct": st.column_config.ProgressColumn("Participação", format="%.1f %%",
                                                                     min_value=0, max_value=100),
                 "energia_mwh": st.column_config.NumberColumn("Energia (MWh)", format="%.1f"),
                 "custo_r": st.column_config.NumberColumn("Custo (R$)", format="%.2f"),
                 "consumo_especifico": st.column_config.NumberColumn("Consumo específico", format="%.4f"),
                 "unidade": "Unidade",
                 "custo_especifico_r": st.column_config.NumberColumn("Custo específico (R$)", format="%.4f"),
             })
st.info("Os consumos específicos têm unidades diferentes (kg/t, kg/refeição, kg/usuário) e não "
        "devem ser comparados entre si: cada um é comparado com o próprio histórico. Um setor "
        "com maior consumo absoluto não é, por isso, menos eficiente.", icon=":material/info:")

mensal = indicadores.por_periodo(df, "MS")
setores = [s for s in SETORES if s in mensal.columns]
col_a, col_b = st.columns(2)
with col_a:
    fig = go.Figure()
    for s in setores:
        fig.add_trace(go.Scatter(x=mensal.index, y=mensal[s], name=painel.nome_setor(s), mode="lines+markers",
                                 line=dict(color=painel.cor_setor(s), width=2), marker=dict(size=8)))
    fig.update_xaxes(tickformat="%m/%Y")
    painel.grafico(painel.layout(fig, "Consumo mensal (kg)", 340, "kg/mês"), "cmp_kg")
with col_b:
    fig = go.Figure()
    for s in setores:
        fig.add_trace(go.Bar(x=mensal.index, y=mensal[s] * ctx.preco, name=painel.nome_setor(s),
                             marker=dict(color=painel.cor_setor(s), line=dict(color=painel.SUPERFICIE, width=1))))
    fig.update_xaxes(tickformat="%m/%Y")
    painel.grafico(painel.layout(fig, "Custo mensal (R$)", 340, "R$/mês"), "cmp_custo")

st.subheader("Evolução relativa (índice: primeiro mês = 100)")
st.caption("Como os setores têm escalas muito diferentes, a evolução é comparada em índice, num único eixo.")
indice = indicadores.indice_base_100(mensal[setores])
fig = go.Figure()
for s in setores:
    fig.add_trace(go.Scatter(x=indice.index, y=indice[s], name=painel.nome_setor(s), mode="lines+markers",
                             line=dict(color=painel.cor_setor(s), width=2), marker=dict(size=8)))
fig.add_hline(y=100, line_color=painel.GRADE, line_width=1)
fig.update_xaxes(tickformat="%m/%Y")
painel.grafico(painel.layout(fig, None, 320, "índice"), "cmp_indice")

st.subheader("Consumo específico mensal")
d = indicadores.diario(df)
fusao = set(ctx.equipamentos.loc[ctx.equipamentos["funcao"] == "Fusão", "equipamento_id"])
f = df[df["setor"] == FUNDICAO]
denominador = {FUNDICAO: f[f["equipamento_id"].isin(fusao)] if fusao else f}
unidades = {FUNDICAO: "kg/t", RESTAURANTE: "kg/refeição", CHUVEIROS: "kg/usuário"}
presentes = [s for s in (FUNDICAO, RESTAURANTE, CHUVEIROS) if s in setores]
if presentes:
    fig = make_subplots(rows=1, cols=len(presentes), subplot_titles=[
        f"{painel.nome_setor(s)} ({unidades[s]})" for s in presentes], horizontal_spacing=0.08)
    for i, s in enumerate(presentes, start=1):
        base = df[df["setor"] == s]
        ativ_base = denominador.get(s, base)
        kg = base.groupby(pd.Grouper(key="data", freq="MS"))["consumo_kg"].sum()
        ativ = ativ_base.groupby(pd.Grouper(key="data", freq="MS"))["atividade_valor"].sum()
        serie = (kg / ativ.replace(0, pd.NA)).dropna()
        fig.add_trace(go.Scatter(x=serie.index, y=serie.values, mode="lines+markers",
                                 line=dict(color=painel.cor_setor(s), width=2), marker=dict(size=8),
                                 name=painel.nome_setor(s), showlegend=False), row=1, col=i)
        fig.update_xaxes(tickformat="%m/%y", row=1, col=i)
    fig = painel.layout(fig, None, 340, legenda=False)
    fig.update_layout(margin=dict(t=44))
    fig.update_annotations(font=dict(size=13, color=painel.TEXTO))
    painel.grafico(fig, "cmp_esp")

st.subheader("Comparar dois períodos")
minimo, maximo = ctx.inicio, ctx.fim
meio = minimo + (maximo - minimo) / 2
c1, c2 = st.columns(2)
periodo_a = c1.date_input("Período A", value=(minimo, meio), min_value=minimo, max_value=maximo,
                          format="DD/MM/YYYY", key="cmp_a")
periodo_b = c2.date_input("Período B", value=(meio, maximo), min_value=minimo, max_value=maximo,
                          format="DD/MM/YYYY", key="cmp_b")
if len(periodo_a) == 2 and len(periodo_b) == 2:
    comp = indicadores.comparar_periodos(df, periodo_a, periodo_b)
    comp.index = [painel.nome_setor(s) for s in comp.index]
    st.dataframe(comp, width="stretch", column_config={
        "media_diaria_a_kg": st.column_config.NumberColumn("Média diária A (kg)", format="%.1f"),
        "media_diaria_b_kg": st.column_config.NumberColumn("Média diária B (kg)", format="%.1f"),
        "variacao_pct": st.column_config.NumberColumn("Variação (%)", format="%.1f"),
    })
    st.caption("Comparação descritiva. Para afirmar que houve redução, use a página "
               "*Análise estatística*, que considera a atividade, a variabilidade e a incerteza.")
