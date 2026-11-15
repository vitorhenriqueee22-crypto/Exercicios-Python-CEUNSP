# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Experimentação e Análise de Dados
# Aluno: Vitor Henrique Santos Das Virgens
# Projeto: Monitoramento e otimização do consumo de GLP
# Módulo: dados_simulados — gerador de dados SINTÉTICOS de demonstração
# ============================================================
"""Gera dados sintéticos rotulados como SIMULADO.

As hipóteses ficam em ``config/hipoteses_simulacao.toml`` e são copiadas para
``dados/dados_simulados/HIPOTESES.md`` a cada geração. Os dados servem para
testar e demonstrar o sistema; NÃO servem para conclusões sobre a empresa.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import numpy as np
import pandas as pd

from .constantes import (
    CHUVEIROS, COLUNAS_REGISTRO, FUNDICAO, PASTA_SIMULADOS, RAIZ, RESTAURANTE,
    SIMULADO, carregar_parametros,
)
from .chuveiros import glp_por_banho_kg

ARQUIVO_HIPOTESES = RAIZ / "config" / "hipoteses_simulacao.toml"


def carregar_hipoteses(caminho: Path | None = None) -> dict:
    with open(caminho or ARQUIVO_HIPOTESES, "rb") as arquivo:
        return tomllib.load(arquivo)


def _registro(**campos) -> dict:
    base = {c: None for c in COLUNAS_REGISTRO}
    base.update(campos)
    base["origem"] = SIMULADO
    base["consumo_unidade"] = "kg"
    return base


def _em(data, inicio, fim) -> bool:
    return pd.Timestamp(inicio) <= data <= pd.Timestamp(fim)


def _anomalias_de(hip: dict, setor: str) -> list[dict]:
    return [a for a in hip.get("anomalias", []) if a["setor"] == setor]


def _intervencao(hip: dict, equipamento: str) -> dict | None:
    for i in hip.get("intervencoes", []):
        if i["equipamento_id"] == equipamento:
            return i
    return None


def gerar(hip: dict | None = None, parametros: dict | None = None) -> dict[str, pd.DataFrame]:
    """Retorna as tabelas simuladas: registros, equipamentos, abastecimentos e
    intervencoes."""
    hip = hip or carregar_hipoteses()
    parametros = parametros or carregar_parametros()
    rng = np.random.default_rng(hip["periodo"]["semente"])
    dias = pd.date_range(hip["periodo"]["inicio"], periods=hip["periodo"]["dias"], freq="D")
    regs: list[dict] = []

    def ruido(desvio):
        return 1.0 + rng.normal(0.0, desvio)

    # ------------------------------------------------------------------ fundição
    f1, f2, f3 = (hip["fornos"][k] for k in ("FORNO-01", "FORNO-02", "FORNO-03"))
    int_f1 = _intervencao(hip, "FORNO-01")
    anom_fund = _anomalias_de(hip, FUNDICAO)
    for dia in dias:
        dsem = dia.dayofweek
        data = dia.strftime("%Y-%m-%d")
        metal_f1 = 0.0
        if dsem in f1["dias_semana"]:
            ciclos = int(rng.integers(f1["ciclos_min"], f1["ciclos_max"] + 1))
            metal_f1 = ciclos * f1["carga_t_por_ciclo"] * rng.uniform(0.9, 1.0)
            horas = min(f1["horas_base"] + ciclos * f1["horas_por_ciclo"] + rng.normal(0, 0.4), 23.5)
            com_carga = ciclos * f1["horas_com_carga_por_ciclo"]
            sem_carga = max(horas - com_carga, 0.3)
            fator = 1.0
            if int_f1 and dia >= pd.Timestamp(int_f1["data_inicio"]):
                fator *= 1.0 - int_f1["reducao"]
            for a in anom_fund:
                if a["equipamento_id"] == "FORNO-01" and _em(dia, a["inicio"], a["fim"]):
                    fator *= a["fator"]
            consumo = (f1["beta_h"] * horas + f1["beta_t"] * metal_f1) * fator * ruido(f1["ruido"])
            regs.append(_registro(
                data=data, setor=FUNDICAO, equipamento_id="FORNO-01",
                consumo_valor=round(consumo, 2), atividade_valor=round(metal_f1, 3),
                atividade_unidade="t", tempo_funcionamento_h=round(horas, 2),
                tempo_sem_carga_h=round(sem_carga, 2), ciclos=ciclos,
                temperatura_c=round(rng.normal(f1["temperatura_trabalho_c"], 8), 1)))
        if dsem in f2["dias_semana"]:
            horas = f2["horas_dia"] + rng.normal(0, 0.5)
            consumo = (f2["beta_h"] * horas + f2["beta_t"] * metal_f1) * ruido(f2["ruido"])
            regs.append(_registro(
                data=data, setor=FUNDICAO, equipamento_id="FORNO-02",
                consumo_valor=round(consumo, 2), atividade_valor=round(metal_f1, 3),
                atividade_unidade="t", tempo_funcionamento_h=round(horas, 2),
                tempo_sem_carga_h=0.0,
                temperatura_c=round(rng.normal(f2["temperatura_trabalho_c"], 6), 1)))
        elif dsem == 6 and f2.get("horas_domingo_sem_producao"):
            horas = f2["horas_domingo_sem_producao"]
            consumo = f2["beta_h"] * horas * ruido(f2["ruido"])
            regs.append(_registro(
                data=data, setor=FUNDICAO, equipamento_id="FORNO-02",
                consumo_valor=round(consumo, 2), atividade_valor=0.0,
                atividade_unidade="t", tempo_funcionamento_h=horas,
                tempo_sem_carga_h=horas,
                temperatura_c=round(rng.normal(f2["temperatura_trabalho_c"], 6), 1)))
        if dsem in f3["dias_semana"]:
            metal = rng.uniform(f3["carga_t_min"], f3["carga_t_max"])
            horas = rng.uniform(f3["horas_min"], f3["horas_max"])
            consumo = (f3["beta_h"] * horas + f3["beta_t"] * metal) * ruido(f3["ruido"])
            regs.append(_registro(
                data=data, setor=FUNDICAO, equipamento_id="FORNO-03",
                consumo_valor=round(consumo, 2), atividade_valor=round(metal, 3),
                atividade_unidade="t", tempo_funcionamento_h=round(horas, 2),
                tempo_sem_carga_h=round(rng.uniform(0.8, 1.6), 2), ciclos=1,
                temperatura_c=round(rng.normal(f3["temperatura_trabalho_c"], 5), 1)))

    # --------------------------------------------------------------- restaurante
    r = hip["restaurante"]
    perfil_c = {int(k): v for k, v in r["perfil_consumo"].items()}
    perfil_r = {int(k): v for k, v in r["perfil_refeicoes"].items()}
    anom_rest = _anomalias_de(hip, RESTAURANTE)
    for dia in dias:
        dsem = dia.dayofweek
        if dsem == 6:
            continue
        if dsem < 5:
            n = max(int(rng.normal(r["refeicoes_media_util"], r["refeicoes_dp_util"])), 0)
        else:
            n = max(int(rng.normal(r["refeicoes_media_sabado"], r["refeicoes_dp_sabado"])), 0)
        fator, extra_noite = 1.0, 0.0
        for a in anom_rest:
            if _em(dia, a["inicio"], a["fim"]):
                fator *= a.get("fator", 1.0)
                extra_noite = a.get("kg_hora_fora_expediente", 0.0)
        total = (r["beta_0"] + r["beta_1"] * n) * fator * ruido(r["ruido"])
        servidas = {h: int(round(n * p)) for h, p in perfil_r.items()}
        ajuste = n - sum(servidas.values())
        servidas[12] = servidas.get(12, 0) + ajuste
        for h, p in perfil_c.items():
            regs.append(_registro(
                data=dia.strftime("%Y-%m-%d"), hora=f"{h:02d}:00", setor=RESTAURANTE,
                equipamento_id="COZINHA", consumo_valor=round(total * p, 3),
                atividade_valor=float(servidas.get(h, 0)), atividade_unidade="refeicoes",
                tempo_funcionamento_h=1.0))
        if extra_noite:
            for h in (21, 22, 23):
                regs.append(_registro(
                    data=dia.strftime("%Y-%m-%d"), hora=f"{h:02d}:00", setor=RESTAURANTE,
                    equipamento_id="COZINHA",
                    consumo_valor=round(extra_noite * ruido(0.05), 3),
                    atividade_valor=0.0, atividade_unidade="refeicoes",
                    tempo_funcionamento_h=1.0))

    # ----------------------------------------------------------------- chuveiros
    c = hip["chuveiros"]
    pc = parametros["chuveiros"]
    int_ch = _intervencao(hip, "AQUECEDOR-01")
    anom_ch = _anomalias_de(hip, CHUVEIROS)
    for dia in dias:
        dsem = dia.dayofweek
        if dsem < 5:
            n = max(int(rng.normal(c["usuarios_media_util"], c["usuarios_dp_util"])), 0)
            perfil = c["perfil_usuarios_util"]
        elif dsem == 5:
            n, perfil = c["usuarios_sabado"], c["perfil_usuarios_sabado"]
        else:
            n, perfil = c["usuarios_domingo"], c["perfil_usuarios_domingo"]
        perfil = {int(k): v for k, v in perfil.items()}
        usuarios_h = {h: int(round(n * p)) for h, p in perfil.items()}
        # Temperatura da água de entrada: senoide anual (máximo em meados de janeiro)
        t_entrada = (c["temp_entrada_media_c"]
                     + c["temp_entrada_amplitude_c"] * np.cos(2 * np.pi * (dia.dayofyear - 15) / 365))
        delta_t = pc["temperatura_saida_c"] - t_entrada
        kg_banho = glp_por_banho_kg(pc["duracao_banho_min"], pc["vazao_l_min"], delta_t,
                                    pc["rendimento_aquecedor"])
        perda = c["perda_espera_kg_h"]
        if int_ch and dia >= pd.Timestamp(int_ch["data_inicio"]):
            perda = int_ch["nova_perda_espera_kg_h"]
        extra_madrugada = 0.0
        for a in anom_ch:
            if _em(dia, a["inicio"], a["fim"]):
                extra_madrugada = a.get("kg_hora_extra_madrugada", 0.0)
        for h in range(24):
            usuarios = usuarios_h.get(h, 0)
            consumo = (perda + usuarios * kg_banho) * ruido(c["ruido"])
            if h <= 5 and usuarios == 0:
                consumo += extra_madrugada
            regs.append(_registro(
                data=dia.strftime("%Y-%m-%d"), hora=f"{h:02d}:00", setor=CHUVEIROS,
                equipamento_id="AQUECEDOR-01", consumo_valor=round(consumo, 3),
                atividade_valor=float(usuarios), atividade_unidade="usuarios",
                tempo_funcionamento_h=1.0, temperatura_c=round(t_entrada, 2)))

    registros = pd.DataFrame(regs, columns=list(COLUNAS_REGISTRO))
    registros["consumo_kg"] = registros["consumo_valor"]

    # ------------------------------------------------------------- equipamentos
    equip = []
    for chave, f in hip["fornos"].items():
        equip.append({"equipamento_id": chave, "nome": f["nome"], "setor": FUNDICAO,
                      "tipo": f["tipo"], "funcao": f["funcao"], "metal_liga": f["metal_liga"],
                      "capacidade_nominal_kg": f["capacidade_nominal_kg"],
                      "potencia_nominal_kg_h": f["potencia_nominal_kg_h"],
                      "temperatura_trabalho_c": f["temperatura_trabalho_c"],
                      "medicao_individual": "sim", "origem": SIMULADO})
    equip.append({"equipamento_id": "COZINHA", "nome": "Cozinha industrial (medidor do setor)",
                  "setor": RESTAURANTE, "tipo": "Conjunto de fogões, fornos e caldeirões",
                  "funcao": "Cocção", "metal_liga": None, "capacidade_nominal_kg": None,
                  "potencia_nominal_kg_h": r["potencia_nominal_kg_h"],
                  "temperatura_trabalho_c": None, "medicao_individual": "não (medidor do setor)",
                  "origem": SIMULADO})
    equip.append({"equipamento_id": "AQUECEDOR-01", "nome": "Aquecedor de acumulação",
                  "setor": CHUVEIROS, "tipo": "Aquecedor de água a gás de acumulação",
                  "funcao": "Aquecimento de água", "metal_liga": None,
                  "capacidade_nominal_kg": None, "potencia_nominal_kg_h": c["potencia_nominal_kg_h"],
                  "temperatura_trabalho_c": pc["temperatura_saida_c"],
                  "medicao_individual": "sim", "origem": SIMULADO})
    equipamentos = pd.DataFrame(equip)

    # ----------------------------------------------------------- abastecimentos
    res = hip["reservatorio"]
    tanque = parametros["reservatorio"]
    capacidade = tanque["capacidade_nominal_kg"]
    alvo = capacidade * tanque["fracao_maxima_enchimento"]
    consumo_dia = registros.groupby("data")["consumo_kg"].sum()
    consumo_dia.index = pd.to_datetime(consumo_dia.index)
    consumo_dia = consumo_dia.reindex(dias, fill_value=0.0)
    estoque = tanque["estoque_inicial_kg"]
    preco = res["preco_inicial_r_kg"]
    mes_atual = dias[0].month
    abastec = []
    for dia in dias:
        if dia.month != mes_atual:
            mes_atual = dia.month
            preco = round(preco * (1 + rng.normal(0, res["variacao_mensal_preco"])), 2)
        if estoque / capacidade * 100 < res["gatilho_abastecimento_pct"]:
            leitura = estoque / capacidade * 100 + rng.normal(0, res["erro_indicador_nivel_pct"])
            massa = round(alvo - estoque - rng.uniform(0, 150), 1)
            abastec.append({"data": dia.strftime("%Y-%m-%d"), "massa_kg": massa,
                            "preco_r_kg": preco, "nota_fiscal": f"SIM-{len(abastec) + 1:04d}",
                            "nivel_antes_pct": round(leitura, 1), "origem": SIMULADO})
            estoque += massa
        estoque -= consumo_dia[dia]
    abastecimentos = pd.DataFrame(abastec)

    intervencoes = pd.DataFrame([
        {"id": i["id"], "setor": i["setor"], "equipamento_id": i["equipamento_id"],
         "descricao": i["descricao"] + " (SIMULADO)", "data_inicio": i["data_inicio"],
         "origem": SIMULADO}
        for i in hip.get("intervencoes", [])
    ])
    return {"registros": registros, "equipamentos": equipamentos,
            "abastecimentos": abastecimentos, "intervencoes": intervencoes}


def _texto_hipoteses(hip: dict) -> str:
    linhas = [
        "# Hipóteses dos dados SIMULADOS",
        "",
        "> **Atenção:** todos os arquivos desta pasta são **dados sintéticos**, gerados por "
        "`src/dados_simulados.py` a partir de `config/hipoteses_simulacao.toml`. "
        "Eles servem para testar e demonstrar o sistema e **não descrevem a empresa**. "
        "Nenhuma conclusão sobre o consumo real pode ser tirada deles.",
        "",
        f"- Período: {hip['periodo']['dias']} dias a partir de {hip['periodo']['inicio']}",
        f"- Semente do gerador: {hip['periodo']['semente']} (dados reprodutíveis)",
        "",
        "## Modelos de consumo",
        "",
    ]
    for chave, f in hip["fornos"].items():
        linhas.append(f"- **{chave}** ({f['nome']}, {f['funcao']}): "
                      f"G = {f['beta_h']}·horas + {f['beta_t']}·t, ruído {f['ruido']:.0%}")
    r = hip["restaurante"]
    linhas.append(f"- **Restaurante**: G = {r['beta_0']} + {r['beta_1']}·refeições, ruído {r['ruido']:.0%}; "
                  f"{r['refeicoes_media_util']} refeições em dias úteis, {r['refeicoes_media_sabado']} "
                  "aos sábados, fechado aos domingos")
    c = hip["chuveiros"]
    linhas.append(f"- **Chuveiros**: perda em espera {c['perda_espera_kg_h']} kg/h + GLP por banho "
                  "calculado pelas Equações 10 a 12 com os parâmetros de `config/parametros.toml`; "
                  f"{c['usuarios_media_util']} usuários em dias úteis")
    linhas += ["", "## Intervenções simuladas", ""]
    for i in hip.get("intervencoes", []):
        efeito = (f"redução de {i['reducao']:.0%}" if "reducao" in i
                  else f"perda em espera passa a {i.get('nova_perda_espera_kg_h')} kg/h")
        linhas.append(f"- {i['id']} — {i['equipamento_id']}, a partir de {i['data_inicio']}: "
                      f"{i['descricao']} ({efeito})")
    linhas += ["", "## Anomalias inseridas de propósito (gabarito da detecção)", ""]
    for a in hip.get("anomalias", []):
        linhas.append(f"- {a['setor']}/{a['equipamento_id']}, {a['inicio']} a {a['fim']}: {a['descricao']}")
    linhas.append("")
    return "\n".join(linhas)


def salvar(tabelas: dict[str, pd.DataFrame], pasta: Path | None = None,
           hip: dict | None = None) -> Path:
    pasta = Path(pasta or PASTA_SIMULADOS)
    pasta.mkdir(parents=True, exist_ok=True)
    for nome, df in tabelas.items():
        saida = df.drop(columns=["consumo_kg"]) if nome == "registros" else df
        saida.to_csv(pasta / f"{nome}.csv", index=False)
    (pasta / "HIPOTESES.md").write_text(_texto_hipoteses(hip or carregar_hipoteses()),
                                        encoding="utf-8")
    return pasta
