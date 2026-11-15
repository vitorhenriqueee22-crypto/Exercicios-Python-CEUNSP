"""Página: Análise da fundição."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from src import estatistica, fundicao, painel  # noqa: E402
from src.constantes import FUNDICAO  # noqa: E402

ctx = painel.contexto()
painel.cabecalho("Fundição", ctx, "Consumo por forno, consumo específico, tempo sem carga e eficiência estimada.")
df = ctx.dados[ctx.dados["setor"] == FUNDICAO]
if df.empty:
    painel.sem_dados()
    st.stop()

equip = ctx.equipamentos[ctx.equipamentos["setor"] == FUNDICAO]
tabela = fundicao.indicadores_por_forno(df, ctx.preco, equip)
diario = fundicao.diario_fornos(df)

with st.expander("Cadastro de fornos", icon=":material/list_alt:"):
    st.caption("Cada forno é analisado separadamente: fusão, espera e tratamento térmico "
               "funcionam de formas diferentes.")
    st.dataframe(equip.drop(columns=["setor"]), hide_index=True, width="stretch")

fornos = list(tabela.index)
rotulo = {f: f"{f} — {tabela.at[f, 'nome']}" if "nome" in tabela.columns else f for f in fornos}
forno = st.segmented_control("Forno", fornos, default=fornos[0], format_func=lambda f: rotulo[f],
                             key="fund_forno") or fornos[0]
t = tabela.loc[forno]
funcao = str(t.get("funcao", ""))

c = st.columns(6)
c[0].metric("kg por hora", painel.num(t["kg_por_h"], 1), border=True, help="Consumo / horas de forno ligado.")
c[1].metric("kg por tonelada", painel.num(t["kg_por_t"], 1), border=True,
            help="Consumo / toneladas processadas no forno.")
c[2].metric("kg por ciclo", painel.num(t["kg_por_ciclo"], 1), border=True)
c[3].metric("R$ por tonelada", painel.reais(t["r_por_t"], 0), border=True)
c[4].metric("Sem carga", painel.pct(t["fracao_sem_carga_pct"]), border=True,
            help="Horas ligado sem carga produtiva / horas ligado.")
c[5].metric("Sem produção", f"{painel.num(t['kg_dias_sem_producao'])} kg", border=True,
            help="Consumo em dias com o forno aquecido e nenhuma tonelada registrada.")

d = diario[diario["equipamento_id"] == forno].sort_values("data")
producao = d[d["metal_t"].fillna(0) > 0].copy()
intervencoes = ctx.intervencoes[ctx.intervencoes["equipamento_id"] == forno]

col_a, col_b = st.columns(2)
with col_a:
    if len(producao):
        producao["media14"] = producao["kg_por_t"].rolling(14, min_periods=3).mean()
        fig = painel.linha_tempo(
            producao, "data", {"kg_por_t": ("kg/t diário", "#b7d3f6"),
                               "media14": ("Média móvel de 14 dias de produção", painel.COR_PRIMARIA)},
            "Consumo específico (kg de GLP por tonelada)", "kg/t",
            marcas=[(i["data_inicio"], i["id"]) for _, i in intervencoes.iterrows()])
        painel.grafico(fig, "fund_kgt")
    else:
        painel.sem_dados("Este forno não registrou toneladas processadas no período.")
with col_b:
    fig = go.Figure(go.Scatter(
        x=d["data"], y=d["consumo_kg"], mode="markers",
        marker=dict(size=8, color=np.where(d["metal_t"].fillna(0) > 0, painel.COR_PRIMARIA, painel.COR_STATUS["serio"]),
                    line=dict(color=painel.SUPERFICIE, width=1)),
        customdata=d[["metal_t", "horas"]],
        hovertemplate="%{x|%d/%m/%Y}<br>%{y:.1f} kg<br>%{customdata[0]:.2f} t · %{customdata[1]:.1f} h<extra></extra>"))
    painel.grafico(painel.layout(fig, "Consumo diário (laranja: sem produção registrada)", 340, "kg/dia",
                                 legenda=False), "fund_diario")

# Modelo da Equação 7 ------------------------------------------------------------
st.subheader("Modelo de consumo do forno")
st.markdown("Equação 7 do relatório: **G = β₀ + β₁·horas + β₂·toneladas + ε**. "
            "β₁ estima o consumo por hora ligado (perdas e manutenção de temperatura); "
            "β₂, o consumo marginal por tonelada.")
try:
    modelo = fundicao.modelo_consumo(producao if len(producao) else d)
except ValueError as erro:
    painel.sem_dados(f"Modelo não ajustado: {erro}")
else:
    col_a, col_b = st.columns([3, 2])
    with col_a:
        x_var = "metal_t" if "metal_t" in modelo.variaveis else modelo.variaveis[0]
        base = producao if len(producao) else d
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=base[x_var], y=base["consumo_kg"], mode="markers", name="Dias",
                                 marker=dict(size=8, color=painel.COR_PRIMARIA, opacity=0.7,
                                             line=dict(color=painel.SUPERFICIE, width=1))))
        fig.add_trace(go.Scatter(x=base.loc[modelo.ajustados.index, x_var], y=modelo.ajustados,
                                 mode="markers", name="Ajustado pelo modelo",
                                 marker=dict(size=8, color=painel.TEXTO_SEC, symbol="x")))
        painel.grafico(painel.layout(fig, "Consumo observado × ajustado", 340, "kg/dia",
                                     "toneladas no dia" if x_var == "metal_t" else "horas ligado"), "fund_modelo")
    with col_b:
        coef = modelo.coeficientes.rename(index={"horas": "horas (β₁)", "metal_t": "toneladas (β₂)",
                                                 "intercepto": "intercepto (β₀)"})
        st.dataframe(coef.style.format({"coef": "{:.3f}", "erro_padrao": "{:.3f}", "t": "{:.2f}",
                                        "p_valor": "{:.3g}", "ic95_inf": "{:.3f}", "ic95_sup": "{:.3f}"}),
                     width="stretch")
        st.markdown(f"R² ajustado = **{painel.num(modelo.r2_ajustado, 3)}** · "
                    f"Durbin-Watson = **{painel.num(modelo.durbin_watson, 2)}** · n = {modelo.n}")
        if len(modelo.variaveis) > 1:
            vif = estatistica.fator_inflacao_variancia(base, modelo.variaveis)
            if (vif > 5).any():
                st.warning(f"Horas e toneladas são fortemente correlacionadas (VIF = "
                           f"{painel.num(vif.max(), 1)}): os coeficientes individuais ficam imprecisos, "
                           "embora a previsão do consumo continue válida. Registrar o tempo sem carga "
                           "separadamente melhora a separação das parcelas.", icon=":material/warning:")
        if modelo.durbin_watson < 1.5 or modelo.durbin_watson > 2.5:
            st.caption("Durbin-Watson distante de 2: resíduos autocorrelacionados; "
                       "valores p tendem a ser otimistas.")

# Eficiência estimada --------------------------------------------------------------
st.subheader("Eficiência térmica estimada")
if funcao.lower() != "fusão":
    st.caption(f"A eficiência pela Equação 6 só se aplica a fornos de fusão. Função deste forno: {funcao or '—'}.")
else:
    liga = dict(ctx.parametros["fundicao"]["liga"])
    with st.expander(f"Propriedades da liga — origem: {liga['origem']}", icon=":material/tune:"):
        st.caption(liga.get("nota", ""))
        c = st.columns(5)
        liga["calor_especifico_solido_kj_kgk"] = c[0].number_input("cₛ sólido (kJ/kg·K)", value=liga["calor_especifico_solido_kj_kgk"], format="%.3f")
        liga["calor_especifico_liquido_kj_kgk"] = c[1].number_input("cₗ líquido (kJ/kg·K)", value=liga["calor_especifico_liquido_kj_kgk"], format="%.3f")
        liga["calor_latente_fusao_kj_kg"] = c[2].number_input("L_f (kJ/kg)", value=liga["calor_latente_fusao_kj_kg"])
        liga["temperatura_fusao_c"] = c[3].number_input("T_fusão (°C)", value=liga["temperatura_fusao_c"])
        liga["temperatura_inicial_c"] = c[4].number_input("T_inicial (°C)", value=liga["temperatura_inicial_c"])
    eta = fundicao.eficiencia_estimada(producao, liga)
    if len(eta):
        c1, c2 = st.columns([1, 3])
        c1.metric("Eficiência média estimada", painel.pct(eta.mean() * 100), border=True,
                  help="η = Q_útil / (m_GLP · PCI). Resultado HIPOTÉTICO enquanto as propriedades "
                       "da liga não vierem da ficha técnica.")
        c2.info("A eficiência herda a origem mais fraca das entradas: com propriedades de liga "
                f"marcadas como {liga['origem']} e dados {ctx.origem}, o resultado é "
                f"**{'SIMULADO' if ctx.simulado else 'HIPOTÉTICO'}** e serve apenas como ordem de grandeza.",
                icon=":material/science:")
    else:
        painel.sem_dados("Sem dias com toneladas e temperatura registradas para estimar a eficiência.")

st.subheader("Comparação entre fornos")
mostrar = tabela.reset_index()[["equipamento_id", "nome", "funcao", "dias_operacao", "consumo_kg",
                                "metal_t", "horas", "kg_por_h", "kg_por_t", "kg_por_ciclo", "r_por_t",
                                "fracao_sem_carga_pct", "kg_dias_sem_producao"]]
st.dataframe(mostrar, hide_index=True, width="stretch", column_config={
    "equipamento_id": "Forno", "nome": "Nome", "funcao": "Função", "dias_operacao": "Dias",
    "consumo_kg": st.column_config.NumberColumn("Consumo (kg)", format="%.0f"),
    "metal_t": st.column_config.NumberColumn("Metal (t)", format="%.1f"),
    "horas": st.column_config.NumberColumn("Horas", format="%.0f"),
    "kg_por_h": st.column_config.NumberColumn("kg/h", format="%.2f"),
    "kg_por_t": st.column_config.NumberColumn("kg/t", format="%.1f"),
    "kg_por_ciclo": st.column_config.NumberColumn("kg/ciclo", format="%.1f"),
    "r_por_t": st.column_config.NumberColumn("R$/t", format="%.0f"),
    "fracao_sem_carga_pct": st.column_config.NumberColumn("Sem carga (%)", format="%.1f"),
    "kg_dias_sem_producao": st.column_config.NumberColumn("kg sem produção", format="%.0f"),
})
st.caption("O kg/t de fornos com funções diferentes não é comparável: o forno de espera e o de "
           "tratamento térmico processam o mesmo metal já fundido.")
painel.baixar_csv(mostrar, "indicadores_fornos.csv")
painel.nota_responsabilidade()
