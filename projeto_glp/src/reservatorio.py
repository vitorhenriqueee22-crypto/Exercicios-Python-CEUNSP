# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Experimentação e Análise de Dados
# Aluno: Vitor Henrique Santos Das Virgens
# Projeto: Monitoramento e otimização do consumo de GLP
# Módulo: reservatorio — monitoramento VIRTUAL do tanque (balanço de massa)
# ============================================================
"""Monitoramento virtual do reservatório (seção 2.10 do relatório).

Enquanto não houver sensor de nível integrado, o estoque é ESTIMADO por
balanço de massa: S_t = S_{t−1} + A_t − G_t (Equação 25).

Capacidade nominal (massa de GLP) não é o mesmo que capacidade volumétrica
(volume de água) nem que limite seguro de enchimento: os três vêm do
fabricante, da distribuidora e da norma aplicável.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def balanco_massa(consumo_diario: pd.Series, abastecimentos: pd.DataFrame,
                  estoque_inicial_kg: float, capacidade_nominal_kg: float) -> pd.DataFrame:
    """Estoque estimado ao fim de cada dia.

    consumo_diario : série indexada por data com o consumo total (kg).
    abastecimentos : colunas ``data`` e ``massa_kg`` (notas fiscais).
    """
    consumo = consumo_diario.copy()
    consumo.index = pd.to_datetime(consumo.index)
    if len(abastecimentos):
        ab = abastecimentos.copy()
        ab["data"] = pd.to_datetime(ab["data"])
        entrada = ab.groupby("data")["massa_kg"].sum()
        inicio = min(consumo.index.min(), entrada.index.min())
        fim = max(consumo.index.max(), entrada.index.max())
    else:
        entrada = pd.Series(dtype=float)
        inicio, fim = consumo.index.min(), consumo.index.max()
    dias = pd.date_range(inicio, fim, freq="D")
    consumo = consumo.reindex(dias, fill_value=0.0)
    entrada = entrada.reindex(dias, fill_value=0.0)
    estoque = estoque_inicial_kg + (entrada - consumo).cumsum()
    return pd.DataFrame({
        "consumo_kg": consumo, "abastecimento_kg": entrada, "estoque_kg": estoque,
        "percentual": estoque / capacidade_nominal_kg * 100,
    }).rename_axis("data")


def autonomia_dias(estoque_kg: float, reserva_kg: float, consumo_medio_diario_kg: float) -> float:
    """Equação 26: Aut = (S_t − S_res) / Ḡ_dia."""
    if consumo_medio_diario_kg <= 0:
        return float("inf")
    return max(estoque_kg - reserva_kg, 0.0) / consumo_medio_diario_kg


def alertas(estado: pd.DataFrame, parametros: dict, consumo_medio_diario_kg: float) -> list[dict]:
    """Alertas de nível baixo, estoque abaixo da reserva, enchimento acima do
    limite configurado e estoque estimado negativo (inconsistência)."""
    ultimo = estado.iloc[-1]
    capacidade = parametros["capacidade_nominal_kg"]
    saida = []
    if ultimo["estoque_kg"] < 0:
        saida.append({"nivel": "critico", "mensagem":
                      "Estoque estimado negativo: faltam abastecimentos no registro ou há erro de medição."})
    elif ultimo["percentual"] < parametros["nivel_alerta_percentual"]:
        saida.append({"nivel": "atencao", "mensagem":
                      f"Nível estimado de {ultimo['percentual']:.0f} %, abaixo do alerta de "
                      f"{parametros['nivel_alerta_percentual']:.0f} %. Programar abastecimento."})
    if 0 <= ultimo["estoque_kg"] < parametros["estoque_minimo_reserva_kg"]:
        saida.append({"nivel": "critico", "mensagem": "Estoque estimado abaixo da reserva mínima."})
    limite = capacidade * parametros["fracao_maxima_enchimento"]
    acima = estado[estado["estoque_kg"] > limite * 1.001]
    if len(acima):
        saida.append({"nivel": "serio", "mensagem":
                      f"Em {len(acima)} dia(s) o estoque estimado superou o limite de enchimento "
                      f"configurado ({limite:,.0f} kg). Verificar notas e parâmetros do tanque."
                      .replace(",", ".")})
    aut = autonomia_dias(ultimo["estoque_kg"], parametros["estoque_minimo_reserva_kg"],
                         consumo_medio_diario_kg)
    if np.isfinite(aut) and aut < 3:
        saida.append({"nivel": "atencao", "mensagem": f"Autonomia estimada de {aut:.1f} dia(s)."})
    return saida


def conciliacao(estado: pd.DataFrame, abastecimentos: pd.DataFrame,
                capacidade_nominal_kg: float) -> pd.DataFrame:
    """Compara a leitura do indicador de nível informada no abastecimento com o
    estoque estimado; diferença crescente indica erro de medição ou perda."""
    if "nivel_antes_pct" not in abastecimentos.columns or not len(abastecimentos):
        return pd.DataFrame()
    ab = abastecimentos.copy()
    ab["data"] = pd.to_datetime(ab["data"])
    linhas = []
    for _, linha in ab.iterrows():
        dia_anterior = linha["data"] - pd.Timedelta(days=1)
        if dia_anterior not in estado.index or pd.isna(linha["nivel_antes_pct"]):
            continue
        estimado = estado.loc[dia_anterior, "estoque_kg"]
        lido = linha["nivel_antes_pct"] / 100 * capacidade_nominal_kg
        linhas.append({"data": linha["data"], "estoque_estimado_kg": estimado,
                       "estoque_lido_kg": lido, "diferenca_kg": lido - estimado})
    return pd.DataFrame(linhas)
