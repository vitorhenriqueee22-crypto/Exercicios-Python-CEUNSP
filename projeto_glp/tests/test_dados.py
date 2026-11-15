"""Testes de importação, validação, banco de dados e dados simulados."""

import io
from datetime import date

import pandas as pd
import pytest

from src import alertas, banco_dados, dados_simulados, importacao, indicadores, relatorios, validacao
from src.constantes import SIMULADO, carregar_parametros

HOJE = date(2026, 11, 15)


def _registros(**alteracoes):
    base = {"data": ["2026-01-05", "2026-01-06"], "setor": ["FUNDICAO", "FUNDICAO"],
            "equipamento_id": ["FORNO-01", "FORNO-01"], "consumo_valor": [250.0, 240.0],
            "consumo_unidade": ["kg", "kg"], "atividade_valor": [2.0, 2.1],
            "atividade_unidade": ["t", "t"], "tempo_funcionamento_h": [14, 13],
            "origem": ["MEDIDO", "MEDIDO"]}
    base.update(alteracoes)
    return pd.DataFrame(base)


def _regras(resultado):
    return set(resultado.relatorio["regra"])


# ------------------------------------------------------------- validação
def test_registros_validos_sem_erros():
    r = validacao.validar_registros(_registros(), hoje=HOJE)
    assert r.aprovado and len(r.dados) == 2
    assert r.dados["consumo_kg"].tolist() == [250.0, 240.0]


def test_coluna_obrigatoria_ausente():
    r = validacao.validar_registros(_registros().drop(columns=["origem"]), hoje=HOJE)
    assert not r.aprovado and len(r.dados) == 0


def test_campo_vazio_negativo_e_data_invalida():
    r = validacao.validar_registros(_registros(consumo_valor=[None, -5.0]), hoje=HOJE)
    assert {"Campos vazios", "Valores negativos"} <= _regras(r)
    assert len(r.dados) == 0
    r = validacao.validar_registros(_registros(data=["2026-13-40", "2027-01-01"]), hoje=HOJE)
    assert _regras(r) == {"Datas inválidas"}
    assert r.n_erros == 2


def test_unidades_incompativeis():
    r = validacao.validar_registros(_registros(atividade_unidade=["refeicoes", "t"]), hoje=HOJE)
    assert "Unidades incompatíveis" in _regras(r) and len(r.dados) == 1
    r = validacao.validar_registros(_registros(consumo_unidade=["m3", "litros"]), hoje=HOJE)
    assert r.n_erros == 2


def test_m3_exige_fator_de_conversao():
    r = validacao.validar_registros(_registros(consumo_unidade=["m3", "kg"]), fator_kg_por_m3=2.0, hoje=HOJE)
    assert r.aprovado
    assert r.dados["consumo_kg"].tolist() == [500.0, 240.0]


def test_duplicados_e_mistura_de_origens():
    dup = pd.concat([_registros(), _registros().iloc[[0]]], ignore_index=True)
    r = validacao.validar_registros(dup, hoje=HOJE)
    assert "Registros duplicados" in _regras(r) and len(r.dados) == 2
    r = validacao.validar_registros(_registros(origem=["MEDIDO", "SIMULADO"]), hoje=HOJE)
    assert "Mistura de origens" in _regras(r) and len(r.dados) == 0
    r = validacao.validar_registros(_registros(origem=["MEDIDO", "SIMULADO"]), permitir_mistura=True, hoje=HOJE)
    assert len(r.dados) == 2


def test_leituras_inconsistentes_e_lacunas():
    equip = pd.DataFrame({"equipamento_id": ["FORNO-01"], "potencia_nominal_kg_h": [10.0]})
    r = validacao.validar_registros(_registros(tempo_funcionamento_h=[30, 13]), equip, hoje=HOJE)
    assert "Leituras inconsistentes" in _regras(r)
    assert any("acima do máximo" in m for m in r.relatorio["mensagem"])
    r = validacao.validar_registros(_registros(data=["2026-01-01", "2026-01-05"]), hoje=HOJE)
    assert "Dados ausentes" in _regras(r) and r.aprovado


# ------------------------------------------------------------- importação
def test_importa_csv_brasileiro_com_sinonimos():
    texto = ("Data;Setor;Equipamento;Consumo (kg);Unidade;Produção;Unidade atividade;Origem\n"
             "2026-01-05;FUNDICAO;FORNO-01;250,5;kg;2,1;t;MEDIDO\n")
    df = importacao.ler_arquivo(io.BytesIO(texto.encode("utf-8")), "consumo.csv")
    assert {"data", "equipamento_id", "consumo_valor", "consumo_unidade", "atividade_valor"} <= set(df.columns)
    r = validacao.validar_registros(df, hoje=HOJE)
    assert r.aprovado and r.dados["consumo_kg"].iloc[0] == pytest.approx(250.5)


