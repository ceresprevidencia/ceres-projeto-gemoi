"""
Relatórios PDF - Fundação Ceres
================================

Módulo responsável por gerar os relatórios em PDF usados no acompanhamento de:

1. Enquadramento Diário;
2. Limites Operacionais;
3. Risco de Mercado dos Planos.

Principais decisões da refatoração
----------------------------------
- Imports, cores, fontes, paths e helpers visuais foram centralizados.
- A criação de estilos e tabelas foi reaproveitada entre relatórios.
- A lógica de preparação de dados ficou separada da lógica de renderização PDF.
- Funções públicas foram mantidas com os mesmos nomes para reduzir impacto:
    - gerar_pdf(...)
    - gerar_pdf_limites_operacionais(...)
    - gerar_pdf_risco_planos(...)

Observação: este módulo depende das funções `fmt_br` e `formatar_percentual_br`
de `utils.helpers`. Caso esse módulo não esteja disponível no ambiente de teste,
há fallbacks locais simples para facilitar desenvolvimento.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any, Iterable, Sequence
from xml.sax.saxutils import escape as xml_escape
import warnings

import pandas as pd
from reportlab.graphics import renderPDF
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from svglib.svglib import svg2rlg

try:
    # Preferência: manter a formatação já usada pelo projeto.
    from utils.helpers import fmt_br, formatar_percentual_br
except Exception:  # pragma: no cover - fallback apenas para ambiente isolado
    def fmt_br(valor: Any, casas: int = 2) -> str:
        """Fallback local para número no padrão brasileiro."""
        try:
            return f"{float(valor):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except Exception:
            return str(valor)

    def formatar_percentual_br(valor: Any, casas: int = 2) -> str:
        """Fallback local para percentual no padrão brasileiro."""
        try:
            return f"{float(valor):.{casas}f}%".replace(".", ",")
        except Exception:
            return str(valor)


pd.options.display.float_format = "{:.2f}".format


# =============================================================================
# CONFIGURAÇÕES GERAIS
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent
FONTS_DIR = (BASE_DIR / ".." / ".." / "fonts").resolve()
LOGO_RELATIVE_PATH = Path("images") / "c1_fundo_claro.svg"

# Paleta oficial usada nos relatórios.
VERDE_ESCURO = colors.HexColor("#016837")
VERDE_TITULO = colors.HexColor("#0B2F13")
VERDE_CLARO = colors.HexColor("#A8EC7D")
VERDE_BORDA = colors.HexColor("#014d2a")
CINZA_BORDA = colors.HexColor("#dddddd")
VERMELHO_FUNDO = colors.HexColor("#ffcccc")
FUNDO_PAGINA = colors.HexColor("#fafbeb")
TEXTO_PADRAO = colors.HexColor("#333333")
TEXTO_TABELA = colors.HexColor("#222222")
ZEBRA_FUNDO = colors.HexColor("#f7f7f7")

REGIME_POLITICA = "Política de Investimentos"
RODAPE_NAO_ELEGIVEIS = "(*) Não Elegíveis desde maio/2026, (**) Não elegível desde maio/2025."

SEGMENTOS_AGREGADOS = [
    "Renda Fixa",
    "Renda Variável",
    "Imobiliário",
    "Estruturado",
    "Operações com Participantes",
    "Exterior",
]
SEGMENTOS_EMISSORES = {"Emissores (Art. 27)", "Emissores (Art. 28)"}

ORDEM_REGRAS_POLITICA = [
    "Renda Fixa",
    "Títulos da dívida pública mobiliária federal",
    "Cotas de classes de ETF de RF composto exclusivamente por títulos públicos",
    "Ativos financeiros RF de instituições financeiras autorizadas pelo Bacen",
    "Ativos financeiros RF de sociedade por ações cap aberto e cias securitizadoras",
    "Cotas de classes de ETF de RF",
    "Títulos das dívidas públicas mobiliárias estaduais e municipais",
    "Obrigações de organismos multilaterais emitidas no País",
    "Ativos financeiros RF de inst. financeiras não bancárias e cooperativas de crédito",
    "Debêntures Incentivadas - Lei 12.431 e Debêntures de Infraestrutura - Lei 14.801",
    "Cotas de classe FIDC e cotas de classes de cotas de FIDCs, CCBs e CCCBs",
    "CPRs, CRAs, CDCAs e Was",
    "Demais ativos",
    "Renda Variável",
    "Ações e cotas de classes de fundos de índice segmento especial",
    "Ações e cotas de classe de fundos de índice segmento não especial",
    "Brazilian Depositary Receipts (BDR) e ETF internacional",
    "Certificado de Ouro físico padrão negociado em bolsa de mercadorias e de futuros",
    "Estruturado",
    "Cotas de classes Fundos de Investimento em Participações - FIP",
    "Cotas de classes Fundos de Invest. nas Cadeias Produtivas Agroindustriais - FIAGRO",
    "Certificado de Operações Estruturadas - COE",
    "Cotas de classes de fundos de investimento \"Ações - Mercado de Acesso\"",
    "Cotas de classes de Fundos tipificadas como Multimercado",
    "Créditos de descarbonização – CBIO e Créditos de Carbono",
    "Imobiliário",
    "Cotas de classes Fundo de Invest. Imobiliário (FII) e Cotas de Classes em Cotas de FII",
    "Certificados de recebíveis imobiliários - CRI",
    "Células de crédito imobiliário - CCI",
    "Imóveis",
    "Operações com Participantes",
    "Empréstimo Simples",
    "Financiamento Imobiliário",
    "Exterior",
    "Cotas de classes de fundos e cotas de classe de FICs Renda Fixa - Dívida Externa",
    "Cotas de classes de FI, destinados a investidores qualificados e Offshore",
    "Cotas de classes de FI, destinados a investidores qualificados e ativos no exterior",
    "Cotas de classes de FI, destinados ao público em geral e Offshore",
    "Ativos financeiros no exterior pertencentes às carteiras dos fundos locais",
]

NOMES_PLANOS = {
    "Ceres FlexCeres_CV": "Ceres FlexCeres",
    "Epagri Saldado_BD": "Epagri Saldado",
    "Epagri Básico_BD": "Epagri Básico",
    "Epamig Básico_BD": "Epamig Básico",
    "Embrapa FlexCeres_CV": "Embrapa FlexCeres",
    "ABDI FlexCeres_CD": "ABDI FlexCeres",
    "Cidasc FlexCeres_CV": "Cidasc FlexCeres",
    "Epamig FlexCeres_CV": "Epamig FlexCeres",
    "Emater DF FlexCeres_CV": "EmaterDF FlexCeres",
    "Ceres Básico_BD": "Ceres Básico",
    "Emater MG Básico_BD": "EmaterMG Básico",
    "Família Ceres_CD": "Família Ceres",
    "Epagri FlexCeres_CV": "Epagri FlexCeres",
    "Embrapa Básico_BD": "Embrapa Básico",
    "Emater MG FlexCeres_CV": "EmaterMG FlexCeres",
    "Epamig Saldado_BD": "Epamig Saldado",
    "Emater MG Saldado_BD": "EmaterMG Saldado",
    "PGA": "PGA",
}


@dataclass(frozen=True)
class TableSpec:
    """Configuração declarativa de uma tabela PDF."""

    headers: list[str]
    col_widths: list[float]
    header_aligns: list[str]
    col_aligns: list[str]


@dataclass(frozen=True)
class FontSet:
    """Nomes das fontes registradas, já com fallback para fontes padrão."""

    regular: str = "Helvetica"
    bold: str = "Helvetica-Bold"
    italic_serif: str = "Times-Italic"


# =============================================================================
# FONTES E ESTILOS
# =============================================================================

def _localizar_fonte(*termos_obrigatorios: str) -> Path | None:
    """Procura uma fonte dentro de FONTS_DIR usando termos no nome do arquivo."""
    if not FONTS_DIR.exists():
        return None

    termos = [termo.lower() for termo in termos_obrigatorios]
    for arquivo in list(FONTS_DIR.rglob("*.ttf")) + list(FONTS_DIR.rglob("*.otf")):
        nome = arquivo.name.lower()
        if all(termo in nome for termo in termos):
            return arquivo
    return None


def _registrar_fonte(nome_pdf: str, arquivo: Path | None) -> str | None:
    """Registra uma fonte no ReportLab e retorna o nome usado no PDF."""
    if arquivo is None or not arquivo.exists():
        return None
    try:
        pdfmetrics.registerFont(TTFont(nome_pdf, str(arquivo)))
        return nome_pdf
    except Exception as exc:
        warnings.warn(f"Não foi possível registrar a fonte {nome_pdf}: {exc}", RuntimeWarning, stacklevel=2)
        return None


def registrar_fontes() -> FontSet:
    """
    Registra as fontes do projeto, mas nunca quebra a geração do PDF.

    Se as fontes oficiais não existirem no ambiente, Helvetica/Times são usadas.
    """
    figtree_regular = _localizar_fonte("figtree", "regular") or _localizar_fonte("figtree")
    figtree_bold = _localizar_fonte("figtree", "bold") or _localizar_fonte("figtree", "semibold") or figtree_regular
    source_serif = (
        _localizar_fonte("source", "serif", "italic")
        or _localizar_fonte("sourceserif", "italic")
        or _localizar_fonte("source", "serif")
    )

    regular = _registrar_fonte("Figtree", figtree_regular) or "Helvetica"
    bold = _registrar_fonte("Figtree-Bold", figtree_bold) or "Helvetica-Bold"
    italic_serif = _registrar_fonte("SourceSerif-Italic", source_serif) or "Times-Italic"

    if regular == "Figtree" and bold == "Figtree-Bold":
        pdfmetrics.registerFontFamily("Figtree", normal=regular, bold=bold, italic=regular, boldItalic=bold)

    return FontSet(regular=regular, bold=bold, italic_serif=italic_serif)


FONTES = registrar_fontes()


def criar_estilos():
    """Cria todos os estilos usados pelos relatórios em um único lugar."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "Titulo",
        fontName=FONTES.bold,
        fontSize=16,
        textColor=VERDE_TITULO,
        spaceAfter=0,
        spaceBefore=8 * mm,
        leading=19,
    ))
    styles.add(ParagraphStyle(
        "TituloPrincipal",
        parent=styles["Title"],
        fontName=FONTES.bold,
        fontSize=25,
        leading=30,
        textColor=VERDE_TITULO,
        alignment=TA_CENTER,
        spaceAfter=0,
    ))
    styles.add(ParagraphStyle(
        "Subtitulo",
        fontName=FONTES.bold,
        fontSize=11.5,
        textColor=VERDE_TITULO,
        spaceBefore=2 * mm,
        spaceAfter=1.5 * mm,
        leading=14,
    ))
    styles.add(ParagraphStyle("SubtituloCentro", parent=styles["Subtitulo"], alignment=TA_CENTER))
    styles.add(ParagraphStyle(
        "TituloSecao",
        parent=styles["Heading2"],
        fontName=FONTES.bold,
        fontSize=14,
        leading=18,
        textColor=VERDE_TITULO,
        spaceBefore=4,
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        "NomePlano",
        fontName=FONTES.italic_serif,
        fontSize=10.5,
        textColor=VERDE_TITULO,
        spaceBefore=0,
        spaceAfter=1.5 * mm,
        leading=13,
    ))
    styles.add(ParagraphStyle(
        "CorpoTexto",
        fontName=FONTES.regular,
        fontSize=9.5,
        leading=12,
        spaceAfter=1.5 * mm,
        textColor=TEXTO_PADRAO,
    ))
    styles.add(ParagraphStyle(
        "TextoNormal",
        parent=styles["BodyText"],
        fontName=FONTES.regular,
        fontSize=9.5,
        leading=13.5,
        textColor=TEXTO_PADRAO,
        alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        "RodaPe",
        fontName=FONTES.italic_serif,
        fontSize=7,
        leading=9,
        spaceAfter=1.5 * mm,
        textColor=TEXTO_PADRAO,
        leftIndent=1 * mm,
    ))
    styles.add(ParagraphStyle(
        "DataPos",
        fontName=FONTES.regular,
        fontSize=9,
        alignment=TA_RIGHT,
        textColor=VERDE_TITULO,
    ))

    # Estilos de célula: os nomes são usados em TableSpec.
    styles.add(ParagraphStyle(
        "ThCell",
        fontName=FONTES.bold,
        fontSize=6.8,
        leading=8.2,
        textColor=VERDE_CLARO,
        alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle("ThCellRight", parent=styles["ThCell"], alignment=TA_RIGHT))
    styles.add(ParagraphStyle("ThCellCenter", parent=styles["ThCell"], alignment=TA_CENTER))
    styles.add(ParagraphStyle(
        "TdCell",
        fontName=FONTES.regular,
        fontSize=6.8,
        leading=8.2,
        textColor=TEXTO_TABELA,
        alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle("TdCellRight", parent=styles["TdCell"], alignment=TA_RIGHT))
    styles.add(ParagraphStyle("TdCellCenter", parent=styles["TdCell"], alignment=TA_CENTER))
    return styles


# =============================================================================
# HELPERS GENÉRICOS
# =============================================================================

def _is_politica(regime: str) -> bool:
    return regime == REGIME_POLITICA


def _date_to_br(data: Any) -> str:
    """Converte datas para dd/mm/aaaa sem exigir um tipo específico."""
    if hasattr(data, "strftime"):
        return data.strftime("%d/%m/%Y")
    return str(data)


def _safe_text(valor: Any, default: str = "—") -> str:
    """Texto seguro para células do ReportLab."""
    return default if pd.isna(valor) else str(valor)


def _p(texto: Any, style) -> Paragraph:
    """Atalho para criar Paragraphs com tratamento de nulos."""
    return Paragraph(_safe_text(texto), style)


def _nome_plano(valor_original: Any) -> str:
    """Remove prefixos internos e aplica o nome amigável do plano."""
    if pd.isna(valor_original):
        return ""

    texto = str(valor_original).strip()
    if texto.upper() in {"[CERES TOTAL]", "CERES TOTAL"}:
        return "Consolidado"

    texto = texto.replace("[", "").replace("]", "").strip()
    chave = texto.split("=", 1)[-1] if "=" in texto else texto
    return NOMES_PLANOS.get(chave, chave)


def _formatar_numero(valor: Any, prefixo: str = "", sufixo: str = "", casas: int = 2) -> str:
    """Formata número com prefixo/sufixo e fallback para hífen."""
    try:
        return f"{prefixo}{fmt_br(valor, casas)}{sufixo}"
    except Exception:
        return "-"


def _formatar_valor_por_coluna(valor: Any, coluna: str) -> str:
    """Escolhe formatação monetária, percentual ou textual a partir do nome da coluna."""
    if pd.isna(valor):
        return "—"

    col = str(coluna).upper()
    if any(marcador in col for marcador in ["R$", "PATRIM", "EXPOSI"]):
        return fmt_br(valor)
    if any(marcador in col for marcador in ["%", "PERC"]):
        return formatar_percentual_br(valor)
    return str(valor)


def _cor_svg(cor: colors.Color) -> str:
    """Converte cor do ReportLab para hexadecimal válido em SVG."""
    valor = cor.hexval()
    if isinstance(valor, str):
        valor = valor.lower()
        if valor.startswith("0x"):
            return "#" + valor.replace("0x", "").zfill(6)
        if valor.startswith("#"):
            return valor
        return "#" + valor.zfill(6)
    return f"#{int(valor):06x}"


def _resolve_asset_path(relative_path: Path) -> Path | None:
    """Localiza assets procurando no diretório atual, no módulo e nos pais."""
    for base in [Path.cwd(), BASE_DIR, *BASE_DIR.parents]:
        path = base / relative_path
        if path.exists():
            return path
    return None


# =============================================================================
# DOCUMENTO, FUNDO E LOGO
# =============================================================================

def _criar_documento(buffer: BytesIO, title: str | None = None) -> SimpleDocTemplate:
    """Factory padrão dos documentos em A4 paisagem."""
    return SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=1 * cm,
        rightMargin=1 * cm,
        topMargin=1 * cm,
        bottomMargin=1 * cm,
        title=title,
    )


def _page_width(margem_extra: float = 2.4 * cm) -> float:
    """Largura útil usada para calcular colunas."""
    return landscape(A4)[0] - margem_extra


def _desenhar_logo(canvas, doc, logo_path: Path | None = None, *, compacta: bool = True) -> None:
    """Desenha o logo, sem falhar caso o arquivo esteja ausente ou inválido."""
    path = logo_path or _resolve_asset_path(LOGO_RELATIVE_PATH)
    if path is None:
        return

    logo_width = 22 if compacta else 3.2 * cm
    logo_height = 22 if compacta else 0.9 * cm
    x = doc.pagesize[0] - logo_width - 1.2 * cm
    y = doc.pagesize[1] - logo_height - 1.2 * cm

    try:
        if path.suffix.lower() == ".svg":
            drawing = svg2rlg(str(path))
            if drawing and drawing.width and drawing.height:
                drawing.scale(logo_width / drawing.width, logo_height / drawing.height)
                drawing.drawOn(canvas, x, y)
        else:
            canvas.drawImage(ImageReader(str(path)), x, y, width=logo_width, height=logo_height)
    except Exception as exc:
        warnings.warn(f"Erro ao carregar logo: {exc}", RuntimeWarning, stacklevel=2)


def _fundo_pagina(canvas, doc) -> None:
    """Fundo padrão dos relatórios de enquadramento e limites operacionais."""
    canvas.saveState()
    canvas.setFillColor(FUNDO_PAGINA)
    canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], stroke=0, fill=1)
    if doc.page == 1:
        _desenhar_logo(canvas, doc)
    canvas.restoreState()


