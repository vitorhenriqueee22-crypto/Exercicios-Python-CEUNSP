"""Testes dos métodos estatísticos (seção 2.9 do relatório)."""

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from src import anomalias, estatistica

RNG = np.random.default_rng(42)


def test_descritiva_confere_com_numpy():
    x = RNG.normal(100, 10, 200)
    d = estatistica.descritiva(x)
    assert d["n"] == 200
    assert d["media"] == pytest.approx(np.mean(x))
    assert d["mediana"] == pytest.approx(np.median(x))
    assert d["desvio_padrao"] == pytest.approx(np.std(x, ddof=1))
    assert d["variancia"] == pytest.approx(np.var(x, ddof=1))
    assert d["cv_percentual"] == pytest.approx(np.std(x, ddof=1) / np.mean(x) * 100)
    assert d["iqr"] == pytest.approx(np.quantile(x, 0.75) - np.quantile(x, 0.25))
    assert d["moda"] is None          # contínua sem repetição


def test_moda_dados_discretos():
    assert estatistica.descritiva([1, 2, 2, 3, 2, 4])["moda"] == 2


def test_descritiva_amostra_vazia():
    with pytest.raises(ValueError):
        estatistica.descritiva([])


def test_shapiro_wilk():
    assert estatistica.shapiro_wilk(RNG.normal(0, 1, 100)).normal
    assert not estatistica.shapiro_wilk(RNG.exponential(1, 200)).normal
    assert np.isnan(estatistica.shapiro_wilk([1, 2]).p_valor)


def test_welch_detecta_reducao_real():
    antes = RNG.normal(120, 5, 60)
    depois = RNG.normal(110, 5, 60)          # redução verdadeira de 8,3 %
    r = estatistica.comparar_antes_depois(antes, depois, pareado=False)
    assert r.teste == "t de Welch"
    assert r.significativo
    assert r.ic95_reducao[0] < 10 < r.ic95_reducao[1]
    esperado = stats.ttest_ind(antes, depois, equal_var=False, alternative="greater").pvalue
    assert r.p_valor == pytest.approx(esperado)


def test_sem_reducao_nao_e_significativo():
    antes, depois = RNG.normal(100, 5, 50), RNG.normal(100, 5, 50)
    assert not estatistica.comparar_antes_depois(antes, depois, pareado=False).significativo


def test_aumento_nao_e_reducao():
    antes, depois = RNG.normal(100, 5, 50), RNG.normal(110, 5, 50)
    r = estatistica.comparar_antes_depois(antes, depois, pareado=False)
    assert not r.significativo
    assert r.reducao_percentual < 0


def test_pareado_usa_t_pareado_e_confere_com_scipy():
    base = RNG.normal(120, 10, 20)
    antes, depois = base, base - 3 + RNG.normal(0, 1, 20)
    r = estatistica.comparar_antes_depois(antes, depois, pareado=True)
    assert r.teste.startswith("t pareado")
    assert r.p_valor == pytest.approx(stats.ttest_rel(antes, depois, alternative="greater").pvalue)
    assert r.significativo


def test_nao_normal_escolhe_teste_nao_parametrico():
    antes = RNG.exponential(10, 80) + 100
    depois = RNG.exponential(10, 80) + 95
    r = estatistica.comparar_antes_depois(antes, depois, pareado=False)
    assert r.teste == "Mann-Whitney"
    rp = estatistica.comparar_antes_depois(antes[:30], depois[:30], pareado=True,
                                           metodo="nao_parametrico")
    assert rp.teste.startswith("Wilcoxon")


def test_pareado_exige_mesmo_tamanho():
    with pytest.raises(ValueError):
        estatistica.comparar_antes_depois([1, 2, 3, 4], [1, 2, 3], pareado=True)


def test_regressao_recupera_coeficientes():
    n = 300
    x1, x2 = RNG.uniform(0, 10, n), RNG.uniform(0, 5, n)
    y = 14 + 3.2 * x1 + 85 * x2 + RNG.normal(0, 2, n)
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2})
    reg = estatistica.regressao_linear(df, "y", ["x1", "x2"])
    coef = reg.coeficientes["coef"]
    assert coef["intercepto"] == pytest.approx(14, abs=1.0)
    assert coef["x1"] == pytest.approx(3.2, abs=0.1)
    assert coef["x2"] == pytest.approx(85, abs=0.5)
    assert reg.r2 > 0.99
    assert 1.6 < reg.durbin_watson < 2.4
    prev = reg.prever({"x1": [5.0], "x2": [2.0]})
    verdadeiro = 14 + 3.2 * 5 + 85 * 2
    assert prev["pi_inf"].iloc[0] < verdadeiro < prev["pi_sup"].iloc[0]


def test_regressao_simples_confere_com_linregress():
    x = RNG.uniform(100, 700, 80)
    y = 14 + 0.032 * x + RNG.normal(0, 1, 80)
    reg = estatistica.regressao_linear(pd.DataFrame({"x": x, "y": y}), "y", ["x"])
    ref = stats.linregress(x, y)
    assert reg.coeficientes.loc["x", "coef"] == pytest.approx(ref.slope)
    assert reg.coeficientes.loc["x", "p_valor"] == pytest.approx(ref.pvalue, rel=1e-6, abs=1e-300)
    assert reg.r2 == pytest.approx(ref.rvalue ** 2)


def test_vif_e_tamanho_amostra():
    x1 = RNG.normal(0, 1, 200)
    df = pd.DataFrame({"a": x1, "b": RNG.normal(0, 1, 200), "c": x1 * 2 + RNG.normal(0, 0.05, 200)})
    vif = estatistica.fator_inflacao_variancia(df, ["a", "b", "c"])
    assert vif["b"] < 1.5 and vif["a"] > 10
    assert estatistica.tamanho_amostra_por_periodo(5, 2.5) == 25   # ((1,645+0,842)·2)² ≈ 24,7


def test_correlacao():
    x = np.arange(50, dtype=float)
    c = estatistica.correlacao(x, 2 * x + 1)
    assert c["pearson_r"] == pytest.approx(1.0)
    assert c["spearman_rho"] == pytest.approx(1.0)


def test_anomalias_detectam_valor_inserido():
    x = pd.Series(RNG.normal(50, 2, 100))
    x.iloc[40] = 80
    assert anomalias.cercas_tukey(x)["anomalia"].iloc[40]
    z = anomalias.escore_z_robusto(x)
    assert z["anomalia"].iloc[40] and z["anomalia"].sum() <= 3


def test_carta_imr_limites():
    x = pd.Series([10.0, 12.0, 11.0, 13.0, 12.0])
    carta = anomalias.carta_imr(x)
    mr = np.mean([2, 1, 2, 1])
    assert carta.lsc == pytest.approx(x.mean() + 2.66 * mr, abs=0.01)
    assert carta.lic == pytest.approx(x.mean() - 2.66 * mr, abs=0.01)


def test_cusum_e_consumo_sem_atividade():
    assert anomalias.cusum([1, -1, 2]).tolist() == [1, 0, 2]
    df = pd.DataFrame({"consumo_kg": [5.0, 3.0, 0.0], "atividade_valor": [0, 2, 0]})
    assert len(anomalias.consumo_sem_atividade(df)) == 1
