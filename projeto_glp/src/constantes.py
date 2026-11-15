# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Experimentação e Análise de Dados
# Aluno: Vitor Henrique Santos Das Virgens
# Projeto: Monitoramento e otimização do consumo de GLP
# Módulo: constantes — fatores de conversão, origens e esquema de dados
# ============================================================
"""Constantes do sistema, com fonte e classe de origem.

Fontes (ver relatório ABNT, seção 2.3):
    PCI e massa específica do GLP: ANP, Anuário Estatístico 2026, tabela de
    fatores de conversão (valores médios do Balanço Energético Nacional/EPE).
"""

from __future__ import annotations

import os
from pathlib import Path
import tomllib

# ---------------------------------------------------------------------------
# Caminhos do projeto
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parents[1]
PASTA_DADOS = RAIZ / "dados"
PASTA_REAIS = PASTA_DADOS / "dados_reais"
PASTA_SIMULADOS = PASTA_DADOS / "dados_simulados"
PASTA_REFERENCIAS = PASTA_DADOS / "referencias"
PASTA_RESULTADOS = RAIZ / "resultados"
ARQUIVO_PARAMETROS = RAIZ / "config" / "parametros.toml"
# O caminho do banco pode ser trocado pela variável de ambiente GLP_BANCO (usada nos testes)
ARQUIVO_BANCO = Path(os.environ.get("GLP_BANCO", PASTA_DADOS / "glp.db"))

# ---------------------------------------------------------------------------
# Propriedades do GLP (REFERÊNCIA: ANP, 2026)
# ---------------------------------------------------------------------------
PCI_KCAL_KG = 11_100.0           # poder calorífico inferior, kcal/kg
MASSA_ESPECIFICA_LIQUIDO_T_M3 = 0.552  # valor médio de conversão (fase líquida)
FONTE_PCI = ("ANP. Anuário estatístico 2026: fatores de conversão "
             "(valores médios BEN/EPE).")

# Conversões de unidade (convenções)
KJ_POR_KCAL = 4.1868             # caloria internacional
KJ_POR_KWH = 3600.0
KCAL_POR_TEP = 1.0e7             # convenção do BEN

# Valores CALCULADOS a partir da referência
PCI_KJ_KG = PCI_KCAL_KG * KJ_POR_KCAL        # 46.473,48 kJ/kg
PCI_KWH_KG = PCI_KJ_KG / KJ_POR_KWH          # 12,909 kWh/kg

# Água (REFERÊNCIA: Bergman et al., 2014 — valor próximo de 300 K)
CALOR_ESPECIFICO_AGUA_KJ_KGK = 4.18

# ---------------------------------------------------------------------------
# Classes de origem (Quadro 3 do relatório)
# ---------------------------------------------------------------------------
MEDIDO = "MEDIDO"
SIMULADO = "SIMULADO"
REFERENCIA = "REFERENCIA"
CALCULADO = "CALCULADO"
HIPOTESE = "HIPOTESE"
ORIGENS_REGISTRO = (MEDIDO, SIMULADO)

# Hierarquia: um valor calculado herda a classe mais fraca das entradas.
_FORCA_ORIGEM = {MEDIDO: 3, REFERENCIA: 3, CALCULADO: 2, HIPOTESE: 1, SIMULADO: 0}


def origem_resultante(*origens: str) -> str:
    """Retorna a classe de origem de um resultado calculado a partir das
    classes das entradas (a mais fraca prevalece)."""
    if not origens:
        raise ValueError("Informe ao menos uma origem.")
    for origem in origens:
        if origem not in _FORCA_ORIGEM:
            raise ValueError(f"Origem desconhecida: {origem}")
    mais_fraca = min(origens, key=lambda o: _FORCA_ORIGEM[o])
    if _FORCA_ORIGEM[mais_fraca] == 3:
        return CALCULADO
    return mais_fraca


# ---------------------------------------------------------------------------
# Setores e unidades
# ---------------------------------------------------------------------------
FUNDICAO = "FUNDICAO"
RESTAURANTE = "RESTAURANTE"
CHUVEIROS = "CHUVEIROS"
GERAL = "GERAL"
SETORES = (FUNDICAO, RESTAURANTE, CHUVEIROS, GERAL)

NOME_SETOR = {
    FUNDICAO: "Fundição",
    RESTAURANTE: "Restaurante",
    CHUVEIROS: "Chuveiros",
    GERAL: "Geral (não setorizado)",
}

# Unidades de atividade aceitas por setor (normalização do consumo)
UNIDADES_ATIVIDADE = {
    FUNDICAO: ("t", "ciclos"),
    RESTAURANTE: ("refeicoes",),
    CHUVEIROS: ("usuarios", "banhos"),
    GERAL: ("t", "refeicoes", "usuarios", "banhos", "ciclos"),
}

UNIDADES_CONSUMO = ("kg", "t", "m3")
FATOR_PARA_KG = {"kg": 1.0, "t": 1000.0}     # m3 exige fator explícito

# Paleta categórica validada (skill de visualização; ordem fixa, nunca reciclada)
COR_SETOR = {
    FUNDICAO: "#2a78d6",
    RESTAURANTE: "#eb6834",
    CHUVEIROS: "#1baf7a",
    GERAL: "#8a8985",
}
CORES_CATEGORICAS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
                     "#e87ba4", "#008300", "#6250d6", "#e34948"]
COR_STATUS = {"bom": "#0ca30c", "atencao": "#fab219", "serio": "#ec835a",
              "critico": "#d03b3b"}

# ---------------------------------------------------------------------------
# Esquema do registro de consumo (Quadro 12 do relatório)
# ---------------------------------------------------------------------------
COLUNAS_OBRIGATORIAS = ("data", "setor", "consumo_valor", "consumo_unidade", "origem")
COLUNAS_OPCIONAIS = (
    "hora", "equipamento_id", "atividade_valor", "atividade_unidade",
    "tempo_funcionamento_h", "tempo_sem_carga_h", "ciclos", "temperatura_c",
    "observacoes",
)
COLUNAS_REGISTRO = (
    "data", "hora", "setor", "equipamento_id", "consumo_valor", "consumo_unidade",
    "atividade_valor", "atividade_unidade", "tempo_funcionamento_h",
    "tempo_sem_carga_h", "ciclos", "temperatura_c", "origem", "observacoes",
)
COLUNAS_NUMERICAS = (
    "consumo_valor", "atividade_valor", "tempo_funcionamento_h",
    "tempo_sem_carga_h", "ciclos", "temperatura_c",
)


def carregar_parametros(caminho: Path | None = None) -> dict:
    """Lê o arquivo TOML de parâmetros."""
    caminho = Path(caminho) if caminho else ARQUIVO_PARAMETROS
    with open(caminho, "rb") as arquivo:
        return tomllib.load(arquivo)


def kg_para_kwh(massa_kg):
    """Equação 1: E = m · PCI (resultado em kWh)."""
    return massa_kg * PCI_KWH_KG


def kg_para_kj(massa_kg):
    """Equação 1: E = m · PCI (resultado em kJ)."""
    return massa_kg * PCI_KJ_KG