def test_importa_excel(tmp_path):
    caminho = tmp_path / "consumo.xlsx"
    _registros().to_excel(caminho, index=False)
    r = validacao.validar_registros(importacao.ler_arquivo(caminho), hoje=HOJE)
    assert r.aprovado and len(r.dados) == 2


def test_formato_nao_suportado():
    with pytest.raises(ValueError):
        importacao.ler_arquivo(io.BytesIO(b"x"), "dados.pdf")


# ------------------------------------------------------------- banco de dados
def test_banco_insere_ignora_duplicados_e_filtra_origem(tmp_path):
    banco = tmp_path / "b.db"
    dados = validacao.validar_registros(_registros(), hoje=HOJE).dados
    assert banco_dados.inserir_registros(dados, banco)["inseridos"] == 2
    assert banco_dados.inserir_registros(dados, banco)["ignorados"] == 2
    assert banco_dados.origens_disponiveis(banco) == {"MEDIDO": 2}
    assert banco_dados.ler_registros(banco, origem="SIMULADO").empty
    assert len(banco_dados.ler_registros(banco, inicio="2026-01-06")) == 1


def test_banco_carrega_simulados(tmp_path, simulados):
    pasta = tmp_path / "sim"
    dados_simulados.salvar(simulados, pasta)
    banco = tmp_path / "s.db"
    saida = banco_dados.carregar_simulados(banco, pasta)
    assert saida["inseridos"] == len(simulados["registros"])
    assert len(banco_dados.ler_tabela("equipamentos", banco)) == len(simulados["equipamentos"])
    assert (pasta / "HIPOTESES.md").read_text(encoding="utf-8").startswith("# Hipóteses")


# ------------------------------------------------------------- dados simulados
def test_simulados_reprodutiveis_e_rotulados(simulados):
    outra = dados_simulados.gerar()
    pd.testing.assert_frame_equal(outra["registros"], simulados["registros"])
    for nome in ("registros", "equipamentos", "abastecimentos", "intervencoes"):
        assert set(simulados[nome]["origem"]) == {SIMULADO}


def test_simulados_passam_na_validacao(registros):
    r = validacao.validar_registros(registros.drop(columns=["consumo_kg"]), hoje=HOJE)
    assert r.n_erros == 0 and len(r.dados) == len(registros)


def test_deteccao_encontra_anomalias_inseridas(simulados):
    lista = alertas.gerar_alertas(simulados["registros"], carregar_parametros(), preco=7.0)
    datas = {(a["setor"], a["data"].strftime("%Y-%m-%d")) for _, a in lista.iterrows()}
    assert ("Fundição", "2026-01-20") in datas
    assert {("Restaurante", d) for d in ("2026-03-10", "2026-03-11", "2026-03-12")} <= datas
    assert {("Chuveiros", f"2026-08-{d}") for d in range(15, 22)} <= datas


def test_intervencoes_simuladas_sao_detectadas(simulados):
    tab = relatorios.tabela_intervencoes(simulados["registros"], simulados["intervencoes"])
    f1 = tab.set_index("id").loc["INT-01"]
    assert f1["significativo"]
    assert f1["ic95_inf_pct"] < 8 < f1["ic95_sup_pct"]        # redução simulada de 8 %
    assert tab.set_index("id").loc["INT-02", "significativo"]


def test_consumo_especifico_fundicao_nao_conta_metal_duas_vezes(simulados):
    reg, equip = simulados["registros"], simulados["equipamentos"]
    esp = indicadores.especifico_por_setor(reg, 7.0, equip).loc["FUNDICAO", "consumo_especifico"]
    t_fundidas = reg.loc[reg["equipamento_id"] == "FORNO-01", "atividade_valor"].sum()
    assert esp > reg.loc[reg["setor"] == "FUNDICAO", "consumo_kg"].sum() / reg.loc[
        reg["setor"] == "FUNDICAO", "atividade_valor"].sum()
    assert esp == pytest.approx(
        reg[(reg["setor"] == "FUNDICAO") & reg["data"].isin(
            reg.loc[(reg["equipamento_id"] == "FORNO-01") & (reg["atividade_valor"] > 0), "data"])
            ]["consumo_kg"].sum() / t_fundidas)


def test_exportacoes(simulados):
    reg = simulados["registros"]
    tabelas = relatorios.tabelas_resumo(reg, 7.0, simulados["equipamentos"])
    assert relatorios.exportar_excel(tabelas, SIMULADO)[:2] == b"PK"
    md = relatorios.relatorio_markdown(reg, 7.0, SIMULADO, simulados["intervencoes"], None,
                                       simulados["equipamentos"])
    assert "NÃO descrevem a empresa" in md and "INT-01" in md