def _fundo_com_rodape_risco(canvas, doc) -> None:
    """Fundo e rodapé específicos do relatório de risco dos planos."""
    largura, altura = landscape(A4)
    canvas.saveState()
    canvas.setFillColor(FUNDO_PAGINA)
    canvas.rect(0, 0, largura, altura, stroke=0, fill=1)
    canvas.setFont(FONTES.regular, 7)
    canvas.setFillColor(TEXTO_PADRAO)
    canvas.drawCentredString(largura / 2, 0.75 * cm, f"Relatório de Risco de Mercado - Planos | Página {doc.page}")
    canvas.restoreState()


def _add_linha_horizontal(
    elements: list,
    *,
    width: str = "100%",
    thickness: float = 0.4,
    space_after: float = 4 * mm,
    space_before: float = 1 * mm,
) -> None:
    """Adiciona separador horizontal com a identidade visual do relatório."""
    elements.append(HRFlowable(width=width, thickness=thickness, color=VERDE_ESCURO, spaceAfter=space_after, spaceBefore=space_before))


# =============================================================================
# FLOWABLES REUTILIZÁVEIS
# =============================================================================

class RoundedTableFlowable(Flowable):
    """
    Tabela com borda arredondada.

    Esta classe encapsula a Table do ReportLab para manter cantos arredondados,
    fundo e borda consistentes, inclusive quando a tabela é quebrada entre páginas.
    """

    def __init__(
        self,
        table: Table,
        width: float | None = None,
        radius: float = 6,
        stroke_color=None,
        fill_color=None,
        stroke_width: float = 0.75,
        padding: float = 0,
        h_align: str = "LEFT",
        header_color=None,
    ):
        super().__init__()
        self.table = table
        self.width = width
        self.radius = radius
        self.stroke_color = stroke_color or CINZA_BORDA
        self.fill_color = fill_color
        self.stroke_width = stroke_width
        self.padding = padding
        self.h_align = h_align
        self.header_color = header_color
        self._avail_width = width or 0
        self._table_width = width or 0
        self._table_height = 0

    def wrap(self, avail_width, avail_height):
        self._avail_width = avail_width
        table_width, table_height = self.table.wrapOn(self.canv, self.width or avail_width, avail_height)
        self._table_width = table_width
        self._table_height = table_height
        return avail_width if self.h_align in {"CENTER", "RIGHT"} else table_width, table_height + self.padding * 2

    def split(self, avail_width, avail_height):
        partes = self.table.split(self.width or avail_width, max(avail_height - self.padding * 2, 1))
        return [
            RoundedTableFlowable(
                table=parte,
                width=self.width,
                radius=self.radius,
                stroke_color=self.stroke_color,
                fill_color=self.fill_color,
                stroke_width=self.stroke_width,
                padding=self.padding,
                h_align=self.h_align,
                header_color=self.header_color,
            )
            for parte in partes
        ]

    def draw(self):
        if self.h_align == "CENTER":
            x = max((self._avail_width - self._table_width) / 2, 0)
        elif self.h_align == "RIGHT":
            x = max(self._avail_width - self._table_width, 0)
        else:
            x = 0
        y = self.padding

        self.canv.saveState()

        # Primeiro, desenha um fundo arredondado opcional.
        if self.fill_color is not None:
            self.canv.setFillColor(self.fill_color)
            self.canv.roundRect(x, y, self._table_width, self._table_height, self.radius, stroke=0, fill=1)

        # Clip arredondado garante que a tabela respeite os cantos arredondados.
        clip = self.canv.beginPath()
        clip.roundRect(x, y, self._table_width, self._table_height, self.radius)
        self.canv.clipPath(clip, stroke=0, fill=0)

        if self.header_color is not None:
            row_heights = self.table._rowHeights or []
            header_height = row_heights[0] if row_heights and row_heights[0] is not None else 22
            self.canv.setFillColor(self.header_color)
            self.canv.rect(x, y + self._table_height - header_height, self._table_width, header_height, stroke=0, fill=1)

        self.table.drawOn(self.canv, x, y)
        self.canv.restoreState()

        self.canv.saveState()
        self.canv.setStrokeColor(self.stroke_color)
        self.canv.setLineWidth(self.stroke_width)
        self.canv.roundRect(x, y, self._table_width, self._table_height, self.radius, stroke=1, fill=0)
        self.canv.restoreState()


