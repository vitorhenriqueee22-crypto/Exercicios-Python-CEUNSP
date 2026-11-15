"""Página: Análise estatística."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402
from scipy import stats  # noqa: E402

from src import anomalias, estatistica, painel, relatorios  # noqa: E402
from src.constantes import FUNDICAO  # noqa: E402

ctx = painel.contexto()
painel.cabecalho("Análise estatística", ctx,
                 "Estatística descritiva, normalidade, avaliação de intervenções, correlação, regressão e anomalias.")
if ctx.simulado:
    st.caption(":material/science: Com dados simulados, os resultados demonstram os métodos; "
               "não são conclusões sobre a empresa.")

setores = [s for s in relatorios.VARIAVEIS if s in set(ctx.dados["setor"])]
if not setores:
    painel.sem_dados()
    st.stop()
c = st.columns(3)
setor = c[0].selectbox("Setor", setores, format_func=painel.nome_setor, key="est_setor")
equipamento = None
if setor == FUNDICAO:
    fornos = sorted(ctx.dados.loc[ctx.dados["setor"] == FUNDICAO, "equipamento_id"].dropna().unique())
    equipamento = c[1].selectbox("Forno", fornos, key="est_forno")
variaveis = relatorios.VARIAVEIS[setor]
d = relatorios.tabela_diaria(ctx.dados, setor, equipamento, ctx.preco)
metrica = c[2].selectbox("Variável analisada", list(variaveis), format_func=variaveis.get, key="est_metrica")
serie = d[["data", metrica]].dropna()
if setor == FUNDICAO and metrica in ("kg_por_t", "kg_por_h"):
    serie = serie[np.isfinite(serie[metrica])]
nome = variaveis[metrica]
cor = painel.cor_setor(setor)

aba_desc, aba_norm, aba_teste, aba_reg, aba_anom = st.tabs(
    ["Descritiva", "Normalidade", "Antes × depois", "Correlação e regressão", "Anomalias e CUSUM"])

# ----------------------------------------------------------------- descritiva
with aba_desc:
    if len(serie) == 0:
        painel.sem_dados("Sem valores para a variável escolhida.")
    else:
        desc = estatistica.descritiva(serie[metrica])
        rotulos = {"n": "n", "media": "Média", "mediana": "Mediana", "moda": "Moda",
                   "variancia": "Variância", "desvio_padrao": "Desvio-padrão", "minimo": "Mínimo",
                   "maximo": "Máximo", "q1": "1º quartil", "q3": "3º quartil",
                   "iqr": "Amplitude interquartil", "cv_percentual": "Coeficiente de variação (%)"}
        tabela = pd.DataFrame({"Estatística": [rotulos[k] for k in desc],
                               "Valor": ["—" if v is None else painel.num(v, 0 if k == "n" else 4)
                                         for k, v in desc.items()]})
        col_a, col_b = st.columns([1, 2])
        col_a.dataframe(tabela, hide_index=True, width="stretch")
        if desc["moda"] is None:
            col_a.caption("Moda não calculada: variável contínua sem valores repetidos.")
        with col_b:
            fig = go.Figure(go.Histogram(x=serie[metrica], marker=dict(color=cor, line=dict(color=painel.SUPERFICIE, width=1)),
                                         nbinsx=30, hovertemplate="%{x}<br>%{y} dias<extra></extra>"))
            painel.grafico(painel.layout(fig, f"Distribuição — {nome}", 300, "dias", nome, False), "est_hist")
            fig = go.Figure(go.Box(x=serie[metrica], marker_color=cor, boxpoints="outliers", name=""))
            painel.grafico(painel.layout(fig, None, 160, None, nome, False), "est_box")
        serie_mm = serie.assign(media=serie[metrica].rolling(14, min_periods=3).mean())
        fig = painel.linha_tempo(serie_mm, "data", {metrica: (nome, "#b7d3f6"),
                                                    "media": ("Média móvel de 14 registros", cor)},
                                 f"Evolução temporal — {nome}", nome)
        painel.grafico(fig, "est_serie")
        tend = estatistica.tendencia(serie.set_index("data")[metrica]) if len(serie) >= 3 else None
        if tend:
            direcao = "crescente" if tend["inclinacao_por_periodo"] > 0 else "decrescente"
            st.caption(f"Tendência linear {direcao} de {painel.num(tend['variacao_percentual_por_periodo'], 3)} % "
                       f"da média por registro (p = {tend['p_valor']:.2g}; "
                       f"{'significativa' if tend['significativa'] else 'não significativa'} a 5 %).")

# --------------------------------------------------------------- normalidade
with aba_norm:
    sw = estatistica.shapiro_wilk(serie[metrica])
    c = st.columns(3)
    c[0].metric("Estatística W", painel.num(sw.estatistica, 4), border=True)
    c[1].metric("Valor p", f"{sw.p_valor:.3g}" if np.isfinite(sw.p_valor) else "—", border=True)
    c[2].metric("Conclusão (α = 5 %)", "Normalidade aceita" if sw.normal else "Normalidade rejeitada", border=True)
    st.markdown("**H₀:** os dados seguem distribuição normal · **H₁:** não seguem (Shapiro; Wilk, 1965).")
    if sw.observacao:
        st.caption(sw.observacao)
    if sw.n >= 3:
        (teoricos, ordenados), (inclin, intercepto, _) = stats.probplot(serie[metrica], dist="norm")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=teoricos, y=ordenados, mode="markers", name="Observações",
                                 marker=dict(size=8, color=cor, opacity=0.7)))
        fig.add_trace(go.Scatter(x=teoricos, y=inclin * teoricos + intercepto, mode="lines",
                                 name="Referência normal", line=dict(color=painel.TEXTO, width=2)))
        painel.grafico(painel.layout(fig, "Gráfico quantil-quantil", 340, nome, "quantis teóricos da normal"), "est_qq")

# ------------------------------------------------------------- antes × depois
with aba_teste:
    modo = st.radio("Tipo de comparação", ["Períodos da série (amostras independentes)",
                                           "Dados pareados (digitar valores)"], horizontal=True, key="est_modo")
    metodo = st.radio("Escolha do teste", ["auto", "parametrico", "nao_parametrico"], horizontal=True,
                      format_func={"auto": "Automática (Quadro 8)", "parametrico": "Paramétrico",
                                   "nao_parametrico": "Não paramétrico"}.get, key="est_metodo")
    resultado, antes, depois = None, None, None
    if modo.startswith("Períodos"):
        intervs = ctx.intervencoes
        if equipamento:
            intervs = intervs[intervs["equipamento_id"] == equipamento]
        else:
            intervs = intervs[intervs["setor"] == setor]
        opcoes = ["Data escolhida"] + [f"{i['id']} — {i['descricao']} ({i['data_inicio']})"
                                       for _, i in intervs.iterrows()]
        c = st.columns(3)
        escolha = c[0].selectbox("Intervenção", opcoes, index=1 if len(opcoes) > 1 else 0, key="est_interv")
        if escolha == "Data escolhida":
            meio = serie["data"].iloc[len(serie) // 2] if len(serie) else pd.Timestamp(ctx.inicio)
            data_corte = pd.Timestamp(c[1].date_input("Data da mudança", value=meio.date(), format="DD/MM/YYYY"))
        else:
            data_corte = pd.Timestamp(intervs.iloc[opcoes.index(escolha) - 1]["data_inicio"])
            c[1].date_input("Data da mudança", value=data_corte.date(), disabled=True, format="DD/MM/YYYY")
        janela = c[2].number_input("Janela antes e depois (dias)", min_value=7, max_value=365, value=90)
        antes = serie[(serie["data"] < data_corte) & (serie["data"] >= data_corte - pd.Timedelta(days=janela))][metrica]
        depois = serie[(serie["data"] >= data_corte) & (serie["data"] < data_corte + pd.Timedelta(days=janela))][metrica]
        pareado = False
    else:
        st.caption("Use quando as observações forem pareadas: mesmo forno, mesma liga, cargas equivalentes "
                   "medidas antes e depois. Separe os valores por ponto e vírgula ou quebra de linha.")
        c = st.columns(2)
        txt_a = c[0].text_area("Antes", "121,3; 118,9; 124,0; 119,5; 122,8; 120,1; 123,4; 118,2", key="est_pa")
        txt_b = c[1].text_area("Depois", "112,0; 110,4; 115,9; 111,8; 113,2; 109,7; 114,5; 110,9", key="est_pb")
        st.caption("Os valores iniciais são exemplos ilustrativos (HIPOTÉTICOS).")

        def _ler(txt):
            partes = [p.strip().replace(",", ".") for p in txt.replace("\n", ";").split(";") if p.strip()]
            return [float(p) for p in partes]
        try:
            antes, depois = pd.Series(_ler(txt_a)), pd.Series(_ler(txt_b))
        except ValueError:
            st.error("Valores inválidos: use números separados por ponto e vírgula.")
            antes, depois = pd.Series(dtype=float), pd.Series(dtype=float)
        pareado = True
        if len(antes) != len(depois):
            st.error("Dados pareados exigem a mesma quantidade de valores antes e depois.")
            antes = depois = pd.Series(dtype=float)
    try:
        resultado = estatistica.comparar_antes_depois(antes, depois, pareado=pareado, metodo=metodo)
    except ValueError as erro:
        st.info(f"Teste não executado: {erro}", icon=":material/info:")
    if resultado:
        st.markdown(f"**{resultado.hipoteses[0]}**  \n**{resultado.hipoteses[1]}**  \n"
                    f"Nível de significância α = {painel.pct(resultado.alfa * 100, 0)} · teste unilateral · "
                    f"d = antes − depois")
        c = st.columns(5)
        c[0].metric("Média antes", painel.num(resultado.media_antes, 3), border=True, help=f"n = {resultado.n_antes}")
        c[1].metric("Média depois", painel.num(resultado.media_depois, 3), border=True, help=f"n = {resultado.n_depois}")
        c[2].metric("Redução média", painel.pct(resultado.reducao_percentual), border=True,
                    help=f"IC 95 %: {painel.pct(resultado.ic95_reducao_percentual[0])} a "
                         f"{painel.pct(resultado.ic95_reducao_percentual[1])}")
        c[3].metric("Valor p", f"{resultado.p_valor:.3g}", border=True, help=resultado.teste)
        c[4].metric("Tamanho de efeito", painel.num(resultado.tamanho_efeito, 2), border=True,
                    help="Diferença média em desvios-padrão (Cohen, 1988).")
        (st.success if resultado.significativo else st.warning)(
            f"**{resultado.teste}.** {resultado.conclusao}",
            icon=":material/check_circle:" if resultado.significativo else ":material/help:")
        for chave, norm in resultado.normalidade.items():
            st.caption(f"Shapiro-Wilk ({chave}): W = {painel.num(norm.estatistica, 3)}, "
                       f"p = {norm.p_valor:.3g} → {'normal' if norm.normal else 'não normal'}.")
        for ressalva in resultado.ressalvas:
            st.caption(f":material/warning: {ressalva}")
        fig = go.Figure()
        fig.add_trace(go.Box(y=antes, name="Antes", marker_color=painel.COR_NEUTRA, boxmean=True))
        fig.add_trace(go.Box(y=depois, name="Depois", marker_color=cor, boxmean=True))
        painel.grafico(painel.layout(fig, "Distribuição antes e depois", 320, nome, legenda=False), "est_box_ad")
        with st.expander("Tamanho de amostra para o próximo experimento", icon=":material/science:"):
            desvio = float(np.std(np.concatenate([np.asarray(antes) - np.mean(antes),
                                                  np.asarray(depois) - np.mean(depois)]), ddof=1))
            c = st.columns(3)
            reducao_min = c[0].number_input("Redução mínima a detectar (%)", min_value=0.5, value=3.0, step=0.5)
            poder = c[1].slider("Poder do teste", 0.5, 0.99, 0.80)
            n = estatistica.tamanho_amostra_por_periodo(desvio, resultado.media_antes * reducao_min / 100,
                                                        poder=poder, pareado=pareado)
            c[2].metric("Observações por período", n, border=True)
            st.caption("Aproximação normal, teste unilateral a 5 %, com o desvio-padrão observado.")

# --------------------------------------------------- correlação e regressão
with aba_reg:
    numericas = [v for v in variaveis if v in d.columns and d[v].notna().sum() >= 3 and d[v].nunique() > 1]
    if len(numericas) < 2:
        painel.sem_dados("Variáveis insuficientes para correlação.")
    else:
        metodo_corr = st.radio("Coeficiente", ["pearson", "spearman"], horizontal=True,
                               format_func=str.capitalize, key="est_corr")
        matriz = estatistica.matriz_correlacao(d[numericas].replace([np.inf, -np.inf], np.nan), metodo_corr)
        rot = [variaveis[v] for v in numericas]
        fig = go.Figure(go.Heatmap(z=matriz.values, x=rot, y=rot, zmin=-1, zmax=1,
                                   colorscale=[[0, "#e34948"], [0.5, "#f0efec"], [1, "#2a78d6"]],
                                   text=np.round(matriz.values, 2), texttemplate="%{text}",
                                   hovertemplate="%{y} × %{x}<br>r = %{z:.3f}<extra></extra>"))
        painel.grafico(painel.layout(fig, "Matriz de correlação", 380, legenda=False), "est_corr_mat")
        st.caption("Azul: correlação positiva; vermelho: negativa; cinza: ausência de correlação linear. "
                   "Correlação não implica causalidade.")
        st.markdown("**Regressão linear (mínimos quadrados)**")
        c = st.columns([1, 2])
        y = c[0].selectbox("Variável resposta (y)", numericas, format_func=variaveis.get, key="est_y")
        candidatas = [v for v in numericas if v != y]
        padrao = [v for v in ("metal_t", "horas", "refeicoes", "usuarios", "temp_entrada_c") if v in candidatas][:2]
        xs = c[1].multiselect("Variáveis explicativas (x)", candidatas, default=padrao or candidatas[:1],
                              format_func=variaveis.get, key="est_xs")
        if xs:
            try:
                reg = estatistica.regressao_linear(d.replace([np.inf, -np.inf], np.nan), y, xs)
            except ValueError as erro:
                st.info(f"Regressão não ajustada: {erro}")
            else:
                st.code(reg.equacao(y), language=None)
                c = st.columns(4)
                c[0].metric("R²", painel.num(reg.r2, 3), border=True)
                c[1].metric("R² ajustado", painel.num(reg.r2_ajustado, 3), border=True)
                c[2].metric("Erro-padrão residual", painel.num(reg.erro_padrao_residual, 3), border=True)
                c[3].metric("Durbin-Watson", painel.num(reg.durbin_watson, 2), border=True,
                            help="Próximo de 2: sem autocorrelação de primeira ordem.")
                st.dataframe(reg.coeficientes.style.format("{:.4g}"), width="stretch")
                if len(xs) > 1:
                    vif = estatistica.fator_inflacao_variancia(d, xs)
                    if (vif > 5).any():
                        st.warning("Multicolinearidade (VIF > 5) entre: " + ", ".join(
                            variaveis[v] for v in vif.index[vif > 5]) + ". Os coeficientes individuais "
                            "ficam imprecisos.", icon=":material/warning:")
                fig = go.Figure(go.Scatter(x=reg.ajustados, y=reg.residuos, mode="markers",
                                           marker=dict(size=8, color=cor, opacity=0.7)))
                fig.add_hline(y=0, line_color=painel.TEXTO_SEC, line_width=1)
                painel.grafico(painel.layout(fig, "Resíduos × valores ajustados", 300, "resíduo",
                                             "valor ajustado", False), "est_res")
                st.caption("Resíduos sem padrão em torno de zero indicam modelo adequado; funil ou curva "
                           "indicam heterocedasticidade ou relação não linear.")

# ---------------------------------------------------------- anomalias e CUSUM
with aba_anom:
    c = st.columns(2)
    metodo_an = c[0].radio("Método", ["z_robusto", "tukey", "imr"], horizontal=True, key="est_anom",
                           format_func={"z_robusto": "Escore z robusto", "tukey": "Cercas de Tukey",
                                        "imr": "Gráfico I-MR"}.get)
    limite = ctx.parametros["estatistica"]["limite_escore_z_robusto"]
    if len(serie) < 5:
        painel.sem_dados("Série curta demais para detectar anomalias.")
    else:
        valores = serie[metrica].reset_index(drop=True)
        mascara = anomalias.detectar(valores, metodo_an, limite=limite)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=serie["data"], y=valores, mode="lines", name=nome, line=dict(color=cor, width=2)))
        marcados = serie.reset_index(drop=True)[mascara.values]
        fig.add_trace(go.Scatter(x=marcados["data"], y=marcados[metrica], mode="markers", name="Anomalia",
                                 marker=dict(size=10, color=painel.COR_STATUS["critico"], symbol="diamond",
                                             line=dict(color=painel.SUPERFICIE, width=1))))
        if metodo_an == "imr":
            carta = anomalias.carta_imr(valores)
            for yv, txt in ((carta.lsc, "LSC"), (carta.linha_central, "LC"), (carta.lic, "LIC")):
                fig.add_hline(y=yv, line_color=painel.TEXTO_SEC, line_width=1, annotation_text=txt,
                              annotation_position="right")
        painel.grafico(painel.layout(fig, f"{int(mascara.sum())} ponto(s) fora do padrão", 340, nome), "est_anom_g")
        st.caption("Pontos marcados são indícios para investigação, não conclusões. Quando o consumo "
                   "depende da atividade, aplique o método aos resíduos do modelo (abaixo) para não "
                   "marcar como anômalos os dias de maior produção.")

        st.markdown("**CUSUM em relação à linha de base**")
        explicativas = {FUNDICAO: ["metal_t", "horas"], "RESTAURANTE": ["refeicoes"],
                        "CHUVEIROS": ["usuarios", "temp_entrada_c"]}[setor]
        explicativas = [v for v in explicativas if v in d.columns and d[v].nunique() > 1]
        datas = d["data"]
        c = st.columns(2)
        fim_base = c[0].date_input("Fim do período de linha de base", format="DD/MM/YYYY",
                                   value=(datas.min() + (datas.max() - datas.min()) / 3).date(), key="est_fb")
        base = d[(d["data"] <= pd.Timestamp(fim_base)) & (d["consumo_kg"] > 0)]
        if explicativas and len(base) > len(explicativas) + 5:
            modelo = estatistica.regressao_linear(base, "consumo_kg", explicativas)
            ativos = d[d["consumo_kg"] > 0].dropna(subset=explicativas)
            previsto = modelo.prever(ativos[explicativas])["previsto"]
            res = ativos["consumo_kg"] - previsto
            cus = anomalias.cusum(res)
            fig = go.Figure(go.Scatter(x=ativos["data"], y=cus, mode="lines", line=dict(color=cor, width=2),
                                       name="CUSUM", hovertemplate="%{x|%d/%m/%Y}<br>%{y:,.0f} kg<extra></extra>"))
            fig.add_vline(x=pd.Timestamp(fim_base).timestamp() * 1000, line_color=painel.TEXTO_SEC, line_width=1)
            fig.add_hline(y=0, line_color=painel.GRADE, line_width=1)
            painel.grafico(painel.layout(fig, "Soma acumulada de (consumo real − previsto pela linha de base)", 340,
                                         "kg acumulados", legenda=False), "est_cusum")
            st.caption(f"Linha de base: {modelo.equacao('G', 3)} (R² = {painel.num(modelo.r2, 3)}). "
                       "Inclinação para baixo após a linha vertical indica consumo abaixo do esperado; "
                       "para cima, acima do esperado (Page, 1954).")
        else:
            painel.sem_dados("Período de linha de base curto demais para ajustar o modelo.")
