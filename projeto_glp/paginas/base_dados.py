"""Página: Base de dados (importação, validação e consulta)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from src import banco_dados, importacao, painel, validacao  # noqa: E402
from src.constantes import MEDIDO, NOME_SETOR, PASTA_SIMULADOS, SIMULADO  # noqa: E402

ctx = painel.contexto()
painel.cabecalho("Base de dados", ctx, "Importação de planilhas, validação, consulta e hipóteses dos dados simulados.")

origens = banco_dados.origens_disponiveis()
c = st.columns(3)
c[0].metric("Registros medidos", painel.num(origens.get(MEDIDO, 0)), border=True)
c[1].metric("Registros simulados", painel.num(origens.get(SIMULADO, 0)), border=True)
c[2].metric("Equipamentos cadastrados", painel.num(len(ctx.equipamentos)), border=True)

aba_imp, aba_consulta, aba_hip = st.tabs(["Importar planilha", "Consultar registros", "Dados simulados"])

with aba_imp:
    st.markdown("Envie um arquivo **CSV** (separador `;` ou `,`) ou **Excel (.xlsx)** com as colunas do "
                "registro de consumo. Os registros são validados antes de entrar no banco; nada é "
                "corrigido automaticamente.")
    modelo = importacao.modelo_planilha()
    st.download_button("Baixar planilha-modelo (CSV)",
                       modelo.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                       file_name="modelo_registros_glp.csv", mime="text/csv", icon=":material/download:")
    with st.expander("Colunas e regras de validação", icon=":material/rule:"):
        st.markdown(
            "- Obrigatórias: `data` (AAAA-MM-DD), `setor` (FUNDICAO, RESTAURANTE, CHUVEIROS ou GERAL), "
            "`consumo_valor`, `consumo_unidade` (kg, t ou m3) e `origem` (MEDIDO).\n"
            "- Opcionais: `hora`, `equipamento_id`, `atividade_valor`, `atividade_unidade` "
            "(t, ciclos, refeicoes, usuarios, banhos), `tempo_funcionamento_h`, `tempo_sem_carga_h`, "
            "`ciclos`, `temperatura_c`, `observacoes`.\n"
            "- Rejeitados: campos obrigatórios vazios, valores negativos, datas inválidas ou futuras, "
            "unidades incompatíveis, m³ sem fator de conversão, mistura de MEDIDO e SIMULADO.\n"
            "- Avisos: duplicados, equipamento não cadastrado, consumo acima da potência nominal, "
            "lacunas na série diária.")
    arquivo = st.file_uploader("Arquivo", type=["csv", "xlsx"], key="bd_arquivo")
    fator_m3 = st.number_input("Fator de conversão kg/m³ (só para leituras em m³, informado pelo fornecedor)",
                               min_value=0.0, value=0.0, step=0.01, format="%.3f")
    if arquivo is not None:
        try:
            bruto = importacao.ler_arquivo(arquivo, arquivo.name)
        except Exception as erro:  # noqa: BLE001 — mensagem ao usuário
            st.error(f"Não foi possível ler o arquivo: {erro}")
            st.stop()
        resultado = validacao.validar_registros(bruto, ctx.equipamentos, fator_m3 or None)
        c = st.columns(4)
        c[0].metric("Linhas lidas", resultado.total_lido, border=True)
        c[1].metric("Aceitas", len(resultado.dados), border=True)
        c[2].metric("Erros", resultado.n_erros, border=True)
        c[3].metric("Avisos", resultado.n_avisos, border=True)
        if len(resultado.relatorio):
            st.dataframe(resultado.relatorio, hide_index=True, width="stretch", column_config={
                "linha_arquivo": "Linha", "campo": "Campo", "nivel": "Nível", "regra": "Regra",
                "mensagem": "Mensagem"})
            painel.baixar_csv(resultado.relatorio, "relatorio_validacao.csv", "Baixar relatório de validação")
        origens_arquivo = set(resultado.dados["origem"].dropna())
        if not len(resultado.dados):
            st.error("Nenhum registro aceito.")
        elif origens_arquivo != {MEDIDO}:
            st.warning("Somente registros com origem MEDIDO podem ser gravados por esta tela. "
                       "Dados simulados são gerados pelo próprio sistema.", icon=":material/block:")
        else:
            st.dataframe(resultado.dados.head(50), hide_index=True, width="stretch")
            if st.button(f"Gravar {len(resultado.dados)} registro(s) aceitos como MEDIDO",
                         type="primary", icon=":material/save:"):
                saida = banco_dados.inserir_registros(resultado.dados, arquivo=arquivo.name)
                painel.limpar_cache()
                st.success(f"{saida['inseridos']} registro(s) gravado(s); {saida['ignorados']} já existiam "
                           f"(lote {saida['lote']}). Selecione \"Medidos\" na barra lateral.")

with aba_consulta:
    df = ctx.dados
    c = st.columns(2)
    setores = c[0].multiselect("Setores", sorted(df["setor"].unique()), default=sorted(df["setor"].unique()),
                               format_func=lambda s: NOME_SETOR.get(s, s))
    equipamentos = c[1].multiselect("Equipamentos", sorted(df["equipamento_id"].dropna().unique()))
    filtrado = df[df["setor"].isin(setores)]
    if equipamentos:
        filtrado = filtrado[filtrado["equipamento_id"].isin(equipamentos)]
    st.caption(f"{painel.num(len(filtrado))} registro(s) — origem {ctx.origem}.")
    st.dataframe(filtrado.drop(columns=["id", "lote"], errors="ignore").assign(
        data=filtrado["data"].dt.strftime("%Y-%m-%d")), hide_index=True, width="stretch", height=420)
    painel.baixar_csv(filtrado, f"registros_{ctx.origem}.csv")
    with st.expander("Histórico de importações", icon=":material/history:"):
        st.dataframe(banco_dados.ler_tabela("importacoes"), hide_index=True, width="stretch")

with aba_hip:
    hipoteses = PASTA_SIMULADOS / "HIPOTESES.md"
    if hipoteses.exists():
        st.markdown(hipoteses.read_text(encoding="utf-8"))
    st.markdown("As hipóteses ficam em `config/hipoteses_simulacao.toml`. Depois de editá-las, "
                "regenere os dados:")
    if st.button("Regenerar dados simulados", icon=":material/refresh:"):
        with st.spinner("Gerando dados simulados…"):
            saida = banco_dados.carregar_simulados(regenerar=True)
        painel.limpar_cache()
        st.success(f"{saida['inseridos']} registros simulados gerados.")
    abast = banco_dados.ler_tabela("abastecimentos", origem=SIMULADO)
    if len(abast):
        st.caption(f"{len(abast)} abastecimentos simulados; preço médio "
                   f"{painel.reais(pd.to_numeric(abast['preco_r_kg']).mean())}/kg (HIPÓTESE).")
