"""Testes de fumaça do painel: cada página executa sem exceções."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

RAIZ = Path(__file__).resolve().parents[1]
PAGINAS = sorted((RAIZ / "paginas").glob("*.py"))


@pytest.mark.parametrize("pagina", PAGINAS, ids=[p.stem for p in PAGINAS])
def test_pagina_executa_sem_erros(pagina):
    app = AppTest.from_file(str(pagina), default_timeout=180)
    app.run()
    assert not app.exception, [e.value for e in app.exception]
    textos = " ".join(w.value for w in app.warning) + " ".join(e.value for e in app.error)
    assert "SIMULADO" in textos or "SIMULAÇÃO" in textos   # a origem dos dados é sempre exibida


def test_entrada_do_painel_com_filtros():
    app = AppTest.from_file(str(RAIZ / "dashboard.py"), default_timeout=180)
    app.run()
    assert not app.exception, [e.value for e in app.exception]
    assert app.sidebar.radio[0].value == "SIMULADO"
    assert app.sidebar.number_input[0].value == pytest.approx(7.0)


def test_simulacao_reage_aos_parametros():
    app = AppTest.from_file(str(RAIZ / "paginas" / "simulacao.py"), default_timeout=180)
    app.run()
    app.number_input[0].set_value(1000.0)    # consumo atual
    app.number_input[1].set_value(10.0)      # preço
    app.run()
    assert not app.exception
    valores = {m.label: m.value for m in app.metric}
    assert valores["Economia diária"] == "R$ 1.500,00"      # 15 % de 1.000 kg × R$ 10
