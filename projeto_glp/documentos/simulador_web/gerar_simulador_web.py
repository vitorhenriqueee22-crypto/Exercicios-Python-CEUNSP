"""
Gera a versão web estática do simulador (simulador_glp.html).

Os indicadores, os testes de hipóteses (por janela de dias), os alertas e o
balanço do reservatório são calculados pelo sistema em Python (pasta src) a
partir dos dados SIMULADOS e embutidos na página como JSON. A página só
desenha os gráficos e recalcula a simulação de economia no navegador.

Execução (a partir da raiz do repositório):
    python projeto_glp/documentos/simulador_web/gerar_simulador_web.py
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ))

from src import (alertas, chuveiros, dados_simulados, estatistica, fundicao,  # noqa: E402
                 indicadores, relatorios, reservatorio, restaurante)
from src.constantes import PCI_KWH_KG, carregar_parametros  # noqa: E402


def r(x, c=3):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return None
    return round(float(x), c)


def exportar() -> dict:
    hip = dados_simulados.carregar_hipoteses()
    par = carregar_parametros()
    tab = dados_simulados.gerar(hip, par)
    reg = tab["registros"]
    preco = par["geral"]["preco_glp_r_por_kg"]
    out = {"preco": preco, "pci_kwh_kg": PCI_KWH_KG,
           "periodo": [str(reg["data"].min()), str(reg["data"].max())],
           "dias_mes": par["geral"]["dias_operacao_mes"], "dias_ano": par["geral"]["dias_operacao_ano"]}

    mensal = indicadores.por_periodo(reg, "MS")
    out["mensal"] = {"rotulos": [d.strftime("%m/%Y") for d in mensal.index],
                     "setores": {s: [r(v, 1) for v in mensal[s]] for s in mensal.columns}}
    part = indicadores.participacao(reg, preco)
    out["total_kg"] = r(part["consumo_kg"].sum(), 1)
    out["dias"] = int(pd.to_datetime(reg["data"]).nunique())
    esp = indicadores.especifico_por_setor(reg, preco, tab["equipamentos"])
    out["setores"] = {s: {"kg": r(part.loc[s, "consumo_kg"], 1), "pct": r(part.loc[s, "participacao_pct"], 2),
                          "ce": r(esp.loc[s, "consumo_especifico"], 4), "unidade": esp.loc[s, "unidade"]}
                      for s in part.index}

    fornos = fundicao.indicadores_por_forno(reg, preco, tab["equipamentos"])
    out["fornos"] = [{"id": i, "nome": f["nome"], "funcao": f["funcao"], "kg": r(f["consumo_kg"], 0),
                      "t": r(f["metal_t"], 1), "kg_h": r(f["kg_por_h"], 2), "kg_t": r(f["kg_por_t"], 1),
                      "kg_ciclo": r(f["kg_por_ciclo"], 1), "sem_carga": r(f["fracao_sem_carga_pct"], 1),
                      "kg_sem_prod": r(f["kg_dias_sem_producao"], 0)} for i, f in fornos.iterrows()]
    d = fundicao.diario_fornos(reg)
    f1 = d[(d.equipamento_id == "FORNO-01") & (d.metal_t > 0)].sort_values("data")
    out["forno01"] = {"datas": f1["data"].dt.strftime("%Y-%m-%d").tolist(),
                      "kg_t": [r(v, 2) for v in f1["kg_por_t"]]}
    out["eta_media"] = r(fundicao.eficiencia_estimada(f1, par["fundicao"]["liga"]).mean() * 100, 1)

    dr = restaurante.diario(reg, preco)
    prod = dr[dr.refeicoes > 0]
    mr = restaurante.modelo_consumo(dr)
    fx = restaurante.por_faixa(dr, par["restaurante"]["faixas_refeicoes"])
    out["restaurante"] = {
        "refeicoes": prod["refeicoes"].astype(int).tolist(), "kg": [r(v, 2) for v in prod["consumo_kg"]],
        "b0": r(mr.coeficientes.loc["intercepto", "coef"], 3), "b1": r(mr.coeficientes.loc["refeicoes", "coef"], 5),
        "r2aj": r(mr.r2_ajustado, 3), "g_por_ref": r(prod["consumo_kg"].sum() / prod["refeicoes"].sum() * 1000, 1),
        "kg_dia": r(prod["consumo_kg"].mean(), 1),
        "faixas": {"rotulos": list(fx.index), "g_por_ref": [r(v * 1000, 1) for v in fx["kg_por_refeicao_medio"]],
                   "dias": fx["dias"].astype(int).tolist()}}

    dc = chuveiros.diario(reg, preco)
    perfil = chuveiros.perfil_horario(reg)
    uteis = dc[dc.data.dt.dayofweek < 5]
    corr = estatistica.correlacao(uteis.temp_entrada_c, uteis.consumo_kg - uteis.kg_sem_uso)
    out["chuveiros"] = {
        "perfil_kg": [r(v, 3) for v in perfil["kg_medio"]], "perfil_usuarios": [r(v, 1) for v in perfil["usuarios_medios"]],
        "datas": dc["data"].dt.strftime("%Y-%m-%d").tolist(), "kg": [r(v, 2) for v in dc["consumo_kg"]],
        "kg_sem_uso": [r(v, 2) for v in dc["kg_sem_uso"]],
        "g_por_usuario": r(dc.consumo_kg.sum() / dc.usuarios.sum() * 1000, 0),
        "pct_sem_uso": r(dc.kg_sem_uso.sum() / dc.consumo_kg.sum() * 100, 1),
        "kg_dia": r(dc.consumo_kg.mean(), 1), "pearson_r": r(corr["pearson_r"], 3)}

    out["intervencoes"] = []
    for i in hip["intervencoes"]:
        serie = relatorios.serie_metrica(reg, i["setor"], i["equipamento_id"])
        item = {"id": i["id"], "setor": i["setor"], "equipamento": i["equipamento_id"],
                "descricao": i["descricao"], "inicio": i["data_inicio"],
                "metrica": relatorios.METRICA_PADRAO[i["setor"]], "janelas": {},
                "serie": {"datas": [x.strftime("%Y-%m-%d") for x in serie.index],
                          "valores": [r(v, 3) for v in serie.values]}}
        for j in (30, 60, 90, 120, 180):
            res = relatorios.avaliar_intervencao(reg, i, j)["resultado"]
            item["janelas"][str(j)] = {
                "n_antes": res.n_antes, "n_depois": res.n_depois, "media_antes": r(res.media_antes),
                "media_depois": r(res.media_depois), "reducao_pct": r(res.reducao_percentual, 2),
                "ic": [r(v, 2) for v in res.ic95_reducao_percentual], "teste": res.teste,
                "p": float(res.p_valor), "efeito": r(res.tamanho_efeito, 2), "significativo": res.significativo,
                "normalidade": {k: {"w": r(v.estatistica, 3), "p": float(v.p_valor), "normal": v.normal}
                                for k, v in res.normalidade.items()}}
        out["intervencoes"].append(item)

    cons = reg.assign(data=pd.to_datetime(reg.data)).groupby("data").consumo_kg.sum()
    pr = par["reservatorio"]
    est = reservatorio.balanco_massa(cons, tab["abastecimentos"], pr["estoque_inicial_kg"], pr["capacidade_nominal_kg"])
    out["reservatorio"] = {
        "datas": est.index.strftime("%Y-%m-%d").tolist(), "estoque": [r(v, 0) for v in est.estoque_kg],
        "abastecimentos": [{"data": a["data"], "kg": r(a["massa_kg"], 0), "preco": a["preco_r_kg"]}
                           for _, a in tab["abastecimentos"].iterrows()],
        "capacidade": pr["capacidade_nominal_kg"], "fracao_max": pr["fracao_maxima_enchimento"],
        "reserva": pr["estoque_minimo_reserva_kg"], "alerta_pct": pr["nivel_alerta_percentual"],
        "media30": r(cons.tail(30).mean(), 1)}

    dd = indicadores.diario(reg)
    tot = dd.groupby("data").consumo_kg.sum()
    esc = {"TOTAL": {"kg_dia": r(tot[tot > 0].mean(), 1), "atividade": None, "unidade": None}}
    unidades = {"FUNDICAO": "t/dia", "RESTAURANTE": "refeições/dia", "CHUVEIROS": "usuários/dia"}
    for s, u in unidades.items():
        g = dd[dd.setor == s].groupby("data").agg(kg=("consumo_kg", "sum"), a=("atividade", "sum"))
        if s == "FUNDICAO":   # toneladas fundidas (fornos de fusão), sem contar o metal duas vezes
            g["a"] = f1.groupby("data").metal_t.sum().reindex(g.index).fillna(0)
        esc[s] = {"kg_dia": r(g.kg[g.kg > 0].mean(), 1), "atividade": r(g.a[g.a > 0].mean(), 2), "unidade": u}
    out["escopos"] = esc

    lista = alertas.gerar_alertas(reg, par, preco=preco)
    out["alertas"] = [{"nivel": a["nivel"], "setor": a["setor"], "data": a["data"].strftime("%d/%m/%Y"),
                       "mensagem": a["mensagem"]} for _, a in lista.iterrows()]
    return out


def main() -> None:
    dados = json.dumps(exportar(), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = (AQUI / "modelo.html").read_text(encoding="utf-8").replace("__DADOS__", dados)
    destino = AQUI / "simulador_glp.html"
    destino.write_text(html, encoding="utf-8")
    print(f"Gerado: {destino} ({len(html) // 1024} KB)")


if __name__ == "__main__":
    main()
