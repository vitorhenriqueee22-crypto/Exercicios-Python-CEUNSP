# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Experimentação e Análise de Dados
# Aluno: Vitor Henrique Santos Das Virgens
# Projeto: Monitoramento e otimização do consumo de GLP
# Módulo: estatistica — descritiva, inferência, correlação e regressão
# ============================================================
"""Métodos estatísticos do projeto (seção 2.9 do relatório).

- Estatística descritiva (Equações 15 a 17);
- Diagnóstico de normalidade de Shapiro-Wilk;
- Comparação antes/depois de intervenções (Quadro 8): t pareado, Wilcoxon,
  t de Welch e Mann-Whitney, com IC 95 % e tamanho de efeito;
- Correlação de Pearson e de Spearman;
- Regressão linear por mínimos quadrados, com erros-padrão, valores p,
  R² ajustado, Durbin-Watson e intervalos de predição.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats

ALFA_PADRAO = 0.05


# ---------------------------------------------------------------------------
# Estatística descritiva
# ---------------------------------------------------------------------------
def descritiva(valores, casas_moda: int | None = None) -> dict:
    """Média, mediana, moda, variância, desvio-padrão, mínimo, máximo,
    quartis, amplitude interquartil e coeficiente de variação.

    A moda só é calculada para dados discretos ou quando ``casas_moda`` é
    informado (dados contínuos arredondados em classes)."""
    x = pd.Series(valores, dtype=float).dropna()
    n = len(x)
    if n == 0:
        raise ValueError("Amostra vazia.")
    media = x.mean()
    desvio = x.std(ddof=1) if n > 1 else np.nan
    q1, q3 = x.quantile(0.25), x.quantile(0.75)
    moda = None
    base = x.round(casas_moda) if casas_moda is not None else x
    if casas_moda is not None or np.allclose(x, x.round()):
        contagens = base.value_counts()
        if len(contagens) and contagens.iloc[0] > 1:
            moda = float(contagens.index[0])
    return {
        "n": n,
        "media": media,
        "mediana": x.median(),
        "moda": moda,
        "variancia": x.var(ddof=1) if n > 1 else np.nan,
        "desvio_padrao": desvio,
        "minimo": x.min(),
        "maximo": x.max(),
        "q1": q1,
        "q3": q3,
        "iqr": q3 - q1,
        "cv_percentual": desvio / media * 100 if media else np.nan,
    }


# ---------------------------------------------------------------------------
# Normalidade
# ---------------------------------------------------------------------------
@dataclass
class ResultadoNormalidade:
    estatistica: float
    p_valor: float
    n: int
    normal: bool
    observacao: str


def shapiro_wilk(valores, alfa: float = ALFA_PADRAO) -> ResultadoNormalidade:
    """Teste de Shapiro-Wilk (Shapiro; Wilk, 1965). H0: os dados são normais."""
    x = pd.Series(valores, dtype=float).dropna().to_numpy()
    n = len(x)
    if n < 3:
        return ResultadoNormalidade(np.nan, np.nan, n, False,
                                    "Amostra com menos de 3 valores: teste não aplicável.")
    if np.allclose(x, x[0]):
        return ResultadoNormalidade(np.nan, np.nan, n, False,
                                    "Valores constantes: teste não aplicável.")
    w, p = stats.shapiro(x)
    obs = ""
    if n < 20:
        obs = "Amostra pequena: o teste tem pouco poder para detectar não normalidade."
    elif n > 5000:
        obs = "Amostra grande: desvios pequenos e sem importância prática levam à rejeição."
    return ResultadoNormalidade(float(w), float(p), n, bool(p >= alfa), obs)


# ---------------------------------------------------------------------------
# Comparação antes × depois (Quadro 8)
# ---------------------------------------------------------------------------
@dataclass
class ResultadoComparacao:
    teste: str
    pareado: bool
    n_antes: int
    n_depois: int
    media_antes: float
    media_depois: float
    reducao_media: float              # antes − depois (positiva = redução)
    reducao_percentual: float
    ic95_reducao: tuple[float, float]
    ic95_reducao_percentual: tuple[float, float]
    estatistica: float
    p_valor: float
    tamanho_efeito: float
    alfa: float
    significativo: bool
    normalidade: dict = field(default_factory=dict)
    hipoteses: tuple[str, str] = ("", "")
    conclusao: str = ""
    ressalvas: list[str] = field(default_factory=list)


def _ic_media(d: np.ndarray, confianca: float = 0.95) -> tuple[float, float]:
    n = len(d)
    if n < 2:
        return (np.nan, np.nan)
    erro = stats.sem(d)
    t = stats.t.ppf((1 + confianca) / 2, n - 1)
    return (float(d.mean() - t * erro), float(d.mean() + t * erro))


def _ic_welch(a: np.ndarray, b: np.ndarray, confianca: float = 0.95) -> tuple[float, float]:
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    gl = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
    t = stats.t.ppf((1 + confianca) / 2, gl)
    dif = a.mean() - b.mean()
    margem = t * np.sqrt(va + vb)
    return (float(dif - margem), float(dif + margem))


def comparar_antes_depois(antes, depois, pareado: bool, alfa: float = ALFA_PADRAO,
                          metodo: str = "auto") -> ResultadoComparacao:
    """Verifica se o consumo (de preferência específico) diminuiu após uma
    intervenção.

    Hipóteses unilaterais (seção 2.9.3):
        H0: μ_d ≤ 0 — a intervenção não reduz o consumo médio;
        H1: μ_d > 0 — a intervenção reduz o consumo médio,
    com d = antes − depois.

    ``metodo``: "auto" (escolha pelo Quadro 8), "parametrico" ou
    "nao_parametrico".
    """
    a = pd.Series(antes, dtype=float).dropna().to_numpy()
    b = pd.Series(depois, dtype=float).dropna().to_numpy()
    if pareado and len(antes) != len(depois):
        raise ValueError("Dados pareados exigem o mesmo número de observações antes e depois.")
    if pareado:
        mascara = ~(pd.isna(pd.Series(antes, dtype=float)).to_numpy()
                    | pd.isna(pd.Series(depois, dtype=float)).to_numpy())
        a = np.asarray(antes, dtype=float)[mascara]
        b = np.asarray(depois, dtype=float)[mascara]
    if len(a) < 3 or len(b) < 3:
        raise ValueError("São necessárias ao menos 3 observações em cada período.")

    hipoteses = ("H0: a intervenção não reduz o consumo médio (μ_d ≤ 0)",
                 "H1: a intervenção reduz o consumo médio (μ_d > 0)")
    media_a, media_b = float(a.mean()), float(b.mean())
    ressalvas: list[str] = []

    if pareado:
        d = a - b
        norm = shapiro_wilk(d, alfa)
        normalidade = {"diferencas": norm}
        usar_param = norm.normal if metodo == "auto" else metodo == "parametrico"
        if usar_param:
            res = stats.ttest_rel(a, b, alternative="greater")
            teste, estat, p = "t pareado (Student)", float(res.statistic), float(res.pvalue)
        else:
            res = stats.wilcoxon(d, alternative="greater", zero_method="wilcox")
            teste, estat, p = "Wilcoxon dos postos sinalizados", float(res.statistic), float(res.pvalue)
        ic = _ic_media(d)
        efeito = float(d.mean() / d.std(ddof=1)) if d.std(ddof=1) > 0 else np.nan
        reducao = float(d.mean())
    else:
        na, nb = shapiro_wilk(a, alfa), shapiro_wilk(b, alfa)
        normalidade = {"antes": na, "depois": nb}
        usar_param = (na.normal and nb.normal) if metodo == "auto" else metodo == "parametrico"
        if usar_param:
            res = stats.ttest_ind(a, b, equal_var=False, alternative="greater")
            teste, estat, p = "t de Welch", float(res.statistic), float(res.pvalue)
        else:
            res = stats.mannwhitneyu(a, b, alternative="greater")
            teste, estat, p = "Mann-Whitney", float(res.statistic), float(res.pvalue)
        ic = _ic_welch(a, b)
        desvio_comb = np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
        efeito = float((media_a - media_b) / desvio_comb) if desvio_comb > 0 else np.nan
        reducao = media_a - media_b
        ressalvas.append("Amostras independentes: confirme que as condições operacionais "
                         "(produção, mix, estação) são comparáveis entre os períodos.")

    reducao_pct = reducao / media_a * 100 if media_a else np.nan
    ic_pct = tuple(v / media_a * 100 for v in ic) if media_a else (np.nan, np.nan)
    significativo = bool(p < alfa)
    if significativo:
        conclusao = (f"Rejeita-se H0 ao nível de {alfa:.0%}: há evidência estatística de "
                     f"redução média de {reducao:.3g} ({reducao_pct:.1f} %), com IC 95 % de "
                     f"{ic[0]:.3g} a {ic[1]:.3g}.")
    else:
        conclusao = (f"Não se rejeita H0 ao nível de {alfa:.0%}: os dados não permitem afirmar "
                     f"que houve redução (p = {p:.3g}).")
    if min(len(a), len(b)) < 10:
        ressalvas.append("Amostra pequena: o teste tem baixo poder; uma redução real pode não ser detectada.")
    ressalvas.append("Séries diárias podem ser autocorrelacionadas; verifique o Durbin-Watson "
                     "dos resíduos ou agregue por semana.")
    return ResultadoComparacao(
        teste=teste, pareado=pareado, n_antes=len(a), n_depois=len(b),
        media_antes=media_a, media_depois=media_b, reducao_media=reducao,
        reducao_percentual=reducao_pct, ic95_reducao=ic, ic95_reducao_percentual=ic_pct,
        estatistica=estat, p_valor=p, tamanho_efeito=efeito, alfa=alfa,
        significativo=significativo, normalidade=normalidade, hipoteses=hipoteses,
        conclusao=conclusao, ressalvas=ressalvas,
    )


def tamanho_amostra_por_periodo(desvio_padrao: float, reducao_minima: float,
                                alfa: float = ALFA_PADRAO, poder: float = 0.80,
                                pareado: bool = True) -> int:
    """Número aproximado de observações por período para detectar uma redução
    mínima com teste unilateral (aproximação normal)."""
    if reducao_minima <= 0 or desvio_padrao <= 0:
        raise ValueError("Desvio-padrão e redução mínima devem ser positivos.")
    z = stats.norm.ppf(1 - alfa) + stats.norm.ppf(poder)
    fator = 1 if pareado else 2
    return int(np.ceil(fator * (z * desvio_padrao / reducao_minima) ** 2))


# ---------------------------------------------------------------------------
# Correlação
# ---------------------------------------------------------------------------
def correlacao(x, y) -> dict:
    """Coeficientes de Pearson (linear) e de Spearman (monotônico)."""
    dados = pd.DataFrame({"x": x, "y": y}).astype(float).dropna()
    if len(dados) < 3:
        raise ValueError("São necessários ao menos 3 pares de valores.")
    pr = stats.pearsonr(dados["x"], dados["y"])
    sr = stats.spearmanr(dados["x"], dados["y"])
    return {"n": len(dados), "pearson_r": float(pr.statistic), "pearson_p": float(pr.pvalue),
            "spearman_rho": float(sr.statistic), "spearman_p": float(sr.pvalue)}


def matriz_correlacao(df: pd.DataFrame, metodo: str = "pearson") -> pd.DataFrame:
    return df.astype(float).corr(method=metodo)


# ---------------------------------------------------------------------------
# Regressão linear (mínimos quadrados ordinários)
# ---------------------------------------------------------------------------
@dataclass
class ResultadoRegressao:
    variaveis: list[str]
    coeficientes: pd.DataFrame        # coef, erro_padrao, t, p_valor, ic95_inf, ic95_sup
    r2: float
    r2_ajustado: float
    erro_padrao_residual: float
    n: int
    gl_residuos: int
    durbin_watson: float
    residuos: pd.Series
    ajustados: pd.Series
    _xtx_inv: np.ndarray = field(repr=False, default=None)

    def prever(self, novos: pd.DataFrame | dict, confianca: float = 0.95) -> pd.DataFrame:
        """Previsão com intervalo de predição (para uma nova observação)."""
        novos = pd.DataFrame(novos)
        X = np.column_stack([np.ones(len(novos))] + [novos[v].astype(float) for v in self.variaveis])
        beta = self.coeficientes["coef"].to_numpy()
        previsto = X @ beta
        t = stats.t.ppf((1 + confianca) / 2, self.gl_residuos)
        var_pred = self.erro_padrao_residual ** 2 * (1 + np.einsum("ij,jk,ik->i", X, self._xtx_inv, X))
        margem = t * np.sqrt(var_pred)
        return pd.DataFrame({"previsto": previsto, "pi_inf": previsto - margem,
                             "pi_sup": previsto + margem}, index=novos.index)

    def equacao(self, nome_y: str = "y", casas: int = 4) -> str:
        termos = [f"{self.coeficientes.loc['intercepto', 'coef']:.{casas}g}"]
        for v in self.variaveis:
            c = self.coeficientes.loc[v, "coef"]
            termos.append(f"{'+' if c >= 0 else '−'} {abs(c):.{casas}g}·{v}")
        return f"{nome_y} = " + " ".join(termos)


def durbin_watson(residuos) -> float:
    """Estatística de Durbin-Watson (Durbin; Watson, 1950). Valores próximos
    de 2 indicam ausência de autocorrelação de primeira ordem."""
    e = np.asarray(residuos, dtype=float)
    return float(np.sum(np.diff(e) ** 2) / np.sum(e ** 2))


def regressao_linear(df: pd.DataFrame, y: str, xs: list[str]) -> ResultadoRegressao:
    """Ajusta y = β0 + Σ βi·xi + ε por mínimos quadrados ordinários."""
    dados = df[[y] + list(xs)].astype(float).dropna()
    n, k = len(dados), len(xs)
    if n <= k + 1:
        raise ValueError("Observações insuficientes para o número de variáveis.")
    X = np.column_stack([np.ones(n)] + [dados[v].to_numpy() for v in xs])
    Y = dados[y].to_numpy()
    xtx_inv = np.linalg.pinv(X.T @ X)
    beta = xtx_inv @ X.T @ Y
    ajustados = X @ beta
    residuos = Y - ajustados
    gl = n - k - 1
    sse = float(residuos @ residuos)
    sst = float(((Y - Y.mean()) ** 2).sum())
    s2 = sse / gl
    ep = np.sqrt(np.diag(xtx_inv) * s2)
    t_val = np.divide(beta, ep, out=np.full_like(beta, np.nan), where=ep > 0)
    p_val = 2 * stats.t.sf(np.abs(t_val), gl)
    tcrit = stats.t.ppf(0.975, gl)
    nomes = ["intercepto"] + list(xs)
    coef = pd.DataFrame({"coef": beta, "erro_padrao": ep, "t": t_val, "p_valor": p_val,
                         "ic95_inf": beta - tcrit * ep, "ic95_sup": beta + tcrit * ep},
                        index=nomes)
    r2 = 1 - sse / sst if sst > 0 else np.nan
    r2_aj = 1 - (1 - r2) * (n - 1) / gl if sst > 0 else np.nan
    return ResultadoRegressao(
        variaveis=list(xs), coeficientes=coef, r2=r2, r2_ajustado=r2_aj,
        erro_padrao_residual=float(np.sqrt(s2)), n=n, gl_residuos=gl,
        durbin_watson=durbin_watson(residuos),
        residuos=pd.Series(residuos, index=dados.index),
        ajustados=pd.Series(ajustados, index=dados.index), _xtx_inv=xtx_inv,
    )


def fator_inflacao_variancia(df: pd.DataFrame, xs: list[str]) -> pd.Series:
    """VIF de cada variável explicativa. VIF > 5 indica multicolinearidade:
    os coeficientes individuais ficam imprecisos, embora a previsão possa
    continuar boa."""
    dados = df[list(xs)].astype(float).dropna()
    saida = {}
    for v in xs:
        outras = [o for o in xs if o != v]
        if not outras:
            saida[v] = 1.0
            continue
        r2 = regressao_linear(dados, v, outras).r2
        saida[v] = 1 / (1 - r2) if r2 < 1 else np.inf
    return pd.Series(saida, name="vif")


def tendencia(serie: pd.Series) -> dict:
    """Tendência linear de uma série temporal (inclinação por período)."""
    s = pd.Series(serie, dtype=float).dropna()
    if len(s) < 3:
        raise ValueError("Série curta demais para estimar tendência.")
    t = np.arange(len(s))
    res = stats.linregress(t, s.to_numpy())
    media = s.mean()
    return {"inclinacao_por_periodo": float(res.slope),
            "variacao_percentual_por_periodo": float(res.slope / media * 100) if media else np.nan,
            "p_valor": float(res.pvalue), "r2": float(res.rvalue ** 2),
            "significativa": bool(res.pvalue < ALFA_PADRAO)}
