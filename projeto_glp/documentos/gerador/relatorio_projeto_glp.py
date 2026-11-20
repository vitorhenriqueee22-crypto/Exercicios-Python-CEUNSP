"""
Relatório técnico-científico do projeto — Fases 1 a 7.

Projeto: Sistema inteligente de monitoramento, análise estatística e
otimização do consumo de GLP industrial.

Execução (a partir da raiz do repositório):
    python projeto_glp/documentos/gerador/relatorio_projeto_glp.py

Requisitos: python-docx; para numerar o sumário automaticamente,
LibreOffice (soffice) e Poppler (pdftotext). Sem eles, o .docx é gerado
com "00" no lugar dos números de página do sumário.

Todos os valores numéricos citados no texto estão definidos neste arquivo,
com a respectiva classificação de origem (REFERÊNCIA, CALCULADO, HIPÓTESE).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import capitulos_fases_3_a_7  # noqa: E402
from abnt_docx import Conteudo, DocumentoABNT, Metadados, paginar_com_libreoffice  # noqa: E402

PASTA_DOCUMENTOS = Path(__file__).resolve().parents[1]
ARQUIVO_DOCX = PASTA_DOCUMENTOS / "Relatorio_Projeto_GLP_ABNT.docx"
ARQUIVO_PDF = PASTA_DOCUMENTOS / "Relatorio_Projeto_GLP_ABNT.pdf"

# Dados de identificação a completar pelo autor (não inventados):
CIDADE = "[Cidade]"
ORIENTADOR = "[Nome do(a) professor(a) da disciplina]"
DATA_ACESSO = "13 nov. 2026"


# ---------------------------------------------------------------------------
# Valores numéricos (com origem)
# ---------------------------------------------------------------------------
def fmt(valor: float, casas: int = 2) -> str:
    """Formata número no padrão brasileiro (vírgula decimal, ponto de milhar)."""
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


PCI_KCAL_KG = 11_100                 # REFERÊNCIA: ANP (2026), valores médios BEN/EPE
MASSA_ESPECIFICA_T_M3 = 0.552        # REFERÊNCIA: ANP (2026)
KJ_POR_KCAL = 4.1868                 # convenção (caloria internacional)
KCAL_POR_TEP = 1.0e7                 # convenção do BEN: 1 tep = 10^7 kcal
PCI_KJ_KG = PCI_KCAL_KG * KJ_POR_KCAL            # CALCULADO
PCI_MJ_KG = PCI_KJ_KG / 1000                       # CALCULADO
PCI_KWH_KG = PCI_KJ_KG / 3600                      # CALCULADO
TEP_POR_T = PCI_KCAL_KG * 1000 / KCAL_POR_TEP      # CALCULADO

# Exemplo hipotético de aquecimento de água (todas as entradas são HIPÓTESES,
# exceto o calor específico da água e o PCI, que são REFERÊNCIAS)
EX_VOLUME_L = 100.0
EX_MASSA_ESP_AGUA = 1.0              # kg/L — simplificação
EX_CP_AGUA = 4.18                    # kJ/(kg·K) — REFERÊNCIA (Bergman et al., 2014)
EX_DELTA_T = 20.0                    # K
EX_RENDIMENTO = 0.80
EX_Q_KJ = EX_VOLUME_L * EX_MASSA_ESP_AGUA * EX_CP_AGUA * EX_DELTA_T
EX_Q_KWH = EX_Q_KJ / 3600
EX_M_GLP = EX_Q_KJ / (EX_RENDIMENTO * PCI_KJ_KG)

# Caso publicado (Vergnhanini Filho; Spegiorin, 2013) — valores REFERÊNCIA
CASO_INVEST = 112_000.0
CASO_ECON_MES = 5_800.0
CASO_PAYBACK_MESES = CASO_INVEST / CASO_ECON_MES  # CALCULADO (retorno simples)


# ---------------------------------------------------------------------------
# Metadados e elementos pré-textuais
# ---------------------------------------------------------------------------
RESUMO = (
    "Este relatório apresenta o desenvolvimento de um sistema de monitoramento, análise "
    "estatística e apoio à decisão para o consumo de gás liquefeito de petróleo (GLP) em uma "
    "indústria mecânica, considerando três usos finais: fundição de peças, restaurante "
    "industrial e aquecimento de água para chuveiros. O trabalho foi organizado em sete fases. "
    "Na pesquisa, foram consolidados, com fontes identificadas, o fator de conversão de massa "
    f"de GLP em energia (poder calorífico inferior de {fmt(PCI_KCAL_KG, 0)} kcal/kg, adotado pelo "
    "Balanço Energético Nacional), as equações de consumo específico, custo e eficiência, os "
    "indicadores de cada setor e os métodos estatísticos para descrever o consumo, detectar "
    "anomalias e verificar se intervenções reduziram o consumo. No diagnóstico, verificou-se que "
    "o repositório existente continha apenas exercícios independentes, que foram preservados. "
    "Na modelagem e no desenvolvimento, foi construída em Python uma ferramenta modular com "
    "importação e validação de planilhas, banco de dados SQLite, painel interativo em Streamlit "
    "com dez páginas, simulação de cenários de economia e monitoramento virtual do reservatório, "
    "com a origem de cada dado sempre identificada como medida, de referência, calculada, "
    "hipotética ou simulada. Como não havia medições da empresa, o sistema foi testado com dados "
    "sintéticos que continham intervenções e anomalias conhecidas: os testes automatizados "
    "foram aprovados, as anomalias inseridas foram detectadas e a redução de 8 % simulada em um "
    "forno foi estimada com intervalo de confiança que contém o valor verdadeiro. Os testes "
    "também evidenciaram limitações, como a multicolinearidade entre horas de operação e massa "
    "fundida e a autocorrelação dos resíduos, que orientam os requisitos de coleta de dados "
    "reais. Conclui-se que a ferramenta está pronta para receber dados medidos, mas que as "
    "conclusões sobre a empresa dependem dessa coleta, preferencialmente com medição por setor."
)

ABSTRACT = (
    "This report presents the development of a system for monitoring, statistical analysis and "
    "decision support for liquefied petroleum gas (LPG) consumption in a mechanical industry, "
    "covering three end uses: metal casting, an industrial restaurant and water heating for "
    "employee showers. The work was organized in seven phases. The research phase "
    "consolidated, with identified sources, the mass-to-energy conversion factor for LPG "
    f"(lower heating value of {fmt(PCI_KCAL_KG, 0)} kcal/kg, adopted by the Brazilian Energy "
    "Balance), the equations for specific consumption, cost and efficiency, the indicators of "
    "each sector, and the statistical methods used to describe consumption, detect anomalies and "
    "verify whether interventions reduced consumption. The assessment phase found that the "
    "existing repository contained only independent exercises, which were preserved. In the "
    "modeling and development phases, a modular Python tool was built with spreadsheet import "
    "and validation, an SQLite database, a ten-page interactive Streamlit dashboard, savings "
    "scenario simulation and virtual tank monitoring, always identifying the origin of each "
    "value as measured, reference, calculated, hypothetical or simulated. Since no company "
    "measurements were available, the system was tested with synthetic data containing known "
    "interventions and anomalies: the automated tests passed, the inserted anomalies were "
    "detected, and the simulated 8 % reduction in one furnace was estimated with a confidence "
    "interval containing the true value. The tests also revealed limitations, such as "
    "multicollinearity between operating hours and melted mass and autocorrelated residuals, "
    "which guide the requirements for collecting real data. The tool is ready to receive "
    "measured data, but conclusions about the company depend on that collection, preferably "
    "with metering by sector."
)

SIGLAS = [
    ("ABNT", "Associação Brasileira de Normas Técnicas"),
    ("ANP", "Agência Nacional do Petróleo, Gás Natural e Biocombustíveis"),
    ("BEN", "Balanço Energético Nacional"),
    ("CBMERJ", "Corpo de Bombeiros Militar do Estado do Rio de Janeiro"),
    ("CEUNSP", "Centro Universitário Nossa Senhora do Patrocínio"),
    ("CONPET", "Programa Nacional da Racionalização do Uso dos Derivados do Petróleo e do Gás Natural"),
    ("CSV", "*Comma-separated values* (valores separados por vírgula)"),
    ("CUSUM", "*Cumulative sum* (soma acumulada)"),
    ("CV", "Coeficiente de variação"),
    ("DOE", "*U.S. Department of Energy*"),
    ("EPE", "Empresa de Pesquisa Energética"),
    ("EVO", "*Efficiency Valuation Organization*"),
    ("GLP", "Gás liquefeito de petróleo"),
    ("IC", "Intervalo de confiança"),
    ("IDE", "Indicador de desempenho energético"),
    ("I-MR", "Gráfico de controle de valores individuais e amplitude móvel"),
    ("Inmetro", "Instituto Nacional de Metrologia, Qualidade e Tecnologia"),
    ("IQR", "*Interquartile range* (amplitude interquartil)"),
    ("ISO", "*International Organization for Standardization*"),
    ("LBE", "Linha de base energética"),
    ("M&V", "Medição e verificação"),
    ("MAD", "*Median absolute deviation* (desvio absoluto mediano)"),
    ("NBR", "Norma Brasileira"),
    ("NR", "Norma Regulamentadora"),
    ("PBE", "Programa Brasileiro de Etiquetagem"),
    ("PCI", "Poder calorífico inferior"),
    ("PCS", "Poder calorífico superior"),
    ("PIMVP", "Protocolo Internacional de Medição e Verificação de Performance"),
    ("SGE", "Sistema de gestão da energia"),
    ("SQL", "*Structured Query Language* (linguagem de consulta estruturada)"),
    ("tep", "Tonelada equivalente de petróleo"),
    ("VIF", "*Variance inflation factor* (fator de inflação da variância)"),
    ("WCM", "*World Class Manufacturing*"),
]

SIMBOLOS = [
    ("A", "medida de atividade (t de metal, refeições, usuários, banhos, ciclos)"),
    ("C", "custo do GLP, em R$"),
    ("CE", "consumo específico de GLP, em kg por unidade de atividade"),
    ("c", "calor específico, em kJ/(kg·K)"),
    ("d̄", "média das diferenças pareadas"),
    ("E", "energia, em kJ ou kWh"),
    ("G", "consumo de GLP em um período, em kg"),
    ("L_{f}", "calor latente de fusão, em kJ/kg"),
    ("m", "massa, em kg"),
    ("n", "tamanho da amostra"),
    ("p", "preço do GLP, em R$/kg"),
    ("Q", "quantidade de calor, em kJ"),
    ("r", "percentual de redução simulado (fração)"),
    ("S_{t}", "estoque estimado de GLP no instante t, em kg"),
    ("s", "desvio-padrão amostral"),
    ("T", "temperatura, em °C ou K"),
    ("V", "volume, em m³ ou L"),
    ("x̄", "média amostral"),
    ("α", "nível de significância"),
    ("β", "coeficiente de regressão"),
    ("ε", "erro aleatório do modelo"),
    ("η", "rendimento ou eficiência térmica (fração)"),
    ("μ_{d}", "média populacional das diferenças"),
    ("ρ", "massa específica, em kg/m³"),
]

META = Metadados(
    instituicao=["Centro Universitário Nossa Senhora do Patrocínio", "Curso de Engenharia Elétrica"],
    autor="Vitor Henrique Santos Das Virgens",
    titulo="Sistema inteligente de monitoramento, análise estatística e otimização do consumo de GLP industrial",
    subtitulo="fundamentação, desenvolvimento, testes e validação de uma ferramenta de apoio à decisão",
    natureza=(
        "Relatório técnico-científico apresentado à disciplina de Experimentação e Análise de "
        "Dados do curso de Engenharia Elétrica do Centro Universitário Nossa Senhora do "
        "Patrocínio (CEUNSP), referente às Fases 1 a 7 do projeto."
    ),
    orientador=ORIENTADOR,
    local=CIDADE,
    ano="2026",
    resumo=RESUMO,
    palavras_chave=["GLP", "eficiência energética", "inferência estatística",
                    "monitoramento energético", "painel de indicadores"],
    abstract=ABSTRACT,
    keywords=["LPG", "energy efficiency", "statistical inference", "energy monitoring",
              "dashboard"],
    siglas=SIGLAS,
    simbolos=SIMBOLOS,
)

FONTE_AUTOR = "elaborado pelo autor (2026)."


# ---------------------------------------------------------------------------
# Conteúdo textual
# ---------------------------------------------------------------------------
def montar_conteudo() -> Conteudo:
    c = Conteudo()

    # =====================================================================
    c.h1("1", "INTRODUÇÃO")
    c.h2("1.1", "CONTEXTO E JUSTIFICATIVA")
    c.p(
        "O gás liquefeito de petróleo (GLP) é utilizado em indústrias mecânicas como fonte de "
        "calor em processos de fusão e aquecimento de metais, na cocção de alimentos em "
        "restaurantes corporativos e no aquecimento de água para uso dos funcionários. Em "
        "muitas empresas, o consumo é conhecido apenas pelo total comprado, registrado nas notas "
        "fiscais de abastecimento, sem distinção entre os setores que utilizam o combustível. "
        "Sem essa distinção, não é possível saber onde estão as maiores perdas, nem verificar se "
        "uma melhoria operacional produziu economia real."
    )
    c.p(
        "A ABNT NBR ISO 50001 estabelece requisitos para sistemas de gestão da energia baseados "
        "em melhoria contínua, nos quais o desempenho energético é acompanhado por indicadores "
        "de desempenho energético (IDE) comparados a uma linha de base energética (LBE) "
        "(ABNT, 2018b). A ABNT NBR ISO 50006 orienta o estabelecimento e a manutenção desses "
        "indicadores e linhas de base, que podem ser aplicados à organização inteira, a um "
        "processo ou a um equipamento (ABNT, 2024b). Este projeto aplica esses conceitos ao "
        "consumo de GLP, com apoio de métodos estatísticos para separar variações aleatórias de "
        "mudanças reais de desempenho."
    )
    c.p(
        "Comparar apenas os quilogramas consumidos por setor pode levar a conclusões erradas, "
        "pois um setor com maior consumo absoluto pode simplesmente produzir mais. Por isso, "
        "sempre que houver dados, o consumo será normalizado pela atividade de cada setor: "
        "toneladas de metal processado na fundição, refeições no restaurante e usuários ou "
        "banhos nos chuveiros."
    )

    c.h2("1.2", "OBJETIVOS")
    c.h3("1.2.1", "Objetivo geral")
    c.p(
        "Desenvolver uma ferramenta de monitoramento e apoio à decisão que quantifique o "
        "consumo de GLP por setor, construa indicadores de eficiência, identifique consumo fora "
        "do padrão, estime o impacto financeiro de melhorias e avalie estatisticamente se "
        "intervenções reduziram o consumo, sem atuar sobre os equipamentos."
    )
    c.h3("1.2.2", "Objetivos específicos")
    c.alineas([
        "reunir fundamentação técnica e científica sobre o uso de GLP em fundição, cozinha "
        "industrial e aquecimento de água, com fontes identificadas",
        "definir fórmulas de conversão de massa em energia, de custo e de consumo específico",
        "definir indicadores de desempenho energético para cada setor",
        "definir os métodos estatísticos de descrição, comparação, correlação, regressão e "
        "detecção de anomalias",
        "propor uma arquitetura de software modular, com importação e validação de dados, "
        "banco de dados histórico e painel interativo",
        "distinguir, em todas as etapas, dados medidos, de referência, calculados, hipotéticos "
        "e simulados",
    ])

    c.h2("1.3", "QUESTÕES QUE O SISTEMA DEVE RESPONDER")
    c.p(
        "O Quadro 1 relaciona as perguntas de negócio do projeto com o método previsto para "
        "respondê-las e os dados necessários."
    )
    c.quadro(
        "Perguntas do projeto, métodos e dados necessários",
        ["Pergunta", "Método ou indicador", "Dados necessários"],
        [
            ["Quanto GLP é consumido por dia, semana e mês?", "Agregação temporal do consumo (kg)",
             "Leituras de medidores ou abastecimentos com data"],
            ["Qual setor consome mais?", "Consumo por setor e participação percentual",
             "Medição por setor (submedição)"],
            ["Quanto cada setor representa no custo?", "Custo por setor (Equação 2)",
             "Consumo por setor e preço (R$/kg)"],
            ["O consumo está aumentando ou diminuindo?", "Série temporal, médias móveis, regressão",
             "Histórico contínuo de consumo"],
            ["Há desperdício ou consumo fora do padrão?",
             "Detecção de anomalias (Quadro 9) e consumo fora do horário produtivo",
             "Consumo com resolução diária ou horária"],
            ["Quais variáveis influenciam o consumo?", "Correlação e regressão (seção 2.9.4)",
             "Produção, horas, temperatura, refeições, usuários"],
            ["Qual o consumo de referência de cada setor?", "Linha de base energética (seção 2.4)",
             "Período de referência representativo"],
            ["Quanto se poderia economizar?", "Simulação de cenários (seção 2.8)",
             "Consumo atual, preço, dias de operação"],
            ["Uma intervenção reduziu o consumo?", "Testes de hipóteses e IC (seção 2.9.3)",
             "Dados antes e depois em condições comparáveis"],
        ],
        [5.0, 5.5, 5.5],
        FONTE_AUTOR,
    )

    c.h2("1.4", "ESCOPO, PREMISSAS E LIMITES")
    c.p(
        "O sistema é uma ferramenta de monitoramento, análise e apoio à decisão. Ele não envia "
        "comandos a reguladores, válvulas, pressostatos, queimadores ou dispositivos de "
        "segurança. Qualquer ajuste de combustão, manutenção ou alteração de instalação "
        "sugerido pelas análises é apresentado como recomendação a ser avaliada por "
        "profissionais habilitados, de acordo com os manuais dos fabricantes e as normas "
        "aplicáveis."
    )
    c.p("As seguintes premissas orientam todo o projeto:")
    c.alineas([
        "nenhum dado da empresa é inventado; na falta de medições, são usados dados sintéticos "
        "identificados como SIMULADOS, com hipóteses explícitas e parâmetros editáveis",
        "estimativas não são apresentadas como medições",
        "conclusões estatísticas sobre a empresa só são tiradas de dados medidos",
        "maior consumo absoluto não é, por si só, evidência de ineficiência",
        "toda fórmula é documentada e toda informação externa tem fonte identificada",
    ])

    c.h2("1.5", "ORGANIZAÇÃO DO TRABALHO EM FASES")
    c.p(
        "O desenvolvimento foi dividido em sete fases, com validação ao final de cada uma antes "
        "de avançar para a seguinte (Quadro 2). Os capítulos 2 a 8 deste relatório "
        "correspondem às Fases 1 a 7, e o capítulo 9 traz as considerações finais."
    )
    c.quadro(
        "Fases do projeto e capítulos correspondentes",
        ["Fase", "Conteúdo", "Capítulo"],
        [
            ["1 – Pesquisa", "Fundamentação técnica, fórmulas, indicadores e métodos", "2"],
            ["2 – Diagnóstico", "Análise do repositório existente", "3"],
            ["3 – Modelagem", "Estrutura de dados, validações, parâmetros e arquitetura", "4"],
            ["4 – Desenvolvimento", "Módulos Python, painel em Streamlit e linha de comando", "5"],
            ["5 – Testes", "Testes automatizados e verificação com gabarito simulado", "6"],
            ["6 – Documentação", "Instalação, execução e uso", "7"],
            ["7 – Validação", "Limitações, requisitos de dados reais e implantação", "8"],
        ],
        [3.5, 8.0, 4.5],
        FONTE_AUTOR,
    )

    # =====================================================================
    c.h1("2", "FASE 1 — FUNDAMENTAÇÃO TÉCNICA E CIENTÍFICA")
    c.h2("2.1", "MÉTODO DA PESQUISA")
    c.p(
        "A pesquisa priorizou publicações oficiais (ANP, EPE e Inmetro), normas técnicas, "
        "protocolos internacionais de medição e verificação, artigos científicos e trabalhos "
        "acadêmicos, conforme solicitado no escopo do projeto. As buscas foram feitas em "
        "mecanismos de busca na internet, em português e em inglês, em 13 de novembro de 2026."
    )
    c.p(
        "Duas limitações devem ser registradas. Primeiro, o ambiente de trabalho não permitiu "
        "abrir diretamente alguns documentos oficiais (por exemplo, os arquivos do portal "
        "gov.br); nesses casos, o conteúdo foi confirmado pelos trechos indexados de várias "
        "edições da mesma publicação, e o documento original deve ser conferido antes da "
        "versão final. Segundo, o texto integral das normas ABNT, que é pago, não foi "
        "consultado: elas são citadas apenas pelo título e pelo escopo. Os itens que ainda "
        "precisam de verificação estão reunidos no Quadro 10."
    )

    c.h2("2.2", "CLASSIFICAÇÃO DA ORIGEM DOS DADOS")
    c.p(
        "Para evitar que estimativas sejam confundidas com medições, todo valor manipulado pelo "
        "sistema terá uma classe de origem (Quadro 3). Um valor calculado herda a classe mais "
        "fraca entre as suas entradas: se qualquer entrada for hipotética, o resultado também é "
        "hipotético; se qualquer entrada for simulada, o resultado é simulado."
    )
    c.quadro(
        "Classes de origem dos dados",
        ["Classe", "Definição", "Exemplo no projeto", "Uso permitido"],
        [
            ["REFERÊNCIA", "Valor publicado em fonte externa identificada",
             f"PCI do GLP = {fmt(PCI_KCAL_KG, 0)} kcal/kg (ANP, 2026)",
             "Parâmetro de cálculo, sempre com citação"],
            ["MEDIDO (empresa)", "Dado fornecido ou medido pela empresa",
             "Notas fiscais, leituras de medidores, produção diária",
             "Base para conclusões sobre a empresa"],
            ["CALCULADO", "Resultado de fórmula documentada aplicada a outros dados",
             "kg de GLP por tonelada; custo por refeição",
             "Herda a classe mais fraca das entradas"],
            ["HIPÓTESE", "Valor assumido na falta de medição",
             "Rendimento do aquecedor enquanto não houver dado do fabricante",
             "Cenários e estimativas, sempre sinalizado e editável"],
            ["SIMULADO", "Série sintética gerada por modelo",
             "Dados de demonstração do painel",
             "Testes e demonstração; nunca conclusões sobre a empresa"],
        ],
        [2.8, 4.4, 4.6, 4.2],
        FONTE_AUTOR,
    )

    c.h2("2.3", "GLP: COMPOSIÇÃO, PROPRIEDADES E CONVERSÃO EM ENERGIA")
    c.p(
        "O GLP é uma mistura de hidrocarbonetos, predominantemente propano e butano. No Brasil, "
        "sua especificação e o controle de qualidade são regulados pela Resolução ANP nº 825/2020, "
        "que define os tipos comercializados, entre eles o propano especial, com no mínimo 90 % "
        "de propano e no máximo 5 % de propeno em volume (Brasil, 2020). Como a composição pode "
        "variar entre fornecimentos, o poder calorífico também varia; para monitoramento, "
        "adota-se o valor médio publicado nas tabelas de fatores de conversão do Anuário "
        "Estatístico da ANP, que reproduzem os valores do Balanço Energético Nacional (BEN) da "
        "EPE (ANP, 2026)."
    )
    c.p(
        "A Tabela 1 apresenta os parâmetros adotados. O poder calorífico inferior (PCI) "
        "desconta o calor latente da água formada na combustão e é a base usual dos balanços "
        "energéticos; o poder calorífico superior (PCS) inclui esse calor. Ao comparar o "
        "consumo com o rendimento declarado por fabricantes, é preciso verificar em qual base o "
        "rendimento foi informado, pois misturar PCI e PCS introduz erro sistemático."
    )
    c.tabela(
        "Parâmetros de referência para conversão do GLP",
        ["Parâmetro", "Valor", "Unidade", "Origem"],
        [
            ["Poder calorífico inferior (PCI)", fmt(PCI_KCAL_KG, 0), "kcal/kg", "REFERÊNCIA (ANP, 2026)"],
            ["PCI em unidades do SI", fmt(PCI_MJ_KG, 2), "MJ/kg", "CALCULADO (1 kcal = 4,1868 kJ)"],
            ["PCI em quilowatt-hora", fmt(PCI_KWH_KG, 2), "kWh/kg", "CALCULADO (1 kWh = 3,6 MJ)"],
            ["Energia por tonelada", fmt(TEP_POR_T, 2), "tep/t", "CALCULADO (1 tep = 10^{7} kcal)"],
            ["Massa específica média (fase líquida)", fmt(MASSA_ESPECIFICA_T_M3, 3), "t/m³", "REFERÊNCIA (ANP, 2026)"],
        ],
        [5.6, 2.2, 2.0, 6.2],
        "ANP (2026); valores calculados pelo autor (2026).",
        nota="valores médios para conversão estatística; não substituem a análise do GLP efetivamente fornecido.",
        alinhamentos=["L", "R", "C", "L"],
    )
    c.p("A energia contida em uma massa de GLP é obtida pela Equação 1:")
    c.eq("E = m_{GLP} · PCI")
    c.definicoes([
        ("E", "energia liberada na combustão completa, em kJ (ou kWh, se o PCI for usado em kWh/kg)"),
        ("m_{GLP}", "massa de GLP consumida, em kg"),
        ("PCI", f"poder calorífico inferior, {fmt(PCI_MJ_KG, 2)} MJ/kg ou {fmt(PCI_KWH_KG, 2)} kWh/kg"),
    ])
    c.p(
        "Um cuidado importante refere-se à unidade de medição. Medidores de gás instalados nas "
        "redes internas costumam medir volume de GLP em fase vapor, na pressão e na temperatura "
        "da linha. A massa específica de 0,552 t/m³ refere-se à fase líquida e não pode ser usada "
        "para converter volume de vapor em massa. Nesse caso, a conversão exige o fator "
        "informado pelo fornecedor ou a correção metrológica por pressão, temperatura e "
        "composição. Por esse motivo, o sistema registrará sempre a unidade de origem de cada "
        "leitura e só aceitará conversões com fator explícito."
    )

    c.h2("2.4", "GESTÃO DE ENERGIA, INDICADORES E LINHA DE BASE")
    c.p(
        "Na abordagem da ABNT NBR ISO 50001, a organização identifica os usos significativos "
        "de energia, define IDE e LBE, monitora o desempenho e atua sobre os desvios em ciclos "
        "de melhoria contínua (ABNT, 2018b). A LBE é a referência quantitativa usada para "
        "comparar os valores dos IDE ao longo do tempo e quantificar mudanças de desempenho "
        "(ABNT, 2024b). A ISO 50015 trata dos princípios de medição e verificação (M&V) do "
        "desempenho energético das organizações (ISO, 2014)."
    )
    c.p(
        "O Protocolo Internacional de Medição e Verificação de Performance (PIMVP), mantido "
        "pela *Efficiency Valuation Organization*, padroniza a determinação de economias de "
        "energia (EVO, 2012). Seu princípio central é que a economia não pode ser medida "
        "diretamente, pois corresponde à energia que deixou de ser consumida; ela é determinada "
        "pela comparação entre o consumo medido após a intervenção e o consumo que teria "
        "ocorrido sem ela, estimado pela linha de base ajustada às condições do período de "
        "determinação (Equação 4). O protocolo oferece quatro opções: A e B isolam a medida de "
        "eficiência, medindo os parâmetros principais (A) ou todos os parâmetros (B); C usa a "
        "medição da instalação inteira; e D usa simulação calibrada."
    )
    c.p("O custo e o consumo específico, base dos IDE de razão, são dados pelas Equações 2 e 3:")
    c.eq("C = m_{GLP} · p")
    c.eq("CE = m_{GLP} / A")
    c.definicoes([
        ("C", "custo do GLP no período, em R$"),
        ("p", "preço do GLP, em R$/kg, conforme nota fiscal"),
        ("CE", "consumo específico, em kg por unidade de atividade"),
        ("A", "atividade no período (t de metal, refeições, usuários ou banhos)"),
    ])
    c.p("A economia verificada segundo o PIMVP é expressa pela Equação 4:")
    c.eq("Economia = (G_{LB,aj} − G_{rel}) ± Aj_{NR}")
    c.definicoes([
        ("G_{LB,aj}", "consumo previsto pela linha de base, ajustado às condições do período de relatório, em kg"),
        ("G_{rel}", "consumo medido no período de relatório, em kg"),
        ("Aj_{NR}", "ajustes não rotineiros (mudanças de equipamento, de turno, de produto etc.), em kg"),
    ])
    c.p(
        "Quando o consumo depende de variáveis como produção ou número de refeições, a linha "
        "de base deve ser um modelo de regressão do consumo em função dessas variáveis, e não "
        "uma média simples. O termo independente do modelo representa a parcela de consumo que "
        "não depende da atividade (perdas em espera, pré-aquecimento, chamas acesas sem uso). "
        "Os resíduos do modelo, isto é, as diferenças entre consumo medido e previsto, são a "
        "base da detecção de anomalias e do gráfico de somas acumuladas (CUSUM), técnica "
        "proposta por Page (1954) para detectar mudanças persistentes de nível."
    )

    # ---------------------------------------------------------------------
    c.h2("2.5", "FUNDIÇÃO DE PEÇAS")
    c.h3("2.5.1", "Uso do GLP e tipos de fornos")
    c.p(
        "Em fundições, a fusão é a etapa de maior consumo de energia. Em estudo para o "
        "Departamento de Energia dos Estados Unidos, a fusão respondeu por cerca de 55 % do "
        "consumo de energia da indústria de fundição, e as tecnologias de fusão em uso "
        "apresentavam baixa eficiência térmica (BCS, 2005). O mesmo estudo compara fornos de "
        "diferentes tipos, como fornos cadinho, fornos de revérbero e fornos de torre, além de "
        "fornos elétricos de indução, quanto à eficiência e à perda de metal."
    )
    c.p(
        "Além da fusão, o GLP pode ser usado em fornos de espera (manutenção do metal líquido), "
        "no pré-aquecimento de panelas e moldes e em tratamentos térmicos. Como cada "
        "equipamento tem funcionamento próprio, o sistema não presumirá que todos os fornos "
        "são iguais: cada equipamento será cadastrado com os atributos do Quadro 4."
    )
    c.quadro(
        "Atributos do cadastro de equipamentos da fundição",
        ["Atributo", "Descrição", "Origem esperada"],
        [
            ["Identificador e nome", "Código único do equipamento", "Empresa"],
            ["Tipo", "Cadinho fixo, basculante, revérbero, torre, panela, tratamento térmico, outro", "Empresa"],
            ["Função", "Fusão, espera, pré-aquecimento ou tratamento térmico", "Empresa"],
            ["Metal ou liga", "Ex.: liga de alumínio, zinco, cobre; define propriedades térmicas", "Empresa"],
            ["Capacidade nominal", "Massa de metal por ciclo, em kg", "Fabricante"],
            ["Potência térmica nominal", "kW ou kg/h de GLP do queimador", "Fabricante"],
            ["Queimador e controle", "Tipo de queimador e de controle de combustão", "Fabricante"],
            ["Medição individual", "Indica se há medidor de GLP dedicado", "Empresa"],
            ["Temperatura de trabalho", "Temperatura de vazamento ou de processo, em °C", "Empresa"],
        ],
        [4.0, 8.0, 4.0],
        FONTE_AUTOR,
    )

    c.h3("2.5.2", "Queimadores e eficiência da combustão")
    c.p(
        "O queimador mistura combustível e ar. A combustão completa exige ar em quantidade "
        "igual ou superior à estequiométrica; o ar em excesso não participa da reação, mas é "
        "aquecido e sai pela chaminé, levando energia consigo, enquanto a falta de ar provoca "
        "combustão incompleta, com formação de monóxido de carbono (Çengel; Boles, 2013). Por "
        "isso, o ajuste da relação ar-combustível, verificado pela análise dos gases de "
        "combustão, é uma das principais oportunidades de economia, e deve ser executado por "
        "técnico habilitado."
    )
    c.p(
        "As perdas pelos gases de exaustão tendem a dominar o balanço de fornos de fusão. Em "
        "medições em fornos de revérbero a gás natural para fusão de alumínio secundário, Li "
        "et al. (2006) encontraram eficiência energética efetiva da ordem de 26 % a 29 % na "
        "maioria dos fornos, com perdas pelos gases de exaustão entre 35 % e 50 %. Em um forno "
        "cadinho de fusão de zinco a gás natural, o pré-aquecimento do ar de combustão a 370 °C "
        "reduziu o consumo de gás em 28 %, com investimento de R$ 112.000,00 e economia de "
        "R$ 5.800,00 por mês (Vergnhanini Filho; Spegiorin, 2013), o que corresponde a um "
        f"retorno simples de aproximadamente {fmt(CASO_PAYBACK_MESES, 1)} meses (valor "
        "calculado pelo autor a partir dos dados publicados). Almeida (2019) aplicou uma "
        "metodologia de melhoria focada, do sistema *World Class Manufacturing* (WCM), para "
        "reduzir o consumo de gás natural em um forno de uma fábrica de refusão de alumínio."
    )
    c.p(
        "Esses resultados referem-se a fornos e combustíveis específicos e não podem ser "
        "transferidos diretamente aos fornos da empresa. Eles indicam a ordem de grandeza das "
        "perdas e o tipo de método que será usado; as economias reais só poderão ser estimadas "
        "com medições nos equipamentos da empresa."
    )

    c.h3("2.5.3", "Balanço térmico e eficiência do forno")
    c.p(
        "O calor útil necessário para aquecer, fundir e superaquecer o metal até a temperatura "
        "de vazamento é dado pela soma do calor sensível no estado sólido, do calor latente de "
        "fusão e do calor sensível no estado líquido (Equação 5). A eficiência térmica estimada "
        "do forno é a razão entre esse calor útil e a energia do GLP consumido (Equação 6)."
    )
    c.eq("Q_{útil} = m_{metal} · [c_{s} · (T_{f} − T_{0}) + L_{f} + c_{l} · (T_{v} − T_{f})]")
    c.eq("η_{forno} = Q_{útil} / (m_{GLP} · PCI)")
    c.definicoes([
        ("m_{metal}", "massa de metal processada no ciclo, em kg"),
        ("c_{s}, c_{l}", "calores específicos médios do metal sólido e líquido, em kJ/(kg·K)"),
        ("T_{0}, T_{f}, T_{v}", "temperaturas inicial, de fusão e de vazamento, em °C"),
        ("L_{f}", "calor latente de fusão da liga, em kJ/kg"),
        ("η_{forno}", "eficiência térmica estimada do forno"),
    ])
    c.p(
        "As propriedades da liga (c_{s}, c_{l}, L_{f} e T_{f}) devem ser obtidas da ficha técnica da "
        "liga ou de manuais de referência e serão parâmetros configuráveis, com a fonte "
        "registrada; enquanto não houver fonte, serão tratadas como HIPÓTESE. A eficiência só "
        "será calculada quando houver medição de GLP do forno e registro da massa processada."
    )
    c.p(
        "As principais perdas a investigar são: gases de exaustão; condução e radiação pelas "
        "paredes e pela tampa, que dependem do isolamento térmico, cuja resistência térmica "
        "limita o fluxo de calor para o ambiente (Bergman et al., 2014); calor acumulado no "
        "refratário a cada partida; e tempo de forno ligado sem carga produtiva. Para separar a "
        "parcela fixa da parcela proporcional à produção, propõe-se o modelo de regressão da "
        "Equação 7, ajustado por forno:"
    )
    c.eq("G_{dia} = β_{0} + β_{1} · h_{lig} + β_{2} · M_{metal} + ε")
    c.definicoes([
        ("G_{dia}", "consumo diário de GLP do forno, em kg"),
        ("h_{lig}", "horas de forno ligado no dia"),
        ("M_{metal}", "massa de metal processada no dia, em t"),
        ("β_{0}, β_{1}, β_{2}", "coeficientes estimados por mínimos quadrados"),
        ("ε", "erro aleatório"),
    ])
    c.p(
        "Nesse modelo, β_{1} estima o consumo por hora de funcionamento associado a perdas e "
        "manutenção de temperatura, e β_{2} estima o consumo marginal por tonelada. Um β_{1} "
        "elevado em relação a β_{2} indica que reduzir o tempo de espera sem carga tende a ser "
        "mais vantajoso do que otimizar o ciclo de fusão."
    )

    c.h3("2.5.4", "Indicadores da fundição")
    c.quadro(
        "Indicadores de desempenho energético da fundição",
        ["Indicador", "Fórmula", "Unidade", "Dados necessários"],
        [
            ["Consumo por hora de funcionamento", "G / h_{lig}", "kg/h", "GLP do forno e horas ligado"],
            ["Consumo por tonelada processada", "G / M_{metal}", "kg/t", "GLP do forno e massa processada"],
            ["Consumo por ciclo de fundição", "G / N_{ciclos}", "kg/ciclo", "GLP do forno e número de ciclos"],
            ["Custo por tonelada produzida", "G · p / M_{metal}", "R$/t", "GLP, preço e massa processada"],
            ["Consumo por forno", "Σ G_{forno}", "kg", "Medição individual por forno"],
            ["Eficiência térmica estimada", "Equação 6", "%", "GLP, massa, temperaturas e propriedades da liga"],
            ["Fração de tempo sem carga", "h_{sem carga} / h_{lig}", "%", "Registro de operação do forno"],
            ["GLP consumido em espera", "β_{1} · h_{sem carga}", "kg", "Modelo da Equação 7"],
        ],
        [4.6, 3.6, 2.0, 5.8],
        FONTE_AUTOR,
    )
    c.p(
        "Oportunidades típicas de economia, a serem avaliadas por profissionais habilitados, "
        "incluem: ajuste da relação ar-combustível; manutenção de queimadores; manutenção de "
        "tampas e do isolamento; programação da produção para reduzir o tempo de espera e "
        "fundir cargas completas; e recuperação de calor dos gases para pré-aquecer o ar de "
        "combustão ou a carga. O sistema apenas indicará onde investigar, sem atuar nos "
        "equipamentos."
    )

    # ---------------------------------------------------------------------
    c.h2("2.6", "RESTAURANTE INDUSTRIAL")
    c.h3("2.6.1", "Uso do GLP na cozinha industrial")
    c.p(
        "Em cozinhas industriais, o GLP alimenta equipamentos como fogões de queimadores "
        "abertos, fornos, caldeirões, fritadeiras e chapas. O consumo diário depende do número "
        "de refeições, do cardápio (preparações de cocção longa consomem mais), do rendimento "
        "dos equipamentos e das práticas de operação, como o uso de tampas, o ajuste da chama "
        "ao tamanho da panela e o desligamento de queimadores entre preparos."
    )
    c.p(
        "O Programa Brasileiro de Etiquetagem (PBE), coordenado pelo Inmetro com a participação "
        "do CONPET, classifica fogões e fornos domésticos a gás por eficiência e aquecedores de "
        "água a gás por rendimento (Inmetro, 2023). Nas buscas realizadas, não foram "
        "encontradas tabelas equivalentes para equipamentos de cocção industrial; por isso, o "
        "consumo nominal desses equipamentos deverá vir dos manuais dos fabricantes."
    )
    c.h3("2.6.2", "Lacuna: valor de referência por refeição")
    c.p(
        "As buscas não encontraram, em fontes públicas confiáveis, um valor de referência de "
        "consumo de GLP por refeição aplicável a restaurantes industriais. Por isso, o projeto "
        "não adotará valor externo: o consumo de referência será a linha de base interna, "
        "construída com os dados da própria empresa, como recomenda a abordagem de IDE e LBE "
        "(ABNT, 2024b)."
    )
    c.h3("2.6.3", "Modelo de consumo em função das refeições")
    c.p("O consumo diário do restaurante será modelado pela Equação 8:")
    c.eq("G_{dia} = β_{0} + β_{1} · N_{ref} + ε")
    c.definicoes([
        ("N_{ref}", "número de refeições produzidas no dia"),
        ("β_{0}", "parcela fixa diária (pré-aquecimento, chamas de espera, preparos independentes do volume), em kg"),
        ("β_{1}", "consumo marginal por refeição, em kg/refeição"),
    ])
    c.p(
        "Da Equação 8 decorre a Equação 9, que mostra que o consumo por refeição diminui quando "
        "o número de refeições aumenta, mesmo sem nenhuma mudança de eficiência:"
    )
    c.eq("G_{dia} / N_{ref} = β_{0} / N_{ref} + β_{1}")
    c.p(
        "Assim, comparar o indicador kg/refeição entre dias com quantidades muito diferentes de "
        "refeições é enviesado. A comparação correta é feita entre dias de volume semelhante "
        "(estratificação por faixas de refeições) ou pelos resíduos em relação ao modelo. Efeitos "
        "do dia da semana e do cardápio podem ser incluídos como variáveis adicionais quando "
        "houver dados."
    )
    c.h3("2.6.4", "Indicadores do restaurante")
    c.quadro(
        "Indicadores de desempenho energético do restaurante",
        ["Indicador", "Fórmula", "Unidade", "Dados necessários"],
        [
            ["Consumo diário", "G_{dia}", "kg/dia", "Medição diária do restaurante"],
            ["Consumo por refeição", "G_{dia} / N_{ref}", "kg/refeição", "GLP e contagem de refeições"],
            ["Custo por refeição", "G_{dia} · p / N_{ref}", "R$/refeição", "GLP, preço e refeições"],
            ["Consumo mensal", "Σ G_{dia}", "kg/mês", "Série diária ou abastecimentos"],
            ["Consumo por equipamento", "G_{equip}", "kg", "Submedição por equipamento"],
            ["Parcela fixa diária", "β_{0} (Equação 8)", "kg/dia", "Série com refeições variadas"],
            ["Consumo fora do horário de produção", "G entre fechamento e abertura", "kg", "Leituras horárias"],
            ["Comparação por faixa de refeições", "Média de CE por faixa de N_{ref}", "kg/refeição", "Série diária"],
        ],
        [4.6, 4.2, 2.4, 4.8],
        FONTE_AUTOR,
    )

    # ---------------------------------------------------------------------
    c.h2("2.7", "AQUECIMENTO DE ÁGUA PARA CHUVEIROS")
    c.h3("2.7.1", "Sistemas de aquecimento")
    c.p(
        "O aquecimento de água a gás pode ser feito por aquecedores de passagem (instantâneos), "
        "que aquecem a água apenas durante o uso, ou por aquecedores de acumulação, que mantêm "
        "um reservatório aquecido, eventualmente com circuito de recirculação. Os sistemas "
        "prediais de água quente são tratados pela ABNT NBR 5626:2020, que incorporou o escopo "
        "da antiga NBR 7198 (ABNT, 2020). O PBE classifica os aquecedores de água a gás pelo "
        "rendimento térmico, e esse rendimento declarado deve ser usado como parâmetro no "
        "cálculo (Inmetro, 2023)."
    )
    c.h3("2.7.2", "Demanda térmica e consumo de GLP")
    c.p(
        "A energia para aquecer um volume de água e a massa de GLP correspondente são dadas "
        "pelas Equações 10 e 11; o volume diário de água quente, pela Equação 12 (Bergman et "
        "al., 2014; Çengel; Boles, 2013):"
    )
    c.eq("Q = ρ_{a} · V · c_{a} · (T_{s} − T_{e})")
    c.eq("m_{GLP} = Q / (η · PCI)")
    c.eq("V_{dia} = N_{b} · t_{b} · q_{v}")
    c.definicoes([
        ("ρ_{a}, c_{a}", "massa específica e calor específico da água"),
        ("T_{e}, T_{s}", "temperaturas da água na entrada e na saída do aquecedor, em °C"),
        ("η", "rendimento do aquecedor (dado do fabricante ou etiqueta do PBE)"),
        ("N_{b}", "número de banhos no dia"),
        ("t_{b}", "duração média do banho, em min"),
        ("q_{v}", "vazão média de água quente por chuveiro, em L/min"),
    ])
    c.p(
        "Conforme as premissas do projeto, o número de usuários, a duração dos banhos e a "
        "capacidade dos aquecedores não são presumidos: são parâmetros configuráveis. A "
        "Tabela 2 apresenta um exemplo de cálculo exclusivamente ilustrativo, com entradas "
        "hipotéticas identificadas."
    )
    c.tabela(
        "Exemplo ilustrativo do cálculo de GLP para aquecimento de água",
        ["Grandeza", "Valor", "Unidade", "Origem"],
        [
            ["Volume de água aquecida", fmt(EX_VOLUME_L, 0), "L", "HIPÓTESE"],
            ["Massa específica da água (aproximação)", fmt(EX_MASSA_ESP_AGUA, 2), "kg/L", "HIPÓTESE (simplificação)"],
            ["Calor específico da água", fmt(EX_CP_AGUA, 2), "kJ/(kg·K)", "REFERÊNCIA (Bergman et al., 2014)"],
            ["Elevação de temperatura (T_{s} − T_{e})", fmt(EX_DELTA_T, 0), "K", "HIPÓTESE"],
            ["Rendimento do aquecedor", fmt(EX_RENDIMENTO * 100, 0), "%", "HIPÓTESE"],
            ["PCI do GLP", fmt(PCI_KJ_KG, 0), "kJ/kg", "REFERÊNCIA (ANP, 2026)"],
            ["Calor necessário (Equação 10)", f"{fmt(EX_Q_KJ, 0)} ({fmt(EX_Q_KWH, 2)} kWh)", "kJ", "CALCULADO → HIPOTÉTICO"],
            ["GLP necessário (Equação 11)", fmt(EX_M_GLP, 3), "kg", "CALCULADO → HIPOTÉTICO"],
        ],
        [5.8, 3.4, 2.2, 4.6],
        FONTE_AUTOR,
        nota="por depender de entradas hipotéticas, o resultado é hipotético e não descreve a empresa.",
        alinhamentos=["L", "R", "C", "L"],
    )
    c.h3("2.7.3", "Perdas térmicas e consumo fora do horário de uso")
    c.p(
        "Em sistemas de acumulação, parte do GLP é consumida para repor o calor perdido pelo "
        "reservatório e pela tubulação de recirculação, mesmo sem uso. Em regime permanente, "
        "essa perda pode ser estimada pela Equação 13 (Bergman et al., 2014):"
    )
    c.eq("q_{perda} = U · A_{s} · (T_{a} − T_{amb})")
    c.definicoes([
        ("q_{perda}", "taxa de perda de calor, em W"),
        ("U", "coeficiente global de transferência de calor, em W/(m²·K)"),
        ("A_{s}", "área da superfície do reservatório ou da tubulação, em m²"),
        ("T_{a}, T_{amb}", "temperaturas da água armazenada e do ambiente, em °C"),
    ])
    c.p(
        "Na prática, a perda em espera será identificada pelos dados: consumo em horários sem "
        "banhos (madrugadas, fins de semana) indica perdas de acumulação ou aquecedores ligados "
        "fora do período de uso. A redução da temperatura de armazenamento ou a programação "
        "horária dos aquecedores deve considerar também o risco sanitário de proliferação de "
        "microrganismos na água morna, e por isso depende de avaliação por profissional "
        "habilitado."
    )
    c.h3("2.7.4", "Indicadores dos chuveiros")
    c.quadro(
        "Indicadores de desempenho energético do aquecimento de água",
        ["Indicador", "Fórmula", "Unidade", "Dados necessários"],
        [
            ["Consumo diário", "G_{dia}", "kg/dia", "Medição do sistema de aquecimento"],
            ["Consumo por usuário", "G_{dia} / N_{u}", "kg/usuário", "Contagem de usuários (ex.: controle de acesso)"],
            ["Consumo por banho", "G_{dia} / N_{b}", "kg/banho", "Contagem confiável de banhos"],
            ["Custo diário e mensal", "G · p", "R$", "GLP e preço"],
            ["Perfil horário", "G por hora do dia", "kg/h", "Leituras horárias"],
            ["Demanda térmica estimada", "Equação 10", "kWh/dia", "Volume e temperaturas (medidos ou hipotéticos)"],
            ["Consumo fora do horário de uso", "G sem banhos registrados", "kg", "Leituras horárias e escala de uso"],
            ["Potencial de redução", "Cenários (seção 2.8)", "kg e R$", "Consumo atual e preço (SIMULADO)"],
        ],
        [4.4, 3.8, 2.2, 5.6],
        FONTE_AUTOR,
    )

    # ---------------------------------------------------------------------
    c.h2("2.8", "CUSTOS E SIMULAÇÃO DE ECONOMIA")
    c.p(
        "O preço por quilograma deve vir das notas fiscais de abastecimento da empresa, pois o "
        "preço do GLP a granel inclui frete, tributos e condições contratuais. Como referência "
        "externa para comparação, a ANP publica, no Anuário Estatístico, o preço médio do GLP "
        "ao consumidor em R$/kg por grande região e unidade da Federação (ANP, 2025). O preço "
        "será um parâmetro editável."
    )
    c.p(
        "O módulo de simulação calcula, para um percentual de redução r (por exemplo, 3 %, 5 %, "
        "8 %, 10 % ou 15 %), as economias da Equação 14:"
    )
    c.eq("ΔG = G_{atual} · r ;   ΔC_{dia} = ΔG_{dia} · p ;   ΔC_{mês} = ΔC_{dia} · D_{mês}")
    c.definicoes([
        ("G_{atual}", "consumo atual do setor no período, em kg"),
        ("r", "redução simulada, em fração"),
        ("D_{mês}", "dias de operação no mês"),
        ("ΔC", "economia financeira simulada, em R$"),
    ])
    c.p(
        "A economia anual é obtida com o número de dias de operação no ano. Os resultados desse "
        "módulo são sempre rotulados como SIMULAÇÃO: eles respondem \"quanto valeria uma "
        "redução de r %\", e não \"quanto foi economizado\". Uma economia só será apresentada "
        "como verificada quando for determinada pela comparação com a linha de base ajustada "
        "(Equação 4) e acompanhada da análise estatística da seção 2.9.3. O retorno simples de "
        "uma melhoria é a razão entre o investimento e a economia mensal."
    )

    # ---------------------------------------------------------------------
    c.h2("2.9", "MÉTODOS ESTATÍSTICOS")
    c.h3("2.9.1", "Estatística descritiva")
    c.p(
        "Para cada setor e período, serão calculados média, mediana, moda (apenas para dados "
        "discretos ou agrupados em classes), variância, desvio-padrão, mínimo, máximo, quartis, "
        "amplitude interquartil e coeficiente de variação (Montgomery; Runger, 2018). A "
        "distribuição será apresentada por histogramas e diagramas de caixa, e a evolução "
        "temporal, por séries com médias móveis. As principais fórmulas são:"
    )
    c.eq("x̄ = (Σ x_{i}) / n")
    c.eq("s² = Σ (x_{i} − x̄)² / (n − 1)")
    c.eq("CV = (s / x̄) · 100 %")
    c.p(
        "O coeficiente de variação permite comparar a variabilidade de setores com médias "
        "diferentes. Um CV alto no consumo específico indica processo pouco padronizado e é, "
        "por si só, um indício a investigar."
    )
    c.h3("2.9.2", "Diagnóstico de normalidade")
    c.p(
        "O teste de Shapiro-Wilk verifica a hipótese nula de que a amostra provém de uma "
        "distribuição normal (Shapiro; Wilk, 1965). Com α = 0,05, um valor p menor que 0,05 "
        "leva à rejeição da normalidade. O teste é usado como diagnóstico, junto com o gráfico "
        "quantil-quantil: com amostras pequenas ele tem pouco poder, e com amostras grandes "
        "detecta desvios sem importância prática. No teste t pareado, a normalidade exigida é a "
        "das diferenças, e não a de cada amostra."
    )
    c.h3("2.9.3", "Avaliação estatística de intervenções")
    c.p(
        "Para avaliar se uma intervenção reduziu o consumo, define-se para cada par de "
        "observações comparáveis a diferença d_{i} = y_{antes,i} − y_{depois,i}, em que y é, de "
        "preferência, um consumo específico (por exemplo, kg de GLP por tonelada). As hipóteses "
        "unilaterais, com α = 0,05, são:"
    )
    c.alineas([
        "H_{0}: μ_{d} ≤ 0 — a intervenção não reduz o consumo médio específico de GLP",
        "H_{1}: μ_{d} > 0 — a intervenção reduz o consumo médio específico de GLP",
    ])
    c.p(
        "Quando as observações são naturalmente pareadas (mesmo forno, mesma liga, cargas "
        "equivalentes), usa-se o teste t pareado (Student, 1908), com n − 1 graus de "
        "liberdade (Equação 18). Para dois períodos independentes, usa-se o teste t de Welch "
        "(Equação 19), que não exige variâncias iguais (Welch, 1947). Quando a normalidade não "
        "é aceitável, usam-se os testes não paramétricos de Wilcoxon dos postos sinalizados "
        "para dados pareados (Wilcoxon, 1945) e de Mann-Whitney para amostras independentes "
        "(Mann; Whitney, 1947). O Quadro 8 resume a escolha."
    )
    c.eq("t = d̄ / (s_{d} / √n)")
    c.eq("t_{W} = (x̄_{1} − x̄_{2}) / √(s_{1}²/n_{1} + s_{2}²/n_{2})")
    c.p(
        "Além do valor p, serão sempre informados o intervalo de confiança de 95 % para a "
        "redução média (Equação 20) e o tamanho de efeito (Equação 21), pois uma redução pode "
        "ser estatisticamente significativa e economicamente irrelevante, ou o contrário "
        "(Cohen, 1988):"
    )
    c.eq("IC_{95%} = d̄ ± t_{α/2; n−1} · s_{d} / √n")
    c.eq("d_{z} = d̄ / s_{d}")
    c.quadro(
        "Escolha do teste para comparar antes e depois",
        ["Estrutura dos dados", "Pressuposto atendido", "Teste", "Referência"],
        [
            ["Pareados (mesmo equipamento e condições equivalentes)",
             "Diferenças aproximadamente normais", "t pareado", "Student (1908)"],
            ["Pareados", "Diferenças não normais ou com valores extremos",
             "Wilcoxon dos postos sinalizados", "Wilcoxon (1945)"],
            ["Independentes (dois períodos)", "Amostras aproximadamente normais",
             "t de Welch", "Welch (1947)"],
            ["Independentes", "Amostras não normais", "Mann-Whitney", "Mann e Whitney (1947)"],
            ["Consumo dependente de variáveis (produção, refeições)",
             "Modelo de regressão adequado", "Comparação com linha de base ajustada", "EVO (2012)"],
        ],
        [4.6, 4.4, 3.6, 3.4],
        FONTE_AUTOR,
    )
    c.p(
        "Uma redução percentual isolada não será considerada prova de melhoria. A análise "
        "também verificará:"
    )
    c.alineas([
        "a comparabilidade das condições: mix de produtos, carga dos fornos, número de "
        "refeições, temperatura da água de entrada e estação do ano; quando houver diferenças, "
        "usa-se consumo específico ou linha de base ajustada (EVO, 2012)",
        "a independência das observações: séries diárias costumam ser autocorrelacionadas, o "
        "que torna os valores p otimistas; os resíduos serão avaliados pelo teste de "
        "Durbin-Watson (Durbin; Watson, 1950) e, se necessário, os dados serão agregados por "
        "semana",
        "o tamanho da amostra: o número mínimo de observações por período será estimado antes "
        "da intervenção, a partir da variabilidade observada",
        "a qualidade dos dados: falhas, leituras corrigidas e mudanças de medidor",
        "eventos simultâneos que possam explicar a mudança (troca de turno, de fornecedor ou "
        "de produto)",
    ])
    c.h3("2.9.4", "Correlação e regressão")
    c.p(
        "A associação entre o consumo e as variáveis explicativas (quantidade produzida, tempo "
        "de funcionamento, temperatura, número de refeições, número de usuários, número de "
        "ciclos e condições ambientais) será medida pelo coeficiente de Pearson, para relações "
        "lineares, e pelo de Spearman, para relações monotônicas ou na presença de valores "
        "extremos. Modelos de regressão linear simples e múltipla, ajustados por mínimos "
        "quadrados, serão usados para construir linhas de base e previsões, com avaliação do "
        "coeficiente de determinação ajustado, da significância dos coeficientes e da análise "
        "de resíduos, e com intervalos de predição para as projeções (Montgomery; Runger, "
        "2018). Correlação não implica causalidade: os modelos indicam onde investigar, não "
        "comprovam a causa do consumo."
    )
    c.h3("2.9.5", "Detecção de anomalias")
    c.p(
        "Os métodos do Quadro 9 serão aplicados ao consumo específico ou, preferencialmente, aos "
        "resíduos da linha de base, para que dias de maior produção não sejam marcados como "
        "anômalos. Toda anomalia gera um alerta para investigação, e não uma conclusão "
        "automática de desperdício."
    )
    c.eq("M_{i} = 0,6745 · (x_{i} − x̃) / MAD")
    c.eq("LSC, LIC = x̄ ± 2,66 · MR̄")
    c.eq("CUSUM_{t} = Σ_{k=1..t} (G_{k} − Ĝ_{k})")
    c.quadro(
        "Métodos de detecção de anomalias",
        ["Método", "Regra", "Aplicação", "Referência"],
        [
            ["Cercas de Tukey", "Valor fora de [Q1 − 1,5·IQR; Q3 + 1,5·IQR]",
             "Valores extremos isolados", "Tukey (1977)"],
            ["Escore z modificado", "|M_{i}| > 3,5 (Equação 22)",
             "Robusto a valores extremos", "Iglewicz e Hoaglin (1993)"],
            ["Gráfico de controle I-MR", "Ponto fora dos limites da Equação 23",
             "Acompanhamento diário", "Montgomery (2013)"],
            ["CUSUM dos resíduos", "Mudança persistente de inclinação (Equação 24)",
             "Desvios pequenos e sustentados", "Page (1954)"],
            ["Consumo fora de período produtivo", "Consumo com atividade nula",
             "Espera, aquecedores ligados, possíveis vazamentos", "Seções 2.5 a 2.7"],
        ],
        [3.6, 4.6, 4.4, 3.4],
        FONTE_AUTOR,
        nota="consumo inesperado com atividade nula pode indicar vazamento; nesse caso, a "
             "verificação é atribuição de profissional habilitado, conforme os procedimentos de "
             "segurança da empresa.",
    )
    c.h3("2.9.6", "Projeção de consumo e de custos")
    c.p(
        "A projeção de consumo será feita com os modelos de regressão, a partir da atividade "
        "planejada (produção, refeições ou usuários previstos), e apresentada com intervalo de "
        "predição. A projeção de custos multiplica o consumo projetado pelo preço configurado. "
        "Projeções baseadas em dados simulados serão rotuladas como tal."
    )

    # ---------------------------------------------------------------------
    c.h2("2.10", "MONITORAMENTO DO RESERVATÓRIO")
    c.p(
        "Três grandezas não devem ser confundidas. A capacidade volumétrica é o volume total de "
        "água que o recipiente comporta; a capacidade nominal é a massa de GLP indicada para o "
        "recipiente; e o limite de enchimento preserva um espaço para a expansão do líquido. "
        "Para recipientes transportáveis abastecidos no local, nota técnica do Corpo de "
        "Bombeiros do Rio de Janeiro limita o enchimento a 85 % da capacidade volumétrica e "
        "classifica como estacionário o recipiente com capacidade volumétrica superior a 0,5 m³ "
        "(CBMERJ, 2022). Para recipientes estacionários, o limite de enchimento e a capacidade "
        "nominal serão informados conforme os dados do fabricante, da distribuidora e da norma "
        "aplicável, e nunca presumidos. As centrais de GLP são objeto da ABNT NBR 13523 e das "
        "instruções técnicas dos corpos de bombeiros estaduais."
    )
    c.p(
        "Enquanto não houver sensor de nível integrado, o monitoramento será virtual, por "
        "balanço de massa (Equação 25), e a autonomia será estimada pela Equação 26:"
    )
    c.eq("S_{t} = S_{t−1} + A_{t} − G_{t}")
    c.eq("Aut = (S_{t} − S_{res}) / Ḡ_{dia}")
    c.definicoes([
        ("S_{t}", "estoque estimado de GLP no tanque, em kg"),
        ("A_{t}", "massa abastecida no período, conforme nota fiscal, em kg"),
        ("G_{t}", "consumo medido no período, em kg"),
        ("S_{res}", "estoque mínimo de reserva configurado, em kg"),
        ("Ḡ_{dia}", "consumo médio diário recente, em kg/dia"),
        ("Aut", "autonomia estimada, em dias"),
    ])
    c.p(
        "O percentual de abastecimento será exibido em relação à capacidade nominal "
        "configurada. A cada abastecimento, a leitura do indicador de nível do tanque, "
        "informada pela distribuidora, será comparada ao estoque calculado; uma diferença "
        "crescente indica erro de medição ou perda e deve ser investigada. A massa específica "
        "de 0,552 t/m³ é um valor médio de conversão, e não a densidade do GLP armazenado, que "
        "varia com a temperatura e a composição. O painel deixará explícito que o "
        "monitoramento é virtual."
    )

    # ---------------------------------------------------------------------
    c.h2("2.11", "ARQUITETURA DE SISTEMAS DE MONITORAMENTO ENERGÉTICO")
    c.p(
        "Um sistema de monitoramento energético organiza-se em camadas: medição, aquisição, "
        "armazenamento, processamento, apresentação e decisão. Neste projeto, as duas primeiras "
        "camadas serão inicialmente substituídas pela importação de planilhas CSV e Excel; a "
        "integração com sensores fica prevista como evolução, sempre em modo somente leitura."
    )
    c.alineas([
        "medição: medidor geral (o mesmo das notas fiscais), submedidores por setor e, quando "
        "viável, por equipamento; a diferença entre o medidor geral e a soma dos submedidores "
        "indica consumo não medido",
        "aquisição: leitura manual em planilha, e futuramente telemetria de medidores e do "
        "nível do tanque",
        "armazenamento: banco de dados histórico em SQLite",
        "processamento: validação, cálculo de indicadores, estatística e detecção de anomalias",
        "apresentação: painel interativo e relatórios",
        "decisão: plano de ação, com medidas avaliadas por profissionais e verificadas pelos "
        "métodos da seção 2.9.3",
    ])

    c.h2("2.12", "LACUNAS E PONTOS A VERIFICAR")
    c.p(
        "O Quadro 10 reúne as informações que não puderam ser confirmadas nesta fase e que "
        "deverão ser verificadas antes da versão final do trabalho."
    )
    c.quadro(
        "Pontos a verificar e lacunas da pesquisa",
        ["Item", "Situação", "Ação recomendada"],
        [
            ["Resolução ANP nº 825/2020",
             "Fontes indicam 25/08/2020 ou 28/08/2020 como data de assinatura; partes podem ter sido alteradas pela Resolução ANP nº 980/2025",
             "Conferir texto consolidado no portal da ANP"],
            ["Fatores de conversão (ANP, 2026)",
             "Valores confirmados em várias edições indexadas; PDF original não aberto",
             "Conferir o PDF do Anuário 2026"],
            ["ABNT NBR 13523, NBR 15358 e NBR 15526",
             "Edições citadas variam entre as fontes consultadas",
             "Consultar o catálogo da ABNT"],
            ["ABNT NBR ISO 50006:2024", "Texto integral não consultado",
             "Consultar a norma para os detalhes de LBE e IDE"],
            ["Consumo de GLP por refeição", "Nenhum valor público confiável encontrado",
             "Usar linha de base interna"],
            ["Eficiência de fornos cadinho a GLP",
             "Valores encontrados vêm de fabricantes ou de fontes antigas",
             "Não adotados; usar medições da empresa"],
            ["Limite de enchimento de tanques estacionários", "Não confirmado nas fontes",
             "Obter com fabricante, distribuidora e norma"],
            ["Aplicabilidade das NR-13 e NR-20", "Não analisada",
             "Verificar com o engenheiro responsável e o SESMT"],
            ["Base do rendimento dos aquecedores (PCI ou PCS)", "Varia por fabricante",
             "Conferir manuais e etiquetas"],
            ["Dados do evento de Vergnhanini Filho e Spegiorin (2013)",
             "Fontes divergem quanto ao local e à numeração do evento",
             "Conferir nos anais da ABM"],
        ],
        [4.6, 6.4, 5.0],
        FONTE_AUTOR,
    )

    # =====================================================================
    c.h1("3", "FASE 2 — DIAGNÓSTICO DO REPOSITÓRIO EXISTENTE")
    c.h2("3.1", "INVENTÁRIO")
    c.p(
        "O repositório analisado contém um arquivo README.md e 24 scripts Python independentes, "
        "nomeados de \"Ex1 (Terça).py\" a \"Ex24 (Terça).py\", com 1.043 linhas no total. Os "
        "scripts são exercícios da disciplina de Programação em Python, com aplicações em "
        "sistemas elétricos. As únicas bibliotecas usadas são math e json, da biblioteca "
        "padrão, e NumPy (exercícios 22 a 24). Não há arquivo de dependências, testes "
        "automatizados, pacotes nem dados de entrada externos. O Quadro 11 resume o inventário."
    )
    c.quadro(
        "Inventário dos exercícios existentes",
        ["Exercícios", "Temas", "Relação com o projeto GLP"],
        [
            ["1 a 4, 21 a 24", "Resistência com temperatura, fasores, rendimento de transformador, "
             "fator de potência, queda de tensão, operações com NumPy, perdas ôhmicas, matriz Ybus",
             "Nenhuma relação direta"],
            ["5, 11", "Validação de telemetria; varredura de leituras com descarte de ruído e alarme",
             "Conceitos de validação de leituras e alarmes"],
            ["9, 10, 13", "Valor eficaz de amostras; fatiamento temporal, demanda máxima, média e fator de carga",
             "Conceitos de estatística e de perfis horários"],
            ["12", "Transiente térmico de resfriamento de motor", "Analogia com perdas térmicas"],
            ["6 a 8, 14 a 20", "Proteção, controle de temperatura, níveis de tensão, buffer, "
             "imutabilidade de ajustes, modelagem de ativos, desbalanceamento, JSON, deslastre de cargas",
             "Conceitos de cadastro de ativos e serialização"],
        ],
        [2.8, 8.6, 4.6],
        "elaborado pelo autor (2026), a partir dos arquivos do repositório.",
    )
    c.h2("3.2", "PONTOS QUE PODEM SER APROVEITADOS")
    c.p(
        "Nenhum script é diretamente reutilizável como módulo do sistema, mas há padrões e "
        "conceitos a aproveitar:"
    )
    c.alineas([
        "o cabeçalho padronizado de identificação acadêmica, que será mantido nos novos módulos",
        "a organização do código em etapas numeradas e comentadas, adequada à apresentação "
        "acadêmica",
        "a lógica de validação de leituras e de alarmes dos exercícios 5 e 11, que será "
        "generalizada no módulo de validação",
        "o cálculo de perfil horário, valores máximo e médio e fator de carga dos exercícios 10 "
        "e 13, análogo aos indicadores de consumo por horário",
        "o modelo de resfriamento do exercício 12, conceitualmente próximo das perdas térmicas "
        "de reservatórios e fornos",
    ])
    c.h2("3.3", "LIMITAÇÕES E INCONSISTÊNCIAS ENCONTRADAS")
    c.p(
        "Todos os scripts não interativos foram executados sem erro. Os exercícios 3, 5, 6, 7 e "
        "8 exigem entrada pelo teclado e não foram executados automaticamente. Foram "
        "identificados os seguintes pontos:"
    )
    c.alineas([
        "o exercício 10 tem como tema declarado a integração de consumo horário com tarifação "
        "horossazonal, mas o código não aplica tarifas: ele repete o cálculo do exercício 13 "
        "(demanda máxima, mínima, média e fator de carga)",
        "no exercício 11, se a primeira leitura válida já for uma falta (corrente acima de "
        "200 A), o contador de leituras fica igual a zero e a média provoca divisão por zero; "
        "com os dados atuais isso não ocorre",
        "os nomes dos arquivos contêm espaços, parênteses e acentos, o que impede importá-los "
        "como módulos Python; o arquivo do exercício 13 tem dois espaços no nome",
        "os parâmetros estão fixos no código, sem leitura de arquivos, validação de entrada ou "
        "testes automatizados",
        "não há arquivo requirements.txt, arquivo .gitignore nem documentação de execução",
    ])
    c.h2("3.4", "DECISÃO")
    c.p(
        "Os exercícios são registros de atividades avaliadas e foram preservados sem alteração; "
        "os pontos da seção 3.3 ficam apenas registrados. O sistema de GLP foi desenvolvido em "
        "uma pasta própria, projeto_glp, isolada dos exercícios. Nenhuma funcionalidade "
        "existente foi removida ou substituída. A inclusão de uma seção no README principal "
        "com o link para o projeto depende de aprovação do autor."
    )

    # Capítulos 4 a 9 (Fases 3 a 7): ver capitulos_fases_3_a_7.py
    capitulos_fases_3_a_7.adicionar(c, FONTE_AUTOR)

    # =====================================================================
    c.referencias([
        "AGÊNCIA NACIONAL DO PETRÓLEO, GÁS NATURAL E BIOCOMBUSTÍVEIS (Brasil). **Anuário "
        "estatístico brasileiro do petróleo, gás natural e biocombustíveis 2025**: tabela 3.22: "
        "preço médio do GLP ao consumidor, segundo grandes regiões e unidades da Federação – "
        "2015-2024. Rio de Janeiro: ANP, 2025. Disponível em: https://www.gov.br/anp/pt-br/"
        "centrais-de-conteudo/dados-abertos/arquivos/anuario-estatistico-2025/secao-3/"
        f"anuario-abertos-metadados-tabela3-22.docx. Acesso em: {DATA_ACESSO}.",
        "AGÊNCIA NACIONAL DO PETRÓLEO, GÁS NATURAL E BIOCOMBUSTÍVEIS (Brasil). **Anuário "
        "estatístico brasileiro do petróleo, gás natural e biocombustíveis 2026**: fatores de "
        "conversão. Rio de Janeiro: ANP, 2026. Disponível em: https://www.gov.br/anp/pt-br/"
        "centrais-de-conteudo/publicacoes/anuario-estatistico/arquivos-anuario-estatistico-2026/"
        f"outras-pecas-documentais/fatores-de-conversao-2026.pdf. Acesso em: {DATA_ACESSO}.",
        "ALMEIDA, T. H. T. de. **Análise e melhoria do consumo de gás natural numa fábrica de "
        "fusão de alumínio**. Orientadora: Mônica Santos de Araújo Abreu. 2019. Trabalho de "
        "Conclusão de Curso (Graduação em Engenharia Mecânica) – Universidade Federal de "
        "Pernambuco, Recife, 2019. Disponível em: https://repositorio.ufpe.br/bitstream/123456789/"
        "47844/1/THALES%20HENRIQUE%20TORRES%20DE%20ALMEIDA-AN%c3%81LISE%20E%20MELHORIA%20DO%20"
        "CONSUMO%20DE%20G%c3%81S%20NATURAL%20NUMA%20F%c3%81BRICA%20DE%20FUS%c3%83O%20DE%20"
        f"ALUM%c3%8dNIO.pdf. Acesso em: {DATA_ACESSO}.",
        "ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR 6024**: informação e documentação: "
        "numeração progressiva das seções de um documento: apresentação. Rio de Janeiro: ABNT, 2012a.",
        "ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR 6027**: informação e documentação: "
        "sumário: apresentação. Rio de Janeiro: ABNT, 2012b.",
        "ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR 10719**: informação e documentação: "
        "relatório técnico e/ou científico: apresentação. Rio de Janeiro: ABNT, 2015.",
        "ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR 6023**: informação e documentação: "
        "referências: elaboração. Rio de Janeiro: ABNT, 2018a.",
        "ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR ISO 50001**: sistemas de gestão da "
        "energia: requisitos com orientações para uso. Rio de Janeiro: ABNT, 2018b.",
        "ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR 5626**: sistemas prediais de água fria "
        "e água quente: projeto, execução, operação e manutenção. Rio de Janeiro: ABNT, 2020.",
        "ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR 6028**: informação e documentação: "
        "resumo, resenha e recensão: apresentação. Rio de Janeiro: ABNT, 2021.",
        "ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR 10520**: informação e documentação: "
        "citações em documentos: apresentação. Rio de Janeiro: ABNT, 2023.",
        "ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR 14724**: informação e documentação: "
        "trabalhos acadêmicos: apresentação. Rio de Janeiro: ABNT, 2024a.",
        "ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR ISO 50006**: sistemas de gestão de "
        "energia: avaliação do desempenho energético utilizando indicadores de desempenho "
        "energético e linhas de base energética. Rio de Janeiro: ABNT, 2024b.",
        "BCS, INCORPORATED. **Advanced melting technologies**: energy saving concepts and "
        "opportunities for the metal casting industry. Washington, DC: U.S. Department of "
        "Energy, 2005. Disponível em: https://www1.eere.energy.gov/manufacturing/resources/"
        f"metalcasting/pdfs/advancedmeltingtechnologies.pdf. Acesso em: {DATA_ACESSO}.",
        "BERGMAN, T. L. *et al*. **Fundamentos de transferência de calor e de massa**. 7. ed. "
        "Rio de Janeiro: LTC, 2014.",
        "BRASIL. Agência Nacional do Petróleo, Gás Natural e Biocombustíveis. Resolução ANP nº "
        "825, de 28 de agosto de 2020. Dispõe sobre a especificação e o controle da qualidade "
        "dos gases liquefeitos de petróleo (GLP) comercializados pelos agentes econômicos no "
        "território nacional. **Diário Oficial da União**, Brasília, DF, 31 ago. 2020.",
        "CORPO DE BOMBEIROS MILITAR DO ESTADO DO RIO DE JANEIRO. **Nota Técnica NT 4-05**: "
        "gás (GLP/GN): manipulação, armazenamento e comercialização. Rio de Janeiro: CBMERJ, "
        "2022. Disponível em: https://www.cbmerj.rj.gov.br/wp-content/uploads/2024/05/"
        f"NT-4-05-Gas-GLPGN-Manipulacao-armazenamento-e-comercializacao-2022.pdf. Acesso em: {DATA_ACESSO}.",
        "COHEN, J. **Statistical power analysis for the behavioral sciences**. 2nd ed. "
        "Hillsdale: Lawrence Erlbaum Associates, 1988.",
        "ÇENGEL, Y. A.; BOLES, M. A. **Termodinâmica**. 7. ed. Porto Alegre: AMGH, 2013.",
        "DURBIN, J.; WATSON, G. S. Testing for serial correlation in least squares regression: "
        "I. **Biometrika**, Oxford, v. 37, n. 3/4, p. 409-428, 1950.",
        "EFFICIENCY VALUATION ORGANIZATION. **Protocolo internacional de medição e verificação "
        "de performance**: conceitos e opções para a determinação de economias de energia e de "
        "água: volume 1. EVO 10000-1:2012 (Br). [*S. l.*]: EVO, 2012.",
        "HARRIS, C. R. *et al*. Array programming with NumPy. **Nature**, London, v. 585, "
        "p. 357-362, 2020. DOI: 10.1038/s41586-020-2649-2.",
        "IGLEWICZ, B.; HOAGLIN, D. C. **How to detect and handle outliers**. Milwaukee: ASQC "
        "Quality Press, 1993.",
        "INSTITUTO NACIONAL DE METROLOGIA, QUALIDADE E TECNOLOGIA (Brasil). **Programa "
        "Brasileiro de Etiquetagem**: tabela de eficiência energética: aquecedor de água a gás: "
        "acumulação. Rio de Janeiro: Inmetro, 2023. Disponível em: https://www.gov.br/inmetro/"
        "pt-br/assuntos/avaliacao-da-conformidade/programa-brasileiro-de-etiquetagem/"
        "tabelas-de-eficiencia-energetica/aquecedores-de-agua-a-gas/"
        f"aquecedor-de-agua-a-gas-acumulacao.pdf. Acesso em: {DATA_ACESSO}.",
        "INTERNATIONAL ORGANIZATION FOR STANDARDIZATION. **ISO 50015**: energy management "
        "systems: measurement and verification of energy performance of organizations: "
        "general principles and guidance. Geneva: ISO, 2014.",
        "LI, T. *et al*. Performance of secondary aluminum melting: thermodynamic analysis and "
        "plant-site experiments. **Energy**, Oxford, v. 31, n. 12, p. 1769-1779, 2006. DOI: "
        "10.1016/j.energy.2005.08.005.",
        "MANN, H. B.; WHITNEY, D. R. On a test of whether one of two random variables is "
        "stochastically larger than the other. **The Annals of Mathematical Statistics**, "
        "v. 18, n. 1, p. 50-60, 1947.",
        "MCKINNEY, W. Data structures for statistical computing in Python. *In*: PYTHON IN "
        "SCIENCE CONFERENCE, 9., 2010, Austin. **Proceedings** [...]. Austin: SciPy, 2010. "
        "p. 56-61.",
        "MONTGOMERY, D. C. **Introduction to statistical quality control**. 7th ed. Hoboken: "
        "Wiley, 2013.",
        "MONTGOMERY, D. C.; RUNGER, G. C. **Applied statistics and probability for engineers**. "
        "7th ed. Hoboken: Wiley, 2018.",
        "PAGE, E. S. Continuous inspection schemes. **Biometrika**, Oxford, v. 41, n. 1/2, "
        "p. 100-115, 1954.",
        "PLOTLY TECHNOLOGIES. **Collaborative data science**. Montréal: Plotly Technologies, "
        f"2015. Disponível em: https://plot.ly. Acesso em: {DATA_ACESSO}.",
        "SHAPIRO, S. S.; WILK, M. B. An analysis of variance test for normality (complete "
        "samples). **Biometrika**, Oxford, v. 52, n. 3/4, p. 591-611, 1965.",
        "STREAMLIT. **Streamlit documentation**. [*S. l.*], 2026. Disponível em: "
        f"https://docs.streamlit.io. Acesso em: {DATA_ACESSO}.",
        "STUDENT. The probable error of a mean. **Biometrika**, Oxford, v. 6, n. 1, p. 1-25, 1908.",
        "TUKEY, J. W. **Exploratory data analysis**. Reading: Addison-Wesley, 1977.",
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
    documento = DocumentoABNT(META, montar_conteudo())
    try:
        paginas = paginar_com_libreoffice(documento, ARQUIVO_DOCX, ARQUIVO_PDF)
        print(f"Sumário paginado ({len(paginas)} entradas).")
    except (RuntimeError, FileNotFoundError, OSError) as erro:
        documento.salvar(ARQUIVO_DOCX)
        print(f"Aviso: paginação automática indisponível ({erro}). "
              "Atualize os números do sumário manualmente.")
    print(f"Gerado: {ARQUIVO_DOCX}")
    if ARQUIVO_PDF.exists():
        print(f"Gerado: {ARQUIVO_PDF}")


if __name__ == "__main__":
    main()
