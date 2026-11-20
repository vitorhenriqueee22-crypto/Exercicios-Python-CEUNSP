# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Experimentação e Análise de Dados
# Aluno: Vitor Henrique Santos Das Virgens
# Projeto: Monitoramento e otimização do consumo de GLP
# Módulo: validacao — regras de qualidade dos dados (Quadro 13)
# ============================================================
"""Validação dos registros de consumo.

Regras (Quadro 13 do relatório): campos vazios, valores negativos, registros
duplicados, datas inválidas, unidades incompatíveis, leituras inconsistentes,
dados ausentes e mistura de dados medidos com simulados.

O sistema não corrige dados silenciosamente: cada problema gera uma linha no
relatório, com nível ERRO (registro rejeitado) ou AVISO (registro mantido).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import numpy as np
import pandas as pd

from .constantes import (
    COLUNAS_NUMERICAS, COLUNAS_OBRIGATORIAS, COLUNAS_REGISTRO, FATOR_PARA_KG,
    ORIGENS_REGISTRO, SETORES, UNIDADES_ATIVIDADE, UNIDADES_CONSUMO,
)

ERRO = "ERRO"
AVISO = "AVISO"


@dataclass
class ResultadoValidacao:
    dados: pd.DataFrame                      # registros aceitos, com consumo_kg
    relatorio: pd.DataFrame                  # problemas encontrados
    total_lido: int = 0
    resumo: dict = field(default_factory=dict)

    @property
    def aprovado(self) -> bool:
        return not (self.relatorio["nivel"] == ERRO).any() if len(self.relatorio) else True

    @property
    def n_erros(self) -> int:
        return int((self.relatorio["nivel"] == ERRO).sum()) if len(self.relatorio) else 0

    @property
    def n_avisos(self) -> int:
        return int((self.relatorio["nivel"] == AVISO).sum()) if len(self.relatorio) else 0


class _Relatorio:
    def __init__(self) -> None:
        self.linhas: list[dict] = []

    def add(self, indice, campo, nivel, regra, mensagem) -> None:
        linha = int(indice) + 2 if indice is not None else None   # +1 cabeçalho, +1 base 1
        self.linhas.append({"linha_arquivo": linha, "campo": campo, "nivel": nivel,
                            "regra": regra, "mensagem": mensagem})

    def df(self) -> pd.DataFrame:
        return pd.DataFrame(self.linhas, columns=["linha_arquivo", "campo", "nivel",
                                                  "regra", "mensagem"])


def _vazio(valor) -> bool:
    return valor is None or (isinstance(valor, float) and np.isnan(valor)) or \
        (isinstance(valor, str) and valor.strip() == "") or pd.isna(valor)


def validar_registros(
    df: pd.DataFrame,
    equipamentos: pd.DataFrame | None = None,
    fator_kg_por_m3: float | None = None,
    permitir_mistura: bool = False,
    hoje: date | None = None,
) -> ResultadoValidacao:
    """Valida um DataFrame de registros de consumo.

    Parâmetros
    ----------
    equipamentos : cadastro (colunas ``equipamento_id`` e, opcionalmente,
        ``potencia_nominal_kg_h``) para checar identificadores e leituras
        acima da capacidade do queimador.
    fator_kg_por_m3 : fator de conversão informado pelo fornecedor para
        leituras em m³ (fase vapor). Sem ele, leituras em m³ são rejeitadas.
    permitir_mistura : só com True o arquivo pode conter MEDIDO e SIMULADO.
    """
    rel = _Relatorio()
    hoje = hoje or date.today()
    total = len(df)
    df = df.copy()

    # 1. Colunas obrigatórias -------------------------------------------------
    faltantes = [c for c in COLUNAS_OBRIGATORIAS if c not in df.columns]
    if faltantes:
        rel.add(None, ", ".join(faltantes), ERRO, "Campos vazios",
                f"Colunas obrigatórias ausentes: {', '.join(faltantes)}.")
        return ResultadoValidacao(pd.DataFrame(columns=list(COLUNAS_REGISTRO) + ["consumo_kg"]),
                                  rel.df(), total, {"lidos": total, "aceitos": 0})
    for coluna in COLUNAS_REGISTRO:
        if coluna not in df.columns:
            df[coluna] = np.nan

    rejeitar = pd.Series(False, index=df.index)

    def erro(idx, campo, regra, msg):
        rel.add(idx, campo, ERRO, regra, msg)
        rejeitar.loc[idx] = True

    # 2. Campos vazios ---------------------------------------------------------
    for coluna in COLUNAS_OBRIGATORIAS:
        for idx in df.index[df[coluna].map(_vazio)]:
            erro(idx, coluna, "Campos vazios", f"Campo obrigatório '{coluna}' vazio.")

    # 3. Texto padronizado ----------------------------------------------------
    for coluna in ("setor", "origem", "consumo_unidade", "atividade_unidade", "equipamento_id"):
        df[coluna] = df[coluna].map(lambda v: np.nan if _vazio(v) else str(v).strip())
    for coluna in ("setor", "origem"):
        df[coluna] = df[coluna].str.upper()
    for coluna in ("consumo_unidade", "atividade_unidade"):
        df[coluna] = (df[coluna].str.lower().str.replace("³", "3", regex=False)
                      .str.replace("refeições", "refeicoes", regex=False)
                      .str.replace("usuários", "usuarios", regex=False))

    # 4. Datas e horas -------------------------------------------------------
    datas = pd.to_datetime(df["data"], errors="coerce", format="mixed", dayfirst=False)
    for idx in df.index[datas.isna() & ~df["data"].map(_vazio)]:
        erro(idx, "data", "Datas inválidas", f"Data inválida: '{df.at[idx, 'data']}'.")
    futuras = datas.dt.date > hoje
    for idx in df.index[futuras.fillna(False)]:
        erro(idx, "data", "Datas inválidas", f"Data futura: {datas[idx].date()}.")
    df["data"] = datas.dt.strftime("%Y-%m-%d")

    horas_txt = df["hora"].map(lambda v: "" if _vazio(v) else str(v).strip())
    horas = pd.to_datetime(horas_txt.where(horas_txt != ""), format="mixed", errors="coerce")
    for idx in df.index[(horas_txt != "") & horas.isna()]:
        erro(idx, "hora", "Datas inválidas", f"Hora inválida: '{horas_txt[idx]}'.")
    df["hora"] = horas.dt.strftime("%H:%M").where(horas.notna(), None)

    # 5. Domínios -------------------------------------------------------------
    for idx in df.index[df["setor"].notna() & ~df["setor"].isin(SETORES)]:
        erro(idx, "setor", "Unidades incompatíveis",
             f"Setor '{df.at[idx, 'setor']}' desconhecido. Use {', '.join(SETORES)}.")
    for idx in df.index[df["origem"].notna() & ~df["origem"].isin(ORIGENS_REGISTRO)]:
        erro(idx, "origem", "Campos vazios",
             f"Origem '{df.at[idx, 'origem']}' inválida. Use MEDIDO ou SIMULADO.")

    # 6. Números ---------------------------------------------------------------
    for coluna in COLUNAS_NUMERICAS:
        brutos = df[coluna]
        if brutos.dtype == object:
            brutos = brutos.map(lambda v: str(v).replace(",", ".") if isinstance(v, str) else v)
        numeros = pd.to_numeric(brutos, errors="coerce")
        invalidos = numeros.isna() & ~df[coluna].map(_vazio)
        for idx in df.index[invalidos]:
            erro(idx, coluna, "Leituras inconsistentes",
                 f"Valor não numérico em '{coluna}': '{df.at[idx, coluna]}'.")
        df[coluna] = numeros

    # 7. Valores negativos ---------------------------------------------------
    for coluna in ("consumo_valor", "atividade_valor", "tempo_funcionamento_h",
                   "tempo_sem_carga_h", "ciclos"):
        for idx in df.index[df[coluna] < 0]:
            erro(idx, coluna, "Valores negativos", f"Valor negativo em '{coluna}'.")

    # 8. Unidades --------------------------------------------------------------
    for idx in df.index[df["consumo_unidade"].notna() & ~df["consumo_unidade"].isin(UNIDADES_CONSUMO)]:
        erro(idx, "consumo_unidade", "Unidades incompatíveis",
             f"Unidade de consumo '{df.at[idx, 'consumo_unidade']}' não aceita (use kg, t ou m3).")
    if not fator_kg_por_m3:
        for idx in df.index[df["consumo_unidade"] == "m3"]:
            erro(idx, "consumo_unidade", "Unidades incompatíveis",
                 "Leitura em m³ sem fator de conversão para kg informado pelo fornecedor.")
    for idx in df.index:
        setor, unidade = df.at[idx, "setor"], df.at[idx, "atividade_unidade"]
        valor = df.at[idx, "atividade_valor"]
        if pd.notna(valor) and _vazio(unidade):
            erro(idx, "atividade_unidade", "Unidades incompatíveis",
                 "Atividade informada sem unidade.")
        elif not _vazio(unidade) and setor in UNIDADES_ATIVIDADE \
                and unidade not in UNIDADES_ATIVIDADE[setor]:
            erro(idx, "atividade_unidade", "Unidades incompatíveis",
                 f"Unidade de atividade '{unidade}' incompatível com o setor {setor}.")

    # 9. Tempo de funcionamento -------------------------------------------
    limite_horas = np.where(df["hora"].notna(), 1.0, 24.0)
    for idx in df.index[df["tempo_funcionamento_h"] > limite_horas]:
        erro(idx, "tempo_funcionamento_h", "Leituras inconsistentes",
             "Tempo de funcionamento maior que o período do registro.")
    for idx in df.index[(df["tempo_sem_carga_h"] > df["tempo_funcionamento_h"]).fillna(False)]:
        erro(idx, "tempo_sem_carga_h", "Leituras inconsistentes",
             "Tempo sem carga maior que o tempo de funcionamento.")

    # 10. Mistura de origens -------------------------------------------------
    origens = set(df.loc[df["origem"].isin(ORIGENS_REGISTRO), "origem"])
    if len(origens) > 1 and not permitir_mistura:
        for idx in df.index:
            rejeitar.loc[idx] = True
        rel.add(None, "origem", ERRO, "Mistura de origens",
                "O arquivo mistura registros MEDIDO e SIMULADO. Separe os arquivos "
                "ou autorize explicitamente a mistura.")

    # 11. Conversão para kg ---------------------------------------------------
    fatores = df["consumo_unidade"].map(FATOR_PARA_KG)
    if fator_kg_por_m3:
        fatores = fatores.where(df["consumo_unidade"] != "m3", fator_kg_por_m3)
    df["consumo_kg"] = df["consumo_valor"] * fatores

    # 12. Equipamentos e leituras acima da capacidade ----------------------
    if equipamentos is not None and len(equipamentos):
        cadastro = equipamentos.set_index("equipamento_id")
        conhecidos = set(cadastro.index)
        for idx in df.index[df["equipamento_id"].notna() & ~df["equipamento_id"].isin(conhecidos)]:
            rel.add(idx, "equipamento_id", AVISO, "Leituras inconsistentes",
                    f"Equipamento '{df.at[idx, 'equipamento_id']}' não cadastrado.")
        if "potencia_nominal_kg_h" in cadastro.columns:
            potencia = df["equipamento_id"].map(cadastro["potencia_nominal_kg_h"])
            horas_ref = df["tempo_funcionamento_h"].fillna(
                pd.Series(np.where(df["hora"].notna(), 1.0, 24.0), index=df.index))
            maximo = potencia * horas_ref * 1.10
            for idx in df.index[(df["consumo_kg"] > maximo).fillna(False)]:
                rel.add(idx, "consumo_valor", AVISO, "Leituras inconsistentes",
                        f"Consumo de {df.at[idx, 'consumo_kg']:.1f} kg acima do máximo "
                        f"nominal estimado ({maximo[idx]:.1f} kg). Revisar leitura.")

    # 13. Duplicados ------------------------------------------------------------
    chave = ["data", "hora", "setor", "equipamento_id"]
    duplicados = df.duplicated(subset=chave, keep="first") & ~rejeitar
    for idx in df.index[duplicados]:
        rel.add(idx, "data", AVISO, "Registros duplicados",
                "Registro repetido (mesma data, hora, setor e equipamento); mantido o primeiro.")

    aceitos = df.loc[~rejeitar & ~duplicados].copy()

    # 14. Dados ausentes (lacunas na série diária) ------------------------
    lacunas = {}
    if len(aceitos):
        for (setor, equip), grupo in aceitos.groupby(
                ["setor", aceitos["equipamento_id"].fillna("-")]):
            dias = pd.to_datetime(grupo["data"]).dt.normalize().drop_duplicates().sort_values()
            if len(dias) < 2:
                continue
            completos = pd.date_range(dias.iloc[0], dias.iloc[-1], freq="D")
            ausentes = completos.difference(dias)
            if len(ausentes):
                lacunas[f"{setor}/{equip}"] = len(ausentes)
        for serie, n in lacunas.items():
            rel.add(None, "data", AVISO, "Dados ausentes",
                    f"{serie}: {n} dia(s) sem registro no período (não interpolado). "
                    "Pode ser dia sem operação; confirmar.")

    aceitos = aceitos[list(COLUNAS_REGISTRO) + ["consumo_kg"]].reset_index(drop=True)
    resumo = {"lidos": total, "aceitos": len(aceitos),
              "rejeitados": int(rejeitar.sum()), "duplicados": int(duplicados.sum()),
              "series_com_lacunas": lacunas}
    return ResultadoValidacao(aceitos, rel.df(), total, resumo)
