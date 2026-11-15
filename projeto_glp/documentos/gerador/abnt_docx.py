"""
Motor de formatação de documentos .docx segundo as normas ABNT.

Normas atendidas (apresentação gráfica):
    - ABNT NBR 14724:2024  — trabalhos acadêmicos (margens, fonte, espaçamento,
                             paginação, elementos pré-textuais);
    - ABNT NBR 10719:2015  — relatório técnico e/ou científico;
    - ABNT NBR 6024:2012   — numeração progressiva das seções;
    - ABNT NBR 6027:2012   — sumário;
    - ABNT NBR 6028:2021   — resumo;
    - ABNT NBR 6023:2018   — referências (o texto das referências é fornecido
                             pelo arquivo de conteúdo);
    - ABNT NBR 10520:2023  — citações (sistema autor-data, no conteúdo).

Uso resumido:
    conteudo = Conteudo()
    conteudo.h1("1", "INTRODUÇÃO")
    conteudo.p("Texto com **negrito**, *itálico*, m_{GLP} e x^{2}.")
    doc = DocumentoABNT(metadados, conteudo)
    doc.salvar("saida.docx", paginas=None)

O sumário e as listas de ilustrações/tabelas são gerados com números de
página calculados em duas passagens (ver ``paginar_com_libreoffice``).
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import (
    WD_ALIGN_PARAGRAPH,
    WD_LINE_SPACING,
    WD_TAB_ALIGNMENT,
    WD_TAB_LEADER,
)
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

# ---------------------------------------------------------------------------
# Parâmetros de layout (NBR 14724:2024, seção 5)
# ---------------------------------------------------------------------------
FONTE = "Arial"
FONTE_MONO = "Courier New"
TAMANHO_TEXTO = 12
TAMANHO_MENOR = 10          # citações longas, legendas, fontes, tabelas, paginação
MARGEM_SUP_CM = 3.0
MARGEM_ESQ_CM = 3.0
MARGEM_INF_CM = 2.0
MARGEM_DIR_CM = 2.0
LARGURA_TEXTO_CM = 21.0 - MARGEM_ESQ_CM - MARGEM_DIR_CM   # 16 cm em A4
RECUO_PARAGRAFO_CM = 1.25
ESPACO_15_LINHA_PT = 18     # uma linha em branco com entrelinha 1,5 (fonte 12)

PLACEHOLDER_PAGINA = "00"
LINHAS_TABELA_INDIVISIVEL = 12


# ---------------------------------------------------------------------------
# Modelo de conteúdo
# ---------------------------------------------------------------------------
@dataclass
class Bloco:
    tipo: str
    dados: dict = field(default_factory=dict)


class Conteudo:
    """Sequência de blocos textuais e pós-textuais do documento."""

    def __init__(self) -> None:
        self.blocos: list[Bloco] = []
        self._n_eq = 0
        self._n_quadro = 0
        self._n_tabela = 0
        self._n_figura = 0

    # Títulos ---------------------------------------------------------------
    def h1(self, indicativo: str | None, titulo: str) -> None:
        self.blocos.append(Bloco("h1", {"ind": indicativo, "titulo": titulo}))

    def h2(self, indicativo: str, titulo: str) -> None:
        self.blocos.append(Bloco("h2", {"ind": indicativo, "titulo": titulo}))

    def h3(self, indicativo: str, titulo: str) -> None:
        self.blocos.append(Bloco("h3", {"ind": indicativo, "titulo": titulo}))

    # Texto -----------------------------------------------------------------
    def p(self, texto: str, recuo: bool = True) -> None:
        self.blocos.append(Bloco("p", {"texto": texto, "recuo": recuo}))

    def alineas(self, itens: list[str]) -> None:
        self.blocos.append(Bloco("alineas", {"itens": itens}))

    def definicoes(self, itens: list[tuple[str, str]]) -> None:
        """Lista 'em que:' após equações: [(símbolo, descrição), ...]."""
        self.blocos.append(Bloco("definicoes", {"itens": itens}))

    def eq(self, expressao: str) -> int:
        self._n_eq += 1
        self.blocos.append(Bloco("eq", {"expr": expressao, "n": self._n_eq}))
        return self._n_eq

    # Ilustrações e tabelas -------------------------------------------------
    def quadro(self, titulo, cabecalho, linhas, larguras_cm, fonte, nota=None) -> int:
        self._n_quadro += 1
        self.blocos.append(Bloco("tabela", {
            "rotulo": "Quadro", "n": self._n_quadro, "titulo": titulo,
            "cabecalho": cabecalho, "linhas": linhas, "larguras": larguras_cm,
            "fonte": fonte, "nota": nota, "estilo": "quadro",
        }))
        return self._n_quadro

    def tabela(self, titulo, cabecalho, linhas, larguras_cm, fonte, nota=None,
               alinhamentos=None) -> int:
        self._n_tabela += 1
        self.blocos.append(Bloco("tabela", {
            "rotulo": "Tabela", "n": self._n_tabela, "titulo": titulo,
            "cabecalho": cabecalho, "linhas": linhas, "larguras": larguras_cm,
            "fonte": fonte, "nota": nota, "estilo": "tabela",
            "alinhamentos": alinhamentos,
        }))
        return self._n_tabela

    def figura_texto(self, titulo: str, linhas: list[str], fonte: str) -> int:
        """Figura composta por texto monoespaçado (ex.: árvore de diretórios)."""
        self._n_figura += 1
        self.blocos.append(Bloco("figura_texto", {
            "n": self._n_figura, "titulo": titulo, "linhas": linhas, "fonte": fonte,
        }))
        return self._n_figura

    def figura_imagem(self, titulo: str, caminho, fonte: str, largura_cm: float = 15.0) -> int:
        """Figura a partir de arquivo de imagem (PNG/JPG)."""
        self._n_figura += 1
        self.blocos.append(Bloco("figura_imagem", {
            "n": self._n_figura, "titulo": titulo, "caminho": str(caminho), "fonte": fonte,
            "largura": largura_cm,
        }))
        return self._n_figura

    def figura_fluxo(self, titulo: str, etapas: list[tuple[str, str]], fonte: str) -> int:
        """Figura de fluxo linear: [(nome_etapa, descrição_curta), ...]."""
        self._n_figura += 1
        self.blocos.append(Bloco("figura_fluxo", {
            "n": self._n_figura, "titulo": titulo, "etapas": etapas, "fonte": fonte,
        }))
        return self._n_figura

    # Pós-textuais ----------------------------------------------------------
    def referencias(self, itens: list[str]) -> None:
        self.blocos.append(Bloco("h1", {"ind": None, "titulo": "REFERÊNCIAS"}))
        self.blocos.append(Bloco("referencias", {"itens": itens}))

    # Consultas para sumário e listas ---------------------------------------
    def entradas_sumario(self) -> list[tuple[str, str | None, str]]:
        return [(b.tipo, b.dados["ind"], b.dados["titulo"])
                for b in self.blocos if b.tipo in ("h1", "h2", "h3")]

    def entradas_ilustracoes(self) -> list[str]:
        saida = []
        for b in self.blocos:
            if b.tipo == "tabela" and b.dados["rotulo"] == "Quadro":
                saida.append(f"Quadro {b.dados['n']} – {b.dados['titulo']}")
            elif b.tipo in ("figura_texto", "figura_fluxo", "figura_imagem"):
                saida.append(f"Figura {b.dados['n']} – {b.dados['titulo']}")
        return saida

    def entradas_tabelas(self) -> list[str]:
        return [f"Tabela {b.dados['n']} – {b.dados['titulo']}"
                for b in self.blocos
                if b.tipo == "tabela" and b.dados["rotulo"] == "Tabela"]


@dataclass
class Metadados:
    instituicao: list[str]
    autor: str
    titulo: str
    subtitulo: str
    natureza: str
    orientador: str
    local: str
    ano: str
    resumo: str
    palavras_chave: list[str]
    abstract: str
    keywords: list[str]
    siglas: list[tuple[str, str]]
    simbolos: list[tuple[str, str]]


# ---------------------------------------------------------------------------
# Utilidades de XML
# ---------------------------------------------------------------------------
_TOKEN = re.compile(r"(\*\*.+?\*\*|\*[^*\s][^*]*?\*|_\{[^}]*\}|\^\{[^}]*\}|`[^`]+`)")


def _rfonts(run, nome: str) -> None:
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for atributo in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(atributo), nome)


def adicionar_runs(par, texto: str, tamanho: int | None = None,
                   negrito: bool | None = None, fonte: str = FONTE) -> None:
    """Adiciona texto ao parágrafo interpretando a marcação leve:
    **negrito**, *itálico*, _{subscrito}, ^{sobrescrito}, `monoespaçado`."""
    for parte in _TOKEN.split(texto):
        if not parte:
            continue
        estilo = {}
        conteudo = parte
        if parte.startswith("**") and parte.endswith("**") and len(parte) > 4:
            conteudo, estilo = parte[2:-2], {"bold": True}
        elif parte.startswith("*") and parte.endswith("*") and len(parte) > 2:
            conteudo, estilo = parte[1:-1], {"italic": True}
        elif parte.startswith("_{") and parte.endswith("}"):
            conteudo, estilo = parte[2:-1], {"subscript": True}
        elif parte.startswith("^{") and parte.endswith("}"):
            conteudo, estilo = parte[2:-1], {"superscript": True}
        elif parte.startswith("`") and parte.endswith("`"):
            conteudo, estilo = parte[1:-1], {"mono": True}
        run = par.add_run(conteudo)
        _rfonts(run, FONTE_MONO if estilo.get("mono") else fonte)
        if tamanho:
            run.font.size = Pt(tamanho - 1 if estilo.get("mono") else tamanho)
        if negrito is not None:
            run.bold = negrito
        if estilo.get("bold"):
            run.bold = True
        if estilo.get("italic"):
            run.italic = True
        if estilo.get("subscript"):
            run.font.subscript = True
        if estilo.get("superscript"):
            run.font.superscript = True


def _formatar(par, alinhamento=WD_ALIGN_PARAGRAPH.JUSTIFY, recuo_primeira=0.0,
              recuo_esq=0.0, entrelinha=1.5, antes=0, depois=0,
              manter_com_proximo=False) -> None:
    pf = par.paragraph_format
    pf.alignment = alinhamento
    pf.first_line_indent = Cm(recuo_primeira) if recuo_primeira else Cm(0)
    pf.left_indent = Cm(recuo_esq) if recuo_esq else Cm(0)
    pf.right_indent = Cm(0)
    pf.space_before = Pt(antes)
    pf.space_after = Pt(depois)
    if entrelinha == 1.0:
        pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
    else:
        pf.line_spacing = entrelinha
    pf.keep_with_next = manter_com_proximo
    pf.widow_control = True


def _campo(par, instrucao: str, valor: str, tamanho: int) -> None:
    def _run():
        r = par.add_run()
        _rfonts(r, FONTE)
        r.font.size = Pt(tamanho)
        return r

    r1 = _run()
    fc = OxmlElement("w:fldChar")
    fc.set(qn("w:fldCharType"), "begin")
    r1._r.append(fc)
    r2 = _run()
    it = OxmlElement("w:instrText")
    it.set(qn("xml:space"), "preserve")
    it.text = f" {instrucao} "
    r2._r.append(it)
    r3 = _run()
    fc = OxmlElement("w:fldChar")
    fc.set(qn("w:fldCharType"), "separate")
    r3._r.append(fc)
    r4 = _run()
    r4.text = valor
    r5 = _run()
    fc = OxmlElement("w:fldChar")
    fc.set(qn("w:fldCharType"), "end")
    r5._r.append(fc)


def _sombrear(celula, cor: str = "D9D9D9") -> None:
    tcpr = celula._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), cor)
    tcpr.append(shd)


def _bordas_tabela(tabela, estilo: str) -> None:
    tblpr = tabela._tbl.tblPr
    existentes = tblpr.find(qn("w:tblBorders"))
    if existentes is not None:
        tblpr.remove(existentes)
    bordas = OxmlElement("w:tblBorders")
    if estilo == "quadro":       # quadro: bordas fechadas
        lados = {"top": "single", "left": "single", "bottom": "single",
                 "right": "single", "insideH": "single", "insideV": "single"}
    elif estilo == "tabela":     # tabela (IBGE): laterais abertas
        lados = {"top": "single", "left": "nil", "bottom": "single",
                 "right": "nil", "insideH": "nil", "insideV": "single"}
    else:                        # sem bordas
        lados = {k: "nil" for k in ("top", "left", "bottom", "right", "insideH", "insideV")}
    for lado, valor in lados.items():
        el = OxmlElement(f"w:{lado}")
        el.set(qn("w:val"), valor)
        if valor != "nil":
            el.set(qn("w:sz"), "4")
            el.set(qn("w:space"), "0")
            el.set(qn("w:color"), "000000")
        bordas.append(el)
    tblpr.append(bordas)


def _borda_celula(celula, lado: str) -> None:
    tcpr = celula._tc.get_or_add_tcPr()
    tcb = tcpr.find(qn("w:tcBorders"))
    if tcb is None:
        tcb = OxmlElement("w:tcBorders")
        tcpr.append(tcb)
    el = OxmlElement(f"w:{lado}")
    el.set(qn("w:val"), "single")
    el.set(qn("w:sz"), "4")
    el.set(qn("w:space"), "0")
    el.set(qn("w:color"), "000000")
    tcb.append(el)


def _larguras(tabela, larguras_cm: list[float]) -> None:
    tabela.autofit = False
    tblpr = tabela._tbl.tblPr
    tblw = tblpr.find(qn("w:tblW"))
    if tblw is None:
        tblw = OxmlElement("w:tblW")
        tblpr.append(tblw)
    tblw.set(qn("w:w"), str(int(round(sum(larguras_cm) * 567))))
    tblw.set(qn("w:type"), "dxa")
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblpr.append(layout)
    for gc, largura in zip(tabela._tbl.tblGrid.findall(qn("w:gridCol")), larguras_cm):
        gc.set(qn("w:w"), str(int(round(largura * 567))))
    for linha in tabela.rows:
        for celula, largura in zip(linha.cells, larguras_cm):
            celula.width = Cm(largura)


def _repetir_cabecalho(linha) -> None:
    trpr = linha._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trpr.append(el)
    nao_quebrar = OxmlElement("w:cantSplit")
    nao_quebrar.set(qn("w:val"), "true")
    trpr.append(nao_quebrar)


def _iniciar_paginacao(secao, inicio: int = 1) -> None:
    sectpr = secao._sectPr
    pg = OxmlElement("w:pgNumType")
    pg.set(qn("w:start"), str(inicio))
    cols = sectpr.find(qn("w:cols"))
    if cols is not None:
        cols.addprevious(pg)
    else:
        sectpr.append(pg)


# ---------------------------------------------------------------------------
# Documento
# ---------------------------------------------------------------------------
class DocumentoABNT:
    def __init__(self, meta: Metadados, conteudo: Conteudo) -> None:
        self.meta = meta
        self.conteudo = conteudo

    # Construção -------------------------------------------------------------
    def construir(self, paginas: dict[str, int] | None = None) -> Document:
        self.paginas = paginas or {}
        self.doc = Document()
        self._estilos()
        self._pagina(self.doc.sections[0])

        self._capa()
        secao = self.doc.add_section(WD_SECTION.NEW_PAGE)
        self._pagina(secao)
        _iniciar_paginacao(secao, 1)
        secao.header.is_linked_to_previous = False
        self._folha_rosto()
        self._resumo("RESUMO", self.meta.resumo, "Palavras-chave", self.meta.palavras_chave)
        if self.meta.abstract:
            self._resumo("ABSTRACT", self.meta.abstract, "Keywords", self.meta.keywords)
        if self.conteudo.entradas_ilustracoes():
            self._lista("LISTA DE ILUSTRAÇÕES", self.conteudo.entradas_ilustracoes())
        if self.conteudo.entradas_tabelas():
            self._lista("LISTA DE TABELAS", self.conteudo.entradas_tabelas())
        if self.meta.siglas:
            self._lista_duas_colunas("LISTA DE ABREVIATURAS E SIGLAS", self.meta.siglas, 3.0)
        if self.meta.simbolos:
            self._lista_duas_colunas("LISTA DE SÍMBOLOS", self.meta.simbolos, 3.0)
        self._sumario()

        secao = self.doc.add_section(WD_SECTION.NEW_PAGE)
        self._pagina(secao)
        # add_section copia as propriedades da seção anterior, inclusive o
        # reinício da paginação; a parte textual deve continuar a contagem.
        for pg in secao._sectPr.findall(qn("w:pgNumType")):
            secao._sectPr.remove(pg)
        secao.header.is_linked_to_previous = False
        cab = secao.header.paragraphs[0]
        _formatar(cab, alinhamento=WD_ALIGN_PARAGRAPH.RIGHT, entrelinha=1.0)
        _campo(cab, "PAGE", "1", TAMANHO_MENOR)

        primeiro = True
        for bloco in self.conteudo.blocos:
            self._renderizar(bloco, primeiro_h1=primeiro)
            if bloco.tipo == "h1":
                primeiro = False
        return self.doc

    def salvar(self, caminho: Path, paginas: dict[str, int] | None = None) -> Path:
        self.construir(paginas)
        caminho = Path(caminho)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        self.doc.save(caminho)
        return caminho

    # Configuração -----------------------------------------------------------
    def _pagina(self, secao) -> None:
        secao.page_width = Cm(21.0)
        secao.page_height = Cm(29.7)
        secao.top_margin = Cm(MARGEM_SUP_CM)
        secao.left_margin = Cm(MARGEM_ESQ_CM)
        secao.bottom_margin = Cm(MARGEM_INF_CM)
        secao.right_margin = Cm(MARGEM_DIR_CM)
        secao.header_distance = Cm(2.0)    # paginação a 2 cm da borda superior
        secao.footer_distance = Cm(1.0)

    def _estilos(self) -> None:
        estilos = self.doc.styles
        normal = estilos["Normal"]
        normal.font.name = FONTE
        normal.font.size = Pt(TAMANHO_TEXTO)
        rpr = normal.element.get_or_add_rPr()
        rfonts = rpr.find(qn("w:rFonts"))
        if rfonts is None:
            rfonts = OxmlElement("w:rFonts")
            rpr.insert(0, rfonts)
        for atributo in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            rfonts.set(qn(atributo), FONTE)
        pf = normal.paragraph_format
        pf.line_spacing = 1.5
        pf.space_before = Pt(0)
        pf.space_after = Pt(0)

        # NBR 6024: destaque gradativo — 1ª negrito/maiúsc.; 2ª maiúsc.; 3ª negrito
        config = {
            "Heading 1": {"bold": True},
            "Heading 2": {"bold": False},
            "Heading 3": {"bold": True},
        }
        for nome, cfg in config.items():
            est = estilos[nome]
            est.font.name = FONTE
            est.font.size = Pt(TAMANHO_TEXTO)
            est.font.bold = cfg["bold"]
            est.font.italic = False
            est.font.color.rgb = RGBColor(0, 0, 0)
            rpr = est.element.get_or_add_rPr()
            rfonts = rpr.find(qn("w:rFonts"))
            if rfonts is None:
                rfonts = OxmlElement("w:rFonts")
                rpr.insert(0, rfonts)
            for atributo in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
                rfonts.set(qn(atributo), FONTE)
            for atributo in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
                if rfonts.get(qn(atributo)) is not None:
                    del rfonts.attrib[qn(atributo)]
            epf = est.paragraph_format
            epf.space_before = Pt(ESPACO_15_LINHA_PT)
            epf.space_after = Pt(ESPACO_15_LINHA_PT)
            epf.line_spacing = 1.5
            epf.keep_with_next = True
            epf.alignment = WD_ALIGN_PARAGRAPH.LEFT

    # Elementos pré-textuais -------------------------------------------------
    def _par(self, texto="", alinhamento=WD_ALIGN_PARAGRAPH.CENTER, negrito=False,
             tamanho=TAMANHO_TEXTO, antes=0, depois=0, entrelinha=1.0, recuo_esq=0.0):
        par = self.doc.add_paragraph()
        _formatar(par, alinhamento=alinhamento, entrelinha=entrelinha, antes=antes,
                  depois=depois, recuo_esq=recuo_esq)
        if texto:
            adicionar_runs(par, texto, tamanho=tamanho, negrito=negrito or None)
        return par

    def _quebra_pagina(self, par) -> None:
        par.paragraph_format.page_break_before = True

    def _capa(self) -> None:
        m = self.meta
        for linha in m.instituicao:
            self._par(linha.upper(), negrito=True, entrelinha=1.5)
        self._par(m.autor.upper(), negrito=True, antes=96)
        self._par(m.titulo.upper() + ":", negrito=True, antes=150, entrelinha=1.5)
        self._par(m.subtitulo, negrito=False, entrelinha=1.5)
        self._par(m.local, negrito=True, antes=210)
        self._par(m.ano, negrito=True)

    def _folha_rosto(self) -> None:
        m = self.meta
        self._par(m.autor.upper(), negrito=True)
        self._par(m.titulo.upper() + ":", negrito=True, antes=170, entrelinha=1.5)
        self._par(m.subtitulo, entrelinha=1.5)
        self._par(m.natureza, alinhamento=WD_ALIGN_PARAGRAPH.JUSTIFY, antes=60,
                  recuo_esq=LARGURA_TEXTO_CM / 2)
        self._par(f"Orientador(a): {m.orientador}", alinhamento=WD_ALIGN_PARAGRAPH.LEFT,
                  antes=12, recuo_esq=LARGURA_TEXTO_CM / 2)
        self._par(m.local, negrito=True, antes=200)
        self._par(m.ano, negrito=True)

    def _titulo_sem_indicativo(self, texto: str) -> None:
        par = self._par(texto, negrito=True, depois=ESPACO_15_LINHA_PT, entrelinha=1.5)
        self._quebra_pagina(par)

    def _resumo(self, titulo: str, texto: str, rotulo: str, palavras: list[str]) -> None:
        self._titulo_sem_indicativo(titulo)
        par = self.doc.add_paragraph()
        _formatar(par, entrelinha=1.5)
        adicionar_runs(par, texto)
        par = self.doc.add_paragraph()
        _formatar(par, alinhamento=WD_ALIGN_PARAGRAPH.LEFT, entrelinha=1.5,
                  antes=ESPACO_15_LINHA_PT)
        adicionar_runs(par, f"**{rotulo}:** " + "; ".join(palavras) + ".")

    def _linha_pontilhada(self, prefixo: str, texto: str, chave: str, negrito=False,
                          recuo_titulo_cm: float = 0.0) -> None:
        par = self.doc.add_paragraph()
        _formatar(par, alinhamento=WD_ALIGN_PARAGRAPH.LEFT, entrelinha=1.5)
        pf = par.paragraph_format
        if recuo_titulo_cm:
            pf.left_indent = Cm(recuo_titulo_cm)
            pf.first_line_indent = Cm(-recuo_titulo_cm)
            pf.tab_stops.add_tab_stop(Cm(recuo_titulo_cm), WD_TAB_ALIGNMENT.LEFT)
        pf.tab_stops.add_tab_stop(Cm(LARGURA_TEXTO_CM), WD_TAB_ALIGNMENT.RIGHT,
                                  WD_TAB_LEADER.DOTS)
        pagina = self.paginas.get(chave)
        numero = str(pagina) if pagina is not None else PLACEHOLDER_PAGINA
        corpo = (prefixo + "\t" if recuo_titulo_cm else "") + texto
        adicionar_runs(par, corpo, negrito=negrito or None)
        adicionar_runs(par, "\t" + numero, negrito=negrito or None)

    def _lista(self, titulo: str, entradas: list[str]) -> None:
        self._titulo_sem_indicativo(titulo)
        for entrada in entradas:
            self._linha_pontilhada("", entrada, chave_de(entrada))

    def _lista_duas_colunas(self, titulo: str, itens: list[tuple[str, str]], col_cm: float) -> None:
        self._titulo_sem_indicativo(titulo)
        for termo, descricao in itens:
            par = self.doc.add_paragraph()
            _formatar(par, alinhamento=WD_ALIGN_PARAGRAPH.LEFT, entrelinha=1.5)
            pf = par.paragraph_format
            pf.left_indent = Cm(col_cm)
            pf.first_line_indent = Cm(-col_cm)
            pf.tab_stops.add_tab_stop(Cm(col_cm), WD_TAB_ALIGNMENT.LEFT)
            adicionar_runs(par, f"{termo}\t{descricao}")

    def _sumario(self) -> None:
        self._titulo_sem_indicativo("SUMÁRIO")
        for nivel, ind, titulo in self.conteudo.entradas_sumario():
            negrito = nivel in ("h1", "h3")
            texto = titulo
            self._linha_pontilhada(ind or "", texto, chave_de(f"{ind or ''} {titulo}"),
                                   negrito=negrito,
                                   recuo_titulo_cm=1.6 if ind else 0.0)

    # Elementos textuais -----------------------------------------------------
    def _renderizar(self, bloco: Bloco, primeiro_h1: bool) -> None:
        d = bloco.dados
        t = bloco.tipo
        if t in ("h1", "h2", "h3"):
            estilo = {"h1": "Heading 1", "h2": "Heading 2", "h3": "Heading 3"}[t]
            par = self.doc.add_paragraph(style=estilo)
            texto = f"{d['ind']} {d['titulo']}" if d["ind"] else d["titulo"]
            adicionar_runs(par, texto)
            if t == "h1":
                if not primeiro_h1:
                    par.paragraph_format.page_break_before = True
                par.paragraph_format.space_before = Pt(0)
                if not d["ind"]:
                    par.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif t == "p":
            par = self.doc.add_paragraph()
            _formatar(par, recuo_primeira=RECUO_PARAGRAFO_CM if d["recuo"] else 0.0)
            adicionar_runs(par, d["texto"])
        elif t == "alineas":
            n = len(d["itens"])
            for i, item in enumerate(d["itens"]):
                letra = chr(ord("a") + i)
                par = self.doc.add_paragraph()
                _formatar(par)
                pf = par.paragraph_format
                pf.left_indent = Cm(RECUO_PARAGRAFO_CM + 0.65)
                pf.first_line_indent = Cm(-0.65)
                pf.tab_stops.add_tab_stop(Cm(RECUO_PARAGRAFO_CM + 0.65), WD_TAB_ALIGNMENT.LEFT)
                final = "." if i == n - 1 else ";"
                texto = item.rstrip(" .;")
                adicionar_runs(par, f"{letra})\t{texto}{final}")
        elif t == "definicoes":
            par = self.doc.add_paragraph()
            _formatar(par, recuo_primeira=0.0)
            adicionar_runs(par, "em que:")
            for k, (simbolo, descricao) in enumerate(d["itens"]):
                final = "." if k == len(d["itens"]) - 1 else ";"
                par = self.doc.add_paragraph()
                _formatar(par, alinhamento=WD_ALIGN_PARAGRAPH.LEFT, entrelinha=1.0, depois=3)
                pf = par.paragraph_format
                pf.left_indent = Cm(RECUO_PARAGRAFO_CM + 2.0)
                pf.first_line_indent = Cm(-2.0)
                pf.tab_stops.add_tab_stop(Cm(RECUO_PARAGRAFO_CM + 2.0), WD_TAB_ALIGNMENT.LEFT)
                adicionar_runs(par, f"{simbolo}\t= {descricao}{final}")
        elif t == "eq":
            par = self.doc.add_paragraph()
            _formatar(par, alinhamento=WD_ALIGN_PARAGRAPH.LEFT, antes=6, depois=6)
            pf = par.paragraph_format
            pf.tab_stops.add_tab_stop(Cm(LARGURA_TEXTO_CM / 2), WD_TAB_ALIGNMENT.CENTER)
            pf.tab_stops.add_tab_stop(Cm(LARGURA_TEXTO_CM), WD_TAB_ALIGNMENT.RIGHT)
            adicionar_runs(par, f"\t{d['expr']}\t({d['n']})")
        elif t == "tabela":
            self._tabela(d)
        elif t == "figura_texto":
            self._figura_texto(d)
        elif t == "figura_fluxo":
            self._figura_fluxo(d)
        elif t == "figura_imagem":
            self._legenda(f"Figura {d['n']} – {d['titulo']}")
            par = self.doc.add_paragraph()
            _formatar(par, alinhamento=WD_ALIGN_PARAGRAPH.CENTER, entrelinha=1.0,
                      manter_com_proximo=True)
            par.add_run().add_picture(d["caminho"], width=Cm(d["largura"]))
            self._fonte(d["fonte"], None)
        elif t == "referencias":
            for ref in d["itens"]:
                par = self.doc.add_paragraph()
                _formatar(par, alinhamento=WD_ALIGN_PARAGRAPH.LEFT, entrelinha=1.0,
                          depois=TAMANHO_TEXTO)
                adicionar_runs(par, ref)
        else:
            raise ValueError(f"Tipo de bloco desconhecido: {t}")

    def _legenda(self, texto: str) -> None:
        par = self.doc.add_paragraph()
        _formatar(par, alinhamento=WD_ALIGN_PARAGRAPH.CENTER, entrelinha=1.0,
                  antes=6, depois=4, manter_com_proximo=True)
        adicionar_runs(par, texto, tamanho=TAMANHO_MENOR)

    def _fonte(self, fonte: str, nota: str | None) -> None:
        par = self.doc.add_paragraph()
        _formatar(par, alinhamento=WD_ALIGN_PARAGRAPH.LEFT, entrelinha=1.0, antes=3,
                  depois=0 if nota else 12, manter_com_proximo=bool(nota))
        adicionar_runs(par, f"Fonte: {fonte}", tamanho=TAMANHO_MENOR)
        if nota:
            par = self.doc.add_paragraph()
            _formatar(par, alinhamento=WD_ALIGN_PARAGRAPH.JUSTIFY, entrelinha=1.0, depois=12)
            adicionar_runs(par, f"Nota: {nota}", tamanho=TAMANHO_MENOR)

    def _celula(self, celula, texto: str, negrito=False, alinhamento=WD_ALIGN_PARAGRAPH.LEFT,
                tamanho=TAMANHO_MENOR, manter=True) -> None:
        celula.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
        linhas = texto.split("\n")
        for i, linha in enumerate(linhas):
            par = celula.paragraphs[0] if i == 0 else celula.add_paragraph()
            _formatar(par, alinhamento=alinhamento, entrelinha=1.0, antes=1, depois=1,
                      manter_com_proximo=manter)
            adicionar_runs(par, linha, tamanho=tamanho, negrito=negrito or None)

    def _tabela(self, d: dict) -> None:
        self._legenda(f"{d['rotulo']} {d['n']} – {d['titulo']}")
        cab, linhas = d["cabecalho"], d["linhas"]
        tabela = self.doc.add_table(rows=1 + len(linhas), cols=len(cab))
        tabela.alignment = WD_TABLE_ALIGNMENT.CENTER
        _bordas_tabela(tabela, d["estilo"])
        _larguras(tabela, d["larguras"])
        alinh = d.get("alinhamentos") or ["L"] * len(cab)
        mapa = {"L": WD_ALIGN_PARAGRAPH.LEFT, "C": WD_ALIGN_PARAGRAPH.CENTER,
                "R": WD_ALIGN_PARAGRAPH.RIGHT}
        _repetir_cabecalho(tabela.rows[0])
        for j, texto in enumerate(cab):
            cel = tabela.rows[0].cells[j]
            self._celula(cel, texto, negrito=True, alinhamento=WD_ALIGN_PARAGRAPH.CENTER)
            if d["estilo"] == "quadro":
                _sombrear(cel)
            else:
                _borda_celula(cel, "bottom")
        # Tabelas curtas ficam inteiras na mesma página, junto com a fonte;
        # tabelas longas podem continuar na página seguinte (cabeçalho repetido).
        manter = len(linhas) <= LINHAS_TABELA_INDIVISIVEL
        for i, linha in enumerate(linhas, start=1):
            trpr = tabela.rows[i]._tr.get_or_add_trPr()
            cs = OxmlElement("w:cantSplit")
            cs.set(qn("w:val"), "true")
            trpr.append(cs)
            for j, texto in enumerate(linha):
                self._celula(tabela.rows[i].cells[j], str(texto), alinhamento=mapa[alinh[j]],
                             manter=manter)
        self._fonte(d["fonte"], d.get("nota"))

    def _figura_texto(self, d: dict) -> None:
        self._legenda(f"Figura {d['n']} – {d['titulo']}")
        tabela = self.doc.add_table(rows=1, cols=1)
        tabela.alignment = WD_TABLE_ALIGNMENT.CENTER
        _bordas_tabela(tabela, "quadro")
        _larguras(tabela, [LARGURA_TEXTO_CM])
        cel = tabela.rows[0].cells[0]
        for i, linha in enumerate(d["linhas"]):
            par = cel.paragraphs[0] if i == 0 else cel.add_paragraph()
            _formatar(par, alinhamento=WD_ALIGN_PARAGRAPH.LEFT, entrelinha=1.0,
                      manter_com_proximo=True)
            run = par.add_run(linha if linha else " ")
            _rfonts(run, FONTE_MONO)
            run.font.size = Pt(9)
        self._fonte(d["fonte"], None)

    def _figura_fluxo(self, d: dict) -> None:
        self._legenda(f"Figura {d['n']} – {d['titulo']}")
        etapas = d["etapas"]
        n = len(etapas)
        seta_cm = 0.5
        caixa_cm = (LARGURA_TEXTO_CM - seta_cm * (n - 1)) / n
        larguras = []
        for i in range(n):
            larguras.append(caixa_cm)
            if i < n - 1:
                larguras.append(seta_cm)
        tabela = self.doc.add_table(rows=1, cols=len(larguras))
        tabela.alignment = WD_TABLE_ALIGNMENT.CENTER
        _bordas_tabela(tabela, "nenhuma")
        _larguras(tabela, larguras)
        for i, (nome, desc) in enumerate(etapas):
            cel = tabela.rows[0].cells[2 * i]
            for lado in ("top", "left", "bottom", "right"):
                _borda_celula(cel, lado)
            _sombrear(cel, "F2F2F2")
            cel.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            par = cel.paragraphs[0]
            _formatar(par, alinhamento=WD_ALIGN_PARAGRAPH.CENTER, entrelinha=1.0, antes=2)
            adicionar_runs(par, nome, tamanho=9, negrito=True)
            par = cel.add_paragraph()
            _formatar(par, alinhamento=WD_ALIGN_PARAGRAPH.CENTER, entrelinha=1.0, depois=2)
            adicionar_runs(par, desc, tamanho=8)
            if i < n - 1:
                seta = tabela.rows[0].cells[2 * i + 1]
                seta.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                par = seta.paragraphs[0]
                _formatar(par, alinhamento=WD_ALIGN_PARAGRAPH.CENTER, entrelinha=1.0)
                adicionar_runs(par, "→", tamanho=12, negrito=True)
        self._fonte(d["fonte"], None)


# ---------------------------------------------------------------------------
# Paginação em duas passagens (sumário e listas)
# ---------------------------------------------------------------------------
def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKC", texto)
    texto = re.sub(r"[*`]|_\{|\^\{|\}", "", texto)
    return re.sub(r"\s+", " ", texto).strip().upper()


def chave_de(texto: str) -> str:
    return _normalizar(texto)


def _localizar_paginas(pdf: Path, chaves: list[str]) -> dict[str, int]:
    """Localiza, em ordem, a página (numeração exibida) de cada título/legenda."""
    saida = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], check=True,
                           capture_output=True, text=True).stdout
    paginas = saida.split("\f")
    linhas_por_pagina = [[_normalizar(l) for l in p.splitlines() if l.strip()] for p in paginas]

    # Início da parte textual: primeira página após o sumário em que a
    # primeira chave aparece sem pontilhado.
    resultado: dict[str, int] = {}
    pagina_atual = 0
    for chave in chaves:
        encontrada = None
        for idx in range(pagina_atual, len(linhas_por_pagina)):
            for linha in linhas_por_pagina[idx]:
                if "...." in linha or ". . ." in linha:
                    continue
                if linha == chave or (len(linha) >= min(len(chave), 30) and chave.startswith(linha)):
                    encontrada = idx
                    break
            if encontrada is not None:
                break
        if encontrada is None:
            raise RuntimeError(f"Não foi possível localizar no PDF: {chave!r}")
        # pdf página 1 = capa (não contada); folha de rosto = 1
        resultado[chave] = encontrada  # índice 0-based == página exibida
        pagina_atual = encontrada
    return resultado


def converter_pdf(docx: Path, destino: Path) -> Path:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise RuntimeError("LibreOffice (soffice) não encontrado.")
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", tmp,
                        str(docx)], check=True, capture_output=True, timeout=300)
        gerado = Path(tmp) / (docx.stem + ".pdf")
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(gerado, destino)
    return destino


def paginar_com_libreoffice(documento: DocumentoABNT, caminho_docx: Path,
                            caminho_pdf: Path | None = None) -> dict[str, int]:
    """Gera o .docx em duas passagens para preencher o sumário e as listas
    com os números de página reais (contagem a partir da folha de rosto)."""
    caminho_docx = Path(caminho_docx)
    documento.salvar(caminho_docx, paginas=None)
    with tempfile.TemporaryDirectory() as tmp:
        pdf_tmp = converter_pdf(caminho_docx, Path(tmp) / "passagem1.pdf")
        paginas = _localizar_paginas(pdf_tmp, _ordenar_por_aparicao(documento.conteudo))
    documento.salvar(caminho_docx, paginas=paginas)
    if caminho_pdf:
        converter_pdf(caminho_docx, Path(caminho_pdf))
    return paginas


def _ordenar_por_aparicao(conteudo: Conteudo) -> list[str]:
    chaves = []
    for b in conteudo.blocos:
        d = b.dados
        if b.tipo in ("h1", "h2", "h3"):
            chaves.append(chave_de(f"{d['ind'] or ''} {d['titulo']}"))
        elif b.tipo == "tabela":
            chaves.append(chave_de(f"{d['rotulo']} {d['n']} – {d['titulo']}"))
        elif b.tipo in ("figura_texto", "figura_fluxo", "figura_imagem"):
            chaves.append(chave_de(f"Figura {d['n']} – {d['titulo']}"))
    return chaves