class SvgFlowable(Flowable):
    """Renderiza texto SVG como Flowable do ReportLab."""

    def __init__(self, svg_text: str, width: float, height: float, h_align: str = "CENTER"):
        super().__init__()
        self.svg_text = svg_text
        self.width = width
        self.height = height
        self.h_align = h_align
        self._avail_width = width
        self.drawing = svg2rlg(BytesIO(svg_text.encode("utf-8")))
        self._scale_drawing()

    def _scale_drawing(self) -> None:
        if not self.drawing:
            return
        scale = min(self.width / self.drawing.width, self.height / self.drawing.height)
        self.drawing.scale(scale, scale)
        self.drawing.width *= scale
        self.drawing.height *= scale

    def wrap(self, avail_width, avail_height):
        self._avail_width = avail_width
        return avail_width, self.height

    def draw(self):
        if not self.drawing:
            return
        if self.h_align == "CENTER":
            x = max((self._avail_width - self.drawing.width) / 2, 0)
        elif self.h_align == "RIGHT":
            x = max(self._avail_width - self.drawing.width, 0)
        else:
            x = 0
        y = max((self.height - self.drawing.height) / 2, 0)
        renderPDF.draw(self.drawing, self.canv, x, y)


def svg_arquivo_para_flowable(path: Path, width: float, height: float, h_align: str = "CENTER"):
    """Carrega SVG de arquivo; se não existir, reserva o espaço com Spacer."""
    if not path.exists():
        return Spacer(width, height)
    return SvgFlowable(svg_text=path.read_text(encoding="utf-8"), width=width, height=height, h_align=h_align)


# =============================================================================
# TABELAS PADRONIZADAS
# =============================================================================

def _center_table_spec(headers: list[str], widths: list[float], *, first_left: bool = True) -> TableSpec:
    """Cria TableSpec com alinhamento central, mantendo primeira coluna à esquerda."""
    aligns = ["CENTER"] * len(headers)
    header_aligns = ["ThCellCenter"] * len(headers)
    if first_left and headers:
        aligns[0] = "LEFT"
        header_aligns[0] = "ThCell"
    return TableSpec(headers, widths, header_aligns, aligns)


def _construir_tabela(
    headers_text: Sequence[str],
    rows_para: Sequence[Sequence[Paragraph]],
    col_widths: Sequence[float],
    linhas_desenquadradas: Iterable[int],
    styles,
    header_aligns: Sequence[str] | None = None,
    col_aligns: Sequence[str] | None = None,
) -> RoundedTableFlowable:
    """Monta tabela padrão dos relatórios de enquadramento/limites."""
    header_aligns = list(header_aligns or ["ThCell"] * len(headers_text))
    col_aligns = list(col_aligns or [])
    linhas_desenquadradas = set(linhas_desenquadradas or set())

    header_row = [_p(header, styles[style_name]) for header, style_name in zip(headers_text, header_aligns)]
    data = [header_row] + list(rows_para)
    tabela = Table(data, colWidths=list(col_widths), repeatRows=1)

    comandos = [
        ("BACKGROUND", (0, 0), (-1, 0), VERDE_TITULO),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, 0), 1.5, VERDE_BORDA),
        ("LINEBELOW", (0, 1), (-1, -1), 0.5, CINZA_BORDA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]

    for col_idx, align in enumerate(col_aligns):
        comandos.append(("ALIGN", (col_idx, 0), (col_idx, -1), align))

    # +1 porque a linha 0 é o cabeçalho.
    desenq_rows = {idx + 1 for idx in linhas_desenquadradas}
    for row_idx in range(2, len(data), 2):
        if row_idx not in desenq_rows:
            comandos.append(("BACKGROUND", (0, row_idx), (-1, row_idx), ZEBRA_FUNDO))
    for idx in linhas_desenquadradas:
        comandos.append(("BACKGROUND", (0, idx + 1), (-1, idx + 1), VERMELHO_FUNDO))

    tabela.setStyle(TableStyle(comandos))
    return RoundedTableFlowable(tabela, radius=6, stroke_color=CINZA_BORDA, header_color=VERDE_ESCURO)


