"""Página: Relatórios."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st  # noqa: E402

from src import alertas, painel, relatorios  # noqa: E402

ctx = painel.contexto()
painel.cabecalho("Relatórios", ctx, "Resumo do período, avaliação de intervenções e exportação.")
df = ctx.dados
if df.empty:
    painel.sem_dados()
    st.stop()

estoque_inicial = ctx.parametros["reservatorio"].get("estoque_inicial_kg", 0.0)
lista = alertas.gerar_alertas(df, ctx.parametros, ctx.abastecimentos, estoque_inicial, ctx.preco,
                              dados_reservatorio=ctx.todos)

st.subheader("Avaliação das intervenções registradas")
janela = st.slider("Janela antes e depois (dias)", 14, 180, 90, step=7)
if len(ctx.intervencoes):
    tab = relatorios.tabela_intervencoes(ctx.todos, ctx.intervencoes, janela)
    st.dataframe(tab, hide_index=True, width="stretch", column_config={
        "id": "ID", "setor": "Setor", "equipamento": "Equipamento", "descricao": "Descrição",
        "inicio": "Início", "metrica": "Métrica", "n_antes": "n antes", "n_depois": "n depois",
        "media_antes": st.column_config.NumberColumn("Média antes", format="%.3f"),
        "media_depois": st.column_config.NumberColumn("Média depois", format="%.3f"),
        "reducao_pct": st.column_config.NumberColumn("Redução (%)", format="%.1f"),
        "ic95_inf_pct": st.column_config.NumberColumn("IC 95 % inf. (%)", format="%.1f"),
        "ic95_sup_pct": st.column_config.NumberColumn("IC 95 % sup. (%)", format="%.1f"),
        "teste": "Teste", "p_valor": st.column_config.NumberColumn("Valor p", format="%.2e"),
        "significativo": st.column_config.CheckboxColumn("Redução significativa (5 %)"),
    })
    st.caption("Amostras independentes (períodos antes e depois). Confirme que produção, mix de "
               "produtos e estação são comparáveis antes de atribuir a diferença à intervenção.")
else:
    painel.sem_dados("Nenhuma intervenção registrada.")

st.subheader("Exportar")
tabelas = relatorios.tabelas_resumo(df, ctx.preco, ctx.equipamentos, lista)
md = relatorios.relatorio_markdown(df, ctx.preco, ctx.origem, ctx.intervencoes, lista, ctx.equipamentos)
sufixo = f"{ctx.origem}_{ctx.inicio:%Y%m%d}_{ctx.fim:%Y%m%d}"
c = st.columns(2)
c[0].download_button("Planilha com todas as tabelas (.xlsx)", relatorios.exportar_excel(tabelas, ctx.origem),
                     file_name=f"relatorio_glp_{sufixo}.xlsx", icon=":material/table_view:",
                     mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
c[1].download_button("Relatório resumido (.md)", md.encode("utf-8"), file_name=f"relatorio_glp_{sufixo}.md",
                     mime="text/markdown", icon=":material/description:")

st.subheader("Pré-visualização do relatório")
with st.container(border=True):
    st.markdown(md)
