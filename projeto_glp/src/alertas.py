# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Experimentação e Análise de Dados
# Aluno: Vitor Henrique Santos Das Virgens
# Projeto: Monitoramento e otimização do consumo de GLP
# Módulo: alertas — consolidação dos alertas de consumo fora do padrão
# ============================================================
"""Gera a lista de alertas exibida na visão geral e nos relatórios.

Cada alerta é um indício para investigação. O sistema não conclui que houve
desperdício e não atua sobre os equipamentos.
"""

from __future__ import annotations

import pandas as pd

from . import anomalias, chuveiros, fundicao, reservatorio, restaurante
from .constantes import NOME_SETOR

NIVEIS = ("critico", "serio", "atencao")


def _n(valor, casas: int = 1) -> str:
    """Número no padrão brasileiro."""
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _alerta(nivel, setor, data, mensagem, metodo) -> dict:
    return {"nivel": nivel, "setor": NOME_SETOR.get(setor, setor), "data": data,
            "mensagem": mensagem, "metodo": metodo}


def gerar_alertas(df: pd.DataFrame, parametros: dict, abastecimentos: pd.DataFrame | None = None,
                  estoque_inicial_kg: float | None = None, preco: float = 0.0,
                  dados_reservatorio: pd.DataFrame | None = None) -> pd.DataFrame:
    """``dados_reservatorio``: histórico completo usado no balanço de massa do
    tanque (o estoque depende de todo o histórico, não só do período filtrado)."""
    saida: list[dict] = []
    limite_z = parametros.get("estatistica", {}).get("limite_escore_z_robusto", 3.5)

    # Fundição: resíduos do modelo de cada forno e consumo sem produção
    d = fundicao.diario_fornos(df)
    for forno, g in d.groupby("equipamento_id"):
        operando = g[g["metal_t"].fillna(0) > 0]
        if len(operando) >= 15:
            try:
                modelo = fundicao.modelo_consumo(operando)
                z = anomalias.escore_z_robusto(modelo.residuos, limite_z)
                for idx in z.index[z["anomalia"] & (z["escore_m"] > 0)]:
                    linha = operando.loc[idx]
                    saida.append(_alerta(
                        "serio", "FUNDICAO", linha["data"],
                        f"{forno}: consumo de {_n(linha['consumo_kg'], 0)} kg, acima do esperado pelo "
                        f"modelo (escore {_n(z.at[idx, 'escore_m'], 1)}).", "Escore z robusto dos resíduos"))
            except ValueError:
                pass
        sem_prod = g[(g["metal_t"].fillna(0) == 0) & (g["consumo_kg"] > 0)]
        if len(sem_prod):
            saida.append(_alerta(
                "atencao", "FUNDICAO", sem_prod["data"].max(),
                f"{forno}: {len(sem_prod)} dia(s) com consumo sem produção registrada, total de "
                f"{_n(sem_prod['consumo_kg'].sum(), 0)} kg (forno aquecido sem carga).",
                "Consumo sem atividade"))

    # Restaurante: resíduos do modelo e consumo fora do horário
    dr = restaurante.diario(df, preco)
    if (dr["refeicoes"] > 0).sum() >= 15:
        modelo = restaurante.modelo_consumo(dr)
        z = anomalias.escore_z_robusto(modelo.residuos, limite_z)
        for idx in z.index[z["anomalia"] & (z["escore_m"] > 0)]:
            linha = dr.loc[idx]
            saida.append(_alerta(
                "serio", "RESTAURANTE", linha["data"],
                f"Consumo de {_n(linha['consumo_kg'], 1)} kg para {_n(linha['refeicoes'], 0)} refeições, "
                f"acima do esperado (escore {_n(z.at[idx, 'escore_m'], 1)}).",
                "Escore z robusto dos resíduos"))
    pr = parametros.get("restaurante", {})
    fora = restaurante.fora_do_horario(df, pr.get("hora_abertura", 6), pr.get("hora_fechamento", 20))
    for _, linha in fora.iterrows():
        saida.append(_alerta(
            "critico", "RESTAURANTE", linha["data"],
            f"{_n(linha['kg_fora_horario'], 1)} kg consumidos com a cozinha fechada. Verificar "
            "queimadores e possíveis vazamentos (profissional habilitado).",
            "Consumo fora do horário"))

    # Chuveiros: consumo em horas sem uso acima do padrão
    dc = chuveiros.diario(df, preco)
    if len(dc) >= 15:
        z = anomalias.escore_z_robusto(dc["kg_sem_uso"], limite_z)
        for idx in z.index[z["anomalia"] & (z["escore_m"] > 0)]:
            linha = dc.loc[idx]
            saida.append(_alerta(
                "serio", "CHUVEIROS", linha["data"],
                f"{_n(linha['kg_sem_uso'], 1)} kg em horas sem usuários, acima do padrão. "
                "Verificar programação e termostato do aquecedor.",
                "Escore z robusto"))

    # Reservatório
    base_tanque = dados_reservatorio if dados_reservatorio is not None else df
    if abastecimentos is not None and estoque_inicial_kg is not None and len(base_tanque):
        consumo = (base_tanque.assign(data=pd.to_datetime(base_tanque["data"]))
                   .groupby("data")["consumo_kg"].sum())
        estado = reservatorio.balanco_massa(consumo, abastecimentos, estoque_inicial_kg,
                                            parametros["reservatorio"]["capacidade_nominal_kg"])
        for a in reservatorio.alertas(estado, parametros["reservatorio"], consumo.tail(30).mean()):
            saida.append(_alerta(a["nivel"], "GERAL", estado.index[-1], a["mensagem"],
                                 "Balanço de massa (virtual)"))

    tabela = pd.DataFrame(saida, columns=["nivel", "setor", "data", "mensagem", "metodo"])
    if len(tabela):
        tabela["data"] = pd.to_datetime(tabela["data"])
        tabela["ordem"] = tabela["nivel"].map({n: i for i, n in enumerate(NIVEIS)})
        tabela = tabela.sort_values(["data", "ordem"], ascending=[False, True]).drop(columns="ordem")
    return tabela.reset_index(drop=True)