# =============================================================================
# RELATÓRIO DE ENQUADRAMENTO DIÁRIO
# =============================================================================

def _limpar_texto_descricao(texto: Any) -> str:
    """Remove prefixo técnico das descrições que contêm 'Art.'."""
    texto = "" if pd.isna(texto) else str(texto)
    return texto[8:] if "Art." in texto else texto


def _remove_grp(valor: Any) -> str:
    """Remove prefixo de grupo econômico quando a origem vem no formato chave=valor."""
    if pd.isna(valor):
        return "—"
    texto = str(valor)
    return texto.split("=")[-1] if "grupo" in texto.lower() else texto


def _is_desenquadrado(status: Any) -> bool:
    return str(status).strip().upper() == "DESENQUADRADO"


def _status_rows(df: pd.DataFrame) -> set[int]:
    """Retorna índices das linhas que devem ser destacadas em vermelho."""
    return {i for i, (_, row) in enumerate(df.iterrows()) if _is_desenquadrado(row.get("STATUS"))}


def _filtrar_plano(df: pd.DataFrame, plano_selecionado: str, regime: str) -> pd.DataFrame:
    """Filtra o DataFrame para o plano e regime informados."""
    return df[(df["ESTRUTURA_ASSOCIADA"] == plano_selecionado) & (df["CONJUNTO"] == regime)].copy()


def _segmentos_ordenados(df_plano: pd.DataFrame) -> list[str]:
    """Ordena segmentos, priorizando a ordem de apresentação oficial."""
    segmentos = list(df_plano["SEGMENTO"].dropna().unique())
    ordem = {segmento: i for i, segmento in enumerate(SEGMENTOS_AGREGADOS)}
    return sorted(segmentos, key=lambda segmento: ordem.get(segmento, len(ordem)))


def _preparar_segmento(df_plano: pd.DataFrame, segmento: str, regime: str) -> pd.DataFrame:
    """Aplica regras de limpeza, ordenação e grupo econômico para um segmento."""
    df_seg = df_plano[df_plano["SEGMENTO"] == segmento].copy().sort_values(by="ORDEM")
    df_seg["DESCRICAO"] = df_seg["DESCRICAO"].apply(_limpar_texto_descricao)

    if _is_politica(regime):
        # Na política, a linha agregadora do próprio segmento aparece em tabela separada.
        df_seg = df_seg[df_seg["DESCRICAO"] != segmento].copy()
        if segmento not in SEGMENTOS_EMISSORES:
            df_seg["DESCRICAO"] = pd.Categorical(df_seg["DESCRICAO"], categories=ORDEM_REGRAS_POLITICA, ordered=True)
            df_seg = df_seg.sort_values(by="DESCRICAO")

    if segmento in SEGMENTOS_EMISSORES:
        df_seg["GRP_ECONOMICO"] = df_seg["AGREGACAO"].apply(_remove_grp)

    return df_seg


def _normal_spec(page_w: float, regime: str) -> TableSpec:
    headers = ["Descrição", "Limite %", "Limite R$", "Posição R$", "Limite Utilizado %", "Status"]
    weights = [0.30, 0.14, 0.14, 0.14, 0.14, 0.14] if _is_politica(regime) else [0.25, 0.15, 0.15, 0.15, 0.15, 0.15]
    return _center_table_spec(headers, [page_w * weight for weight in weights])


def _emissor_spec(page_w: float, regime: str) -> TableSpec:
    if _is_politica(regime):
        headers = ["Descrição", "Grupo Econômico", "Limite %", "Limite R$", "Posição R$", "Limite Utilizado %", "Status"]
        weights = [0.22, 0.15, 0.12, 0.12, 0.12, 0.12, 0.15]
    else:
        headers = ["Descrição", "Grupo Econômico", "Limite R$", "Posição R$", "Limite Utilizado %", "Status"]
        weights = [0.20, 0.15, 0.15, 0.15, 0.15, 0.20]
    return _center_table_spec(headers, [page_w * weight for weight in weights])


def _agregado_spec(page_w: float) -> TableSpec:
    headers = ["Segmento de Aplicação", "Limite %", "Limite R$", "Posição %", "Posição R$", "Limite Utilizado %", "Status"]
    weights = [0.22, 0.12, 0.13, 0.13, 0.13, 0.13, 0.14]
    return _center_table_spec(headers, [page_w * weight for weight in weights])


def _rows_agregado(df_agregado: pd.DataFrame, styles) -> list[list[Paragraph]]:
    return [[
        _p(row["DESCRICAO"], styles["TdCell"]),
        _p(formatar_percentual_br(row["LIMITE_PERCENTUAL"]), styles["TdCellCenter"]),
        _p(fmt_br(row["VALOR_LIMITE_REGRA"]), styles["TdCellCenter"]),
        _p(formatar_percentual_br(row["PCT_ATUAL"]), styles["TdCellCenter"]),
        _p(fmt_br(row["VALOR_ATUAL"]), styles["TdCellCenter"]),
        _p(formatar_percentual_br(row["PERCENTUAL_UTILIZADO"]), styles["TdCellCenter"]),
        _p(row["STATUS"], styles["TdCellCenter"]),
    ] for _, row in df_agregado.iterrows()]


def _add_tabela_agregada(elements: list, df_plano: pd.DataFrame, styles, page_w: float) -> None:
    """Adiciona a tabela agregada de segmentos, exibida apenas para Política."""
    elements.append(Paragraph("Limites de Alocação e Concentração", styles["SubtituloCentro"]))

    df_agregado = df_plano[df_plano["DESCRICAO"].isin(SEGMENTOS_AGREGADOS)].copy()
    df_agregado["DESCRICAO"] = pd.Categorical(df_agregado["DESCRICAO"], categories=SEGMENTOS_AGREGADOS, ordered=True)
    df_agregado = df_agregado.sort_values("DESCRICAO")

    referencia = df_agregado["VALOR_REFERENCIA"].replace(0, pd.NA)
    df_agregado["PCT_ATUAL"] = ((df_agregado["VALOR_ATUAL"] / referencia) * 100).fillna(0)

    rows = _rows_agregado(df_agregado, styles)
    rows.append([
        _p("Total de Recursos Garantidores", styles["TdCell"]),
        _p("-", styles["TdCellCenter"]),
        _p("-", styles["TdCellCenter"]),
        _p(formatar_percentual_br(df_agregado["PCT_ATUAL"].sum()), styles["TdCellCenter"]),
        _p(fmt_br(df_agregado["VALOR_ATUAL"].sum()), styles["TdCellCenter"]),
        _p("-", styles["TdCellCenter"]),
        _p("-", styles["TdCellCenter"]),
    ])

    spec = _agregado_spec(page_w)
    elements.append(_construir_tabela(spec.headers, rows, spec.col_widths, _status_rows(df_agregado), styles, spec.header_aligns, spec.col_aligns))
    _add_linha_horizontal(elements, width="60%", thickness=0.05, space_after=4 * mm, space_before=8 * mm)


def _rows_segmento_normal(df_seg: pd.DataFrame, styles) -> list[list[Paragraph]]:
    return [[
        _p(row["DESCRICAO"], styles["TdCell"]),
        _p(formatar_percentual_br(row["LIMITE_PERCENTUAL"]), styles["TdCellCenter"]),
        _p(fmt_br(row["VALOR_LIMITE_REGRA"]), styles["TdCellCenter"]),
        _p(fmt_br(row["VALOR_ATUAL"]), styles["TdCellCenter"]),
        _p(formatar_percentual_br(row["PERCENTUAL_UTILIZADO"]), styles["TdCellCenter"]),
        _p(row["STATUS"], styles["TdCellCenter"]),
    ] for _, row in df_seg.iterrows()]


