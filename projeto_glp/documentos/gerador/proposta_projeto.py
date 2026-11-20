"""
Trabalho escrito (normas ABNT) da Proposta de Projeto:
"Otimização de Processos Baseada em Inferência Estatística", aplicada ao
consumo de GLP industrial.

Estrutura pedida no enunciado da disciplina:
    a) Resumo
    b) Contexto e Problema de Engenharia
    c) Formulação das Hipóteses Estatísticas
    d) Metodologia de Inferência Estatística
    e) Referências

Execução (a partir da raiz do repositório):
    python projeto_glp/documentos/gerador/proposta_projeto.py

Os números da aplicação demonstrativa são calculados no momento da geração
pelo código do sistema (pasta projeto_glp/src), com dados SIMULADOS.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
RAIZ_PROJETO = AQUI.parents[1]
for caminho in (AQUI, RAIZ_PROJETO):
    if str(caminho) not in sys.path:
        sys.path.insert(0, str(caminho))

from abnt_docx import Conteudo, DocumentoABNT, Metadados, paginar_com_libreoffice  # noqa: E402
from src import chuveiros, dados_simulados, estatistica, fundicao, relatorios, restaurante  # noqa: E402
from src.constantes import PCI_KCAL_KG, PCI_KWH_KG, carregar_parametros  # noqa: E402

PASTA_DOCUMENTOS = AQUI.parent
ARQUIVO_DOCX = PASTA_DOCUMENTOS / "Proposta_Projeto_GLP_ABNT.docx"
ARQUIVO_PDF = PASTA_DOCUMENTOS / "Proposta_Projeto_GLP_ABNT.pdf"
FIGURA_PAINEL = PASTA_DOCUMENTOS / "figuras" / "painel_estatistica_antes_depois.png"

# Identificação (completar; não inventar nomes de integrantes)
INTEGRANTES = [   # até 4 integrantes, com RGM
    "Vitor Henrique Santos Das Virgens – RGM 48303577",
    "Sérgio Júnior – RGM 50097237",
    "Raul Amaral – RGM 5049502000",
    "Luís Henrique – RGM 046624929",
]
CIDADE = "Salto"
ORIENTADOR = "Vanessa Silva Pereira Araújo"
ROTULO_ORIENTADOR = "Professora"
DATA_ACESSO = "13 nov. 2026"
REPOSITORIO = "https://github.com/vitorhenriqueee22-crypto/Exercicios-Python-CEUNSP"
_AUTORIA = "pelos autores" if len(INTEGRANTES) > 1 else "pelo autor"
FONTE_AUTOR = f"elaborado {_AUTORIA} (2026)."
FONTE_SIM = f"elaborado {_AUTORIA} (2026), com dados SIMULADOS."


def fmt(valor: float, casas: int = 2) -> str:
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_p(p: float) -> str:
    return "< 0,001" if p < 0.001 else fmt(p, 3)


def p_txt(p: float) -> str:
    """'p < 0,001' ou 'p = 0,123'."""
    return "p < 0,001" if p < 0.001 else f"p = {fmt(p, 3)}"


# ---------------------------------------------------------------------------
# Aplicação demonstrativa (dados SIMULADOS)
# ---------------------------------------------------------------------------
def demonstracao() -> dict:
    hip = dados_simulados.carregar_hipoteses()
    par = carregar_parametros()
    tab = dados_simulados.gerar(hip, par)
    reg = tab["registros"]
    preco = par["geral"]["preco_glp_r_por_kg"]
    interv = {i["id"]: i for i in hip["intervencoes"]}

    # Fundição — INT-01 (kg/t, 90 dias antes × 90 dias depois)
    av1 = relatorios.avaliar_intervencao(reg, interv["INT-01"], 90)
    r1 = av1["resultado"]
    antes1 = av1["antes"]
    n_ind = estatistica.tamanho_amostra_por_periodo(antes1.std(ddof=1), 0.03 * antes1.mean(), pareado=False)
    n_par = estatistica.tamanho_amostra_por_periodo(antes1.std(ddof=1), 0.03 * antes1.mean(), pareado=True)
    d = fundicao.diario_fornos(reg)
    f1 = d[(d["equipamento_id"] == "FORNO-01") & (d["metal_t"] > 0)]
    t_dia = f1["metal_t"].mean()
    dias_ano = par["geral"]["dias_operacao_ano"]
    economia = [v * t_dia * preco * dias_ano for v in (r1.ic95_reducao[0], r1.reducao_media, r1.ic95_reducao[1])]

    # Chuveiros — INT-02 (kg em horas sem uso) e correlação com a temperatura
    av2 = relatorios.avaliar_intervencao(reg, interv["INT-02"], 90)
    r2 = av2["resultado"]
    dc = chuveiros.diario(reg, preco)
    uteis = dc[dc["data"].dt.dayofweek < 5]
    corr = estatistica.correlacao(uteis["temp_entrada_c"], uteis["consumo_kg"] - uteis["kg_sem_uso"])

    # Restaurante — linha de base G = β0 + β1·N e teste de β1
    dr = restaurante.diario(reg, preco)
    modelo_r = restaurante.modelo_consumo(dr)
    x = np.asarray(antes1, dtype=float)
    contagem, bordas = np.histogram(x, bins=np.arange(np.floor(x.min() / 5) * 5, x.max() + 5, 5))
    k_modal = int(contagem.argmax())
    desc = {"n": len(x), "media": x.mean(), "mediana": float(np.median(x)), "var": x.var(ddof=1),
            "dp": x.std(ddof=1), "cv": x.std(ddof=1) / x.mean() * 100, "ep": x.std(ddof=1) / np.sqrt(len(x)),
            "amp": x.max() - x.min(), "modal": (bordas[k_modal], bordas[k_modal + 1], int(contagem[k_modal]))}
    return {"hip": hip, "par": par, "r1": r1, "r2": r2, "n_ind": n_ind, "n_par": n_par, "desc": desc,
            "dp_antes": antes1.std(ddof=1), "media_antes": antes1.mean(), "t_dia": t_dia,
            "economia": economia, "corr": corr, "modelo_r": modelo_r, "n_registros": len(reg),
            "preco": preco, "dias_ano": dias_ano}


DEMO = demonstracao()
R1, R2 = DEMO["r1"], DEMO["r2"]

RESUMO = (
    "Este trabalho propõe um projeto de otimização do consumo de gás liquefeito de petróleo "
    "(GLP) em uma indústria mecânica, baseado em inferência estatística. O GLP é usado na fusão "
    "de metais da fundição, na cocção do restaurante industrial e no aquecimento de água dos "
    "chuveiros, e a empresa conhece apenas o total comprado, sem saber como o consumo se "
    "distribui nem se as melhorias operacionais realmente o reduzem. O problema de engenharia "
    "consiste em decidir, com risco de erro controlado, se uma intervenção operacional reduz o "
    "consumo específico de GLP, isto é, o consumo por unidade de atividade: quilogramas por "
    "tonelada fundida, por refeição ou por usuário. Foram formuladas hipóteses estatísticas "
    "unilaterais para cada setor, com nível de significância de 5 %, e definida uma metodologia "
    "que combina a normalização do consumo pela atividade, o diagnóstico de normalidade pelo "
    "teste de Shapiro-Wilk, os testes t pareado e de Welch ou seus equivalentes não "
    "paramétricos de Wilcoxon e de Mann-Whitney, intervalos de confiança, tamanho de efeito, "
    "cálculo do tamanho da amostra e regressão linear para construir linhas de base e ajustar "
    "diferenças de produção. A metodologia foi implementada em uma ferramenta em Python e "
    "verificada com dados simulados, identificados como tais: a redução de 8 % inserida em um "
    f"forno foi estimada em {fmt(R1.reducao_percentual, 1)} %, com intervalo de confiança de "
    f"95 % entre {fmt(R1.ic95_reducao_percentual[0], 1)} % e "
    f"{fmt(R1.ic95_reducao_percentual[1], 1)} %. Conclui-se que a abordagem permite separar "
    "reduções reais de variações aleatórias e estimar a economia com a respectiva incerteza, e "
    "que sua aplicação à empresa depende da coleta de dados medidos por setor."
)

ABSTRACT = (
    "This work proposes a project to optimize liquefied petroleum gas (LPG) consumption in a "
    "mechanical industry based on statistical inference. LPG is used for metal melting in the "
    "foundry, for cooking in the industrial restaurant and for heating shower water, and the "
    "company only knows the total amount purchased, without knowing how consumption is "
    "distributed or whether operational improvements actually reduce it. The engineering "
    "problem is to decide, with a controlled risk of error, whether an operational "
    "intervention reduces the specific LPG consumption, that is, consumption per unit of "
    "activity: kilograms per tonne melted, per meal or per user. One-sided statistical "
    "hypotheses were formulated for each sector at a 5 % significance level, and a methodology "
    "was defined combining normalization of consumption by activity, the Shapiro-Wilk "
    "normality test, the paired and Welch t-tests or their nonparametric counterparts "
    "(Wilcoxon and Mann-Whitney), confidence intervals, effect size, sample size calculation "
    "and linear regression to build baselines and adjust for production differences. The "
    "methodology was implemented in a Python tool and verified with simulated data, labeled as "
    "such: the 8 % reduction inserted in one furnace was estimated at "
    f"{R1.reducao_percentual:.1f} %, with a 95 % confidence interval from "
    f"{R1.ic95_reducao_percentual[0]:.1f} % to {R1.ic95_reducao_percentual[1]:.1f} %. The "
    "approach separates real reductions from random variation and estimates savings with "
    "their uncertainty; applying it to the company depends on collecting measured data by "
    "sector."
)

META = Metadados(
    instituicao=["Centro Universitário Nossa Senhora do Patrocínio", "Curso de Engenharia Elétrica"],
    autor="\n".join(INTEGRANTES),
    titulo="Otimização do consumo de GLP industrial baseada em inferência estatística",
    subtitulo="proposta de projeto",
    natureza=(
        "Trabalho apresentado à disciplina de Experimentação e Análise de Dados do curso de "
        "Engenharia Elétrica do Centro Universitário Nossa Senhora do Patrocínio (CEUNSP), como "
        "proposta de projeto de otimização de processos baseada em inferência estatística."
    ),
    orientador=ORIENTADOR,
    rotulo_orientador=ROTULO_ORIENTADOR,
    local=CIDADE,
    ano="2026",
    resumo=RESUMO,
    palavras_chave=["inferência estatística", "testes de hipóteses", "GLP",
                    "eficiência energética", "otimização de processos"],
    abstract=ABSTRACT,
    keywords=["statistical inference", "hypothesis testing", "LPG", "energy efficiency",
              "process optimization"],
    siglas=[
        ("ABNT", "Associação Brasileira de Normas Técnicas"),
        ("ANP", "Agência Nacional do Petróleo, Gás Natural e Biocombustíveis"),
        ("BEN", "Balanço Energético Nacional"),
        ("CE", "Consumo específico"),
        ("CUSUM", "*Cumulative sum* (soma acumulada)"),
        ("CV", "Coeficiente de variação"),
        ("EVO", "*Efficiency Valuation Organization*"),
        ("GLP", "Gás liquefeito de petróleo"),
        ("IC", "Intervalo de confiança"),
        ("IDE", "Indicador de desempenho energético"),
        ("ISO", "*International Organization for Standardization*"),
        ("LBE", "Linha de base energética"),
        ("MQO", "Mínimos quadrados ordinários"),
        ("PCI", "Poder calorífico inferior"),
        ("PIMVP", "Protocolo Internacional de Medição e Verificação de Performance"),
    ],
    simbolos=[
        ("A", "atividade no período (t, refeições ou usuários)"),
        ("CV", "coeficiente de variação"),
        ("d_{i}", "diferença antes − depois do par i"),
        ("d̄", "média das diferenças"),
        ("d, d_{z}", "tamanho de efeito (amostras independentes e pareadas)"),
        ("EP", "erro padrão da média"),
        ("G", "consumo de GLP, em kg"),
        ("H_{0}, H_{1}", "hipóteses nula e alternativa"),
        ("Md", "mediana"),
        ("Mo", "moda"),
        ("n", "tamanho da amostra"),
        ("p", "valor p do teste de hipóteses"),
        ("P", "preço do GLP, em R$/kg"),
        ("R%", "redução percentual"),
        ("s, s²", "desvio-padrão e variância amostrais"),
        ("x̄", "média amostral"),
        ("α", "nível de significância (probabilidade de erro tipo I)"),
        ("β", "probabilidade de erro tipo II; coeficiente de regressão, conforme o contexto"),
        ("δ", "menor redução de interesse prático"),
        ("μ", "média populacional"),
        ("ν", "graus de liberdade"),
    ],
)


def montar() -> Conteudo:
    c = Conteudo()
    hip, par = DEMO["hip"], DEMO["par"]

    # =====================================================================
    c.h1("1", "CONTEXTO E PROBLEMA DE ENGENHARIA")
    c.h2("1.1", "CONTEXTO")
    c.p(
        "O gás liquefeito de petróleo (GLP) é uma fonte de calor comum em indústrias "
        "mecânicas. Na empresa considerada neste projeto, ele tem três usos: a fusão e o "
        "tratamento térmico de metais na fundição, a cocção de alimentos no restaurante "
        "industrial e o aquecimento de água para os chuveiros dos funcionários. A energia "
        "contida no combustível é dada pela Equação 1, em que se adota o poder calorífico "
        f"inferior médio de {fmt(PCI_KCAL_KG, 0)} kcal/kg publicado pela ANP a partir do Balanço "
        f"Energético Nacional (ANP, 2026), equivalente a {fmt(PCI_KWH_KG, 2)} kWh/kg."
    )
    c.eq("E = m_{GLP} · PCI")
    c.definicoes([
        ("E", "energia liberada na combustão, em kWh"),
        ("m_{GLP}", "massa de GLP consumida, em kg"),
        ("PCI", f"poder calorífico inferior, {fmt(PCI_KWH_KG, 2)} kWh/kg"),
    ])
    c.p(
        "Os processos térmicos industriais têm perdas relevantes e, portanto, espaço para "
        "otimização. Em fundições, a fusão responde pela maior parte da energia consumida, e "
        "os fornos em uso apresentam baixa eficiência térmica (BCS, 2005). Medições em fornos "
        "de fusão de alumínio a gás encontraram eficiência efetiva da ordem de 26 % a 29 %, com "
        "perdas pelos gases de exaustão entre 35 % e 50 % (Li et al., 2006). Em um forno "
        "cadinho de fusão de zinco, o pré-aquecimento do ar de combustão reduziu o consumo de "
        "gás em 28 % (Vergnhanini Filho; Spegiorin, 2013). Esses resultados mostram que há "
        "oportunidades, mas valem para equipamentos específicos: em cada empresa, o efeito de "
        "uma melhoria precisa ser medido e comprovado."
    )
    c.p(
        "A gestão da energia segundo a ABNT NBR ISO 50001 acompanha o desempenho por meio de "
        "indicadores de desempenho energético (IDE) comparados a uma linha de base energética "
        "(LBE) (ABNT, 2018; ABNT, 2024). O Protocolo Internacional de Medição e Verificação de "
        "Performance (PIMVP) acrescenta que a economia não é medida diretamente: ela é a "
        "diferença entre o consumo que teria ocorrido sem a melhoria, estimado pela linha de "
        "base ajustada às condições do período, e o consumo medido depois dela (EVO, 2012)."
    )
    c.h2("1.2", "PROBLEMA DE ENGENHARIA")
    c.p(
        "A empresa conhece apenas o total de GLP comprado, registrado nas notas fiscais de "
        "abastecimento. Não se sabe quanto cada setor consome, nem se as melhorias operacionais "
        "adotadas reduzem o consumo. Na prática, decisões desse tipo costumam se basear em "
        "comparações simples, como \"o consumo caiu 5 % no mês seguinte ao ajuste do forno\". "
        "Essa conclusão é frágil por dois motivos:"
    )
    c.alineas([
        "o consumo varia com a atividade: um mês com menos toneladas fundidas, menos "
        "refeições ou menos usuários consome menos GLP mesmo sem nenhuma melhoria; por isso, "
        "o consumo deve ser normalizado pela atividade (Equação 2)",
        "o consumo diário tem variabilidade natural: uma diferença percentual entre dois "
        "períodos pode ser apenas efeito do acaso, e só a inferência estatística permite "
        "avaliar essa possibilidade com risco de erro conhecido",
    ])
    c.eq("CE = G / A")
    c.definicoes([
        ("CE", "consumo específico de GLP (kg/t, kg/refeição ou kg/usuário)"),
        ("G", "consumo de GLP no período, em kg"),
        ("A", "atividade no período: toneladas fundidas, refeições ou usuários"),
    ])
    c.p(
        "O problema de engenharia deste projeto é, portanto: **decidir, com risco de erro "
        "controlado, se uma intervenção operacional reduz o consumo específico de GLP de um "
        "setor, e estimar a economia resultante com a sua incerteza.** O Quadro 1 resume, para "
        "cada setor, o uso do GLP, a variável de atividade, o indicador e exemplos de "
        "intervenções que a metodologia permite avaliar."
    )
    c.quadro(
        "Setores, indicadores e intervenções a avaliar",
        ["Setor", "Uso do GLP", "Atividade e indicador", "Exemplos de intervenção"],
        [
            ["Fundição", "Fornos de fusão, espera e tratamento térmico",
             "Toneladas fundidas; kg/t por forno",
             "Ajuste da relação ar-combustível; vedação de tampas; redução do tempo de forno ligado sem carga"],
            ["Restaurante", "Fogões, fornos, caldeirões e fritadeiras",
             "Refeições; kg/refeição ajustado pela parcela fixa",
             "Uso de tampas; desligamento entre preparos; manutenção de queimadores"],
            ["Chuveiros", "Aquecedor de água de acumulação",
             "Usuários; kg/usuário e kg nas horas sem uso",
             "Isolamento térmico do reservatório e da tubulação; programação horária do aquecedor"],
        ],
        [2.6, 3.8, 4.2, 5.4],
        FONTE_AUTOR,
        nota="intervenções em equipamentos de GLP devem ser executadas por profissionais "
             "habilitados; o projeto apenas avalia o seu efeito sobre o consumo.",
    )
    c.h2("1.3", "OBJETIVOS")
    c.p(
        "O objetivo geral é aplicar métodos de inferência estatística para verificar se "
        "intervenções operacionais reduzem o consumo específico de GLP e para estimar a "
        "economia correspondente. Os objetivos específicos são:"
    )
    c.alineas([
        "definir, para cada setor, a variável resposta e a forma de normalizá-la pela atividade",
        "formular hipóteses estatísticas testáveis para o efeito das intervenções",
        "estabelecer o delineamento, o tamanho da amostra e os testes adequados a cada situação",
        "construir linhas de base por regressão para ajustar diferenças de produção entre períodos",
        "estimar a economia com intervalo de confiança, distinguindo significância estatística "
        "de relevância econômica",
        "implementar a metodologia em uma ferramenta computacional e verificá-la com dados "
        "simulados de efeito conhecido",
    ])
    c.h2("1.4", "JUSTIFICATIVA E PREMISSAS")
    c.p(
        "Investir em uma melhoria que não funciona, ou abandonar uma que funciona, tem custo "
        "para a empresa. A inferência estatística quantifica esses dois riscos — os erros tipo "
        "I e tipo II — e permite decidir com base em evidência. O projeto adota as seguintes "
        "premissas: nenhum dado da empresa é inventado; enquanto não houver medições, a "
        "metodologia é demonstrada com dados simulados, sempre identificados como tais; maior "
        "consumo absoluto não é tomado como prova de ineficiência; e o sistema apenas monitora "
        "e analisa, sem enviar comandos a equipamentos."
    )

    # =====================================================================
    c.h1("2", "FORMULAÇÃO DAS HIPÓTESES ESTATÍSTICAS")
    c.h2("2.1", "VARIÁVEL RESPOSTA, UNIDADE EXPERIMENTAL E TRATAMENTO")
    c.p(
        "Em todas as hipóteses, o **tratamento** é a intervenção operacional, com dois níveis: "
        "antes e depois. A **unidade experimental** é o dia de operação do equipamento ou do "
        "setor, ou, quando houver registro, o ciclo de fusão. A **variável resposta** é o "
        "consumo específico do setor (Equação 2), e não o consumo absoluto, para que a "
        "comparação não seja distorcida por diferenças de produção. Quando o consumo tiver uma "
        "parcela fixa importante, como no restaurante, a resposta passa a ser o resíduo em "
        "relação à linha de base (seção 3.7)."
    )
    c.p("Para cada par de observações comparáveis, define-se a diferença da Equação 3:")
    c.eq("d_{i} = CE_{antes,i} − CE_{depois,i}")
    c.p("de modo que d > 0 representa redução do consumo específico.")
    c.h2("2.2", "HIPÓTESES PRINCIPAIS")
    c.h3("2.2.1", "Fundição")
    c.p(
        "Para cada forno que receber uma intervenção, a hipótese de interesse é que o consumo "
        "específico médio diminuiu:"
    )
    c.alineas([
        "H_{0}: μ_{d} ≤ 0 — a intervenção não reduz o consumo médio de GLP por tonelada fundida",
        "H_{1}: μ_{d} > 0 — a intervenção reduz o consumo médio de GLP por tonelada fundida",
    ])
    c.p(
        "Quando os períodos antes e depois forem amostras independentes, a hipótese é escrita "
        "em termos das médias: H_{0}: μ_{antes} ≤ μ_{depois} e H_{1}: μ_{antes} > μ_{depois}."
    )
    c.h3("2.2.2", "Restaurante")
    c.p(
        "No restaurante, o consumo diário tem uma parcela fixa (pré-aquecimento, chamas de "
        "espera) e uma parcela proporcional às refeições, modelada pela Equação 4. Por isso, "
        "formulam-se duas hipóteses. A primeira valida a linha de base, verificando se o consumo "
        "depende do número de refeições; a segunda avalia a intervenção pelos resíduos e em "
        "relação a essa linha de base:"
    )
    c.eq("G_{dia} = β_{0} + β_{1} · N_{ref} + ε")
    c.alineas([
        "H_{0}: β_{1} = 0 contra H_{1}: β_{1} > 0 — o consumo diário cresce com o número de refeições",
        "H_{0}: μ_{e} ≥ 0 contra H_{1}: μ_{e} < 0 — depois da intervenção, o consumo fica, em "
        "média, abaixo do previsto pela linha de base, em que e = G_{real} − Ĝ_{linha de base}",
    ])
    c.h3("2.2.3", "Chuveiros")
    c.p(
        "Nos chuveiros, uma intervenção típica (isolamento do reservatório) atua sobre as "
        "perdas em espera, observáveis no consumo das horas sem usuários. Além disso, espera-se "
        "que a água mais fria na entrada exija mais energia por banho:"
    )
    c.alineas([
        "H_{0}: μ_{antes} ≤ μ_{depois} contra H_{1}: μ_{antes} > μ_{depois} — a intervenção reduz "
        "o consumo diário nas horas sem uso",
        "H_{0}: ρ = 0 contra H_{1}: ρ < 0 — o consumo dos banhos diminui quando a temperatura da "
        "água de entrada aumenta",
    ])
    c.h2("2.3", "HIPÓTESES DE VERIFICAÇÃO DOS PRESSUPOSTOS")
    c.p(
        "A escolha dos testes depende de pressupostos que também são verificados como "
        "hipóteses: normalidade (Shapiro-Wilk, com H_{0}: os dados ou as diferenças seguem "
        "distribuição normal) e independência dos resíduos (Durbin-Watson, com H_{0}: ausência "
        "de autocorrelação de primeira ordem). O Quadro 2 reúne todas as hipóteses do projeto."
    )
    c.quadro(
        "Resumo das hipóteses estatísticas",
        ["Setor", "Hipótese alternativa (H₁)", "Variável", "Teste", "α"],
        [
            ["Fundição", "O consumo específico diminui após a intervenção", "kg/t por forno",
             "t pareado ou Welch; Wilcoxon ou Mann-Whitney", "0,05"],
            ["Restaurante", "O consumo cresce com o número de refeições (β₁ > 0)", "kg/dia × refeições",
             "t do coeficiente de regressão", "0,05"],
            ["Restaurante", "Após a intervenção, o consumo fica abaixo da linha de base", "Resíduo (kg/dia)",
             "t para uma amostra ou Wilcoxon", "0,05"],
            ["Chuveiros", "O consumo nas horas sem uso diminui após a intervenção", "kg/dia sem uso",
             "Welch ou Mann-Whitney", "0,05"],
            ["Chuveiros", "Correlação negativa com a temperatura de entrada (ρ < 0)", "kg/dia × °C",
             "Pearson ou Spearman", "0,05"],
            ["Todos", "Os dados não seguem distribuição normal", "Diferenças ou amostras",
             "Shapiro-Wilk", "0,05"],
            ["Todos", "Há autocorrelação nos resíduos", "Resíduos do modelo", "Durbin-Watson", "—"],
        ],
        [2.4, 5.0, 3.0, 4.2, 1.4],
        FONTE_AUTOR,
    )
    c.h2("2.4", "NÍVEL DE SIGNIFICÂNCIA, ERROS E RELEVÂNCIA PRÁTICA")
    c.p(
        "Adota-se nível de significância α = 0,05, isto é, aceita-se 5 % de probabilidade de "
        "concluir que uma intervenção reduziu o consumo quando ela não o reduziu (erro tipo I), "
        "o que levaria a empresa a investir em uma medida ineficaz. O erro tipo II, de "
        "probabilidade β, corresponde a não detectar uma redução que existe, o que levaria ao "
        "abandono de uma melhoria útil; o projeto busca poder 1 − β de pelo menos 0,80, o que "
        "orienta o tamanho da amostra (seção 3.3)."
    )
    c.p(
        "Os testes são unilaterais porque a pergunta de engenharia é direcional: interessa saber "
        "se houve redução. Um aumento do consumo leva à não rejeição de H_{0} e é tratado, na "
        "prática, como ausência de benefício. Como significância estatística não implica "
        "importância econômica, define-se também a menor redução de interesse prático, δ, a "
        "ser acordada com a empresa a partir do custo da intervenção; neste trabalho, adota-se "
        "δ = 3 % como HIPÓTESE ilustrativa."
    )
    c.p("A regra de decisão adotada é:")
    c.alineas([
        "rejeitar H_{0} quando o valor p for menor que α = 0,05: a redução é estatisticamente comprovada",
        "considerar a redução economicamente relevante quando, além disso, o limite inferior do "
        "intervalo de confiança de 95 % da redução for maior que δ",
        "em qualquer caso, informar a estimativa da redução, o intervalo de confiança e o "
        "tamanho de efeito, e nunca uma variação percentual isolada",
    ])

    # =====================================================================
    c.h1("3", "METODOLOGIA DE INFERÊNCIA ESTATÍSTICA")
    c.h2("3.1", "DELINEAMENTO DO ESTUDO")
    c.p(
        "O estudo é do tipo antes e depois (quase-experimental): mede-se o consumo durante um "
        "período de referência, aplica-se a intervenção em data registrada e mede-se de novo. "
        "Para reduzir o risco de que outros fatores expliquem a diferença, o delineamento segue "
        "estas regras:"
    )
    c.alineas([
        "pareamento sempre que possível: comparar o mesmo forno, com a mesma liga e cargas "
        "equivalentes, ou os mesmos dias da semana; o pareamento remove a variação entre "
        "unidades e aumenta o poder do teste",
        "uma intervenção por vez em cada equipamento, com data de início registrada",
        "períodos antes e depois de mesma duração e, quando possível, na mesma estação do ano",
        "normalização pela atividade (Equação 2) e, quando houver parcela fixa ou mudança de "
        "produção, comparação com a linha de base ajustada por regressão (seção 3.7)",
        "exclusão apenas de registros comprovadamente inválidos, documentando o motivo, e nunca "
        "de valores que apenas \"pareçam\" altos",
    ])
    c.h2("3.2", "COLETA E PREPARAÇÃO DOS DADOS")
    c.p(
        "O Quadro 3 lista as variáveis a coletar. Antes da análise, cada registro passa por "
        "validação: campos obrigatórios, valores negativos, datas inválidas, unidades "
        "incompatíveis, duplicidades e lacunas na série. Dados medidos e dados simulados nunca "
        "são misturados na mesma análise."
    )
    c.quadro(
        "Variáveis a coletar",
        ["Variável", "Unidade", "Frequência", "Fonte"],
        [
            ["Consumo de GLP por setor e por equipamento", "kg", "Diária (horária nos chuveiros e no restaurante)", "Submedidores e balanço do tanque"],
            ["Abastecimentos e preço", "kg; R$/kg", "Cada abastecimento", "Notas fiscais"],
            ["Toneladas fundidas, ciclos e horas com e sem carga", "t; ciclos; h", "Diária, por forno", "Apontamento de produção"],
            ["Refeições produzidas", "refeições", "Diária", "Controle do restaurante"],
            ["Usuários dos chuveiros", "usuários", "Diária e horária", "Controle de acesso"],
            ["Temperatura da água de entrada", "°C", "Diária", "Termômetro ou sensor"],
            ["Intervenções", "descrição e data", "Cada ocorrência", "Manutenção e engenharia"],
        ],
        [5.6, 2.4, 4.2, 3.8],
        FONTE_AUTOR,
    )
    c.h2("3.3", "TAMANHO DA AMOSTRA")
    c.p(
        "O número de observações por período necessário para detectar uma redução δ com poder "
        "1 − β, em teste unilateral, é aproximado pela Equação 5 (Montgomery; Runger, 2018):"
    )
    c.eq("n = k · [(z_{1−α} + z_{1−β}) · s / δ]²")
    c.definicoes([
        ("n", "observações por período"),
        ("k", "1 para dados pareados (s das diferenças) e 2 para amostras independentes"),
        ("z_{1−α}, z_{1−β}", "quantis da normal padrão (1,645 e 0,842 para α = 0,05 e poder 0,80)"),
        ("s", "desvio-padrão estimado em um período piloto"),
        ("δ", "menor redução de interesse prático, na unidade da variável"),
    ])
    c.p(
        "Na aplicação demonstrativa (seção 3.9), com os dados simulados do forno de fusão, o "
        f"desvio-padrão do consumo específico no período anterior foi de {fmt(DEMO['dp_antes'], 2)} "
        f"kg/t, para média de {fmt(DEMO['media_antes'], 2)} kg/t. Para detectar δ = 3 % da média, "
        f"seriam necessários cerca de {DEMO['n_ind']} dias de operação em cada período com amostras "
        f"independentes; com pareamento perfeito e o mesmo desvio, cerca de {DEMO['n_par']}. "
        "Esses números são SIMULADOS e servem apenas para ilustrar o cálculo."
    )
    c.h2("3.4", "ESTATÍSTICA DESCRITIVA")
    c.p(
        "Antes dos testes, cada série é descrita por medidas de tendência central e de "
        "dispersão, além de histogramas, diagramas de caixa e séries temporais com média "
        "móvel, que revelam tendências, sazonalidade e valores atípicos (Montgomery; Runger, "
        "2018). As medidas de tendência central são a média aritmética (Equação 6), a mediana "
        "(Equação 7), que é o valor central dos dados ordenados x_{(1)} ≤ x_{(2)} ≤ … ≤ x_{(n)} e "
        "é pouco afetada por valores extremos, e a moda (Mo), que é o valor de maior frequência; "
        "em dados contínuos, como o consumo específico, usa-se a classe de maior frequência do "
        "histograma (classe modal)."
    )
    c.eq("x̄ = (Σ x_{i}) / n")
    c.eq("Md = x_{((n+1)/2)}, se n é ímpar;   Md = [x_{(n/2)} + x_{(n/2+1)}] / 2, se n é par")
    c.p(
        "A dispersão, que representa a variação natural do consumo de um dia para outro, é "
        "medida pela amplitude (A = x_{máx} − x_{mín}), pela variância amostral (Equação 8), "
        "pelo desvio-padrão (Equação 9), pelo coeficiente de variação (Equação 10), que permite "
        "comparar setores com unidades diferentes, e pelo erro padrão da média (Equação 11), "
        "que mede a incerteza da média e diminui com o tamanho da amostra:"
    )
    c.eq("s² = Σ (x_{i} − x̄)² / (n − 1)")
    c.eq("s = √s²")
    c.eq("CV = (s / x̄) · 100 %")
    c.eq("EP = s / √n")
    ds = DEMO["desc"]
    c.p(
        f"Nos dados SIMULADOS do forno de fusão, nos 90 dias anteriores à intervenção (n = "
        f"{ds['n']} dias com produção), obtêm-se x̄ = {fmt(ds['media'], 2)} kg/t, Md = "
        f"{fmt(ds['mediana'], 2)} kg/t, classe modal de {fmt(ds['modal'][0], 0)} a "
        f"{fmt(ds['modal'][1], 0)} kg/t ({ds['modal'][2]} dias), A = {fmt(ds['amp'], 2)} kg/t, "
        f"s² = {fmt(ds['var'], 2)} (kg/t)², s = {fmt(ds['dp'], 2)} kg/t, CV = {fmt(ds['cv'], 1)} % "
        f"e EP = {fmt(ds['ep'], 2)} kg/t. A proximidade entre média e mediana é coerente com uma "
        "distribuição aproximadamente simétrica, o que é confirmado pelo teste de normalidade "
        "da seção 3.5."
    )
    c.h2("3.5", "VERIFICAÇÃO DOS PRESSUPOSTOS")
    c.p(
        "A normalidade é verificada pelo teste de Shapiro-Wilk (Shapiro; Wilk, 1965) e pelo "
        "gráfico quantil-quantil. No teste pareado, verifica-se a normalidade das diferenças, e "
        "não das amostras. O teste é usado como diagnóstico: com amostras pequenas tem pouco "
        "poder e com amostras grandes rejeita desvios sem importância prática. A independência "
        "é avaliada pela estatística de Durbin-Watson dos resíduos (Equação 12), cujo valor "
        "próximo de 2 indica ausência de autocorrelação (Durbin; Watson, 1950). Séries diárias "
        "de consumo costumam ser autocorrelacionadas; nesse caso, os dados são agregados por "
        "semana ou a comparação é feita contra a linha de base. A igualdade de variâncias não é "
        "exigida, pois se usa o teste de Welch."
    )
    c.eq("DW = Σ_{t=2..n} (e_{t} − e_{t−1})² / Σ_{t=1..n} e_{t}²")
    c.h2("3.6", "TESTES DE HIPÓTESES")
    c.p("A escolha do teste segue o Quadro 4.")
    c.quadro(
        "Escolha do teste de hipóteses",
        ["Estrutura dos dados", "Normalidade", "Teste", "Referência"],
        [
            ["Pareados", "Diferenças aproximadamente normais", "t pareado (Equação 13)", "Student (1908)"],
            ["Pareados", "Diferenças não normais", "Wilcoxon dos postos sinalizados", "Wilcoxon (1945)"],
            ["Independentes", "Ambas as amostras aproximadamente normais", "t de Welch (Equações 14 e 15)", "Welch (1947)"],
            ["Independentes", "Alguma amostra não normal", "Mann-Whitney", "Mann e Whitney (1947)"],
            ["Resíduos em relação à linha de base", "Resíduos aproximadamente normais", "t para uma amostra", "Montgomery e Runger (2018)"],
        ],
        [4.2, 4.6, 4.2, 3.0],
        FONTE_AUTOR,
    )
    c.p("O teste t pareado usa a estatística da Equação 13, com n − 1 graus de liberdade:")
    c.eq("t = d̄ / (s_{d} / √n)")
    c.p(
        "Para amostras independentes, o teste de Welch não supõe variâncias iguais (Welch, "
        "1947); a estatística é a da Equação 14, e os graus de liberdade são aproximados pela "
        "Equação 15 (Satterthwaite, 1946), em que o índice 1 indica o período antes e o índice 2, "
        "o período depois da intervenção:"
    )
    c.eq("t_{W} = (x̄_{1} − x̄_{2}) / √(s_{1}²/n_{1} + s_{2}²/n_{2})")
    c.eq("ν = (s_{1}²/n_{1} + s_{2}²/n_{2})² / [(s_{1}²/n_{1})²/(n_{1} − 1) + (s_{2}²/n_{2})²/(n_{2} − 1)]")
    c.p(
        "Os testes de Wilcoxon e de Mann-Whitney comparam postos em vez de valores, e por isso "
        "são robustos a assimetrias e valores extremos (Wilcoxon, 1945; Mann; Whitney, 1947). Em "
        "todos os casos usa-se a alternativa unilateral de redução, e o valor p é comparado "
        "com α = 0,05."
    )
    c.h2("3.7", "INTERVALOS DE CONFIANÇA, TAMANHO DE EFEITO E LINHA DE BASE")
    c.p(
        "O intervalo de confiança de 95 % da redução média mostra a faixa de valores "
        "compatíveis com os dados. Para dados pareados, usa-se a Equação 16; para amostras "
        "independentes, a Equação 17, com os graus de liberdade da Equação 15. Dividindo-se a "
        "redução e os limites do intervalo pela média do período anterior, obtêm-se a redução "
        "percentual (Equação 18) e o seu intervalo de confiança:"
    )
    c.eq("IC_{95%} = d̄ ± t_{0,975; n−1} · s_{d} / √n")
    c.eq("IC_{95%} = (x̄_{1} − x̄_{2}) ± t_{0,975; ν} · √(s_{1}²/n_{1} + s_{2}²/n_{2})")
    c.eq("R% = [(x̄_{1} − x̄_{2}) / x̄_{1}] · 100 %")
    c.p(
        "O tamanho de efeito expressa a redução em desvios-padrão (Cohen, 1988): Equação 19 "
        "para dados pareados e Equação 20 para amostras independentes, em que se usa a média "
        "das variâncias dos dois períodos:"
    )
    c.eq("d_{z} = d̄ / s_{d}")
    c.eq("d = (x̄_{1} − x̄_{2}) / √[(s_{1}² + s_{2}²) / 2]")
    c.p(
        "Quando a atividade muda entre os períodos, ajusta-se por mínimos quadrados ordinários "
        "um modelo de linha de base com os dados do período anterior à intervenção (Equação 4 "
        "no restaurante; consumo em função de horas e toneladas na fundição). A significância "
        "de cada coeficiente é testada por t = β̂ / EP(β̂), e a qualidade do ajuste é avaliada "
        "pelo R² ajustado e pela análise de resíduos. Depois da intervenção, o modelo prevê o "
        "consumo que teria ocorrido sem ela, e a economia verificada é calculada pela Equação "
        "21, conforme o PIMVP (EVO, 2012). A soma acumulada dos resíduos (CUSUM) mostra a partir "
        "de quando o desempenho mudou (Page, 1954)."
    )
    c.eq("Economia = Σ (Ĝ_{linha de base} − G_{medido})")
    c.h2("3.8", "ESTIMATIVA DA ECONOMIA COM INCERTEZA")
    c.p(
        "A economia financeira anual é estimada a partir da redução média do consumo "
        "específico e dos seus limites de confiança, multiplicados pela atividade, pelo preço e "
        "pelos dias de operação (Equação 22). Assim, a empresa recebe não apenas um valor de "
        "economia, mas a faixa plausível desse valor, que pode ser comparada com o custo da "
        "intervenção."
    )
    c.eq("ΔC_{ano} = Δ̄CE · Ā_{dia} · P · D_{ano}")
    c.definicoes([
        ("Δ̄CE", "redução média do consumo específico (e seus limites do IC 95 %)"),
        ("Ā_{dia}", "atividade média diária (por exemplo, toneladas fundidas por dia)"),
        ("P", "preço do GLP, em R$/kg, conforme nota fiscal"),
        ("D_{ano}", "dias de operação por ano"),
    ])
    c.h2("3.9", "IMPLEMENTAÇÃO E APLICAÇÃO DEMONSTRATIVA")
    c.p(
        "A metodologia foi implementada em Python, com as bibliotecas pandas, NumPy e SciPy "
        "(McKinney, 2010; Harris et al., 2020; Virtanen et al., 2020), em uma ferramenta com "
        "painel interativo em Streamlit (Streamlit, 2026), disponível no repositório do projeto "
        f"({REPOSITORIO}). A ferramenta escolhe o teste pelo Quadro 4, calcula os intervalos de "
        "confiança e o tamanho de efeito e informa as ressalvas de cada análise (Figura 1)."
    )
    if FIGURA_PAINEL.exists():
        c.figura_imagem("Avaliação de uma intervenção na ferramenta desenvolvida", FIGURA_PAINEL,
                        FONTE_SIM, 12.5)
    h = DEMO["hip"]
    i1 = next(i for i in h["intervencoes"] if i["id"] == "INT-01")
    c.p(
        "Como ainda não há medições da empresa, a metodologia foi verificada com dados "
        f"SIMULADOS: {fmt(DEMO['n_registros'], 0)} registros de um ano, gerados por modelos com "
        "parâmetros conhecidos e identificados como simulados em todas as saídas. Os dados "
        f"incluem uma intervenção no forno de fusão, em {i1['data_inicio']}, com redução "
        f"verdadeira de {fmt(i1['reducao'] * 100, 0)} % no consumo, e uma intervenção no "
        "aquecedor dos chuveiros, que reduz as perdas em espera. Como o efeito verdadeiro é "
        "conhecido, é possível verificar se os métodos o encontram. A Tabela 1 mostra os "
        "resultados com 90 dias antes e 90 dias depois de cada intervenção."
    )
    c.tabela(
        "Aplicação demonstrativa com dados simulados",
        ["Hipótese", "Média antes", "Média depois", "Redução (IC 95 %)", "Teste", "Valor p", "Decisão"],
        [
            ["Fundição: kg/t", fmt(R1.media_antes, 2), fmt(R1.media_depois, 2),
             f"{fmt(R1.reducao_percentual, 1)} % ({fmt(R1.ic95_reducao_percentual[0], 1)} a {fmt(R1.ic95_reducao_percentual[1], 1)} %)",
             R1.teste, fmt_p(R1.p_valor), "Rejeita H₀" if R1.significativo else "Não rejeita H₀"],
            ["Chuveiros: kg/dia sem uso", fmt(R2.media_antes, 2), fmt(R2.media_depois, 2),
             f"{fmt(R2.reducao_percentual, 1)} % ({fmt(R2.ic95_reducao_percentual[0], 1)} a {fmt(R2.ic95_reducao_percentual[1], 1)} %)",
             R2.teste, fmt_p(R2.p_valor), "Rejeita H₀" if R2.significativo else "Não rejeita H₀"],
        ],
        [2.8, 1.7, 1.7, 3.4, 2.4, 1.6, 2.4],
        FONTE_SIM,
        alinhamentos=["L", "R", "R", "C", "L", "R", "L"],
    )
    def nome_teste(r):
        return f"o teste {r.teste}" if r.teste.startswith("t ") else f"o teste de {r.teste}"

    def frase_normalidade(r, setor):
        normais = [v.normal for v in r.normalidade.values()]
        pv = ", ".join(f"{k}: {p_txt(v.p_valor)}" for k, v in r.normalidade.items())
        if all(normais):
            return (f"{setor}, o teste de Shapiro-Wilk não rejeitou a normalidade ({pv}), e o "
                    f"sistema aplicou {nome_teste(r)}.")
        return (f"{setor}, o teste de Shapiro-Wilk rejeitou a normalidade em ao menos uma "
                f"amostra ({pv}), e o sistema aplicou {nome_teste(r)}, como prevê o Quadro 4.")
    ic_inf, ic_sup = R1.ic95_reducao_percentual
    contem = ic_inf <= 8 <= ic_sup
    relevante = R1.significativo and ic_inf > 3
    c.p(
        frase_normalidade(R1, "Na fundição") + " O intervalo de confiança de "
        f"{fmt(ic_inf, 1)} % a {fmt(ic_sup, 1)} % "
        + ("contém" if contem else "não contém") + " a redução verdadeira de 8 %"
        + (" e tem limite inferior acima de δ = 3 %: pela regra da seção 2.4, a redução seria "
           "estatisticamente comprovada e economicamente relevante."
           if relevante else "; pela regra da seção 2.4, a redução não seria considerada "
           "economicamente relevante.")
        + f" A redução percentual foi ({fmt(R1.media_antes, 2)} − {fmt(R1.media_depois, 2)}) / "
        f"{fmt(R1.media_antes, 2)} = {fmt(R1.reducao_percentual, 1)} % (Equação 18), e o tamanho "
        f"de efeito foi d = {fmt(R1.tamanho_efeito, 2)} (Equação 20). "
        + frase_normalidade(R2, "Nos chuveiros")
    )
    e_inf, e_med, e_sup = DEMO["economia"]
    mr = DEMO["modelo_r"]
    corr = DEMO["corr"]
    c.p(
        f"Aplicando a Equação 22 com {fmt(DEMO['t_dia'], 2)} t/dia, preço de R$ "
        f"{fmt(DEMO['preco'], 2)}/kg e {DEMO['dias_ano']} dias por ano (valores HIPOTÉTICOS), a "
        f"economia anual do forno seria de R$ {fmt(e_med, 0)}, com faixa de R$ {fmt(e_inf, 0)} a "
        f"R$ {fmt(e_sup, 0)}. No restaurante, a linha de base estimou parcela fixa de "
        f"{fmt(mr.coeficientes.loc['intercepto', 'coef'], 2)} kg/dia e "
        f"{fmt(mr.coeficientes.loc['refeicoes', 'coef'] * 1000, 1)} g por refeição, com H_{{0}}: "
        f"β_{{1}} = 0 rejeitada ({p_txt(mr.coeficientes.loc['refeicoes', 'p_valor'])}) e R² "
        f"ajustado de {fmt(mr.r2_ajustado, 3)}; os valores usados na simulação eram "
        f"{fmt(h['restaurante']['beta_0'], 0)} kg/dia e {fmt(h['restaurante']['beta_1'] * 1000, 0)} g "
        "por refeição. Nos chuveiros, a correlação entre a temperatura da água de entrada e o "
        f"consumo dos banhos foi r = {fmt(corr['pearson_r'], 2)} ({p_txt(corr['pearson_p'])}), "
        "o que leva à rejeição de H_{0}: ρ = 0."
    )
    c.p(
        "Todos esses resultados vêm de dados simulados. Eles mostram que a metodologia e a "
        "ferramenta recuperam efeitos conhecidos, mas não descrevem a empresa, cujas conclusões dependem da coleta "
        "dos dados do Quadro 3."
    )
    c.h2("3.10", "LIMITAÇÕES")
    c.alineas([
        "o delineamento antes e depois é observacional: mudanças simultâneas de produção, "
        "cardápio, estação ou turno podem confundir o efeito da intervenção, o que se reduz com "
        "pareamento, normalização e linha de base",
        "a autocorrelação das séries diárias torna os valores p otimistas, e deve ser verificada",
        "quando duas variáveis explicativas variam juntas, como horas de forno ligado e "
        "toneladas fundidas, os coeficientes individuais da regressão ficam imprecisos; "
        "recomenda-se registrar separadamente as horas com e sem carga",
        "os resultados dependem da qualidade da medição; sem submedição por setor, só o "
        "consumo total pode ser analisado",
    ])

    # =====================================================================
    c.h1("4", "CONSIDERAÇÕES FINAIS")
    c.p(
        "O projeto transforma uma pergunta frequente na indústria — \"a melhoria reduziu o "
        "consumo de GLP?\" — em hipóteses estatísticas testáveis, com variável resposta "
        "normalizada pela atividade, risco de erro controlado e estimativa da economia com "
        "incerteza. A aplicação demonstrativa mostrou que os métodos recuperam efeitos "
        "conhecidos em dados simulados e indicou cuidados para a coleta de dados reais. A "
        "próxima etapa é aplicar a metodologia às medições da empresa, começando pelo forno de "
        "fusão, que concentra a maior parte do consumo nos dados simulados, e definir com a "
        "gestão a menor redução de interesse prático para cada intervenção."
    )

    # =====================================================================
    c.referencias([
        "AGÊNCIA NACIONAL DO PETRÓLEO, GÁS NATURAL E BIOCOMBUSTÍVEIS (Brasil). **Anuário "
        "estatístico brasileiro do petróleo, gás natural e biocombustíveis 2026**: fatores de "
        "conversão. Rio de Janeiro: ANP, 2026. Disponível em: https://www.gov.br/anp/pt-br/"
        "centrais-de-conteudo/publicacoes/anuario-estatistico/arquivos-anuario-estatistico-2026/"
        f"outras-pecas-documentais/fatores-de-conversao-2026.pdf. Acesso em: {DATA_ACESSO}.",
        "ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR ISO 50001**: sistemas de gestão da "
        "energia: requisitos com orientações para uso. Rio de Janeiro: ABNT, 2018.",
        "ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR ISO 50006**: sistemas de gestão de "
        "energia: avaliação do desempenho energético utilizando indicadores de desempenho "
        "energético e linhas de base energética. Rio de Janeiro: ABNT, 2024.",
        "BCS, INCORPORATED. **Advanced melting technologies**: energy saving concepts and "
        "opportunities for the metal casting industry. Washington, DC: U.S. Department of "
        "Energy, 2005. Disponível em: https://www1.eere.energy.gov/manufacturing/resources/"
        f"metalcasting/pdfs/advancedmeltingtechnologies.pdf. Acesso em: {DATA_ACESSO}.",
        "COHEN, J. **Statistical power analysis for the behavioral sciences**. 2nd ed. "
        "Hillsdale: Lawrence Erlbaum Associates, 1988.",
        "DURBIN, J.; WATSON, G. S. Testing for serial correlation in least squares regression: "
        "I. **Biometrika**, Oxford, v. 37, n. 3/4, p. 409-428, 1950.",
        "EFFICIENCY VALUATION ORGANIZATION. **Protocolo internacional de medição e verificação "
        "de performance**: conceitos e opções para a determinação de economias de energia e de "
        "água: volume 1. EVO 10000-1:2012 (Br). [*S. l.*]: EVO, 2012.",
        "HARRIS, C. R. *et al*. Array programming with NumPy. **Nature**, London, v. 585, "
        "p. 357-362, 2020. DOI: 10.1038/s41586-020-2649-2.",
        "LI, T. *et al*. Performance of secondary aluminum melting: thermodynamic analysis and "
        "plant-site experiments. **Energy**, Oxford, v. 31, n. 12, p. 1769-1779, 2006. DOI: "
        "10.1016/j.energy.2005.08.005.",
        "MANN, H. B.; WHITNEY, D. R. On a test of whether one of two random variables is "
        "stochastically larger than the other. **The Annals of Mathematical Statistics**, "
        "v. 18, n. 1, p. 50-60, 1947.",
        "MCKINNEY, W. Data structures for statistical computing in Python. *In*: PYTHON IN "
        "SCIENCE CONFERENCE, 9., 2010, Austin. **Proceedings** [...]. Austin: SciPy, 2010. "
        "p. 56-61.",
        "MONTGOMERY, D. C.; RUNGER, G. C. **Applied statistics and probability for engineers**. "
        "7th ed. Hoboken: Wiley, 2018.",
        "PAGE, E. S. Continuous inspection schemes. **Biometrika**, Oxford, v. 41, n. 1/2, "
        "p. 100-115, 1954.",
        "SATTERTHWAITE, F. E. An approximate distribution of estimates of variance components. "
        "**Biometrics Bulletin**, v. 2, n. 6, p. 110-114, 1946.",
        "SHAPIRO, S. S.; WILK, M. B. An analysis of variance test for normality (complete "
        "samples). **Biometrika**, Oxford, v. 52, n. 3/4, p. 591-611, 1965.",
        "STREAMLIT. **Streamlit documentation**. [*S. l.*], 2026. Disponível em: "
        f"https://docs.streamlit.io. Acesso em: {DATA_ACESSO}.",
        "STUDENT. The probable error of a mean. **Biometrika**, Oxford, v. 6, n. 1, p. 1-25, 1908.",
        "VERGNHANINI FILHO, R.; SPEGIORIN, L. Implantação de sistema de recuperação de energia "
        "em forno cadinho de fusão de zinco operando com gás natural. *In*: SEMINÁRIO DE "
        "BALANÇOS ENERGÉTICOS GLOBAIS E UTILIDADES, 34., 2013, São Paulo. **Anais** [...]. São "
        "Paulo: ABM, 2013. p. 218-232.",
        "VIRTANEN, P. *et al*. SciPy 1.0: fundamental algorithms for scientific computing in "
        "Python. **Nature Methods**, New York, v. 17, p. 261-272, 2020. DOI: "
        "10.1038/s41592-019-0686-2.",
        "WELCH, B. L. The generalization of \"Student's\" problem when several different "
        "population variances are involved. **Biometrika**, Oxford, v. 34, n. 1/2, p. 28-35, 1947.",
        "WILCOXON, F. Individual comparisons by ranking methods. **Biometrics Bulletin**, "
        "v. 1, n. 6, p. 80-83, 1945.",
    ])
    return c


def main() -> None:
    documento = DocumentoABNT(META, montar())
    try:
        paginas = paginar_com_libreoffice(documento, ARQUIVO_DOCX, ARQUIVO_PDF)
        print(f"Sumário paginado ({len(paginas)} entradas).")
    except (RuntimeError, FileNotFoundError, OSError) as erro:
        documento.salvar(ARQUIVO_DOCX)
        print(f"Aviso: paginação automática indisponível ({erro}).")
    print(f"Gerado: {ARQUIVO_DOCX}")
    if ARQUIVO_PDF.exists():
        print(f"Gerado: {ARQUIVO_PDF}")


if __name__ == "__main__":
    main()
