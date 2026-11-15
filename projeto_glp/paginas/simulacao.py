"""Página: Simulação de economia."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from src import indicadores, painel, simulacao  # noqa: E402
from src.constantes import SETORES  # noqa: E402

ctx = painel.contexto()
painel.cabecalho("Simulação de economia", ctx, "Quanto valeria reduzir o consumo em diferentes percentuais.")
st.error("**SIMULAÇÃO.** Os valores abaixo respondem a \"quanto valeria uma redução de r %\". "
         "Não são economias alcançadas. Uma economia só é considerada verificada após a comparação "
         "com a linha de base e o teste estatístico (página *Análise estatística*).",
         icon=":material/calculate:")

df = ctx.dados
diario = indicadores.diario(df)
opcoes = ["TOTAL"] + [s for s in SETORES if s in set(diario["setor"])]
geral = ctx.parametros["geral"]

c = st.columns(4)
setor = c[0].selectbox("Escopo", opcoes, format_func=lambda s: "Empresa (total)" if s == "TOTAL"
                       else painel.nome_setor(s))
base = diario if setor == "TOTAL" else diario[diario["setor"] == setor]
por_dia = base.groupby("data")["consumo_kg"].sum()
dias_operacao = por_dia[por_dia > 0]
consumo_padrao = float(dias_operacao.mean()) if len(dias_operacao) else 0.0
consumo = c[1].number_input("Consumo atual (kg/dia de operação)", min_value=0.0,
                            value=round(consumo_padrao, 1), step=1.0,
                            help="Média dos dias com consumo no período filtrado.")
preco = c[2].number_input("Preço do GLP (R$/kg)", min_value=0.0, value=float(ctx.preco), step=0.1, format="%.2f")
reducoes = c[3].multiselect("Reduções (%)", [3, 5, 8, 10, 15, 20, 25], default=[3, 5, 8, 10, 15])

c = st.columns(4)
dias_mes = c[0].number_input("Dias de operação por mês", min_value=1, max_value=31, value=int(geral["dias_operacao_mes"]))
dias_ano = c[1].number_input("Dias de operação por ano", min_value=1, max_value=366, value=int(geral["dias_operacao_ano"]))
atividade = None
if setor != "TOTAL":
    ativ_dia = base.groupby("data")["atividade"].sum()
    ativ_padrao = float(ativ_dia[ativ_dia > 0].mean()) if (ativ_dia > 0).any() else 0.0
    atividade = c[2].number_input("Atividade diária (produção, refeições ou usuários)", min_value=0.0,
                                  value=round(ativ_padrao, 2)) or None
investimento = c[3].number_input("Investimento da melhoria (R$, opcional)", min_value=0.0, value=0.0, step=1000.0)

if not reducoes:
    st.info("Escolha ao menos um percentual de redução.")
    st.stop()
cen = simulacao.cenarios_economia(consumo, preco, [r / 100 for r in sorted(reducoes)], dias_mes, dias_ano, atividade)
if investimento > 0:
    cen["retorno_simples_meses"] = [simulacao.retorno_simples_meses(investimento, e) for e in cen["economia_r_mes"]]

maior = cen.iloc[-1]
c = st.columns(4)
c[0].metric(f"GLP poupado em {painel.num(maior['reducao_pct'])} % (kg/ano)", painel.num(maior["glp_economizado_kg_ano"]), border=True)
c[1].metric("Economia diária", painel.reais(maior["economia_r_dia"]), border=True)
c[2].metric("Economia mensal", painel.reais_compacto(maior["economia_r_mes"]), border=True)
c[3].metric("Economia anual", painel.reais_compacto(maior["economia_r_ano"]), border=True)
st.caption("Indicadores acima referem-se ao maior percentual selecionado. Todos os valores são simulados.")

col_a, col_b = st.columns(2)
with col_a:
    fig = go.Figure(go.Bar(x=[f"{painel.num(r)} %" for r in cen["reducao_pct"]], y=cen["economia_r_ano"],
                           marker_color=painel.COR_PRIMARIA,
                           text=[painel.reais(v, 0) for v in cen["economia_r_ano"]], textposition="outside",
                           hovertemplate="%{x}<br>R$ %{y:,.0f}/ano<extra></extra>"))
    fig.update_yaxes(range=[0, cen["economia_r_ano"].max() * 1.2])
    fig.update_xaxes(type="category")
    painel.grafico(painel.layout(fig, "Economia anual simulada por cenário", 340, "R$/ano", "redução", False), "sim_bar")
with col_b:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[f"{painel.num(r)} %" for r in cen["reducao_pct"]], y=cen["consumo_atual_kg_dia"],
                         name="Atual", marker_color=painel.COR_NEUTRA))
    fig.add_trace(go.Bar(x=[f"{painel.num(r)} %" for r in cen["reducao_pct"]], y=cen["consumo_otimizado_kg_dia"],
                         name="Otimizado (simulado)", marker_color=painel.COR_PRIMARIA))
    fig.update_xaxes(type="category")
    painel.grafico(painel.layout(fig, "Consumo atual × otimizado", 340, "kg/dia", "redução"), "sim_comp")

st.dataframe(cen, hide_index=True, width="stretch", column_config={
    "reducao_pct": st.column_config.NumberColumn("Redução (%)", format="%.0f"),
    "consumo_atual_kg_dia": st.column_config.NumberColumn("Atual (kg/dia)", format="%.1f"),
    "consumo_otimizado_kg_dia": st.column_config.NumberColumn("Otimizado (kg/dia)", format="%.1f"),
    "glp_economizado_kg_dia": st.column_config.NumberColumn("Economia (kg/dia)", format="%.1f"),
    "glp_economizado_kg_mes": st.column_config.NumberColumn("Economia (kg/mês)", format="%.0f"),
    "glp_economizado_kg_ano": st.column_config.NumberColumn("Economia (kg/ano)", format="%.0f"),
    "economia_r_dia": st.column_config.NumberColumn("R$/dia", format="%.2f"),
    "economia_r_mes": st.column_config.NumberColumn("R$/mês", format="%.2f"),
    "economia_r_ano": st.column_config.NumberColumn("R$/ano", format="%.2f"),
    "consumo_especifico_atual": st.column_config.NumberColumn("Específico atual", format="%.4f"),
    "consumo_especifico_otimizado": st.column_config.NumberColumn("Específico otimizado", format="%.4f"),
    "retorno_simples_meses": st.column_config.NumberColumn("Retorno simples (meses)", format="%.1f"),
    "classificacao": "Classificação",
})
painel.baixar_csv(cen, "cenarios_economia_SIMULACAO.csv")
