"""Configuração dos testes: banco SQLite temporário, isolado do banco local."""

import os
import tempfile
from pathlib import Path

_PASTA = Path(tempfile.mkdtemp(prefix="glp_testes_"))
os.environ["GLP_BANCO"] = str(_PASTA / "teste.db")

import pytest  # noqa: E402

from src import dados_simulados  # noqa: E402


@pytest.fixture(scope="session")
def simulados():
    """Tabelas simuladas geradas uma vez por sessão de testes."""
    return dados_simulados.gerar()


@pytest.fixture(scope="session")
def registros(simulados):
    return simulados["registros"]
