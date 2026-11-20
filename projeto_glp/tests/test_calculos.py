"""Testes das fórmulas físicas, de custo e de simulação (Equações 1 a 14 e 25-26)."""

import math

import pandas as pd
import pytest

from src import chuveiros, fundicao, reservatorio, simulacao
from src.constantes import (
    CALCULADO, HIPOTESE, MEDIDO, PCI_KJ_KG, PCI_KWH_KG, REFERENCIA, SIMULADO, kg_para_kwh,
    origem_resultante,
)


def test_conversao_pci():
    # 11.100 kcal/kg × 4,1868 kJ/kcal (Tabela 1 do relatório)
    assert PCI_KJ_KG == pytest.approx(46_473.48)
    assert PCI_KWH_KG == pytest.approx(12.909, abs=1e-3)
    assert kg_para_kwh(10) == pytest.approx(129.09, abs=0.01)


@pytest.mark.parametrize("entradas, esperado", [
    ((MEDIDO, REFERENCIA), CALCULADO),
    ((MEDIDO, HIPOTESE), HIPOTESE),
    ((REFERENCIA, HIPOTESE, SIMULADO), SIMULADO),
    ((CALCULADO, MEDIDO), CALCULADO),
])
def test_origem_herda_classe_mais_fraca(entradas, esperado):
    assert origem_resultante(*entradas) == esperado


def test_origem_desconhecida():
    with pytest.raises(ValueError):
        origem_resultante("INVENTADO")


def test_exemplo_tabela_2_do_relatorio():
    # 100 L, ΔT = 20 K, η = 0,80 -> 8.360 kJ e 0,225 kg (Tabela 2)
    q = chuveiros.calor_aquecimento_kj(100, 20)
    assert q == pytest.approx(8_360)
    assert chuveiros.glp_para_calor_kg(q, 0.80) == pytest.approx(0.2249, abs=1e-4)


def test_volume_e_glp_por_banho():
    assert chuveiros.volume_diario_l(10, 8, 6) == 480
    kg = chuveiros.glp_por_banho_kg(8, 6, 20, 0.8)
    assert kg == pytest.approx(48 * 4.18 * 20 / (0.8 * PCI_KJ_KG))


def test_rendimento_invalido():
    with pytest.raises(ValueError):
        chuveiros.glp_para_calor_kg(1000, 1.5)


def test_perda_termica():
    assert chuveiros.perda_termica_w(2.0, 3.0, 60, 20) == pytest.approx(240.0)


def test_balanco_termico_forno():
    # 1 t de metal: 0,9·(660−25) + 397 + 1,18·(720−660) = 1.039,3 kJ/kg
    q = fundicao.calor_util_kj(1000, 0.9, 1.18, 397, 25, 660, 720)
    assert q == pytest.approx(1_039_300)
    eta = fundicao.eficiencia_forno(q, 100.0)
    assert float(eta) == pytest.approx(1_039_300 / (100 * PCI_KJ_KG))


def test_cenarios_economia():
    cen = simulacao.cenarios_economia(400, 7.0, [0.05, 0.10], dias_mes=22, dias_ano=264,
                                      atividade_diaria=2.0)
    linha = cen.iloc[1]
    assert linha["glp_economizado_kg_dia"] == pytest.approx(40)
    assert linha["economia_r_dia"] == pytest.approx(280)
    assert linha["economia_r_mes"] == pytest.approx(280 * 22)
    assert linha["economia_r_ano"] == pytest.approx(280 * 264)
    assert linha["consumo_especifico_otimizado"] == pytest.approx(180)
    assert set(cen["classificacao"]) == {"SIMULAÇÃO"}


@pytest.mark.parametrize("reducao", [-0.1, 1.0, 1.5])
def test_cenario_reducao_invalida(reducao):
    with pytest.raises(ValueError):
        simulacao.cenarios_economia(100, 7, [reducao])


def test_retorno_simples():
    assert simulacao.retorno_simples_meses(112_000, 5_800) == pytest.approx(19.31, abs=0.01)
    assert math.isinf(simulacao.retorno_simples_meses(1000, 0))


def test_balanco_de_massa_do_tanque():
    consumo = pd.Series([100.0, 100.0, 100.0], index=pd.date_range("2026-01-01", periods=3))
    abast = pd.DataFrame({"data": ["2026-01-02"], "massa_kg": [500.0]})
    estado = reservatorio.balanco_massa(consumo, abast, 1000, 2000)
    assert estado["estoque_kg"].tolist() == [900.0, 1300.0, 1200.0]
    assert estado["percentual"].iloc[-1] == pytest.approx(60.0)
    assert reservatorio.autonomia_dias(1200, 200, 100) == pytest.approx(10.0)


def test_alertas_do_tanque():
    parametros = {"capacidade_nominal_kg": 1000, "fracao_maxima_enchimento": 0.85,
                  "estoque_minimo_reserva_kg": 100, "nivel_alerta_percentual": 30}
    consumo = pd.Series([400.0, 400.0], index=pd.date_range("2026-01-01", periods=2))
    estado = reservatorio.balanco_massa(consumo, pd.DataFrame(columns=["data", "massa_kg"]), 900, 1000)
    niveis = {a["nivel"] for a in reservatorio.alertas(estado, parametros, 400)}
    assert "atencao" in niveis
    negativo = reservatorio.balanco_massa(consumo, pd.DataFrame(columns=["data", "massa_kg"]), 500, 1000)
    assert any("negativo" in a["mensagem"] for a in reservatorio.alertas(negativo, parametros, 400))
