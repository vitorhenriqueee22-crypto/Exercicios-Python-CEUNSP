# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Experimentação e Análise de Dados
# Aluno: Vitor Henrique Santos Das Virgens
# Projeto: Monitoramento e otimização do consumo de GLP
# Módulo: banco_dados — histórico em SQLite
# ============================================================
"""Armazenamento do histórico em SQLite.

Registros MEDIDO e SIMULADO ficam na mesma tabela, mas sempre com a coluna
``origem`` preenchida (restrição CHECK), e as consultas filtram por origem.
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd

from .constantes import ARQUIVO_BANCO, COLUNAS_REGISTRO, PASTA_SIMULADOS, SIMULADO

ESQUEMA = """
CREATE TABLE IF NOT EXISTS registros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL,
    hora TEXT,
    setor TEXT NOT NULL,
    equipamento_id TEXT,
    consumo_valor REAL NOT NULL CHECK (consumo_valor >= 0),
    consumo_unidade TEXT NOT NULL,
    consumo_kg REAL NOT NULL CHECK (consumo_kg >= 0),
    atividade_valor REAL,
    atividade_unidade TEXT,
    tempo_funcionamento_h REAL,
    tempo_sem_carga_h REAL,
    ciclos REAL,
    temperatura_c REAL,
    origem TEXT NOT NULL CHECK (origem IN ('MEDIDO', 'SIMULADO')),
    observacoes TEXT,
    lote TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_registro ON registros
    (data, COALESCE(hora, ''), setor, COALESCE(equipamento_id, ''), origem);
CREATE INDEX IF NOT EXISTS ix_registro_data ON registros (origem, data);

CREATE TABLE IF NOT EXISTS equipamentos (
    equipamento_id TEXT NOT NULL,
    nome TEXT, setor TEXT, tipo TEXT, funcao TEXT, metal_liga TEXT,
    capacidade_nominal_kg REAL, potencia_nominal_kg_h REAL,
    temperatura_trabalho_c REAL, medicao_individual TEXT,
    origem TEXT NOT NULL,
    PRIMARY KEY (equipamento_id, origem)
);

CREATE TABLE IF NOT EXISTS abastecimentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL,
    massa_kg REAL NOT NULL CHECK (massa_kg > 0),
    preco_r_kg REAL,
    nota_fiscal TEXT,
    nivel_antes_pct REAL,
    origem TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS intervencoes (
    id TEXT NOT NULL,
    setor TEXT, equipamento_id TEXT, descricao TEXT, data_inicio TEXT,
    origem TEXT NOT NULL,
    PRIMARY KEY (id, origem)
);