def _rows_segmento_emissor(df_seg: pd.DataFrame, styles, regime: str) -> list[list[Paragraph]]:
    """Monta linhas de emissores, ocultando descrições repetidas visualmente."""
    rows: list[list[Paragraph]] = []
    prev_desc = None

    for _, row in df_seg.iterrows():
        desc = row["DESCRICAO"]
        show_desc = desc if desc != prev_desc else ""
        prev_desc = desc

        cells = [_p(show_desc, styles["TdCell"]), _p(row["GRP_ECONOMICO"], styles["TdCell"])]
        if _is_politica(regime):
            cells.append(_p(formatar_percentual_br(row["LIMITE_PERCENTUAL"]), styles["TdCellCenter"]))

        cells.extend([
            _p(fmt_br(row["VALOR_LIMITE_REGRA"]), styles["TdCellCenter"]),
            _p(fmt_br(row["VALOR_ATUAL"]), styles["TdCellCenter"]),
            _p(formatar_percentual_br(row["PERCENTUAL_UTILIZADO"]), styles["TdCellCenter"]),
            _p(row["STATUS"], styles["TdCellCenter"]),
        ])
        rows.append(cells)

    return rows


def _add_segmento(elements: list, df_plano: pd.DataFrame, segmento: str, regime: str, styles, page_w: float) -> None:
    """Adiciona título e tabela de um segmento ao relatório."""
    df_seg = _preparar_segmento(df_plano, segmento, regime)
    elements.append(Paragraph(segmento, styles["Subtitulo"]))

    if segmento in SEGMENTOS_EMISSORES:
        spec = _emissor_spec(page_w, regime)
        rows = _rows_segmento_emissor(df_seg, styles, regime)
    else:
        spec = _normal_spec(page_w, regime)
        rows = _rows_segmento_normal(df_seg, styles)

    elements.append(_construir_tabela(spec.headers, rows, spec.col_widths, _status_rows(df_seg), styles, spec.header_aligns, spec.col_aligns))
    elements.append(Spacer(1, 4 * mm))


def gerar_pdf(df: pd.DataFrame, plano_selecionado: str, data_posicao: Any, regime: str) -> bytes:
    """
    Gera o PDF do Relatório de Enquadramento Diário.

    Parâmetros esperados no DataFrame incluem, entre outros:
    ESTRUTURA_ASSOCIADA, CONJUNTO, SEGMENTO, DESCRICAO, ORDEM, STATUS,
    LIMITE_PERCENTUAL, VALOR_LIMITE_REGRA, VALOR_ATUAL e PERCENTUAL_UTILIZADO.
    """
    buffer = BytesIO()
    styles = criar_estilos()
    page_w = _page_width()
    nome_plano = _nome_plano(plano_selecionado)
    doc = _criar_documento(buffer, title=f"Enquadramento - {nome_plano}")

    elements = [
        Paragraph("Enquadramento Diário - Fundação Ceres", styles["Titulo"]),
        Paragraph(f"Plano: {nome_plano}", styles["NomePlano"]),
        Paragraph(f"Data de posição: {_date_to_br(data_posicao)}", styles["DataPos"]),
        Spacer(1, 3 * mm),
        Paragraph(f"O Relatório verifica a aderência dos investimentos à <b>{regime}</b>.", styles["CorpoTexto"]),
    ]
    _add_linha_horizontal(elements)

    df_plano = _filtrar_plano(df, plano_selecionado, regime)
    if _is_politica(regime):
        _add_tabela_agregada(elements, df_plano, styles, page_w)

    for segmento in _segmentos_ordenados(df_plano):
        _add_segmento(elements, df_plano, segmento, regime, styles, page_w)

    doc.build(elements, onFirstPage=_fundo_pagina, onLaterPages=_fundo_pagina)
    return buffer.getvalue()


# =============================================================================
# RELATÓRIO DE LIMITES OPERACIONAIS
# =============================================================================

from io import BytesIO
from typing import Any

import numpy as np
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def _valor_ou_zero(valor: Any) -> Any:
    """
    Converte valores ausentes ou infinitos em zero.

    Preserva strings válidas, datas e demais valores não numéricos.
    """
    if valor is None:
        return 0

    try:
        ausente = pd.isna(valor)

        # Evita erro quando pd.isna retorna array ou lista.
        if isinstance(ausente, (bool, np.bool_)) and ausente:
            return 0
    except (TypeError, ValueError):
        pass

    if isinstance(valor, (int, float, np.number)):
        try:
            if not np.isfinite(valor):
                return 0
        except TypeError:
            pass

    return valor


def _fmt_br_zero(valor: Any) -> str:
    """
    Formata valores financeiros, exibindo ausentes como zero.
    """
    return fmt_br(_valor_ou_zero(valor))


def _formatar_valor_seguro(
    valor: Any,
    coluna: str,
) -> str:
    """
    Formata valores da tabela de risco sem exibir NaN.
    """
    valor = _valor_ou_zero(valor)

    resultado = _formatar_valor_por_coluna(
        valor,
        coluna,
    )

    if resultado is None:
        return "0"

    texto = str(resultado).strip()

    if texto.lower() in {
        "nan",
        "nat",
        "none",
        "inf",
        "-inf",
    }:
        return "0"

    return texto


def _ajustar_estilos_tabelas(
    styles: dict,
) -> None:
    """
    Aumenta o tamanho da fonte e a entrelinha das tabelas.

    Os estilos são alterados diretamente no dicionário
    retornado por criar_estilos().
    """
    estilos_cabecalho = (
        "ThCell",
        "ThCellRight",
        "ThCellCenter",
    )

    estilos_conteudo = (
        "TdCell",
        "TdCellRight",
        "TdCellCenter",
    )

    for nome_estilo in estilos_cabecalho:
        if nome_estilo not in styles:
            continue

        styles[nome_estilo].fontSize = 11
        styles[nome_estilo].leading = 14
        styles[nome_estilo].spaceBefore = 0
        styles[nome_estilo].spaceAfter = 0

    for nome_estilo in estilos_conteudo:
        if nome_estilo not in styles:
            continue

        styles[nome_estilo].fontSize = 11
        styles[nome_estilo].leading = 15
        styles[nome_estilo].spaceBefore = 0
        styles[nome_estilo].spaceAfter = 0


def _limites_spec(
    page_w: float,
) -> TableSpec:
    headers = [
        "Instituição Financeira",
        "Posição R$",
        "Posição 2026 R$",
        "Alocação 2026 R$",
        "Disp. Alocação R$",
    ]

    # Primeira coluna reduzida.
    # O espaço restante é distribuído entre
    # as quatro colunas financeiras.
    col_widths = [
        page_w * 0.28,
        page_w * 0.17,
        page_w * 0.18,
        page_w * 0.18,
        page_w * 0.19,
    ]

    return TableSpec(
        headers=headers,
        col_widths=col_widths,
        header_aligns=[
            "ThCell",
            "ThCellRight",
            "ThCellRight",
            "ThCellRight",
            "ThCellRight",
        ],
        col_aligns=[
            "LEFT",
            "RIGHT",
            "RIGHT",
            "RIGHT",
            "RIGHT",
        ],
    )


def _risco_spec(
    df: pd.DataFrame,
    page_w: float,
) -> TableSpec:
    cols = list(df.columns)
    n = len(cols)

    if n <= 1:
        return TableSpec(
            headers=cols,
            col_widths=[page_w],
            header_aligns=["ThCell"],
            col_aligns=["LEFT"],
        )

    # Primeira coluna reduzida.
    primeira_coluna = page_w * 0.24

    demais_colunas = (
        page_w - primeira_coluna
    ) / (n - 1)

    return TableSpec(
        headers=cols,
        col_widths=[
            primeira_coluna,
            *(
                [demais_colunas]
                * (n - 1)
            ),
        ],
        header_aligns=[
            "ThCell",
            *(
                ["ThCellCenter"]
                * (n - 1)
            ),
        ],
        col_aligns=[
            "LEFT",
            *(
                ["CENTER"]
                * (n - 1)
            ),
        ],
    )


def _criar_bloco_resumo(
    items: list[tuple[str, Any]],
    page_w: float,
    styles: dict,
) -> Table | None:
    """
    Cria cards horizontais para os indicadores do relatório.

    Indicadores não informados não são exibidos.
    """
    items_validos = [
        (
            label,
            _valor_ou_zero(valor),
        )
        for label, valor in items
        if valor is not None
    ]

    if not items_validos:
        return None

    celulas = []

    for label, valor in items_validos:
        conteudo = Paragraph(
            (
                '<font size="10" color="#667085">'
                f"{label.upper()}"
                "</font>"
                "<br/>"
                '<font size="15">'
                f"<b>{_fmt_br_zero(valor)}</b>"
                "</font>"
            ),
            styles["CorpoTexto"],
        )

        celulas.append(conteudo)

    largura = page_w / len(celulas)

    tabela = Table(
        [celulas],
        colWidths=[
            largura
        ] * len(celulas),
        hAlign="LEFT",
    )

    tabela.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#F6F8FA"),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#D9E0E7"),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#D9E0E7"),
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    12,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    12,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    14,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    14,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
            ]
        )
    )

    return tabela


