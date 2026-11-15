"""Página: Monitoramento virtual do reservatório."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from src import painel, reservatorio  # noqa: E402

ctx = painel.contexto()
painel.cabecalho("Reservatório", ctx, "Estoque estimado, autonomia e abastecimentos.")
st.info("**Monitoramento VIRTUAL.** Sem sensor de nível integrado, o estoque é estimado por "
        "balanço de massa: estoque anterior + abastecimentos (notas fiscais) − consumo medido "
        "(Equação 25). Não substitui a leitura do indicador do tanque.", icon=":material/sensors_off:")

pr = dict(ctx.parametros["reservatorio"])
with st.expander(f"Parâmetros do tanque — origem: {pr['origem']}", expanded=False, icon=":material/tune:"):
    st.caption(pr["nota"])
    c = st.columns(5)
    pr["capacidade_nominal_kg"] = c[0].number_input("Capacidade nominal (kg)", min_value=1.0,
                                                    value=float(pr["capacidade_nominal_kg"]), step=100.0)
    pr["fracao_maxima_enchimento"] = c[1].number_input(
        "Limite de enchimento (fração)", min_value=0.1, max_value=1.0,
        value=float(pr["fracao_maxima_enchimento"]), step=0.01,
        help="Conforme fabricante, distribuidora e norma aplicável. Não confundir com a capacidade nominal.")
    pr["estoque_minimo_reserva_kg"] = c[2].number_input("Reserva mínima (kg)", min_value=0.0,
                                                        value=float(pr["estoque_minimo_reserva_kg"]), step=100.0)
    pr["nivel_alerta_percentual"] = c[3].number_input("Alerta de nível (%)", min_value=0.0, max_value=100.0,
                                                      value=float(pr["nivel_alerta_percentual"]))
    estoque_inicial = c[4].number_input("Estoque no início do histórico (kg)", min_value=0.0,
                                        value=float(pr.get("estoque_inicial_kg", 0.0)), step=100.0)

todos = ctx.todos
if todos.empty:
    painel.sem_dados()
    st.stop()
consumo = todos.groupby(todos["data"].dt.normalize())["consumo_kg"].sum()
estado = reservatorio.balanco_massa(consumo, ctx.abastecimentos, estoque_inicial, pr["capacidade_nominal_kg"])
ultimo = estado.iloc[-1]
media30 = consumo.tail(30).mean()
aut = reservatorio.autonomia_dias(ultimo["estoque_kg"], pr["estoque_minimo_reserva_kg"], media30)
ultimo_abast = pd.to_datetime(ctx.abastecimentos["data"]).max() if len(ctx.abastecimentos) else None
desde = estado.loc[estado.index > ultimo_abast, "consumo_kg"].sum() if ultimo_abast is not None else estado["consumo_kg"].sum()

c = st.columns(5)
c[0].metric("Estoque (kg)", painel.num(ultimo["estoque_kg"]), border=True,
            help=f"Em {estado.index[-1]:%d/%m/%Y}.")
c[1].metric("Nível estimado", painel.pct(ultimo["percentual"], 0), border=True,
            help="Estoque / capacidade nominal configurada.")
c[2].metric("Autonomia (dias)", painel.num(aut, 1), border=True,
            help="(estoque − reserva mínima) / consumo médio dos últimos 30 dias (Equação 26).")
c[3].metric("Desde o abastec. (kg)", painel.num(desde), border=True,
            help="Consumo acumulado desde o último abastecimento.")
c[4].metric("Média 30 dias (kg/dia)", painel.num(media30, 0), border=True)

for a in reservatorio.alertas(estado, pr, media30):
    painel.alerta(a["nivel"], a["mensagem"])

limite = pr["capacidade_nominal_kg"] * pr["fracao_maxima_enchimento"]
alerta_kg = pr["capacidade_nominal_kg"] * pr["nivel_alerta_percentual"] / 100
fig = go.Figure()
fig.add_trace(go.Scatter(x=estado.index, y=estado["estoque_kg"], name="Estoque estimado", mode="lines",
                         line=dict(color=painel.COR_PRIMARIA, width=2),
                         hovertemplate="%{x|%d/%m/%Y}<br>%{y:,.0f} kg<extra></extra>"))
abast = estado[estado["abastecimento_kg"] > 0]
fig.add_trace(go.Scatter(x=abast.index, y=abast["estoque_kg"], name="Abastecimento", mode="markers",
                         marker=dict(size=9, color=painel.cor_setor("CHUVEIROS"), symbol="triangle-up",
                                     line=dict(color=painel.SUPERFICIE, width=1)),
                         customdata=abast[["abastecimento_kg"]],
                         hovertemplate="%{x|%d/%m/%Y}<br>+%{customdata[0]:,.0f} kg<extra></extra>"))
for y, texto in ((limite, "Limite de enchimento configurado"), (alerta_kg, "Nível de alerta"),
                 (pr["estoque_minimo_reserva_kg"], "Reserva mínima")):
    fig.add_hline(y=y, line_color=painel.TEXTO_SEC, line_width=1,
                  annotation_text=texto, annotation_position="top left",
                  annotation_font=dict(size=11, color=painel.TEXTO_SEC))
painel.grafico(painel.layout(fig, "Estoque estimado no tanque", 380, "kg de GLP"), "res_estoque")

col_a, col_b = st.columns([3, 2])
with col_a:
    st.subheader("Histórico de abastecimento")
    if len(ctx.abastecimentos):
        st.dataframe(ctx.abastecimentos.drop(columns=[c for c in ("id",) if c in ctx.abastecimentos.columns]),
                     hide_index=True, width="stretch", column_config={
                         "data": "Data", "massa_kg": st.column_config.NumberColumn("Massa (kg)", format="%.1f"),
                         "preco_r_kg": st.column_config.NumberColumn("Preço (R$/kg)", format="%.2f"),
                         "nota_fiscal": "Nota fiscal",
                         "nivel_antes_pct": st.column_config.NumberColumn("Nível lido antes (%)", format="%.1f"),
                         "origem": "Origem"})
    else:
        painel.sem_dados("Nenhum abastecimento registrado.")
with col_b:
    st.subheader("Conciliação com o indicador do tanque")
    conc = reservatorio.conciliacao(estado, ctx.abastecimentos, pr["capacidade_nominal_kg"])
    if len(conc):
        fig = go.Figure(go.Bar(x=conc["data"], y=conc["diferenca_kg"], marker_color=painel.COR_NEUTRA,
                               hovertemplate="%{x|%d/%m/%Y}<br>%{y:,.0f} kg<extra></extra>"))
        painel.grafico(painel.layout(fig, "Leitura do indicador − estoque estimado", 300, "kg", legenda=False),
                       "res_conc")
        st.caption("Diferenças pequenas e sem tendência são esperadas (erro de leitura). Uma "
                   "diferença negativa crescente indica consumo não medido ou perda e deve ser "
                   "investigada por profissional habilitado.")
    else:
        painel.sem_dados("Sem leituras do indicador de nível nos abastecimentos.")