CREATE TABLE IF NOT EXISTS importacoes (
    lote TEXT PRIMARY KEY,
    arquivo TEXT, data_hora TEXT, lidos INTEGER, aceitos INTEGER,
    inseridos INTEGER, origem TEXT
);
"""

TABELAS_AUXILIARES = ("equipamentos", "abastecimentos", "intervencoes")


def conectar(caminho: Path | None = None) -> sqlite3.Connection:
    caminho = Path(caminho or ARQUIVO_BANCO)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(caminho)
    con.executescript(ESQUEMA)
    return con


def inserir_registros(df: pd.DataFrame, caminho: Path | None = None,
                      arquivo: str = "", lote: str | None = None) -> dict:
    """Insere registros já validados. Registros repetidos (mesma data, hora,
    setor, equipamento e origem) são ignorados e contabilizados."""
    lote = lote or uuid.uuid4().hex[:12]
    dados = df.copy()
    if "consumo_kg" not in dados.columns:
        dados["consumo_kg"] = dados["consumo_valor"]
    colunas = list(COLUNAS_REGISTRO) + ["consumo_kg"]
    dados = dados[colunas].astype(object).where(dados[colunas].notna(), None)
    dados["lote"] = lote
    con = conectar(caminho)
    with con:
        antes = con.execute("SELECT COUNT(*) FROM registros").fetchone()[0]
        con.executemany(
            f"INSERT OR IGNORE INTO registros ({', '.join(colunas + ['lote'])}) "
            f"VALUES ({', '.join('?' * (len(colunas) + 1))})",
            dados.itertuples(index=False, name=None))
        depois = con.execute("SELECT COUNT(*) FROM registros").fetchone()[0]
        origens = ",".join(sorted(set(df["origem"].dropna()))) if len(df) else ""
        con.execute("INSERT INTO importacoes VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (lote, arquivo, datetime.now().isoformat(timespec="seconds"),
                     len(df), len(df), depois - antes, origens))
    con.close()
    return {"lote": lote, "inseridos": depois - antes, "ignorados": len(df) - (depois - antes)}


def ler_registros(caminho: Path | None = None, origem: str | None = None,
                  inicio=None, fim=None) -> pd.DataFrame:
    filtros, args = [], []
    if origem:
        filtros.append("origem = ?")
        args.append(origem)
    if inicio is not None:
        filtros.append("data >= ?")
        args.append(str(pd.Timestamp(inicio).date()))
    if fim is not None:
        filtros.append("data <= ?")
        args.append(str(pd.Timestamp(fim).date()))
    onde = f"WHERE {' AND '.join(filtros)}" if filtros else ""
    con = conectar(caminho)
    df = pd.read_sql_query(f"SELECT * FROM registros {onde} ORDER BY data, hora", con, params=args)
    con.close()
    return df


def gravar_tabela(nome: str, df: pd.DataFrame, caminho: Path | None = None) -> int:
    """Grava uma tabela auxiliar, substituindo as linhas da mesma origem."""
    if nome not in TABELAS_AUXILIARES:
        raise ValueError(f"Tabela desconhecida: {nome}")
    if df.empty:
        return 0
    con = conectar(caminho)
    # Exclui apenas a chave autoincremental (INTEGER PRIMARY KEY)
    colunas = [c[1] for c in con.execute(f"PRAGMA table_info({nome})")
               if not (c[5] and c[2].upper() == "INTEGER")]
    dados = df[[c for c in colunas if c in df.columns]]
    with con:
        for origem in dados["origem"].unique():
            con.execute(f"DELETE FROM {nome} WHERE origem = ?", (origem,))
        dados.to_sql(nome, con, if_exists="append", index=False)
    con.close()
    return len(dados)


def ler_tabela(nome: str, caminho: Path | None = None, origem: str | None = None) -> pd.DataFrame:
    if nome not in TABELAS_AUXILIARES + ("importacoes",):
        raise ValueError(f"Tabela desconhecida: {nome}")
    con = conectar(caminho)
    if origem and nome != "importacoes":
        df = pd.read_sql_query(f"SELECT * FROM {nome} WHERE origem = ?", con, params=(origem,))
    else:
        df = pd.read_sql_query(f"SELECT * FROM {nome}", con)
    con.close()
    return df


def origens_disponiveis(caminho: Path | None = None) -> dict[str, int]:
    con = conectar(caminho)
    linhas = con.execute("SELECT origem, COUNT(*) FROM registros GROUP BY origem").fetchall()
    con.close()
    return dict(linhas)


def carregar_simulados(caminho: Path | None = None, pasta: Path | None = None,
                       regenerar: bool = False) -> dict:
    """Carrega os CSV simulados no banco (gerando-os se não existirem)."""
    from . import dados_simulados  # import local evita ciclo

    pasta = Path(pasta or PASTA_SIMULADOS)
    if regenerar or not (pasta / "registros.csv").exists():
        dados_simulados.salvar(dados_simulados.gerar(), pasta)
    registros = pd.read_csv(pasta / "registros.csv", dtype={"hora": str})
    registros["consumo_kg"] = registros["consumo_valor"]
    con = conectar(caminho)
    with con:
        con.execute("DELETE FROM registros WHERE origem = ?", (SIMULADO,))
    con.close()
    resultado = inserir_registros(registros, caminho, arquivo="dados_simulados/registros.csv")
    for nome in TABELAS_AUXILIARES:
        arquivo = pasta / f"{nome}.csv"
        if arquivo.exists():
            gravar_tabela(nome, pd.read_csv(arquivo), caminho)
    return resultado