def gerar_pdf_limites_operacionais(
    df_limites: pd.DataFrame,
    data_posicao: Any,
    titulo_relatorio: str = "Limites Operacionais -",
    subtitulo_relatorio: str = " Instituições Financeiras",
    disponivel_alocacao_26: Any = None,
    total_exposicao: Any = None,
    total_exposicao_26: Any = None,
    alocado_26: Any = None,
    df_risco: pd.DataFrame | None = None,
) -> bytes:
    """
    Gera o PDF de limites operacionais e, opcionalmente,
    uma página com informações de risco.
    """
    buffer = BytesIO()
    styles = criar_estilos()

    # Aumenta a fonte e a entrelinha das tabelas.
    _ajustar_estilos_tabelas(styles)

    page_w = _page_width()
    doc = _criar_documento(buffer)

    # Cópias defensivas para não alterar
    # os DataFrames recebidos.
    df_limites = df_limites.copy()

    if df_risco is not None:
        df_risco = df_risco.copy()

    titulo = Paragraph(
        (
            f"{titulo_relatorio}"
            f'<font face="{FONTES.italic_serif}">'
            f"<i>{subtitulo_relatorio}</i>"
            "</font>"
        ),
        styles["Titulo"],
    )

    data = Paragraph(
        (
            "Data de posição: "
            f"{_date_to_br(data_posicao)}"
        ),
        styles["DataPos"],
    )

    elements = [
        titulo,
        Spacer(
            1,
            2.5 * mm,
        ),
        data,
        Spacer(
            1,
            5 * mm,
        ),
    ]

    bloco_resumo = _criar_bloco_resumo(
        [
            (
                "Disponível 2026",
                disponivel_alocacao_26,
            ),
            (
                "Alocado 2026",
                alocado_26,
            ),
            (
                "Exposição Geral",
                total_exposicao,
            ),
            (
                "Exposição 2026",
                total_exposicao_26,
            ),
        ],
        page_w,
        styles,
    )

    if bloco_resumo is not None:
        elements.extend(
            [
                bloco_resumo,
                Spacer(
                    1,
                    7 * mm,
                ),
            ]
        )

    spec_lim = _limites_spec(
        page_w
    )

    rows_lim = []

    for _, row in df_limites.iterrows():
        instituicao = _valor_ou_zero(
            row.get(
                "INSTITUICAO_FINANCEIRA"
            )
        )

        # Para a coluna textual, zero
        # é apresentado como texto.
        if instituicao == 0:
            instituicao = "0"

        rows_lim.append(
            [
                _p(
                    instituicao,
                    styles["TdCell"],
                ),
                _p(
                    _fmt_br_zero(
                        row.get(
                            "EXPOSICAO"
                        )
                    ),
                    styles["TdCellRight"],
                ),
                _p(
                    _fmt_br_zero(
                        row.get(
                            "EXPOSICAO_2026"
                        )
                    ),
                    styles["TdCellRight"],
                ),
                _p(
                    _fmt_br_zero(
                        row.get(
                            "FINANCEIRO_AQUISICAO"
                        )
                    ),
                    styles["TdCellRight"],
                ),
                _p(
                    _fmt_br_zero(
                        row.get(
                            "LIMITE_ALOCACAO_2026"
                        )
                    ),
                    styles["TdCellRight"],
                ),
            ]
        )

    tabela_limites = _construir_tabela(
        spec_lim.headers,
        rows_lim,
        spec_lim.col_widths,
        set(),
        styles,
        spec_lim.header_aligns,
        spec_lim.col_aligns,
    )

    elements.extend(
        [
            KeepTogether(
                [
                    Paragraph(
                        "Limites Operacionais",
                        styles["Subtitulo"],
                    ),
                    Spacer(
                        1,
                        2 * mm,
                    ),
                ]
            ),
            tabela_limites,
            Spacer(
                1,
                3 * mm,
            ),
            Paragraph(
                RODAPE_NAO_ELEGIVEIS,
                styles["RodaPe"],
            ),
        ]
    )

    if (
        df_risco is not None
        and not df_risco.empty
    ):
        elements.append(
            PageBreak()
        )

        headers_r = list(
            df_risco.columns
        )

        rows_r = []

        for _, row in df_risco.iterrows():
            linha = []

            for idx, coluna in enumerate(
                headers_r
            ):
                estilo = (
                    styles["TdCell"]
                    if idx == 0
                    else styles["TdCellCenter"]
                )

                valor_formatado = (
                    _formatar_valor_seguro(
                        row.get(coluna),
                        coluna,
                    )
                )

                linha.append(
                    _p(
                        valor_formatado,
                        estilo,
                    )
                )

            rows_r.append(linha)

        spec_r = _risco_spec(
            df_risco,
            page_w,
        )

        tabela_risco = _construir_tabela(
            headers_r,
            rows_r,
            spec_r.col_widths,
            set(),
            styles,
            spec_r.header_aligns,
            spec_r.col_aligns,
        )

        elements.extend(
            [
                Paragraph(
                    "Informações de Risco",
                    styles["Subtitulo"],
                ),
                Spacer(
                    1,
                    2 * mm,
                ),
                tabela_risco,
                Spacer(
                    1,
                    3 * mm,
                ),
                Paragraph(
                    RODAPE_NAO_ELEGIVEIS,
                    styles["RodaPe"],
                ),
            ]
        )

    doc.build(
        elements,
        onFirstPage=_fundo_pagina,
        onLaterPages=_fundo_pagina,
    )

    return buffer.getvalue()



# =============================================================================
# RELATÓRIO DE RISCO DE MERCADO DOS PLANOS
# =============================================================================

def preparar_dados_planos(df_planos_original: pd.DataFrame) -> pd.DataFrame:
    """Normaliza nomes de colunas, seleciona campos relevantes e converte datas."""
    df_planos = df_planos_original.copy()
    df_planos.columns = df_planos.columns.str.upper()

    colunas_map = {
        "TESOURARIA": "Planos",
        "POSICAO": "Posição R$",
        "DATA_COTACAO": "DATA_COTACAO",
        "RISCO": "VaR R$",
        "RISCO/POSICAO_%": "VaR %",
        "LIMITE_INTERNO_%": "Lim. Interno %",
        "STATUS_%": "Status %",
        "VARIACAO_POSICAO_STRESS_1": "Stress (+) R$",
        "VARIACAO_POSICAO_STRESS_1/POSICAO_%": "Stress (+) %",
        "VARIACAO_POSICAO_STRESS_2": "Stress (-) R$",
        "VARIACAO_POSICAO_STRESS_2/POSICAO_%": "Stress (-) %",
    }

    colunas_existentes = [col for col in colunas_map if col in df_planos.columns]
    df_planos = df_planos[colunas_existentes].rename(columns=colunas_map)
    df_planos["DATA_COTACAO"] = pd.to_datetime(df_planos["DATA_COTACAO"], errors="coerce")
    df_planos = df_planos.dropna(subset=["DATA_COTACAO"]).copy()
    df_planos["Planos"] = df_planos["Planos"].apply(_nome_plano)
    return df_planos


def filtrar_data(df_planos: pd.DataFrame, data_selecionada: Any = None) -> tuple[pd.DataFrame, Any]:
    """Filtra a base pela data selecionada; se ausente, usa a data mais recente."""
    if data_selecionada is None:
        data_selecionada = df_planos["DATA_COTACAO"].max().date()
    if isinstance(data_selecionada, pd.Timestamp):
        data_selecionada = data_selecionada.date()
    return df_planos[df_planos["DATA_COTACAO"].dt.date == data_selecionada].copy(), data_selecionada


