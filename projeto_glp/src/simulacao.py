# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Experimentação e Análise de Dados
# Aluno: Vitor Henrique Santos Das Virgens
# Projeto: Monitoramento e otimização do consumo de GLP
# Módulo: simulacao — cenários de economia (Equação 14)
# ============================================================
"""Simulação de cenários de redução de consumo.

Os resultados são SIMULAÇÕES ("quanto valeria uma redução de r %") e não
economias alcançadas. Economia verificada exige comparação com a linha de base
ajustada (Equação 4) e teste estatístico (seção 2.9.3).
"""

from __future__ import annotations

import pandas as pd

REDUCOES_PADRAO = (0.03, 0.05, 0.08, 0.10, 0.15)
ROTULO = "SIMULAÇÃO"


def cenarios_economia(consumo_diario_kg: float, preco_r_kg: float,
                      reducoes=REDUCOES_PADRAO, dias_mes: int = 22,
                      dias_ano: int = 264, atividade_diaria: float | None = None) -> pd.DataFrame:
    """ΔG = G·r; ΔC_dia = ΔG·p; ΔC_mês = ΔC_dia·D_mês; ΔC_ano = ΔC_dia·D_ano."""
    if consumo_diario_kg < 0 or preco_r_kg < 0:
        raise ValueError("Consumo e preço não podem ser negativos.")
    linhas = []
    for r in reducoes:
        if not 0 <= r < 1:
            raise ValueError("A redução deve estar entre 0 e 1 (fração).")
        kg_dia = consumo_diario_kg * r
        linha = {
            "reducao_pct": r * 100,
            "consumo_atual_kg_dia": consumo_diario_kg,
            "consumo_otimizado_kg_dia": consumo_diario_kg - kg_dia,
            "glp_economizado_kg_dia": kg_dia,
            "glp_economizado_kg_mes": kg_dia * dias_mes,
            "glp_economizado_kg_ano": kg_dia * dias_ano,
            "economia_r_dia": kg_dia * preco_r_kg,
            "economia_r_mes": kg_dia * preco_r_kg * dias_mes,
            "economia_r_ano": kg_dia * preco_r_kg * dias_ano,
            "classificacao": ROTULO,
        }
        if atividade_diaria:
            linha["consumo_especifico_atual"] = consumo_diario_kg / atividade_diaria
            linha["consumo_especifico_otimizado"] = (consumo_diario_kg - kg_dia) / atividade_diaria
        linhas.append(linha)
    return pd.DataFrame(linhas)


def retorno_simples_meses(investimento_r: float, economia_mensal_r: float) -> float:
    """Retorno simples (sem desconto) = investimento / economia mensal."""
    if economia_mensal_r <= 0:
        return float("inf")
    return investimento_r / economia_mensal_r
