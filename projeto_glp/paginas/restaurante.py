"""Página: Análise do restaurante industrial."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from src import painel, restaurante  # noqa: E402
from src.constantes import RESTAURANTE  # noqa: E402

ctx = painel.contexto()
painel.cabecalho("Restaurante", ctx, "Consumo por refeição, parcela fixa diária e perfis de uso.")
if ctx.dados[ctx.dados["setor"] == RESTAURANTE].empty:
    painel.sem_dados()
    st.stop()

pr = ctx.parametros["restaurante"]
d = restaurante.diario(ctx.dados, ctx.preco)
producao = d[d["refeicoes"] > 0]
kg_total, ref_total = producao["consumo_kg"].sum(), producao["refeicoes"].sum()
meses = max(d["data"].dt.to_period("M").nunique(), 1)

try:
    modelo = restaurante.modelo_consumo(d)
except ValueError:
    modelo = None

c = st.columns(5)
c[0].metric("Média (kg/dia)", painel.num(producao["consumo_kg"].mean(), 1), border=True,
            help="Média dos dias com refeições produzidas.")
c[1].metric("Por refeição (g)", painel.num(kg_total / ref_total * 1000, 0), border=True,
            help="Razão das somas no período (kg/refeição × 1000).")
c[2].metric("Custo por refeição", painel.reais(kg_total / ref_total * ctx.preco, 3), border=True)
c[3].metric("Média mensal (kg)", painel.num(d["consumo_kg"].sum() / meses, 0), border=True)
c[4].metric("Parcela fixa β₀ (kg/dia)",
            painel.num(modelo.coeficientes.loc["intercepto", "coef"], 1) if modelo else "—",
            border=True, help="Consumo que não depende do número de refeições (Equação 8).")

col_a, col_b = st.columns(2)
with col_a:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=producao["refeicoes"], y=producao["consumo_kg"], mode="markers",
                             name="Dias", marker=dict(size=8, color=painel.COR_SECUNDARIA, opacity=0.75,
                                                      line=dict(color=painel.SUPERFICIE, width=1)),
                             customdata=producao["data"].dt.strftime("%d/%m/%Y"),
                             hovertemplate="%{customdata}<br>%{x:.0f} refeições<br>%{y:.1f} kg<extra></extra>"))
    if modelo:
        x = np.linspace(producao["refeicoes"].min(), producao["refeicoes"].max(), 50)
        prev = modelo.prever({"refeicoes": x})
        fig.add_trace(go.Scatter(x=x, y=prev["previsto"], mode="lines", name="Modelo (Equação 8)",
                                 line=dict(color=painel.TEXTO, width=2)))
        fig.add_trace(go.Scatter(x=np.concatenate([x, x[::-1]]),
                                 y=np.concatenate([prev["pi_sup"], prev["pi_inf"][::-1]]),
                                 fill="toself", fillcolor="rgba(82,81,78,0.12)", line=dict(width=0),
                                 name="Intervalo de predição 95 %", hoverinfo="skip"))
    painel.grafico(painel.layout(fig, "Consumo diário × refeições", 360, "kg/dia", "refeições no dia"),
                   "rest_disp")
    if modelo:
        b0 = modelo.coeficientes.loc["intercepto", "coef"]
        b1 = modelo.coeficientes.loc["refeicoes", "coef"]
        st.caption(f"G = {painel.num(b0, 2)} + {painel.num(b1 * 1000, 1)} g × refeições · "
                   f"R² ajustado = {painel.num(modelo.r2_ajustado, 3)} · n = {modelo.n} dias")
with col_b:
    faixas = restaurante.por_faixa(d, pr["faixas_refeicoes"])
    fig = go.Figure(go.Bar(
        x=faixas.index, y=faixas["kg_por_refeicao_medio"] * 1000, marker_color=painel.COR_SECUNDARIA,
        customdata=faixas[["dias"]],
        hovertemplate="%{x} refeições<br>%{y:.1f} g/refeição<br>%{customdata[0]} dias<extra></extra>"))
    painel.grafico(painel.layout(fig, "Consumo por refeição, por faixa de volume", 360,
                                 "g de GLP por refeição", "refeições no dia", legenda=False), "rest_faixa")
    st.caption("O consumo por refeição cai quando o volume sobe (Equação 9), porque a parcela fixa "
               "é dividida por mais refeições. Compare dias da mesma faixa.")

col_a, col_b = st.columns(2)
with col_a:
    semana = restaurante.por_dia_semana(d)
    fig = go.Figure(go.Bar(x=semana.index, y=semana["kg_dia_medio"], marker_color=painel.COR_SECUNDARIA,
                           customdata=semana[["refeicoes_media"]],
                           hovertemplate="%{x}<br>%{y:.1f} kg/dia<br>%{customdata[0]:.0f} refeições<extra></extra>"))
    painel.grafico(painel.layout(fig, "Consumo médio por dia da semana", 320, "kg/dia", legenda=False), "rest_semana")
with col_b:
    perfil = restaurante.perfil_horario(ctx.dados)
    if len(perfil):
        fig = go.Figure(go.Bar(x=perfil["hora"], y=perfil["kg_medio"], marker_color=painel.COR_SECUNDARIA,
                               customdata=perfil[["refeicoes_medias"]],
                               hovertemplate="%{x}h<br>%{y:.2f} kg<br>%{customdata[0]:.0f} refeições<extra></extra>"))
        fig.add_vrect(x0=-0.5, x1=pr["hora_abertura"] - 0.5, fillcolor="rgba(138,137,133,0.12)", line_width=0)
        fig.add_vrect(x0=pr["hora_fechamento"] - 0.5, x1=23.5, fillcolor="rgba(138,137,133,0.12)", line_width=0)
        fig.update_xaxes(dtick=2, range=[-0.5, 23.5])
        painel.grafico(painel.layout(fig, "Perfil horário médio (cinza: cozinha fechada)", 320,
                                     "kg por hora", "hora do dia", legenda=False), "rest_hora")
    else:
        painel.sem_dados("Sem registros horários para montar o perfil.")

st.subheader("Consumo fora do horário de funcionamento")
fora = restaurante.fora_do_horario(ctx.dados, pr["hora_abertura"], pr["hora_fechamento"])
if fora.empty:
    painel.alerta("bom", f"Nenhum consumo registrado entre {pr['hora_fechamento']}h e {pr['hora_abertura']}h.")
else:
    painel.alerta("critico", f"{len(fora)} dia(s) com consumo com a cozinha fechada, total de "
                  f"{painel.num(fora['kg_fora_horario'].sum(), 1)} kg. Verificar queimadores acesos e "
                  "possíveis vazamentos (profissional habilitado).")
    st.dataframe(fora.assign(data=fora["data"].dt.strftime("%d/%m/%Y")), hide_index=True,
                 column_config={"data": "Data", "kg_fora_horario": st.column_config.NumberColumn(
                     "kg fora do horário", format="%.2f")})

with st.expander("Dados diários", icon=":material/table:"):
    st.dataframe(d.assign(data=d["data"].dt.strftime("%d/%m/%Y")), hide_index=True, width="stretch")
    painel.baixar_csv(d, "restaurante_diario.csv")
painel.nota_responsabilidade()