def montar_metricas_consolidadas(df_data: pd.DataFrame) -> list[list[str]]:
    """Calcula métricas agregadas exibidas no topo do relatório de risco."""
    consolidado = df_data[df_data["Planos"] == "Consolidado"].copy()

    posicao = consolidado["Posição R$"].sum() if "Posição R$" in consolidado.columns else 0
    var_rs = consolidado["VaR R$"].sum() if "VaR R$" in consolidado.columns else 0
    var_pct = consolidado["VaR %"].sum() if "VaR %" in consolidado.columns else 0
    stress_mais_delta = consolidado["Stress (+) R$"].sum() if "Stress (+) R$" in consolidado.columns else 0
    stress_menos_delta = consolidado["Stress (-) R$"].sum() if "Stress (-) R$" in consolidado.columns else 0

    excedido = dentro = 0
    if "Status %" in df_data.columns:
        planos = df_data[df_data["Planos"] != "Consolidado"].copy()
        excedido = planos[planos["Status %"] > 100]["Planos"].count()
        dentro = planos[planos["Status %"] <= 100]["Planos"].count()

    return [
        ["Posição", _formatar_numero(posicao, prefixo="R$ ")],
        ["Risco Paramétrico", _formatar_numero(var_rs, prefixo="R$ ")],
        ["Risco Paramétrico %", _formatar_numero(var_pct, sufixo="%")],
        ["Stress (+)", f"{_formatar_numero(posicao, prefixo='R$ ')} | Variação: {_formatar_numero(stress_mais_delta, prefixo='R$ ')}"],
        ["Stress (-)", f"{_formatar_numero(posicao + stress_menos_delta, prefixo='R$ ')} | Variação: {_formatar_numero(stress_menos_delta, prefixo='R$ ')}"],
        ["Status dos Limites VaR", f"{dentro} dentro | {excedido} acima"],
    ]


def _tabela_metricas(metricas: list[list[str]]) -> RoundedTableFlowable:
    """Cria a tabela das métricas consolidadas."""
    dados = [["Métrica", "Valor"]] + metricas
    largura_total = 24.6 * cm
    tabela = Table(dados, colWidths=[6.2 * cm, 18.4 * cm], repeatRows=1)
    tabela.hAlign = "CENTER"
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), VERDE_TITULO),
        ("TEXTCOLOR", (0, 0), (-1, 0), VERDE_CLARO),
        ("FONTNAME", (0, 0), (-1, 0), FONTES.bold),
        ("FONTNAME", (0, 1), (-1, -1), FONTES.regular),
        ("FONTSIZE", (0, 0), (-1, 0), 8.8),
        ("FONTSIZE", (0, 1), (-1, -1), 8.5),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, CINZA_BORDA),
        ("BOX", (0, 0), (-1, -1), 0, FUNDO_PAGINA),
        ("BACKGROUND", (0, 1), (-1, -1), FUNDO_PAGINA),
        ("TEXTCOLOR", (0, 1), (-1, -1), TEXTO_TABELA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6.5),
    ]))
    return RoundedTableFlowable(tabela, width=largura_total, radius=10, stroke_color=CINZA_BORDA, fill_color=FUNDO_PAGINA, stroke_width=0.7, h_align="CENTER")


def _fmt_pct_svg(valor: Any) -> str:
    try:
        return f"{float(valor):.2f}%".replace(".", ",")
    except Exception:
        return "-"


def _normalizar_range(y_min: float, y_max: float) -> tuple[float, float]:
    """Aplica padding ao eixo Y do gráfico para evitar linhas coladas nas bordas."""
    if pd.isna(y_min) or pd.isna(y_max):
        return 0, 1
    padding = (abs(y_max) * 0.2 if y_max != 0 else 1) if y_min == y_max else (y_max - y_min) * 0.2
    return y_min - padding * 0.1, y_max + padding


def _map_y(valor: float, y_min: float, y_max: float, top: float, height: float) -> float:
    if y_max == y_min:
        return top + height / 2
    return top + height - ((valor - y_min) / (y_max - y_min)) * height


def _path_linha(pontos: list[tuple[float, float]]) -> str:
    if not pontos:
        return ""
    return " ".join([f"M {pontos[0][0]:.2f} {pontos[0][1]:.2f}"] + [f"L {x:.2f} {y:.2f}" for x, y in pontos[1:]])


