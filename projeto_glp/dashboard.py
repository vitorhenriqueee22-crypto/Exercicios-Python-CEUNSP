# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Experimentação e Análise de Dados
# Aluno: Vitor Henrique Santos Das Virgens
# Projeto: Monitoramento e otimização do consumo de GLP
# Arquivo: dashboard.py — painel interativo (Streamlit)
# ============================================================
"""Painel de monitoramento do consumo de GLP.

Execução (a partir da raiz do repositório):
    streamlit run projeto_glp/dashboard.py
"""

import sys
from pathlib import Path

import streamlit as st

RAIZ = Path(__file__).resolve().parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src import painel  # noqa: E402

st.set_page_config(page_title="Monitoramento de GLP", page_icon=":material/local_fire_department:",
                   layout="wide", initial_sidebar_state="expanded")

PAGINAS = {
    "Acompanhamento": [
        st.Page(RAIZ / "paginas" / "visao_geral.py", title="Visão geral",
                icon=":material/dashboard:", default=True),
        st.Page(RAIZ / "paginas" / "fundicao.py", title="Fundição", icon=":material/factory:"),
        st.Page(RAIZ / "paginas" / "restaurante.py", title="Restaurante", icon=":material/restaurant:"),
        st.Page(RAIZ / "paginas" / "chuveiros.py", title="Chuveiros", icon=":material/shower:"),
        st.Page(RAIZ / "paginas" / "comparacao.py", title="Comparação entre setores",
                icon=":material/compare_arrows:"),
        st.Page(RAIZ / "paginas" / "reservatorio.py", title="Reservatório",
                icon=":material/propane_tank:"),
    ],
    "Análise e decisão": [
        st.Page(RAIZ / "paginas" / "estatistica.py", title="Análise estatística",
                icon=":material/query_stats:"),
        st.Page(RAIZ / "paginas" / "simulacao.py", title="Simulação de economia",
                icon=":material/savings:"),
        st.Page(RAIZ / "paginas" / "relatorios.py", title="Relatórios", icon=":material/description:"),
    ],
    "Dados": [
        st.Page(RAIZ / "paginas" / "base_dados.py", title="Base de dados", icon=":material/database:"),
    ],
}

navegacao = st.navigation(PAGINAS)
painel.barra_lateral()
navegacao.run()
