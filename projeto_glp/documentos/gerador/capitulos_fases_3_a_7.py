"""
Capítulos das Fases 3 a 7 do relatório ABNT.

Os números de demonstração (intervenções, anomalias, modelos e testes) são
calculados no momento da geração, a partir dos dados SIMULADOS e do código do
sistema, para que o texto nunca divirja do que o sistema realmente produz.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parents[2]
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

import pandas as pd  # noqa: E402

from src import alertas, dados_simulados, estatistica, fundicao, indicadores, relatorios, restaurante  # noqa: E402
from src.constantes import carregar_parametros  # noqa: E402

PASTA_FIGURAS = RAIZ_PROJETO / "documentos" / "figuras"


def fmt(valor: float, casas: int = 2) -> str:
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_p(p: float) -> str:
    return "< 0,001" if p < 0.001 else fmt(p, 3)


def _contar_testes() -> tuple[int, int]:
    """Executa a suíte de testes e devolve (aprovados, reprovados)."""
    try:
        saida = subprocess.run([sys.executable, "-m", "pytest", "-o", "addopts=", "-q",
                                "-p", "no:cacheprovider"], cwd=RAIZ_PROJETO,
                               capture_output=True, text=True, timeout=900).stdout
    except (OSError, subprocess.TimeoutExpired):
        return (0, 0)
    aprovados = re.search(r"(\d+) passed", saida)
    reprovados = re.search(r"(\d+) failed", saida)
    return (int(aprovados.group(1)) if aprovados else 0, int(reprovados.group(1)) if reprovados else 0)


def calcular_demonstracao() -> dict:
    """Resultados do sistema aplicado aos dados SIMULADOS."""
    hip = dados_simulados.carregar_hipoteses()
    parametros = carregar_parametros()
    tab = dados_simulados.gerar(hip, parametros)
    reg, equip = tab["registros"], tab["equipamentos"]
    preco = parametros["geral"]["preco_glp_r_por_kg"]

    interv = relatorios.tabela_intervencoes(reg, tab["intervencoes"]).set_index("id")
    lista = alertas.gerar_alertas(reg, parametros, preco=preco)
    eventos = []
    nomes = {"FUNDICAO": "Fundição", "RESTAURANTE": "Restaurante", "CHUVEIROS": "Chuveiros"}
    lista = lista.assign(dia=lista["data"].dt.strftime("%Y-%m-%d"))
    corresponde = pd.Series(False, index=lista.index)
    for a in hip["anomalias"]:
        dias = {d.strftime("%Y-%m-%d") for d in pd.date_range(a["inicio"], a["fim"])}
        mascara = (lista["setor"] == nomes[a["setor"]]) & lista["dia"].isin(dias)
        corresponde |= mascara
        eventos.append({"evento": f"{nomes[a['setor']]}: {a['descricao']}",
                        "periodo": f"{a['inicio']} a {a['fim']}" if a["inicio"] != a["fim"] else a["inicio"],
                        "dias": len(dias), "detectados": lista.loc[mascara, "dia"].nunique(),
                        "metodos": ", ".join(sorted(set(lista.loc[mascara, "metodo"])))})
    extras = lista[~corresponde]

    d = fundicao.diario_fornos(reg)
    f1 = d[(d["equipamento_id"] == "FORNO-01") & (d["metal_t"] > 0)]
    modelo_f1 = fundicao.modelo_consumo(f1)
    vif_f1 = estatistica.fator_inflacao_variancia(f1, ["horas", "metal_t"]).max()
    dr = restaurante.diario(reg, preco)
    modelo_r = restaurante.modelo_consumo(dr)
    eta = fundicao.eficiencia_estimada(f1, parametros["fundicao"]["liga"])
    resumo = indicadores.resumo_geral(reg, preco)
    esp = indicadores.especifico_por_setor(reg, preco, equip)
    aprovados, reprovados = _contar_testes()
    return {"hip": hip, "parametros": parametros, "interv": interv, "eventos": eventos,
            "alertas_extras": extras, "n_alertas": len(lista), "modelo_f1": modelo_f1,
            "vif_f1": vif_f1, "modelo_r": modelo_r, "eta": eta, "resumo": resumo, "esp": esp,
            "n_registros": len(reg), "testes": (aprovados, reprovados)}


def adicionar(c, fonte_autor: str) -> None:
    demo = calcular_demonstracao()
    hip, par = demo["hip"], demo["parametros"]

    def prox_quadro() -> int:
        return c._n_quadro + 1

    def prox_tabela() -> int:
        return c._n_tabela + 1

    def prox_figura() -> int:
        return c._n_figura + 1

    # =====================================================================
    c.h1("4", "FASE 3 — MODELAGEM E ARQUITETURA")
    c.p(
        "A arquitetura proposta ao fim da Fase 2 foi aprovada e detalhada nesta fase. Este "
        "capítulo descreve os princípios, a estrutura de diretórios, o modelo de dados, as "
        "regras de validação, o fluxo de dados, as bibliotecas, as páginas do painel e os "
        "parâmetros configuráveis do sistema."
    )
    c.h2("4.1", "PRINCÍPIOS")
    c.alineas([
        "modularidade: cada setor e cada método estatístico em um módulo próprio, reutilizável e "
        "testável",
        "rastreabilidade: toda leitura e todo parâmetro com classe de origem (Quadro 3) e fonte",
        "separação entre dados reais e simulados: pastas, rótulos e consultas distintos, e "
        "bloqueio de análises que misturem as duas origens sem autorização explícita",
        "somente leitura: nenhum comando para equipamentos ou dispositivos de segurança",
        "reprodutibilidade: dados simulados gerados com semente fixa e hipóteses registradas",
        "transparência: fórmulas documentadas no código e neste relatório",
    ])
    c.h2("4.2", "ESTRUTURA DE DIRETÓRIOS")
    c.p(
        f"A Figura {prox_figura()} apresenta a estrutura implementada, adaptada da sugerida no "
        "escopo. As principais adaptações foram a pasta de configuração, com os parâmetros e as "
        "hipóteses da simulação; os módulos de importação, validação, anomalias, alertas, "
        "reservatório e relatórios; a pasta de testes; e a organização do painel em páginas, "
        "registradas no arquivo de entrada pela função de navegação do Streamlit."
    )
    c.figura_texto(
        "Estrutura de diretórios do projeto",
        [
            "projeto_glp/",
            "├── config/",
            "│   ├── parametros.toml          preço, tanque, chuveiros, liga (com origem)",
            "│   └── hipoteses_simulacao.toml hipóteses dos dados SIMULADOS",
            "├── dados/",
            "│   ├── dados_reais/             planilhas da empresa (não versionadas)",
            "│   ├── dados_simulados/         CSV SIMULADOS + HIPOTESES.md",
            "│   └── referencias/             parâmetros de referência com fonte",
            "├── documentos/                  relatórios ABNT, figuras e gerador",
            "├── src/",
            "│   ├── constantes.py            PCI, conversões, origens, esquema",
            "│   ├── importacao.py            leitura de CSV e Excel",
            "│   ├── validacao.py             regras de qualidade dos dados",
            "│   ├── banco_dados.py           histórico em SQLite",
            "│   ├── indicadores.py           consumo, custo, participação, específico",
            "│   ├── estatistica.py           descritiva, testes, IC, regressão, VIF",
            "│   ├── anomalias.py             Tukey, escore z robusto, I-MR, CUSUM",
            "│   ├── alertas.py               consolidação dos alertas",
            "│   ├── fundicao.py              fornos, balanço térmico, modelo",
            "│   ├── restaurante.py           refeições, modelo, perfis",
            "│   ├── chuveiros.py             demanda térmica, perdas, perfis",
            "│   ├── reservatorio.py          balanço de massa, autonomia",
            "│   ├── simulacao.py             cenários de economia",
            "│   ├── relatorios.py            intervenções e exportação",
            "│   ├── dados_simulados.py       gerador de dados sintéticos",
            "│   └── painel.py                utilitários do painel",
            "├── paginas/                     10 páginas do painel",
            "├── tests/                       testes automatizados (pytest)",
            "├── dashboard.py                 entrada do painel",
            "├── main.py                      linha de comando",
            "└── requirements.txt",
        ],
        fonte_autor,
    )
    c.h2("4.3", "MODELO DE DADOS")
    q_campos = prox_quadro()
    c.p(
        f"O registro de consumo, unidade básica do sistema, tem os campos do Quadro {q_campos}. "
        "Pode haver um registro por dia ou por hora, por setor e por equipamento. Tabelas "
        "auxiliares guardam o cadastro de equipamentos (Quadro 4), os abastecimentos (data, "
        "massa, preço, nota fiscal e leitura do indicador de nível), as intervenções "
        "(descrição, setor ou equipamento, data de início) e o histórico de importações. No "
        "banco SQLite, uma restrição impede registros sem origem ou com origem diferente de "
        "MEDIDO e SIMULADO, e um índice único impede a repetição de data, hora, setor, "
        "equipamento e origem."
    )
    c.quadro(
        "Campos do registro de consumo",
        ["Campo", "Tipo", "Obrigatório", "Observação"],
        [
            ["data", "data (AAAA-MM-DD)", "Sim", "Não pode ser futura"],
            ["hora", "hora (HH:MM)", "Não", "Necessária para perfis horários"],
            ["setor", "texto", "Sim", "FUNDICAO, RESTAURANTE, CHUVEIROS ou GERAL"],
            ["equipamento_id", "texto", "Não", "Deve existir no cadastro"],
            ["consumo_valor", "número", "Sim", "Não negativo"],
            ["consumo_unidade", "texto", "Sim", "kg ou t; m³ só com fator de conversão explícito"],
            ["atividade_valor", "número", "Não", "Produção, refeições, usuários, banhos ou ciclos"],
            ["atividade_unidade", "texto", "Se houver atividade", "Compatível com o setor"],
            ["tempo_funcionamento_h", "número", "Não", "Até 24 por dia ou 1 por hora"],
            ["tempo_sem_carga_h", "número", "Não", "Não maior que o tempo de funcionamento"],
            ["ciclos", "número", "Não", "Ciclos de fusão ou cargas"],
            ["temperatura_c", "número", "Não", "Temperatura de processo ou da água de entrada"],
            ["origem", "texto", "Sim", "MEDIDO ou SIMULADO"],
            ["observacoes", "texto", "Não", "Livre"],
        ],
        [4.0, 3.4, 2.8, 5.8],
        fonte_autor,
    )
    c.h2("4.4", "REGRAS DE VALIDAÇÃO")
    q_val = prox_quadro()
    c.p(
        f"As regras do Quadro {q_val} são aplicadas a toda planilha importada. Erros rejeitam o "
        "registro; avisos o mantêm, mas ficam no relatório de importação para revisão."
    )
    c.quadro(
        "Regras de validação na importação",
        ["Verificação", "Regra", "Tratamento"],
        [
            ["Campos vazios", "Colunas e campos obrigatórios preenchidos", "Erro"],
            ["Valores negativos", "Consumo, atividade, horas e ciclos ≥ 0", "Erro"],
            ["Registros duplicados", "Mesma data, hora, setor e equipamento", "Aviso; mantém o primeiro"],
            ["Datas inválidas", "Data e hora válidas; data não futura", "Erro"],
            ["Unidades incompatíveis", "Unidade aceita para o setor; m³ sem fator", "Erro"],
            ["Leituras inconsistentes", "Horas acima do período; tempo sem carga maior que o funcionamento", "Erro"],
            ["Leituras inconsistentes", "Consumo acima de potência nominal × horas × 1,1; equipamento não cadastrado", "Aviso"],
            ["Dados ausentes", "Lacunas na série diária", "Aviso; nada é interpolado"],
            ["Mistura de origens", "MEDIDO e SIMULADO no mesmo arquivo", "Bloqueio, salvo autorização explícita"],
        ],
        [3.8, 7.4, 4.8],
        fonte_autor,
        nota="o sistema não corrige dados silenciosamente.",
    )
    c.h2("4.5", "FLUXO DE DADOS")
    c.figura_fluxo(
        "Fluxo de dados do sistema",
        [
            ("Importação", "CSV e Excel"),
            ("Validação", f"Quadro {q_val}"),
            ("Banco", "SQLite"),
            ("Indicadores", "Quadros 5 a 7"),
            ("Estatística", "testes e anomalias"),
            ("Painel", "Streamlit e relatórios"),
        ],
        fonte_autor,
    )
    c.h2("4.6", "BIBLIOTECAS")
    c.quadro(
        "Bibliotecas utilizadas e justificativas",
        ["Biblioteca", "Uso", "Justificativa"],
        [
            ["pandas", "Tabelas, séries temporais e importação", "Padrão para dados tabulares (McKinney, 2010)"],
            ["NumPy", "Cálculo numérico e regressão por mínimos quadrados", "Base do ecossistema científico (Harris et al., 2020)"],
            ["SciPy", "Testes estatísticos e distribuições", "Shapiro-Wilk, t, Wilcoxon e Mann-Whitney (Virtanen et al., 2020)"],
            ["Plotly", "Gráficos interativos", "Interatividade no painel (Plotly Technologies, 2015)"],
            ["Streamlit", "Painel web", "Painel em Python, sem desenvolvimento web separado (Streamlit, 2026)"],
            ["openpyxl", "Leitura e escrita de .xlsx", "Exigida para importar e exportar Excel"],
            ["sqlite3", "Banco de dados histórico", "Biblioteca padrão do Python, sem servidor"],
            ["pytest", "Testes automatizados", "Uso apenas em desenvolvimento"],
            ["python-docx", "Geração deste relatório", "Uso apenas na documentação"],
        ],
        [3.0, 5.6, 7.4],
        fonte_autor,
        nota="a regressão foi implementada com NumPy e SciPy; não foi necessária biblioteca adicional "
             "de modelos estatísticos. Matplotlib, previsto como opcional, não foi necessário.",
    )
    c.h2("4.7", "PÁGINAS DO PAINEL")
    c.quadro(
        "Páginas do painel interativo",
        ["Página", "Conteúdo principal"],
        [
            ["Visão geral", "Consumo, custo e energia totais, consumo mensal por setor, participação, evolução diária e alertas"],
            ["Fundição", "Indicadores por forno, kg/t ao longo do tempo, modelo da Equação 7, eficiência estimada"],
            ["Restaurante", "kg/refeição, modelo da Equação 8, faixas de refeições, dia da semana, perfil horário, consumo com a cozinha fechada"],
            ["Chuveiros", "kg/usuário, perfil horário, consumo sem uso, relação com a temperatura de entrada, calculadora de demanda"],
            ["Comparação entre setores", "Consumo, participação, custo, consumo específico, índice de evolução, comparação de períodos"],
            ["Reservatório", "Estoque virtual, nível, autonomia, abastecimentos, conciliação com o indicador do tanque"],
            ["Análise estatística", "Descritiva, normalidade, antes × depois, correlação, regressão, anomalias e CUSUM"],
            ["Simulação de economia", "Cenários de redução com consumo, preço, dias, atividade e investimento editáveis"],
            ["Relatórios", "Avaliação das intervenções e exportação em Excel e Markdown"],
            ["Base de dados", "Importação, relatório de validação, consulta e hipóteses dos dados simulados"],
        ],
        [4.4, 11.6],
        fonte_autor,
        nota="todas as páginas exibem a origem dos dados (MEDIDO ou SIMULADO) de forma visível.",
    )
    c.h2("4.8", "PARÂMETROS CONFIGURÁVEIS")
    q_par = prox_quadro()
    c.p(
        "Os parâmetros que não vêm dos registros de consumo ficam no arquivo "
        "config/parametros.toml, cada um com sua classe de origem. O Quadro "
        f"{q_par} lista os valores atuais. Todos os marcados como HIPÓTESE devem ser "
        "substituídos por dados da empresa ou do fabricante antes de qualquer conclusão."
    )
    g, r, ch, liga = par["geral"], par["reservatorio"], par["chuveiros"], par["fundicao"]["liga"]
    c.quadro(
        "Parâmetros configuráveis e respectiva origem",
        ["Parâmetro", "Valor atual", "Origem", "Fonte para substituição"],
        [
            ["Preço do GLP", f"R$ {fmt(g['preco_glp_r_por_kg'])}/kg", "HIPÓTESE", "Nota fiscal de abastecimento"],
            ["Dias de operação", f"{g['dias_operacao_mes']}/mês; {g['dias_operacao_ano']}/ano", "HIPÓTESE", "Calendário de produção"],
            ["Capacidade nominal do tanque", f"{fmt(r['capacidade_nominal_kg'], 0)} kg", "HIPÓTESE", "Placa do recipiente"],
            ["Limite de enchimento", fmt(r["fracao_maxima_enchimento"], 2), "HIPÓTESE", "Fabricante, distribuidora e norma"],
            ["Reserva mínima e nível de alerta", f"{fmt(r['estoque_minimo_reserva_kg'], 0)} kg; {fmt(r['nivel_alerta_percentual'], 0)} %", "HIPÓTESE", "Política de suprimento"],
            ["Duração do banho e vazão", f"{fmt(ch['duracao_banho_min'], 0)} min; {fmt(ch['vazao_l_min'], 0)} L/min", "HIPÓTESE", "Medição em campo"],
            ["Temperatura de saída e rendimento", f"{fmt(ch['temperatura_saida_c'], 0)} °C; {fmt(ch['rendimento_aquecedor'], 2)}", "HIPÓTESE", "Ajuste do aquecedor; etiqueta PBE"],
            ["Propriedades da liga", f"cₛ {fmt(liga['calor_especifico_solido_kj_kgk'])}; cₗ {fmt(liga['calor_especifico_liquido_kj_kgk'])} kJ/(kg·K); L_f {fmt(liga['calor_latente_fusao_kj_kg'], 0)} kJ/kg; T_f {fmt(liga['temperatura_fusao_c'], 0)} °C", "HIPÓTESE", "Ficha técnica da liga"],
            ["Limite do escore z robusto", fmt(par["estatistica"]["limite_escore_z_robusto"], 1), "REFERÊNCIA", "Iglewicz e Hoaglin (1993)"],
            ["Nível de significância", fmt(par["estatistica"]["alfa"], 2), "REFERÊNCIA", "Escopo do projeto"],
        ],
        [4.2, 4.6, 2.4, 4.8],
        fonte_autor,
    )

    # =====================================================================
    c.h1("5", "FASE 4 — DESENVOLVIMENTO")
    c.h2("5.1", "MÓDULOS")
    q_mod = prox_quadro()
    c.p(
        f"O Quadro {q_mod} relaciona cada módulo às equações e seções do capítulo 2 que ele "
        "implementa. Cada função de cálculo tem a equação correspondente documentada no "
        "próprio código."
    )
    c.quadro(
        "Módulos do sistema e métodos implementados",
        ["Módulo", "Responsabilidade", "Equações e métodos"],
        [
            ["constantes", "PCI, conversões, classes de origem, esquema", "Equação 1; Tabela 1; Quadro 3"],
            ["importacao / validacao", "Leitura de CSV/Excel e regras de qualidade", f"Quadro {q_val}"],
            ["banco_dados", "Histórico SQLite, separação por origem", f"Quadro {q_campos}"],
            ["indicadores", "Consumo, custo, energia, participação, consumo específico", "Equações 1 a 3"],
            ["fundicao", "Indicadores por forno, balanço térmico, modelo", "Equações 5 a 7; Quadro 5"],
            ["restaurante", "Modelo por refeições, faixas, perfis", "Equações 8 e 9; Quadro 6"],
            ["chuveiros", "Demanda térmica, perdas, perfis", "Equações 10 a 13; Quadro 7"],
            ["estatistica", "Descritiva, Shapiro-Wilk, testes, IC, efeito, correlação, regressão, VIF", "Equações 15 a 21; Quadro 8"],
            ["anomalias / alertas", "Tukey, escore z robusto, I-MR, CUSUM, consumo sem atividade", "Equações 22 a 24; Quadro 9"],
            ["reservatorio", "Balanço de massa, autonomia, conciliação", "Equações 25 e 26"],
            ["simulacao", "Cenários de redução e retorno simples", "Equação 14"],
            ["relatorios", "Avaliação de intervenções e exportação", "Equação 4; seção 2.9.3"],
            ["dados_simulados", "Dados sintéticos com hipóteses e gabarito", "Seção 5.4"],
        ],
        [3.6, 6.6, 5.8],
        fonte_autor,
    )
    c.h2("5.2", "PAINEL INTERATIVO")
    f0 = prox_figura()
    c.p(
        f"As Figuras {f0} a {f0 + 4} mostram páginas do painel com os dados simulados. A faixa "
        "amarela no topo de cada página informa que os dados são SIMULADOS; com dados medidos, "
        "a faixa passa a indicar a origem MEDIDO. A barra lateral concentra a navegação e os "
        "filtros globais: origem dos dados, período e preço do GLP."
    )
    figuras = [
        ("painel_visao_geral.png", "Painel — visão geral", 15.0),
        ("painel_fundicao.png", "Painel — fundição", 15.0),
        ("painel_estatistica_antes_depois.png", "Painel — avaliação estatística de uma intervenção", 13.5),
        ("painel_reservatorio.png", "Painel — monitoramento virtual do reservatório", 15.0),
        ("painel_simulacao.png", "Painel — simulação de economia", 15.0),
    ]
    for arquivo, titulo, largura in figuras:
        caminho = PASTA_FIGURAS / arquivo
        if caminho.exists():
            c.figura_imagem(titulo, caminho, "elaborado pelo autor (2026), com dados SIMULADOS.", largura)
    c.h2("5.3", "DECISÕES DE IMPLEMENTAÇÃO")
    c.alineas([
        "o consumo específico da fundição como setor usa no denominador apenas as toneladas dos "
        "fornos de fusão, pois o mesmo metal passa depois pelo forno de espera e pelo de "
        "tratamento térmico; somar as toneladas de todos os fornos contaria o metal mais de "
        "uma vez",
        "as anomalias de consumo são procuradas nos resíduos dos modelos (Equações 7 e 8), e "
        "não no consumo bruto, para que dias de maior produção não sejam marcados como anômalos",
        "o estoque do tanque é calculado sobre todo o histórico, independentemente do período "
        "filtrado, porque depende de todos os abastecimentos e consumos anteriores",
        "a escolha do teste estatístico segue o Quadro 8 de forma automática, mas o usuário pode "
        "forçar o teste paramétrico ou o não paramétrico",
        "a página de simulação e todas as exportações rotulam os resultados como SIMULAÇÃO ou "
        "SIMULADO quando for o caso",
        "a gravação no banco pela interface aceita apenas registros MEDIDO; dados simulados só "
        "são criados pelo gerador do sistema",
    ])
    c.h2("5.4", "DADOS SIMULADOS")
    q_sim = prox_quadro()
    c.p(
        "Como não havia medições da empresa, foram gerados dados sintéticos para desenvolver e "
        f"testar o sistema: {fmt(demo['n_registros'], 0)} registros, de {hip['periodo']['inicio']} "
        f"em diante, por {hip['periodo']['dias']} dias, com semente fixa. O Quadro {q_sim} resume "
        "as hipóteses. Os dados incluem duas intervenções e três eventos anômalos inseridos de "
        "propósito, que servem de gabarito: como o efeito verdadeiro é conhecido, é possível "
        "verificar se os métodos o encontram. Esses dados não descrevem a empresa."
    )
    f1, f2, f3 = (hip["fornos"][k] for k in ("FORNO-01", "FORNO-02", "FORNO-03"))
    rr, cc = hip["restaurante"], hip["chuveiros"]
    linhas = [
        ["FORNO-01 (cadinho, fusão)", f"G = {fmt(f1['beta_h'], 1)}·horas + {fmt(f1['beta_t'], 0)}·t; {f1['ciclos_min']} a {f1['ciclos_max']} ciclos de {fmt(f1['carga_t_por_ciclo'], 2)} t; dias úteis"],
        ["FORNO-02 (espera)", f"G = {fmt(f2['beta_h'], 1)}·horas + {fmt(f2['beta_t'], 0)}·t; {fmt(f2['horas_dia'], 0)} h nos dias úteis; {fmt(f2['horas_domingo_sem_producao'], 0)} h aos domingos, sem carga"],
        ["FORNO-03 (tratamento térmico)", f"G = {fmt(f3['beta_h'], 1)}·horas + {fmt(f3['beta_t'], 0)}·t; terças e quintas"],
        ["Restaurante", f"G = {fmt(rr['beta_0'], 0)} + {fmt(rr['beta_1'], 3)}·refeições; {rr['refeicoes_media_util']} refeições nos dias úteis e {rr['refeicoes_media_sabado']} aos sábados"],
        ["Chuveiros", f"Perda em espera de {fmt(cc['perda_espera_kg_h'], 2)} kg/h + GLP por banho pelas Equações 10 a 12; {cc['usuarios_media_util']} usuários nos dias úteis; água de entrada entre {fmt(cc['temp_entrada_media_c'] - cc['temp_entrada_amplitude_c'], 0)} e {fmt(cc['temp_entrada_media_c'] + cc['temp_entrada_amplitude_c'], 0)} °C"],
    ]
    for i in hip["intervencoes"]:
        efeito = (f"redução de {fmt(i['reducao'] * 100, 0)} % no consumo" if "reducao" in i
                  else f"perda em espera passa a {fmt(i['nova_perda_espera_kg_h'], 2)} kg/h")
        linhas.append([f"{i['id']} — intervenção", f"{i['descricao']} ({i['equipamento_id']}, {i['data_inicio']}): {efeito}"])
    for a in hip["anomalias"]:
        linhas.append(["Anomalia inserida", f"{a['setor'].title()}, {a['inicio']} a {a['fim']}: {a['descricao']}"])
    c.quadro("Hipóteses dos dados simulados", ["Elemento", "Hipótese"], linhas, [4.4, 11.6],
             "elaborado pelo autor (2026); config/hipoteses_simulacao.toml.",
             nota="todos os valores são HIPÓTESES de simulação. Ruído aleatório normal de 4 % a 5 % foi aplicado ao consumo.")

    # =====================================================================
    c.h1("6", "FASE 5 — TESTES")
    c.h2("6.1", "TESTES AUTOMATIZADOS")
    aprovados, reprovados = demo["testes"]
    q_test = prox_quadro()
    situacao = (f"Na geração deste relatório, os {aprovados} testes foram executados e todos foram aprovados."
                if aprovados and not reprovados else
                f"Na geração deste relatório: {aprovados} aprovados e {reprovados} reprovados."
                if aprovados else "A suíte de testes não pôde ser executada na geração deste relatório.")
    c.p(
        f"A suíte de testes automatizados (pytest) cobre os grupos do Quadro {q_test}. Os testes "
        "de estatística comparam os resultados com os da biblioteca SciPy e com amostras de "
        "parâmetros conhecidos; os de cálculo conferem os exemplos numéricos deste relatório; "
        "os do painel executam cada página e verificam que a origem dos dados é exibida. "
        + situacao
    )
    c.quadro(
        "Grupos de testes automatizados",
        ["Grupo", "O que é verificado"],
        [
            ["Cálculos", "Conversão do PCI, herança da classe de origem, Tabela 2, balanço térmico, cenários de economia, retorno simples, balanço de massa e alertas do tanque"],
            ["Estatística", "Descritiva contra NumPy; Shapiro-Wilk; Welch e t pareado contra SciPy; escolha de teste não paramétrico; ausência de falso positivo sem redução e com aumento; regressão; VIF; tamanho de amostra; anomalias; I-MR; CUSUM"],
            ["Dados", "Cada regra de validação; importação de CSV brasileiro e Excel; banco de dados; reprodutibilidade e rótulo dos dados simulados; detecção das anomalias e intervenções do gabarito; consumo específico da fundição; exportações"],
            ["Painel", "Execução sem erros das 10 páginas e da entrada; filtros globais; reação da simulação aos parâmetros"],
        ],
        [3.0, 13.0],
        fonte_autor,
    )
    c.h2("6.2", "VERIFICAÇÃO COM O GABARITO DOS DADOS SIMULADOS")
    t_int = prox_tabela()
    c.p(
        f"A Tabela {t_int} mostra a avaliação automática das duas intervenções simuladas, com 90 "
        "dias antes e 90 dias depois de cada uma. A redução verdadeira inserida no FORNO-01 foi "
        "de 8 %; o sistema estimou a redução e o intervalo de confiança a partir dos dados, sem "
        "conhecer esse valor."
    )
    linhas = []
    for idx, t in demo["interv"].iterrows():
        linhas.append([idx, t["metrica"], fmt(t["media_antes"], 3), fmt(t["media_depois"], 3),
                       f"{fmt(t['reducao_pct'], 1)} %", f"{fmt(t['ic95_inf_pct'], 1)} a {fmt(t['ic95_sup_pct'], 1)} %",
                       t["teste"], fmt_p(t["p_valor"])])
    c.tabela(
        "Avaliação das intervenções simuladas",
        ["ID", "Métrica", "Média antes", "Média depois", "Redução", "IC 95 %", "Teste", "Valor p"],
        linhas, [1.6, 3.2, 1.7, 1.7, 1.8, 2.4, 2.0, 1.6],
        "elaborado pelo autor (2026), com dados SIMULADOS.",
        alinhamentos=["L", "L", "R", "R", "R", "C", "L", "R"],
    )
    i1 = demo["interv"].loc["INT-01"]
    c.p(
        f"Para o FORNO-01, o intervalo de confiança de {fmt(i1['ic95_inf_pct'], 1)} % a "
        f"{fmt(i1['ic95_sup_pct'], 1)} % contém a redução verdadeira de 8 %. Para o aquecedor, "
        "o teste de Shapiro-Wilk rejeitou a normalidade, e o sistema escolheu o teste de "
        "Mann-Whitney, como prevê o Quadro 8."
    )
    q_anom = prox_quadro()
    extras = demo["alertas_extras"]
    if len(extras):
        descricao = "; ".join(f"{linha['setor']}: {linha['mensagem']}" for _, linha in extras.iterrows())
        texto_extra = (f" Além desses, o sistema emitiu {len(extras)} alerta(s) que não correspondem "
                       f"a eventos inseridos — {descricao} Esse comportamento também foi simulado "
                       "(forno de espera mantido aquecido aos domingos) e, numa empresa real, "
                       "mereceria investigação.")
    else:
        texto_extra = " Nenhum alerta foi emitido fora dos eventos inseridos."
    c.p(f"O Quadro {q_anom} compara os eventos anômalos inseridos com os alertas gerados.{texto_extra}")
    c.quadro(
        "Eventos anômalos inseridos e alertas gerados",
        ["Evento inserido", "Período", "Dias detectados", "Método"],
        [[e["evento"], e["periodo"], f"{e['detectados']} de {e['dias']}", e["metodos"]] for e in demo["eventos"]],
        [6.6, 3.4, 2.4, 3.6],
        "elaborado pelo autor (2026), com dados SIMULADOS.",
    )
    c.h2("6.3", "DIAGNÓSTICO DOS MODELOS")
    m1, mr = demo["modelo_f1"], demo["modelo_r"]
    t_mod = prox_tabela()
    c.p(
        f"A Tabela {t_mod} compara os coeficientes estimados com os valores usados na "
        "simulação. No restaurante, o modelo recuperou a parcela fixa e o consumo por refeição. "
        "No FORNO-01, a previsão é boa, mas os coeficientes individuais de horas e toneladas "
        f"ficaram imprecisos: o fator de inflação da variância é {fmt(demo['vif_f1'], 1)}, pois "
        "as horas de forno ligado crescem com o número de ciclos e, portanto, com a massa "
        f"fundida. Além disso, a estatística de Durbin-Watson ({fmt(m1.durbin_watson, 2)}) indica "
        "resíduos autocorrelacionados, porque o modelo, ajustado ao ano inteiro, não inclui a "
        "mudança provocada pela intervenção."
    )
    coef1, coefr = m1.coeficientes, mr.coeficientes
    c.tabela(
        "Coeficientes estimados e valores usados na simulação",
        ["Modelo", "Coeficiente", "Estimado", "IC 95 %", "Simulado"],
        [
            ["Restaurante (Eq. 8)", "β₀ (kg/dia)", fmt(coefr.loc["intercepto", "coef"], 2),
             f"{fmt(coefr.loc['intercepto', 'ic95_inf'], 2)} a {fmt(coefr.loc['intercepto', 'ic95_sup'], 2)}", fmt(rr["beta_0"], 2)],
            ["Restaurante (Eq. 8)", "β₁ (kg/refeição)", fmt(coefr.loc["refeicoes", "coef"], 4),
             f"{fmt(coefr.loc['refeicoes', 'ic95_inf'], 4)} a {fmt(coefr.loc['refeicoes', 'ic95_sup'], 4)}", fmt(rr["beta_1"], 4)],
            ["FORNO-01 (Eq. 7)", "β₁ (kg/h)", fmt(coef1.loc["horas", "coef"], 2),
             f"{fmt(coef1.loc['horas', 'ic95_inf'], 2)} a {fmt(coef1.loc['horas', 'ic95_sup'], 2)}", fmt(f1["beta_h"], 2) + " (×0,92 após INT-01)"],
            ["FORNO-01 (Eq. 7)", "β₂ (kg/t)", fmt(coef1.loc["metal_t", "coef"], 2),
             f"{fmt(coef1.loc['metal_t', 'ic95_inf'], 2)} a {fmt(coef1.loc['metal_t', 'ic95_sup'], 2)}", fmt(f1["beta_t"], 2) + " (×0,92 após INT-01)"],
        ],
        [3.6, 3.2, 2.4, 3.8, 3.0],
        "elaborado pelo autor (2026), com dados SIMULADOS.",
        nota=f"R² ajustado: restaurante {fmt(mr.r2_ajustado, 3)}; FORNO-01 {fmt(m1.r2_ajustado, 3)}.",
        alinhamentos=["L", "L", "R", "C", "R"],
    )
    c.p(
        "A lição para a coleta de dados reais é registrar separadamente o tempo de forno ligado "
        "com e sem carga e, quando houver intervenção, ajustar a linha de base apenas com o "
        "período anterior a ela, como prevê o PIMVP (EVO, 2012). A eficiência térmica média "
        f"estimada para o FORNO-01 foi de {fmt(demo['eta'].mean() * 100, 1)} %, valor SIMULADO que "
        "depende de propriedades de liga marcadas como HIPÓTESE."
    )

    # =====================================================================
    c.h1("7", "FASE 6 — DOCUMENTAÇÃO E USO")
    c.p(
        "O arquivo README.md da pasta projeto_glp descreve instalação, execução e uso. Em "
        "resumo, com Python 3.11 ou mais recente:"
    )
    c.alineas([
        "instalar as dependências: `pip install -r requirements.txt`",
        "abrir o painel: `streamlit run dashboard.py`; na primeira execução, o banco é criado "
        "com os dados simulados",
        "validar uma planilha: `python main.py importar arquivo.xlsx`; gravar os registros "
        "aceitos: acrescentar `--gravar`",
        "gerar o relatório resumido em Markdown e Excel: `python main.py resumo --origem MEDIDO "
        "--saida resultados/resumo.md`",
        "regenerar os dados simulados após editar as hipóteses: `python main.py gerar-simulados`",
        "executar os testes: `python -m pytest`",
    ])
    c.p(
        "Para passar a usar dados reais, a sequência é: baixar a planilha-modelo na página Base "
        "de dados; preencher um registro por dia ou por hora, por equipamento, com origem "
        "MEDIDO; importar e corrigir os erros apontados; escolher a origem Medidos na barra "
        "lateral; e substituir em config/parametros.toml os valores marcados como HIPÓTESE."
    )

    # =====================================================================
    c.h1("8", "FASE 7 — VALIDAÇÃO")
    c.h2("8.1", "LIMITAÇÕES")
    c.alineas([
        "todos os resultados apresentados neste relatório vêm de dados SIMULADOS; eles validam os "
        "métodos e o software, não o consumo da empresa",
        "o sistema não mede: depende da qualidade e da resolução dos registros importados; sem "
        "medição por setor, só é possível analisar o consumo total",
        "a conversão de volume de vapor em massa depende de fator informado pelo fornecedor; o "
        "PCI e a massa específica usados são médias nacionais",
        "a comparação antes e depois por períodos é observacional; mudanças simultâneas de "
        "produção, cardápio, estação ou turno podem confundir o efeito da intervenção",
        "séries diárias costumam ser autocorrelacionadas; nesses casos, os valores p dos testes "
        "são otimistas e convém agregar por semana ou usar a linha de base ajustada",
        "o estoque do tanque é virtual: erros de leitura e perdas não medidas se acumulam até a "
        "conciliação com o indicador de nível",
        "a eficiência térmica estimada depende das propriedades da liga e da temperatura "
        "registrada; serve como ordem de grandeza",
        "os pontos de verificação do Quadro 10 (normas, resoluções e editais) continuam pendentes",
    ])
    c.h2("8.2", "REQUISITOS DE DADOS REAIS")
    q_req = prox_quadro()
    c.p(f"O Quadro {q_req} lista os dados necessários para implantar o sistema na empresa, em ordem de prioridade.")
    c.quadro(
        "Dados necessários para a implantação",
        ["Prioridade", "Dado", "Resolução mínima", "Fonte provável"],
        [
            ["1", "Abastecimentos: data, massa, preço, nota fiscal, nível antes", "Cada abastecimento", "Notas fiscais e distribuidora"],
            ["1", "Consumo total de GLP", "Diária", "Medidor geral ou balanço do tanque"],
            ["1", "Cadastro de equipamentos a gás", "Uma vez, com revisões", "Placas, manuais, manutenção"],
            ["2", "Consumo por setor", "Diária (horária no restaurante e nos chuveiros)", "Submedidores"],
            ["2", "Produção da fundição: t fundidas, ciclos, horas ligado e sem carga", "Diária, por forno", "Apontamento de produção"],
            ["2", "Refeições produzidas", "Diária", "Controle do restaurante"],
            ["2", "Usuários dos chuveiros", "Diária", "Controle de acesso ou contagem"],
            ["3", "Temperatura da água de entrada e de saída", "Diária", "Termômetro ou sensor"],
            ["3", "Consumo por forno", "Diária", "Medidores individuais"],
            ["3", "Registro de intervenções", "Cada intervenção", "Manutenção e engenharia"],
        ],
        [2.0, 6.4, 3.8, 3.8],
        fonte_autor,
    )
    c.h2("8.3", "RECOMENDAÇÕES PARA IMPLANTAÇÃO")
    c.alineas([
        "levantar os equipamentos a gás e preencher o cadastro com dados de placa",
        "começar com o consumo total e os abastecimentos, que normalmente já existem, para "
        "calibrar o monitoramento do reservatório",
        "avaliar, com profissional habilitado, a instalação de submedidores por setor, começando "
        "pela fundição, que concentra a maior parte do consumo nos dados simulados",
        "coletar ao menos alguns meses de dados antes de qualquer intervenção, para construir a "
        "linha de base de cada setor, e estimar o número de observações necessário pela página "
        "Análise estatística",
        "registrar cada intervenção com data e descrição, e não fazer duas intervenções "
        "simultâneas no mesmo equipamento, para que o efeito de cada uma possa ser separado",
        "revisar semanalmente os alertas e registrar a causa encontrada, para calibrar os limites",
        "integrar sensores e telemetria apenas em modo de leitura, sem comandos aos equipamentos",
    ])
    c.h2("8.4", "SEGURANÇA E RESPONSABILIDADE TÉCNICA")
    c.p(
        "O sistema é uma ferramenta de monitoramento e análise. Ele não altera reguladores, "
        "válvulas, pressostatos, queimadores ou dispositivos de segurança. Alertas de consumo "
        "com a cozinha fechada ou com forno sem carga são indícios para investigação: a "
        "verificação de possível vazamento e qualquer ajuste de combustão, manutenção ou "
        "alteração de instalação cabem a profissionais habilitados, conforme os manuais dos "
        "fabricantes, as normas aplicáveis e os procedimentos de segurança da empresa."
    )

    # =====================================================================
    c.h1("9", "CONSIDERAÇÕES FINAIS")
    res = demo["resumo"]
    c.p(
        "O projeto resultou em uma ferramenta que transforma registros de consumo de GLP em "
        "indicadores por setor, identifica consumo fora do padrão, simula cenários de economia "
        "e verifica estatisticamente se uma intervenção reduziu o consumo, sempre com a origem "
        "de cada dado à vista. Com os dados simulados, o sistema encontrou as duas intervenções "
        "e os três eventos anômalos inseridos, e estimou a redução verdadeira de 8 % do "
        "FORNO-01 dentro do intervalo de confiança calculado."
    )
    c.p(
        "Os mesmos testes também mostraram por que a coleta de dados importa: quando horas e "
        "toneladas variam juntas, o modelo não separa a perda em espera do consumo de fusão; "
        "quando a série tem uma mudança de regime, os resíduos ficam autocorrelacionados. Esses "
        "achados orientam os requisitos de dados reais do capítulo 8."
    )
    c.p(
        f"Nos dados simulados, a fundição concentrou {fmt(res['participacao_maior_pct'], 1)} % do "
        "consumo, mas isso, por si só, não indica ineficiência: a avaliação de cada setor deve "
        "ser feita pelo consumo específico comparado com o próprio histórico. A próxima etapa é "
        "a aplicação a dados medidos da empresa, que permitirá substituir as hipóteses e "
        "produzir as primeiras conclusões reais."
    )
    c.p("Permanecem pendentes de definição pelo autor:")
    c.alineas([
        "os dados de identificação deste relatório (cidade e nome do professor)",
        "a obtenção dos dados reais listados no Quadro " + str(q_req),
        "a inclusão de um link para o projeto no README principal do repositório",
        "a verificação dos itens do Quadro 10",
    ])
