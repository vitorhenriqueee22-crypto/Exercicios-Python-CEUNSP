# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Experimentação e Análise de Dados
# Aluno: Vitor Henrique Santos Das Virgens
# Projeto: Monitoramento e otimização do consumo de GLP
# Módulo: painel — utilitários compartilhados pelas páginas do Streamlit
# ============================================================
"""Carregamento de dados, filtros globais, formatação e gráficos padrão."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from . import banco_dados
from .constantes import (
    ARQUIVO_BANCO, COR_SETOR, COR_STATUS, MEDIDO, NOME_SETOR, SIMULADO, carregar_parametros,
)

# Tokens visuais (paleta de referência da skill de visualização)
SUPERFICIE = "#fcfcfb"
TEXTO = "#0b0b0b"
TEXTO_SEC = "#52514e"
GRADE = "#e7e6e2"
COR_PRIMARIA = COR_SETOR["FUNDICAO"]
COR_SECUNDARIA = COR_SETOR["RESTAURANTE"]
COR_NEUTRA = "#8a8985"

ICONE_NIVEL = {"critico": ":material/error:", "serio": ":material/warning:",
               "atencao": ":material/info:", "bom": ":material/check_circle:"}
ROTULO_NIVEL = {"critico": "Crítico", "serio": "Sério", "atencao": "Atenção", "bom": "Normal"}


# ---------------------------------------------------------------------------
# Formatação pt-BR
# ---------------------------------------------------------------------------
def num(valor, casas: int = 0) -> str:
    if valor is None or (isinstance(valor, float) and not np.isfinite(valor)):
        return "—"
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def reais(valor, casas: int = 2) -> str:
    return f"R$ {num(valor, casas)}"


def pct(valor, casas: int = 1) -> str:
    return f"{num(valor, casas)} %"


def valor_p(p) -> str:
    """Valor p legível: notação científica abaixo de 0,001."""
    if p is None or not np.isfinite(p):
        return "—"
    texto = f"{p:.2e}" if p < 0.001 else f"{p:.3f}"
    return texto.replace(".", ",")


def massa(kg) -> str:
    """Massa compacta para cartões: kg até 10 t; acima, em toneladas."""
    return f"{num(kg / 1000, 1)} t" if abs(kg) >= 10_000 else f"{num(kg)} kg"


def reais_compacto(valor) -> str:
    if abs(valor) >= 1_000_000:
        return f"R$ {num(valor / 1_000_000, 2)} mi"
    if abs(valor) >= 10_000:
        return f"R$ {num(valor / 1000, 1)} mil"
    return reais(valor, 0)


# ---------------------------------------------------------------------------
# Dados
# ---------------------------------------------------------------------------
def garantir_banco() -> None:
    """Cria o banco com os dados simulados na primeira execução."""
    if not ARQUIVO_BANCO.exists() or SIMULADO not in banco_dados.origens_disponiveis():
        banco_dados.carregar_simulados()


def _assinatura_banco() -> float:
    return ARQUIVO_BANCO.stat().st_mtime if ARQUIVO_BANCO.exists() else 0.0


@st.cache_data(show_spinner="Carregando dados…")
def _carregar(origem: str, assinatura: float) -> dict:
    df = banco_dados.ler_registros(origem=origem)
    df["data"] = pd.to_datetime(df["data"])
    return {
        "registros": df,
        "equipamentos": banco_dados.ler_tabela("equipamentos", origem=origem),
        "abastecimentos": banco_dados.ler_tabela("abastecimentos", origem=origem),
        "intervencoes": banco_dados.ler_tabela("intervencoes", origem=origem),
    }


def limpar_cache() -> None:
    _carregar.clear()


@dataclass
class Contexto:
    origem: str
    inicio: date
    fim: date
    preco: float
    parametros: dict
    dados: pd.DataFrame            # registros filtrados pelo período
    todos: pd.DataFrame            # registros da origem, sem filtro de período
    equipamentos: pd.DataFrame
    abastecimentos: pd.DataFrame
    intervencoes: pd.DataFrame

    @property
    def simulado(self) -> bool:
        return self.origem == SIMULADO


def barra_lateral() -> None:
    """Filtros globais, renderizados no arquivo de entrada (dashboard.py)
    para que os valores se mantenham ao trocar de página."""
    garantir_banco()
    parametros = carregar_parametros()
    origens = banco_dados.origens_disponiveis()
    opcoes = [o for o in (MEDIDO, SIMULADO) if origens.get(o)]
    with st.sidebar:
        st.markdown("### Filtros")
        origem = st.radio(
            "Origem dos dados", opcoes, key="ctx_origem",
            index=0,
            format_func=lambda o: "Medidos (empresa)" if o == MEDIDO else "Simulados (demonstração)",
            help="Dados medidos e simulados nunca são misturados na mesma análise.")
        base = _carregar(origem, _assinatura_banco())["registros"]
        minimo, maximo = base["data"].min().date(), base["data"].max().date()
        periodo = st.date_input("Período", value=(minimo, maximo), min_value=minimo,
                                max_value=maximo, key="ctx_periodo", format="DD/MM/YYYY")
        geral = parametros["geral"]
        st.number_input(
            "Preço do GLP (R$/kg)", min_value=0.0, value=float(geral["preco_glp_r_por_kg"]),
            step=0.10, format="%.2f", key="ctx_preco",
            help=f"Origem do valor padrão: {geral['preco_origem']}. {geral['preco_nota']}")
        if isinstance(periodo, tuple) and len(periodo) == 2:
            st.session_state["ctx_intervalo"] = periodo
        st.caption("Ferramenta de monitoramento e apoio à decisão. "
                   "Não envia comandos a equipamentos de GLP.")


def contexto() -> Contexto:
    garantir_banco()
    parametros = carregar_parametros()
    origens = banco_dados.origens_disponiveis()
    padrao = MEDIDO if origens.get(MEDIDO) else SIMULADO
    origem = st.session_state.get("ctx_origem", padrao)
    if not origens.get(origem):
        origem = padrao
    carregado = _carregar(origem, _assinatura_banco())
    todos = carregado["registros"]
    intervalo = st.session_state.get("ctx_intervalo")
    if intervalo:
        inicio, fim = intervalo
    else:
        inicio, fim = todos["data"].min().date(), todos["data"].max().date()
    dados = todos[(todos["data"] >= pd.Timestamp(inicio)) & (todos["data"] <= pd.Timestamp(fim))]
    preco = float(st.session_state.get("ctx_preco", parametros["geral"]["preco_glp_r_por_kg"]))
    return Contexto(origem, inicio, fim, preco, parametros, dados, todos,
                    carregado["equipamentos"], carregado["abastecimentos"],
                    carregado["intervencoes"])


# ---------------------------------------------------------------------------
# Componentes de interface
# ---------------------------------------------------------------------------
def cabecalho(titulo: str, ctx: Contexto, subtitulo: str | None = None) -> None:
    st.title(titulo)
    if subtitulo:
        st.caption(subtitulo)
    periodo = f"{ctx.inicio:%d/%m/%Y} a {ctx.fim:%d/%m/%Y}"
    if ctx.simulado:
        st.warning(
            f"**Dados SIMULADOS** ({periodo}). São dados sintéticos de demonstração, gerados "
            "com hipóteses explícitas (página *Base de dados*). Não descrevem a empresa e não "
            "servem para conclusões sobre o consumo real.", icon=":material/science:")
    else:
        st.success(f"**Dados MEDIDOS** pela empresa ({periodo}).", icon=":material/fact_check:")


def alerta(nivel: str, mensagem: str) -> None:
    texto = f"**{ROTULO_NIVEL.get(nivel, nivel)}** — {mensagem}"
    icone = ICONE_NIVEL.get(nivel)
    if nivel == "critico":
        st.error(texto, icon=icone)
    elif nivel == "serio":
        st.warning(texto, icon=icone)
    else:
        st.info(texto, icon=icone)


def sem_dados(mensagem: str = "Não há registros deste setor no período selecionado.") -> None:
    st.info(mensagem, icon=":material/info:")


def layout(fig: go.Figure, titulo: str | None = None, altura: int = 360,
           eixo_y: str | None = None, eixo_x: str | None = None,
           legenda: bool = True) -> go.Figure:
    com_legenda = legenda and len(fig.data) > 1
    topo = (48 if titulo else 16) + (30 if com_legenda else 0)
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=15, color=TEXTO), x=0, xanchor="left",
                   y=1, yref="container", yanchor="top", pad=dict(t=12)) if titulo else None,
        height=altura, margin=dict(l=8, r=8, t=topo, b=8),
        font=dict(family="Inter, Arial, sans-serif", size=12, color=TEXTO_SEC),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified" if fig.data and fig.data[0].type == "scatter"
        and getattr(fig.data[0], "mode", "") in ("lines", "lines+markers") else "closest",
        showlegend=legenda,
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0, title=None,
                    traceorder="normal"),
        bargap=0.25, separators=",.",
    )
    fig.update_xaxes(showgrid=False, linecolor=GRADE, title=eixo_x, ticks="outside",
                     tickcolor=GRADE)
    # Datas sempre em formato numérico brasileiro (evita nomes de meses em inglês)
    for eixo in fig.select_xaxes():
        if eixo.type == "date" or any(getattr(t, "x", None) is not None and len(t.x)
                                      and isinstance(t.x[0], (pd.Timestamp, np.datetime64))
                                      for t in fig.data):
            eixo.update(tickformat=eixo.tickformat or "%m/%Y", hoverformat="%d/%m/%Y")
    fig.update_yaxes(gridcolor=GRADE, zeroline=False, linecolor=GRADE, title=eixo_y)
    return fig


def grafico(fig: go.Figure, chave: str | None = None) -> None:
    st.plotly_chart(fig, width="stretch", theme="streamlit", key=chave,
                    config={"displaylogo": False, "locale": "pt-BR"})


def linha_tempo(df: pd.DataFrame, x: str, series: dict[str, tuple[str, str]],
                titulo: str | None = None, eixo_y: str | None = None,
                marcas: list[tuple[str, str]] | None = None, altura: int = 340) -> go.Figure:
    """series: {coluna: (rótulo, cor)}. marcas: [(data, texto)] linhas verticais."""
    fig = go.Figure()
    for coluna, (rotulo, cor) in series.items():
        fig.add_trace(go.Scatter(x=df[x], y=df[coluna], name=rotulo, mode="lines",
                                 line=dict(color=cor, width=2)))
    for data_marca, texto in marcas or []:
        fig.add_vline(x=pd.Timestamp(data_marca).timestamp() * 1000, line_width=1,
                      line_color=TEXTO_SEC)
        fig.add_annotation(x=pd.Timestamp(data_marca), y=1, yref="paper", text=texto,
                           showarrow=False, xanchor="left", yanchor="top",
                           font=dict(size=11, color=TEXTO_SEC), bgcolor="rgba(255,255,255,0.7)")
    return layout(fig, titulo, altura, eixo_y, legenda=len(series) > 1)


def cor_setor(setor: str) -> str:
    return COR_SETOR.get(setor, COR_NEUTRA)


def nome_setor(setor: str) -> str:
    return NOME_SETOR.get(setor, setor)


def baixar_csv(df: pd.DataFrame, nome: str, rotulo: str = "Baixar tabela (CSV)") -> None:
    st.download_button(rotulo, df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                       file_name=nome, mime="text/csv", icon=":material/download:")


def nota_responsabilidade() -> None:
    st.caption(":material/engineering: Recomendações de ajuste, manutenção ou alteração de "
               "instalação devem ser avaliadas por profissionais habilitados, conforme os "
               "manuais dos fabricantes e as normas aplicáveis. O sistema não atua nos equipamentos.")


__all__ = [
    "COR_STATUS", "Contexto", "alerta", "baixar_csv", "barra_lateral", "cabecalho",
    "contexto", "cor_setor", "grafico", "layout", "limpar_cache", "linha_tempo",
    "massa", "nome_setor", "valor_p", "nota_responsabilidade", "num", "pct", "reais",
    "reais_compacto", "sem_dados",
]