def criar_svg_historico_consolidado(df_planos: pd.DataFrame, data_selecionada: Any, mostrar_limite: bool = True, width: int = 1100, height: int = 360) -> str:
    """Monta o SVG do histórico de VaR do consolidado nos últimos 12 meses."""
    ultimos_12_meses = pd.to_datetime(data_selecionada) - pd.DateOffset(months=12)
    df_plot = df_planos[(df_planos["DATA_COTACAO"] >= ultimos_12_meses) & (df_planos["DATA_COTACAO"] <= pd.to_datetime(data_selecionada))].copy()
    df_plot = df_plot[df_plot["Planos"] == "Consolidado"].dropna(subset=["VaR %", "Planos"]).copy()
    df_plot["DATA_COTACAO"] = pd.to_datetime(df_plot["DATA_COTACAO"])
    df_plot = df_plot.sort_values("DATA_COTACAO")

    if df_plot.empty:
        return f"""
        <svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
            <rect width="100%" height="100%" fill="{_cor_svg(FUNDO_PAGINA)}"/>
            <text x="{width / 2}" y="{height / 2}" text-anchor="middle" font-family="Figtree" font-size="16" fill="{_cor_svg(TEXTO_PADRAO)}">
                Não há dados disponíveis para o período selecionado.
            </text>
        </svg>
        """

    meses_pt = {1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"}
    df_plot["EIXO_X"] = df_plot["DATA_COTACAO"].dt.strftime("%Y-%m")
    df_plot["MES_LABEL"] = df_plot["DATA_COTACAO"].dt.month.map(meses_pt)
    df_plot["ANO"] = df_plot["DATA_COTACAO"].dt.strftime("%Y")

    df_eixo_x = df_plot.drop_duplicates(subset=["EIXO_X"])[["EIXO_X", "MES_LABEL", "ANO", "DATA_COTACAO"]].reset_index(drop=True)
    ordem_x = df_eixo_x["EIXO_X"].tolist()

    margin_left, margin_right, margin_top, margin_bottom = 62, 28, 48, 58
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom

    y_min = df_plot["VaR %"].min()
    y_max = df_plot["VaR %"].max()
    if mostrar_limite and "Lim. Interno %" in df_plot.columns:
        y_min = min(y_min, df_plot["Lim. Interno %"].min())
        y_max = max(y_max, df_plot["Lim. Interno %"].max())
    y_min, y_max = _normalizar_range(y_min, y_max)

    def x_pos(eixo_x: str) -> float:
        idx = ordem_x.index(eixo_x)
        return margin_left + plot_w / 2 if len(ordem_x) == 1 else margin_left + idx * (plot_w / (len(ordem_x) - 1))

    pontos_var = [(x_pos(row["EIXO_X"]), _map_y(row["VaR %"], y_min, y_max, margin_top, plot_h)) for _, row in df_plot.iterrows()]
    pontos_limite: list[tuple[float, float]] = []
    if mostrar_limite and "Lim. Interno %" in df_plot.columns:
        pontos_limite = [(x_pos(row["EIXO_X"]), _map_y(row["Lim. Interno %"], y_min, y_max, margin_top, plot_h)) for _, row in df_plot.iterrows() if pd.notna(row["Lim. Interno %"])]

    y_ticks_svg = ""
    for i in range(5):
        valor = y_min + (y_max - y_min) * i / 4
        y = _map_y(valor, y_min, y_max, margin_top, plot_h)
        y_ticks_svg += f"""
        <line x1="{margin_left}" y1="{y:.2f}" x2="{width - margin_right}" y2="{y:.2f}" stroke="{_cor_svg(CINZA_BORDA)}" stroke-width="1"/>
        <text x="{margin_left - 8}" y="{y + 4:.2f}" text-anchor="end" font-family="Figtree" font-size="11" fill="{_cor_svg(TEXTO_PADRAO)}">{_fmt_pct_svg(valor)}</text>
        """

    ticktext_x = [""] * len(df_eixo_x)
    for _, df_ano in df_eixo_x.groupby("ANO", sort=False):
        indices = df_ano.index.tolist()
        indice_central = indices[len(indices) // 2]
        for idx in indices:
            mes = df_eixo_x.loc[idx, "MES_LABEL"]
            ano = df_eixo_x.loc[idx, "ANO"] if idx == indice_central else ""
            ticktext_x[idx] = f"{mes}|{ano}"

    x_ticks_svg = ""
    for idx, row in df_eixo_x.iterrows():
        x = x_pos(row["EIXO_X"])
        mes, ano = ticktext_x[idx].split("|")
        x_ticks_svg += f'<text x="{x:.2f}" y="{height - 32}" text-anchor="middle" font-family="Figtree" font-size="13" fill="{_cor_svg(TEXTO_PADRAO)}">{xml_escape(mes)}</text>'
        if ano:
            x_ticks_svg += f'<text x="{x:.2f}" y="{height - 16}" text-anchor="middle" font-family="Figtree" font-size="13" fill="{_cor_svg(TEXTO_PADRAO)}">{xml_escape(ano)}</text>'

    separadores_svg = ""
    for idx in range(1, len(df_eixo_x)):
        if df_eixo_x.loc[idx, "ANO"] != df_eixo_x.loc[idx - 1, "ANO"]:
            x_sep = (x_pos(df_eixo_x.loc[idx - 1, "EIXO_X"]) + x_pos(df_eixo_x.loc[idx, "EIXO_X"])) / 2
            separadores_svg += f'<text x="{x_sep:.2f}" y="{height - 23}" text-anchor="middle" font-family="Figtree" font-size="13" fill="{_cor_svg(TEXTO_PADRAO)}">|</text>'

    legenda_limite = ""
    path_limite = _path_linha(pontos_limite)
    if path_limite:
        legenda_limite = f"""
        <line x1="248" y1="20" x2="288" y2="20" stroke="{_cor_svg(VERDE_TITULO)}" stroke-width="2" stroke-dasharray="6 5"/>
        <text x="294" y="24" font-family="Figtree" font-size="13" fill="{_cor_svg(TEXTO_PADRAO)}">Consolidado - Lim. Interno</text>
        """

    return f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
        <rect width="100%" height="100%" fill="{_cor_svg(FUNDO_PAGINA)}"/>
        <line x1="88" y1="20" x2="128" y2="20" stroke="{_cor_svg(VERDE_TITULO)}" stroke-width="2"/>
        <text x="134" y="24" font-family="Figtree" font-size="13" fill="{_cor_svg(TEXTO_PADRAO)}">Consolidado</text>
        {legenda_limite}
        {y_ticks_svg}
        <path d="{_path_linha(pontos_var)}" fill="none" stroke="{_cor_svg(VERDE_TITULO)}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="{path_limite}" fill="none" stroke="{_cor_svg(VERDE_TITULO)}" stroke-width="2" stroke-dasharray="6 5" stroke-linecap="round" stroke-linejoin="round"/>
        {x_ticks_svg}
        {separadores_svg}
    </svg>
    """


def preparar_tabela_resumo(df_data: pd.DataFrame) -> pd.DataFrame:
    """Formata a tabela de resumo por plano para exibição no PDF."""
    colunas = [
        "Planos", "Posição R$", "VaR R$", "VaR %", "Lim. Interno %", "Status %",
        "Stress (+) R$", "Stress (+) %", "Stress (-) R$", "Stress (-) %",
    ]
    colunas_existentes = [col for col in colunas if col in df_data.columns]
    df = df_data[colunas_existentes].copy()
    df = df[df["Planos"] != "Consolidado"].copy()

    for col in df.columns:
        if col == "Planos":
            continue
        if "R$" in col:
            df[col] = df[col].apply(lambda x: f"R$ {fmt_br(x)}" if pd.notna(x) else "-")
        elif "%" in col and col != "Status %":
            df[col] = df[col].apply(lambda x: f"{fmt_br(x)}%" if pd.notna(x) else "-")
        elif col == "Status %":
            df[col] = df[col].apply(lambda x: "Dentro" if pd.notna(x) and float(x) <= 100 else "Acima")
    return df


def _tabela_resumo_pdf(df_resumo: pd.DataFrame) -> RoundedTableFlowable:
    """Cria a tabela de resumo por plano com zebra striping."""
    dados = [df_resumo.columns.tolist()] + df_resumo.values.tolist()
    col_widths_base = [4.60 * cm, 2.95 * cm, 2.75 * cm, 2.00 * cm, 2.35 * cm, 2.05 * cm, 2.85 * cm, 2.10 * cm, 2.85 * cm, 2.10 * cm]
    col_widths = col_widths_base[: len(df_resumo.columns)]
    largura_total = sum(col_widths)

    tabela = Table(dados, colWidths=col_widths, repeatRows=1, splitByRow=1)
    tabela.hAlign = "CENTER"
    comandos = [
        ("BACKGROUND", (0, 0), (-1, 0), VERDE_TITULO),
        ("TEXTCOLOR", (0, 0), (-1, 0), VERDE_CLARO),
        ("FONTNAME", (0, 0), (-1, 0), FONTES.bold),
        ("FONTNAME", (0, 1), (-1, -1), FONTES.regular),
        ("FONTSIZE", (0, 0), (-1, 0), 8.8),
        ("FONTSIZE", (0, 1), (-1, -1), 8.4),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, CINZA_BORDA),
        ("BOX", (0, 0), (-1, -1), 0, FUNDO_PAGINA),
        ("TEXTCOLOR", (0, 1), (-1, -1), TEXTO_TABELA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5.5),
        ("TOPPADDING", (0, 0), (-1, -1), 6.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6.2),
    ]
    for linha in range(1, len(dados)):
        comandos.append(("BACKGROUND", (0, linha), (-1, linha), FUNDO_PAGINA if linha % 2 == 1 else ZEBRA_FUNDO))

    tabela.setStyle(TableStyle(comandos))
    return RoundedTableFlowable(tabela, width=largura_total, radius=10, stroke_color=CINZA_BORDA, fill_color=FUNDO_PAGINA, stroke_width=0.7, h_align="CENTER")


def _bloco_cabecalho_risco(styles):
    """Cabeçalho visual do relatório de risco de mercado."""
    logo_path = _resolve_asset_path(LOGO_RELATIVE_PATH) or (BASE_DIR / ".." / ".." / LOGO_RELATIVE_PATH).resolve()
    logo = svg_arquivo_para_flowable(logo_path, width=3.2 * cm, height=0.9 * cm, h_align="RIGHT")
    titulo = Paragraph(
        f"<font color='#0B2F13'>Risco de Mercado - </font>"
        f"<font name='{FONTES.italic_serif}' color='#0B2F13'><i>Planos</i></font>",
        styles["TituloPrincipal"],
    )
    tabela = Table([["", titulo, logo]], colWidths=[3.2 * cm, landscape(A4)[0] - 11 * cm, 3.2 * cm], rowHeights=[1.8 * cm])
    tabela.hAlign = "CENTER"
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), FUNDO_PAGINA),
        ("BOX", (0, 0), (-1, -1), 0, FUNDO_PAGINA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("ALIGN", (2, 0), (2, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return tabela


def gerar_pdf_risco_planos(df_planos_original: pd.DataFrame, data_selecionada: Any = None) -> bytes:
    """Gera o PDF de Risco de Mercado dos Planos."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1.2 * cm,
        leftMargin=1.2 * cm,
        topMargin=1.1 * cm,
        bottomMargin=1.2 * cm,
    )
    styles = criar_estilos()
    elements: list = []

    df_planos = preparar_dados_planos(df_planos_original)
    df_data, data_selecionada = filtrar_data(df_planos, data_selecionada)

    elements.append(_bloco_cabecalho_risco(styles))
    elements.append(Spacer(1, 0.25 * cm))
    elements.append(Paragraph(
        "Este relatório apresenta uma visão do risco de mercado dos planos, com base no VaR "
        "(Value at Risk) paramétrico e nas diretrizes definidas no Manual de Riscos de Investimento. "
        "O VaR é uma medida estatística que estima a perda potencial máxima em um determinado "
        "horizonte de tempo e nível de confiança.",
        styles["TextoNormal"],
    ))
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(Paragraph(f"<b>Data posição:</b> {_date_to_br(data_selecionada)}", styles["TextoNormal"]))
    elements.append(Spacer(1, 0.35 * cm))

    elements.append(KeepTogether([
        Paragraph("Métricas de Risco Consolidado", styles["TituloSecao"]),
        Spacer(1, 0.95 * cm),
        _tabela_metricas(montar_metricas_consolidadas(df_data)),
    ]))
    elements.append(Spacer(1, 0.95 * cm))

    svg_historico = criar_svg_historico_consolidado(df_planos=df_planos, data_selecionada=data_selecionada, mostrar_limite=True)
    elements.append(KeepTogether([
        Paragraph("Histórico VaR Paramétrico - Consolidado", styles["TituloSecao"]),
        Spacer(1, 0.99 * cm),
        SvgFlowable(svg_text=svg_historico, width=25.8 * cm, height=8.5 * cm, h_align="CENTER"),
    ]))

    elements.append(PageBreak())
    elements.append(Paragraph("Resumo de Risco por Plano", styles["TituloSecao"]))
    df_resumo = preparar_tabela_resumo(df_data)
    if df_resumo.empty:
        elements.append(Paragraph("Não há dados disponíveis para exibir.", styles["TextoNormal"]))
    else:
        elements.append(_tabela_resumo_pdf(df_resumo))

    doc.build(elements, onFirstPage=_fundo_com_rodape_risco, onLaterPages=_fundo_com_rodape_risco)
    return buffer.getvalue()
