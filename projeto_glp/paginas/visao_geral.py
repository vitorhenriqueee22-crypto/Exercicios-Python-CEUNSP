"""Página: Visão geral."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from src import alertas, indicadores, painel  # noqa: E402
from src.constantes import SETORES  # noqa: E402

ctx = painel.contexto()
painel.cabecalho("Visão geral", ctx, "Consumo, custo e distribuição do GLP entre os setores.")
df = ctx.dados
if df.empty:
    painel.sem_dados("Não há registros no período selecionado.")
    st.stop()

r = indicadores.resumo_geral(df, ctx.preco)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Consumo total", painel.massa(r["consumo_total_kg"]), border=True,
          help=f"{painel.num(r['consumo_total_kg'])} kg no período.")
c2.metric("Custo total", painel.reais_compacto(r["custo_total_r"]), border=True,
          help=f"{painel.reais(r['custo_total_r'])} = consumo × preço informado na barra lateral.")
c3.metric("Energia (MWh)", painel.num(r["energia_total_mwh"], 0), border=True,
          help="E = m · PCI, com PCI = 11.100 kcal/kg (ANP, 2026).")
c4.metric("Média diária (kg/dia)", painel.num(r["consumo_medio_diario_kg"], 0), border=True,
          help="Consumo total / dias do período.")
st.caption(f"Setor de maior consumo absoluto: **{painel.nome_setor(r['setor_maior_consumo'])}** "
           f"({painel.pct(r['participacao_maior_pct'])} do total). Maior consumo absoluto não indica, "
           "sozinho, ineficiência: compare o consumo específico de cada setor na página "
           "*Comparação entre setores*.")

# Consumo mensal por setor -------------------------------------------------
mensal = indicadores.por_periodo(df, "MS")
col_a, col_b = st.columns([3, 2])
with col_a:
    fig = go.Figure()
    for setor in [s for s in SETORES if s in mensal.columns]:
        fig.add_trace(go.Bar(
            x=mensal.index, y=mensal[setor], name=painel.nome_setor(setor),
            marker=dict(color=painel.cor_setor(setor), line=dict(color=painel.SUPERFICIE, width=1)),
            hovertemplate="%{x|%m/%Y}<br>%{y:,.0f} kg<extra>" + painel.nome_setor(setor) + "</extra>"))
    fig.update_layout(barmode="stack")
    fig.update_xaxes(tickformat="%m/%Y", dtick="M1")
    painel.grafico(painel.layout(fig, "Consumo mensal por setor", 360, "kg"), "vg_mensal")
with col_b:
    part = indicadores.participacao(df, ctx.preco).sort_values("consumo_kg")
    fig = go.Figure(go.Bar(
        y=part["nome"], x=part["participacao_pct"], orientation="h",
        marker=dict(color=[painel.cor_setor(s) for s in part.index]),
        text=[painel.pct(v) for v in part["participacao_pct"]], textposition="outside",
        customdata=part[["consumo_kg", "custo_r"]],
        hovertemplate="%{y}<br>%{x:.1f} %<br>%{customdata[0]:,.0f} kg"
                      "<br>R$ %{customdata[1]:,.0f}<extra></extra>"))
    fig.update_xaxes(range=[0, max(part["participacao_pct"]) * 1.25], ticksuffix=" %")
    painel.grafico(painel.layout(fig, "Participação no consumo", 360, legenda=False), "vg_part")

# Evolução diária -----------------------------------------------------------
diario = df.groupby(df["data"].dt.normalize())["consumo_kg"].sum().rename("kg").to_frame()
diario = diario.reindex(pd.date_range(diario.index.min(), diario.index.max()), fill_value=0.0)
diario["media7"] = diario["kg"].rolling(7, min_periods=1).mean()
diario = diario.rename_axis("data").reset_index()
fig = painel.linha_tempo(
    diario, "data", {"kg": ("Consumo diário", "#b7d3f6"), "media7": ("Média móvel de 7 dias", painel.COR_PRIMARIA)},
    "Evolução do consumo diário total", "kg/dia",
    marcas=[(i["data_inicio"], i["id"]) for _, i in ctx.intervencoes.iterrows()
            if ctx.inicio <= pd.Timestamp(i["data_inicio"]).date() <= ctx.fim])
painel.grafico(fig, "vg_diario")

# Alertas -------------------------------------------------------------------------
st.subheader("Alertas de consumo fora do padrão")
estoque_inicial = ctx.parametros["reservatorio"].get("estoque_inicial_kg", 5000.0)
lista = alertas.gerar_alertas(df, ctx.parametros, ctx.abastecimentos, estoque_inicial, ctx.preco,
                              dados_reservatorio=ctx.todos)
if lista.empty:
    painel.alerta("bom", "Nenhum consumo fora do padrão detectado no período.")
else:
    contagem = lista["nivel"].value_counts()
    st.caption(f"{len(lista)} alerta(s): " + ", ".join(
        f"{contagem.get(n, 0)} {painel.ROTULO_NIVEL[n].lower()}" for n in ("critico", "serio", "atencao")
        if contagem.get(n)) + ". Alertas são indícios para investigação, não conclusões.")
    for _, a in lista.head(8).iterrows():
        painel.alerta(a["nivel"], f"{a['data']:%d/%m/%Y} · {a['setor']} — {a['mensagem']}")
    if len(lista) > 8:
        with st.expander(f"Ver todos os {len(lista)} alertas"):
            st.dataframe(lista.assign(data=lista["data"].dt.strftime("%d/%m/%Y")),
                         hide_index=True, width="stretch")
painel.nota_responsabilidade()
