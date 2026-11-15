"""Página: Análise dos chuveiros e do aquecimento de água."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from src import chuveiros, estatistica, painel  # noqa: E402
from src.constantes import CHUVEIROS  # noqa: E402

ctx = painel.contexto()
painel.cabecalho("Chuveiros", ctx, "Consumo por usuário, perfil horário, perdas em espera e demanda térmica.")
if ctx.dados[ctx.dados["setor"] == CHUVEIROS].empty:
    painel.sem_dados()
    st.stop()

pc = ctx.parametros["chuveiros"]
d = chuveiros.diario(ctx.dados, ctx.preco)
estim = chuveiros.demanda_termica_estimada(d, pc)
meses = max(d["data"].dt.to_period("M").nunique(), 1)
total = d["consumo_kg"].sum()

c = st.columns(5)
c[0].metric("Média (kg/dia)", painel.num(d["consumo_kg"].mean(), 1), border=True)
c[1].metric("Por usuário (g)", painel.num(total / d["usuarios"].sum() * 1000, 0), border=True,
            help="Razão das somas no período.")
c[2].metric("Custo mensal médio", painel.reais(total * ctx.preco / meses, 0), border=True)
c[3].metric("Consumo sem uso", painel.pct(d["kg_sem_uso"].sum() / total * 100), border=True,
            help="Parcela do GLP consumida em horas sem usuários: perdas do reservatório e da "
                 "tubulação ou aquecedor ligado fora do horário.")
c[4].metric("Demanda útil (kWh/dia)", painel.num(estim["demanda_util_kwh"].mean(), 1),
            border=True, help="Estimativa HIPOTÉTICA: usuários registrados × duração × vazão × ΔT "
                              "(parâmetros em config/parametros.toml).")

col_a, col_b = st.columns(2)
with col_a:
    perfil = chuveiros.perfil_horario(ctx.dados)
    fig = go.Figure(go.Bar(x=perfil["hora"], y=perfil["kg_medio"], marker_color=painel.cor_setor(CHUVEIROS),
                           customdata=perfil[["usuarios_medios"]],
                           hovertemplate="%{x}h<br>%{y:.2f} kg<br>%{customdata[0]:.0f} usuários<extra></extra>"))
    fig.update_xaxes(dtick=2, range=[-0.5, 23.5])
    painel.grafico(painel.layout(fig, "Perfil horário médio", 340, "kg por hora", "hora do dia",
                                 legenda=False), "ch_hora")
with col_b:
    serie = d.assign(media=d["kg_sem_uso"].rolling(7, min_periods=1).mean())
    marcas = [(i["data_inicio"], i["id"]) for _, i in ctx.intervencoes.iterrows()
              if i["setor"] == CHUVEIROS]
    fig = painel.linha_tempo(serie, "data", {"consumo_kg": ("Consumo total", painel.cor_setor(CHUVEIROS)),
                                             "kg_sem_uso": ("Consumo em horas sem uso", painel.COR_NEUTRA)},
                             "Consumo diário total e em horas sem uso", "kg/dia", marcas=marcas, altura=340)
    painel.grafico(fig, "ch_serie")

col_a, col_b = st.columns(2)
with col_a:
    uteis = d[d["data"].dt.dayofweek < 5]
    fig = go.Figure(go.Scatter(x=uteis["temp_entrada_c"], y=uteis["consumo_kg"] - uteis["kg_sem_uso"],
                               mode="markers", marker=dict(size=8, color=painel.cor_setor(CHUVEIROS), opacity=0.7,
                                                           line=dict(color=painel.SUPERFICIE, width=1)),
                               hovertemplate="%{x:.1f} °C<br>%{y:.1f} kg<extra></extra>"))
    painel.grafico(painel.layout(fig, "Consumo nos banhos × temperatura da água de entrada (dias úteis)",
                                 340, "kg/dia em horas com uso", "temperatura de entrada (°C)", legenda=False),
                   "ch_temp")
    if uteis["temp_entrada_c"].notna().sum() >= 3:
        corr = estatistica.correlacao(uteis["temp_entrada_c"], uteis["consumo_kg"] - uteis["kg_sem_uso"])
        st.caption(f"Pearson r = {painel.num(corr['pearson_r'], 2)} (p = {corr['pearson_p']:.2g}); "
                   f"Spearman ρ = {painel.num(corr['spearman_rho'], 2)}. Água mais fria na entrada exige "
                   "mais energia por banho (Equação 10). Correlação não prova causa.")
with col_b:
    fig = painel.linha_tempo(estim, "data", {"consumo_kg": ("Consumo registrado", painel.cor_setor(CHUVEIROS)),
                                             "glp_teorico_kg": ("GLP teórico dos banhos (hipótese)", painel.TEXTO_SEC)},
                             "Consumo registrado × GLP teórico dos banhos", "kg/dia", altura=340)
    painel.grafico(fig, "ch_teorico")
    st.caption("A diferença inclui perdas em espera e erros das hipóteses de duração, vazão e "
               "rendimento. Com medições reais, ela estima as perdas do sistema.")

st.subheader("Calculadora de demanda (hipóteses editáveis)")
st.caption("Estimativa pelas Equações 10 a 12 do relatório. Os valores iniciais vêm de "
           f"config/parametros.toml (origem: {pc['origem']}) e não descrevem a empresa.")
c = st.columns(6)
usuarios = c[0].number_input("Banhos por dia", min_value=0, value=int(d["usuarios"].mean()))
duracao = c[1].number_input("Duração (min)", min_value=0.0, value=float(pc["duracao_banho_min"]))
vazao = c[2].number_input("Vazão (L/min)", min_value=0.0, value=float(pc["vazao_l_min"]))
t_entrada = c[3].number_input("Água de entrada (°C)", value=round(float(d["temp_entrada_c"].mean()), 1))
t_saida = c[4].number_input("Água de saída (°C)", value=float(pc["temperatura_saida_c"]))
rendimento = c[5].number_input("Rendimento", min_value=0.05, max_value=1.0, value=float(pc["rendimento_aquecedor"]))
volume = chuveiros.volume_diario_l(usuarios, duracao, vazao)
q = chuveiros.calor_aquecimento_kj(volume, t_saida - t_entrada)
kg = chuveiros.glp_para_calor_kg(q, rendimento)
c = st.columns(4)
c[0].metric("Água quente (L/dia)", painel.num(volume), border=True)
c[1].metric("Calor útil (kWh/dia)", painel.num(q / 3600, 1), border=True)
c[2].metric("GLP estimado (kg/dia)", painel.num(kg, 1), border=True)
c[3].metric("Custo estimado (por mês)", painel.reais(kg * ctx.preco * 30, 0), border=True,
            help="30 dias de uso.")
painel.nota_responsabilidade()
