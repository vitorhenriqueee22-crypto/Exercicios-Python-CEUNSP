# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Experimentação e Análise de Dados
# Aluno: Vitor Henrique Santos Das Virgens
# Projeto: Monitoramento e otimização do consumo de GLP
# Arquivo: main.py — linha de comando
# ============================================================
"""Linha de comando do sistema de monitoramento de GLP.

Exemplos (a partir da pasta projeto_glp):
    python main.py gerar-simulados
    python main.py importar dados/dados_reais/consumo_jan.xlsx
    python main.py resumo --origem MEDIDO
    python main.py painel
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))

from src import alertas, banco_dados, importacao, relatorios, validacao  # noqa: E402
from src.constantes import MEDIDO, PASTA_RESULTADOS, SIMULADO, carregar_parametros  # noqa: E402


def cmd_gerar_simulados(_args) -> None:
    saida = banco_dados.carregar_simulados(regenerar=True)
    print(f"Dados SIMULADOS gerados e carregados: {saida['inseridos']} registros.")
    print("Hipóteses: dados/dados_simulados/HIPOTESES.md")


def cmd_importar(args) -> None:
    bruto = importacao.ler_arquivo(args.arquivo)
    equip = banco_dados.ler_tabela("equipamentos")
    resultado = validacao.validar_registros(bruto, equip, args.fator_m3)
    print(f"Lidas: {resultado.total_lido} · aceitas: {len(resultado.dados)} · "
          f"erros: {resultado.n_erros} · avisos: {resultado.n_avisos}")
    if len(resultado.relatorio):
        PASTA_RESULTADOS.mkdir(exist_ok=True)
        destino = PASTA_RESULTADOS / f"validacao_{Path(args.arquivo).stem}.csv"
        resultado.relatorio.to_csv(destino, index=False, sep=";")
        print(f"Relatório de validação: {destino}")
    if set(resultado.dados["origem"].dropna()) - {MEDIDO}:
        print("Somente registros MEDIDO são importados por este comando.")
        sys.exit(1)
    if args.gravar and len(resultado.dados):
        saida = banco_dados.inserir_registros(resultado.dados, arquivo=Path(args.arquivo).name)
        print(f"Gravados: {saida['inseridos']} · já existentes: {saida['ignorados']}")
    elif len(resultado.dados):
        print("Validação concluída. Use --gravar para gravar os registros aceitos.")


def cmd_resumo(args) -> None:
    banco_dados.carregar_simulados() if not banco_dados.origens_disponiveis() else None
    df = banco_dados.ler_registros(origem=args.origem, inicio=args.inicio, fim=args.fim)
    if df.empty:
        print(f"Sem registros com origem {args.origem}.")
        sys.exit(1)
    parametros = carregar_parametros()
    preco = args.preco or parametros["geral"]["preco_glp_r_por_kg"]
    equip = banco_dados.ler_tabela("equipamentos", origem=args.origem)
    interv = banco_dados.ler_tabela("intervencoes", origem=args.origem)
    abast = banco_dados.ler_tabela("abastecimentos", origem=args.origem)
    lista = alertas.gerar_alertas(df, parametros, abast, parametros["reservatorio"]["estoque_inicial_kg"], preco)
    texto = relatorios.relatorio_markdown(df, preco, args.origem, interv, lista, equip)
    print(texto)
    if args.saida:
        Path(args.saida).write_text(texto, encoding="utf-8")
        planilha = Path(args.saida).with_suffix(".xlsx")
        planilha.write_bytes(relatorios.exportar_excel(
            relatorios.tabelas_resumo(df, preco, equip, lista), args.origem))
        print(f"\nSalvo em {args.saida} e {planilha}")


def cmd_painel(_args) -> None:
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(RAIZ / "dashboard.py")],
                   cwd=RAIZ, check=False)


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Monitoramento e análise do consumo de GLP.")
    sub = parser.add_subparsers(dest="comando", required=True)

    sub.add_parser("gerar-simulados", help="Gera os dados SIMULADOS e carrega no banco.").set_defaults(
        func=cmd_gerar_simulados)

    p = sub.add_parser("importar", help="Valida (e opcionalmente grava) uma planilha CSV/Excel.")
    p.add_argument("arquivo")
    p.add_argument("--gravar", action="store_true", help="Grava os registros aceitos no banco.")
    p.add_argument("--fator-m3", type=float, default=None,
                   help="Fator kg/m³ do fornecedor, para leituras em m³.")
    p.set_defaults(func=cmd_importar)

    p = sub.add_parser("resumo", help="Imprime o relatório resumido do período.")
    p.add_argument("--origem", choices=[MEDIDO, SIMULADO], default=SIMULADO)
    p.add_argument("--inicio")
    p.add_argument("--fim")
    p.add_argument("--preco", type=float, help="Preço do GLP em R$/kg.")
    p.add_argument("--saida", help="Arquivo .md para salvar o relatório (também gera .xlsx).")
    p.set_defaults(func=cmd_resumo)

    sub.add_parser("painel", help="Abre o painel interativo (Streamlit).").set_defaults(func=cmd_painel)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
