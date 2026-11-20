# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Experimentação e Análise de Dados
# Aluno: Vitor Henrique Santos Das Virgens
# Projeto: Monitoramento e otimização do consumo de GLP
# Módulo: importacao — leitura de arquivos CSV e Excel
# ============================================================
"""Leitura de planilhas de consumo (CSV ou Excel) e padronização de colunas.

A importação NÃO corrige valores: ela apenas lê e padroniza nomes de colunas.
A verificação de qualidade é feita pelo módulo ``validacao``.
"""

from __future__ import annotations

import io
import unicodedata
from pathlib import Path

import pandas as pd

from .constantes import COLUNAS_REGISTRO

# Nomes alternativos aceitos nas planilhas -> nome padrão
SINONIMOS = {
    "dia": "data",
    "date": "data",
    "horario": "hora",
    "time": "hora",
    "equipamento": "equipamento_id",
    "id_equipamento": "equipamento_id",
    "consumo": "consumo_valor",
    "consumo_glp": "consumo_valor",
    "consumo_kg": "consumo_valor",
    "unidade": "consumo_unidade",
    "unidade_consumo": "consumo_unidade",
    "producao": "atividade_valor",
    "atividade": "atividade_valor",
    "unidade_atividade": "atividade_unidade",
    "horas": "tempo_funcionamento_h",
    "tempo_funcionamento": "tempo_funcionamento_h",
    "horas_sem_carga": "tempo_sem_carga_h",
    "temperatura": "temperatura_c",
    "obs": "observacoes",
    "observacao": "observacoes",
}


def _sem_acentos(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in texto if not unicodedata.combining(c))


def normalizar_nome_coluna(nome: str) -> str:
    """'Consumo (kg)' -> 'consumo_kg'; aplica sinônimos conhecidos."""
    base = _sem_acentos(nome).strip().lower()
    for caractere in "()[]/-.":
        base = base.replace(caractere, " ")
    base = "_".join(base.split())
    return SINONIMOS.get(base, base)


def normalizar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [normalizar_nome_coluna(c) for c in df.columns]
    return df


def _ler_csv(conteudo: bytes) -> pd.DataFrame:
    texto = conteudo.decode("utf-8-sig", errors="replace")
    primeira = texto.splitlines()[0] if texto else ""
    separador = ";" if primeira.count(";") > primeira.count(",") else ","
    # Com ';' como separador, a vírgula é tratada como separador decimal.
    decimal = "," if separador == ";" else "."
    return pd.read_csv(io.StringIO(texto), sep=separador, decimal=decimal,
                       dtype={"hora": str, "data": str}, keep_default_na=True)


def ler_arquivo(fonte, nome: str | None = None) -> pd.DataFrame:
    """Lê um arquivo CSV ou Excel.

    ``fonte`` pode ser um caminho ou um objeto com ``read()`` (como o arquivo
    enviado pelo painel). ``nome`` é usado para identificar a extensão quando
    ``fonte`` não é um caminho.
    """
    if isinstance(fonte, (str, Path)):
        caminho = Path(fonte)
        nome = nome or caminho.name
        conteudo = caminho.read_bytes()
    else:
        conteudo = fonte.read()
        nome = nome or getattr(fonte, "name", "arquivo.csv")
    extensao = Path(nome).suffix.lower()
    if extensao in (".csv", ".txt"):
        df = _ler_csv(conteudo)
    elif extensao in (".xlsx", ".xlsm"):
        df = pd.read_excel(io.BytesIO(conteudo), engine="openpyxl",
                           dtype={"hora": str})
    else:
        raise ValueError(f"Formato não suportado: {extensao}. Use CSV ou Excel (.xlsx).")
    df = normalizar_colunas(df)
    # Datas lidas pelo Excel como datetime são convertidas para texto ISO
    if "data" in df.columns and pd.api.types.is_datetime64_any_dtype(df["data"]):
        df["data"] = df["data"].dt.strftime("%Y-%m-%d")
    return df


def modelo_planilha() -> pd.DataFrame:
    """Planilha-modelo vazia com as colunas do registro de consumo."""
    exemplo = {
        "data": ["2026-01-05"], "hora": [""], "setor": ["FUNDICAO"],
        "equipamento_id": ["FORNO-01"], "consumo_valor": [250.0],
        "consumo_unidade": ["kg"], "atividade_valor": [2.1],
        "atividade_unidade": ["t"], "tempo_funcionamento_h": [14.0],
        "tempo_sem_carga_h": [5.5], "ciclos": [5], "temperatura_c": [720.0],
        "origem": ["MEDIDO"], "observacoes": ["linha de exemplo — apagar"],
    }
    return pd.DataFrame(exemplo, columns=list(COLUNAS_REGISTRO))
