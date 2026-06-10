"""
Gerador de PDF do Relatorio de Enquadramento Diario - Fundacao Ceres.
"""
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any, Iterable, Sequence
import warnings

import pandas as pd
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
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from svglib.svglib import svg2rlg

# --- IMPORT DAS FUNÇÕES DO SEU UTILS.HELPERS ---
from utils.helpers import fmt_br, formatar_percentual_br


pd.options.display.float_format = '{:.2f}'.format


# -----------------------------------------------------------------------------
# Paths e assets
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
FONTS_DIR = (BASE_DIR / ".." / ".." / "fonts").resolve()
LOGO_RELATIVE_PATH = Path("images") / "c1_fundo_claro.svg"


# -----------------------------------------------------------------------------
# Cores
# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
# Constantes de negocio/layout
# -----------------------------------------------------------------------------
REGIME_POLITICA = "Política de Investimentos"
SEGMENTOS_AGREGADOS = [
    "Renda Fixa",
    "Renda Variável",
    "Imobiliário",
    "Estruturado",
    "Operações com Participantes",
    "Exterior",
]
SEGMENTOS_EMISSORES = {"Emissores (Art. 27)", "Emissores (Art. 28)"}
RODAPE_NAO_ELEGIVEIS = "(*) Não Elegíveis desde maio/2026, (**) Não elegível desde maio/2025."

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
    headers: list[str]
    col_widths: list[float]
    header_aligns: list[str]
    col_aligns: list[str]


# -----------------------------------------------------------------------------
# Fontes e estilos
# -----------------------------------------------------------------------------
def _registrar_fontes() -> None:
    font_files = {
        "Figtree": "Figtree-Regular.ttf",
        "Figtree-Bold": "Figtree-Bold.ttf",
        "Figtree-SemiBold": "Figtree-SemiBold.ttf",
        "SourceSerif": "SourceSerif4_36pt-SemiBoldItalic.ttf",
        "SourceSerif-Italic": "SourceSerif4_36pt-SemiBoldItalic.ttf",
    }

    registered: set[str] = set()
    for font_name, file_name in font_files.items():
        path = FONTS_DIR / file_name
        if not path.exists():
            warnings.warn(f"Fonte nao encontrada: {path}", RuntimeWarning, stacklevel=2)
            continue
        try:
            pdfmetrics.registerFont(TTFont(font_name, str(path)))
            registered.add(font_name)
        except Exception as exc:
            warnings.warn(f"Nao foi possivel registrar a fonte {font_name}: {exc}", RuntimeWarning, stacklevel=2)

    if {"Figtree", "Figtree-Bold"}.issubset(registered):
        pdfmetrics.registerFontFamily(
            "Figtree",
            normal="Figtree",
            bold="Figtree-Bold",
            italic="Figtree",
            boldItalic="Figtree-Bold",
        )

    if "SourceSerif" in registered:
        pdfmetrics.registerFontFamily(
            "SourceSerif",
            normal="SourceSerif",
            italic="SourceSerif",
            bold="SourceSerif",
            boldItalic="SourceSerif",
        )


_registrar_fontes()


def _fonte(nome: str, fallback: str) -> str:
    return nome if nome in pdfmetrics.getRegisteredFontNames() else fallback


def _estilos():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "Titulo",
        fontName=_fonte("Figtree-Bold", "Helvetica-Bold"),
        fontSize=16,
        textColor=VERDE_TITULO,
        spaceAfter=0,
        spaceBefore=8 * mm,
        leading=19,
    ))
    styles.add(ParagraphStyle(
        "Subtitulo",
        fontName=_fonte("Figtree-Bold", "Helvetica-Bold"),
        fontSize=11.5,
        textColor=VERDE_TITULO,
        spaceBefore=2 * mm,
        spaceAfter=1.5 * mm,
        leading=14,
    ))
    styles.add(ParagraphStyle(
        "SubtituloCentro",
        parent=styles["Subtitulo"],
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "NomePlano",
        fontName=_fonte("SourceSerif", "Times-Italic"),
        fontSize=10.5,
        textColor=VERDE_TITULO,
        spaceBefore=0,
        spaceAfter=1.5 * mm,
        leading=13,
    ))
    styles.add(ParagraphStyle(
        "CorpoTexto",
        fontName=_fonte("Figtree", "Helvetica"),
        fontSize=9.5,
        leading=12,
        spaceAfter=1.5 * mm,
        textColor=TEXTO_PADRAO,
    ))
    styles.add(ParagraphStyle(
        "RodaPe",
        fontName=_fonte("SourceSerif", "Times-Italic"),
        fontSize=7,
        leading=9,
        spaceAfter=1.5 * mm,
        textColor=TEXTO_PADRAO,
        leftIndent=1 * mm,
    ))
    styles.add(ParagraphStyle(
        "DataPos",
        fontName=_fonte("Figtree", "Helvetica"),
        fontSize=9,
        alignment=TA_RIGHT,
        textColor=VERDE_TITULO,
    ))

    styles.add(ParagraphStyle(
        "ThCell",
        fontName=_fonte("Figtree-Bold", "Helvetica-Bold"),
        fontSize=6.8,
        leading=8.2,
        textColor=VERDE_CLARO,
        alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle("ThCellRight", parent=styles["ThCell"], alignment=TA_RIGHT))
    styles.add(ParagraphStyle("ThCellCenter", parent=styles["ThCell"], alignment=TA_CENTER))

    styles.add(ParagraphStyle(
        "TdCell",
        fontName=_fonte("Figtree", "Helvetica"),
        fontSize=6.8,
        leading=8.2,
        textColor=TEXTO_TABELA,
        alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle("TdCellRight", parent=styles["TdCell"], alignment=TA_RIGHT))
    styles.add(ParagraphStyle("TdCellCenter", parent=styles["TdCell"], alignment=TA_CENTER))

    return styles


# -----------------------------------------------------------------------------
# Helpers locais
# -----------------------------------------------------------------------------
def _limpar_texto(texto: Any) -> str:
    texto = "" if pd.isna(texto) else str(texto)
    return texto[8:] if "Art." in texto else texto


def _nome_plano(valor_original: str) -> str:
    chave = valor_original.split("=", 1)[-1] if "=" in valor_original else valor_original
    return NOMES_PLANOS.get(chave, chave)


def _remove_grp(palavra: Any) -> str:
    if pd.isna(palavra):
        return "—"
    palavra = str(palavra)
    return palavra.split("=")[-1] if "grupo" in palavra.lower() else palavra


def _p(text: Any, style) -> Paragraph:
    return Paragraph("—" if pd.isna(text) else str(text), style)


def _date_to_br(data_posicao: Any) -> str:
    if hasattr(data_posicao, "strftime"):
        return data_posicao.strftime("%d/%m/%Y")
    return str(data_posicao)


def _is_politica(regime: str) -> bool:
    return regime == REGIME_POLITICA


def _is_desenquadrado(status: Any) -> bool:
    return str(status).strip().upper() == "DESENQUADRADO"


def _status_rows(df: pd.DataFrame) -> set[int]:
    return {
        i
        for i, (_, row) in enumerate(df.iterrows())
        if _is_desenquadrado(row.get("STATUS"))
    }


def _resolve_asset_path(relative_path: Path) -> Path | None:
    candidates = [Path.cwd(), BASE_DIR, *BASE_DIR.parents]
    for base in candidates:
        path = base / relative_path
        if path.exists():
            return path
    return None


# -----------------------------------------------------------------------------
# Documento e pagina
# -----------------------------------------------------------------------------
def _criar_documento(buf: BytesIO, title: str | None = None) -> SimpleDocTemplate:
    return SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=1 * cm,
        rightMargin=1 * cm,
        topMargin=1 * cm,
        bottomMargin=1 * cm,
        title=title,
    )


def _page_width() -> float:
    return landscape(A4)[0] - 2.4 * cm


def _desenhar_logo(canvas, doc, logo_path: Path | None = None) -> None:
    if doc.page != 1:
        return
    path = logo_path or _resolve_asset_path(LOGO_RELATIVE_PATH)
    if path is None:
        return
    logo_width = 22
    logo_height = 22
    x = doc.pagesize[0] - logo_width - 1.2 * cm
    y = doc.pagesize[1] - logo_height - 1.2 * cm
    try:
        if path.suffix.lower() == ".svg":
            drawing = svg2rlg(str(path))
            if drawing and drawing.width and drawing.height:
                drawing.scale(logo_width / drawing.width, logo_height / drawing.height)
                drawing.drawOn(canvas, x, y)
        else:
            logo = ImageReader(str(path))
            canvas.drawImage(logo, x, y, width=logo_width, height=logo_height)
    except Exception as exc:
        warnings.warn(f"Erro ao carregar logo: {exc}", RuntimeWarning, stacklevel=2)


def _fundo_pagina(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFillColor(FUNDO_PAGINA)
    canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], stroke=0, fill=1)
    _desenhar_logo(canvas, doc)
    canvas.restoreState()


def _add_linha_horizontal(elements: list, *, width: str = "100%", thickness: float = 0.4,
                          space_after: float = 4 * mm, space_before: float = 1 * mm) -> None:
    elements.append(HRFlowable(
        width=width, thickness=thickness, color=VERDE_ESCURO,
        spaceAfter=space_after, spaceBefore=space_before,
    ))


# -----------------------------------------------------------------------------
# Tabelas
# -----------------------------------------------------------------------------
class TabelaArredondada(Flowable):
    def __init__(self, tabela, raio=6, cor_borda=CINZA_BORDA, espessura=0.75,
                 cor_header=VERDE_ESCURO, is_continuation=False):
        super().__init__()
        self._tabela = tabela
        self._raio = raio
        self._cor_borda = cor_borda
        self._espessura = espessura
        self._cor_header = cor_header
        self._is_continuation = is_continuation

    def wrap(self, availWidth, availHeight):
        width, height = self._tabela.wrap(availWidth, availHeight)
        self.width = width
        self.height = height
        return width, height

    def split(self, availWidth, availHeight):
        parts = self._tabela.split(availWidth, availHeight)
        return [
            TabelaArredondada(part, raio=self._raio, cor_borda=self._cor_borda, 
                              espessura=self._espessura, cor_header=self._cor_header,
                              is_continuation=(i > 0 or self._is_continuation))
            for i, part in enumerate(parts)
        ]

    def draw(self):
        canvas = self.canv
        width, height = self.width, self.height
        radius = self._raio
        row_heights = self._tabela._rowHeights or []
        header_height = row_heights[0] if row_heights and row_heights[0] is not None else 22

        canvas.saveState()
        clip = canvas.beginPath()
        clip.roundRect(0, 0, width, height, radius)
        canvas.clipPath(clip, stroke=0)
        canvas.setFillColor(self._cor_header)
        canvas.rect(0, height - header_height, width, header_height, stroke=0, fill=1)
        self._tabela.drawOn(canvas, 0, 0)
        canvas.restoreState()
        canvas.setStrokeColor(self._cor_borda)
        canvas.setLineWidth(self._espessura)
        canvas.roundRect(0, 0, width, height, radius, stroke=1, fill=0)


def _construir_tabela(headers_text: Sequence[str], rows_para: Sequence[Sequence[Paragraph]],
                      col_widths: Sequence[float], linhas_desenquadradas: Iterable[int], styles,
                      header_aligns: Sequence[str] | None = None,
                      col_aligns: Sequence[str] | None = None) -> TabelaArredondada:
    header_aligns = list(header_aligns or ["ThCell"] * len(headers_text))
    col_aligns = list(col_aligns or [])
    linhas_desenquadradas = set(linhas_desenquadradas or set())
    header_row = [_p(header, styles[style_name]) for header, style_name in zip(headers_text, header_aligns)]
    data = [header_row] + list(rows_para)
    tabela = Table(data, colWidths=list(col_widths), repeatRows=1)
    estilo_cmds = [
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
        estilo_cmds.append(("ALIGN", (col_idx, 0), (col_idx, -1), align))
    desenq_rows = {idx + 1 for idx in linhas_desenquadradas}
    for row_idx in range(2, len(data), 2):
        if row_idx not in desenq_rows:
            estilo_cmds.append(("BACKGROUND", (0, row_idx), (-1, row_idx), ZEBRA_FUNDO))
    for idx in linhas_desenquadradas:
        estilo_cmds.append(("BACKGROUND", (0, idx + 1), (-1, idx + 1), VERMELHO_FUNDO))
    tabela.setStyle(TableStyle(estilo_cmds))
    return TabelaArredondada(tabela)


# -----------------------------------------------------------------------------
# Specs de Tabela
# -----------------------------------------------------------------------------
def _center_table_spec(headers: list[str], widths: list[float], *, first_left: bool = True) -> TableSpec:
    aligns = ["CENTER"] * len(headers)
    header_aligns = ["ThCellCenter"] * len(headers)
    if first_left and headers:
        aligns[0] = "LEFT"
        header_aligns[0] = "ThCell"
    return TableSpec(headers, widths, header_aligns, aligns)

def _normal_spec(page_w: float, regime: str) -> TableSpec:
    headers = ["Descrição", "Limite %", "Limite R$", "Posição R$", "Limite Utilizado %", "Status"]
    weights = [0.30, 0.14, 0.14, 0.14, 0.14, 0.14] if _is_politica(regime) else [0.25, 0.15, 0.15, 0.15, 0.15, 0.15]
    return _center_table_spec(headers, [page_w * w for w in weights])

def _emissor_spec(page_w: float, regime: str) -> TableSpec:
    if _is_politica(regime):
        headers = ["Descrição", "Grupo Econômico", "Limite %", "Limite R$", "Posição R$", "Limite Utilizado %", "Status"]
        weights = [0.22, 0.15, 0.12, 0.12, 0.12, 0.12, 0.15]
    else:
        headers = ["Descrição", "Grupo Econômico", "Limite R$", "Posição R$", "Limite Utilizado %", "Status"]
        weights = [0.20, 0.15, 0.15, 0.15, 0.15, 0.20]
    return _center_table_spec(headers, [page_w * w for w in weights])

def _agregado_spec(page_w: float) -> TableSpec:
    headers = ["Segmento de Aplicação", "Limite %", "Limite R$", "Posição %", "Posição R$", "Limite Utilizado %", "Status"]
    weights = [0.22, 0.12, 0.13, 0.13, 0.13, 0.13, 0.14]
    return _center_table_spec(headers, [page_w * w for w in weights])


# -----------------------------------------------------------------------------
# Lógica de Dados e Rows
# -----------------------------------------------------------------------------
def _filtrar_plano(df: pd.DataFrame, plano_selecionado: str, regime: str) -> pd.DataFrame:
    return df[(df["ESTRUTURA_ASSOCIADA"] == plano_selecionado) & (df["CONJUNTO"] == regime)].copy()

def _segmentos_ordenados(df_plano: pd.DataFrame) -> list[str]:
    segmentos = list(df_plano["SEGMENTO"].dropna().unique())
    ordem = {segmento: i for i, segmento in enumerate(SEGMENTOS_AGREGADOS)}
    return sorted(segmentos, key=lambda s: ordem.get(s, len(ordem)))

def _preparar_segmento(df_plano: pd.DataFrame, segmento: str, regime: str) -> pd.DataFrame:
    df_seg = df_plano[df_plano["SEGMENTO"] == segmento].copy().sort_values(by="ORDEM")
    df_seg["DESCRICAO"] = df_seg["DESCRICAO"].apply(_limpar_texto)
    if _is_politica(regime):
        df_seg = df_seg[df_seg["DESCRICAO"] != segmento].copy()
        if segmento not in SEGMENTOS_EMISSORES:
            df_seg["DESCRICAO"] = pd.Categorical(df_seg["DESCRICAO"], categories=ORDEM_REGRAS_POLITICA, ordered=True)
            df_seg = df_seg.sort_values(by="DESCRICAO")
    if segmento in SEGMENTOS_EMISSORES:
        df_seg["GRP_ECONOMICO"] = df_seg["AGREGACAO"].apply(_remove_grp)
    return df_seg

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
    elements.append(Paragraph("Limites de Alocação e Concentração", styles["SubtituloCentro"]))
    df_agregado = df_plano[df_plano["DESCRICAO"].isin(SEGMENTOS_AGREGADOS)].copy()
    df_agregado["DESCRICAO"] = pd.Categorical(df_agregado["DESCRICAO"], categories=SEGMENTOS_AGREGADOS, ordered=True)
    df_agregado = df_agregado.sort_values("DESCRICAO")
    referencia = df_agregado["VALOR_REFERENCIA"].replace(0, pd.NA)
    df_agregado["PCT_ATUAL"] = ((df_agregado["VALOR_ATUAL"] / referencia) * 100).fillna(0)
    
    rows = _rows_agregado(df_agregado, styles)
    rows.append([
        _p("Total de Recursos Garantidores", styles["TdCell"]), _p("-", styles["TdCellCenter"]),
        _p("-", styles["TdCellCenter"]), _p(formatar_percentual_br(df_agregado["PCT_ATUAL"].sum()), styles["TdCellCenter"]),
        _p(fmt_br(df_agregado["VALOR_ATUAL"].sum()), styles["TdCellCenter"]), _p("-", styles["TdCellCenter"]),
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
    rows, prev_desc = [], None
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


# -----------------------------------------------------------------------------
# Funções Principais de PDF
# -----------------------------------------------------------------------------
def gerar_pdf(df: pd.DataFrame, plano_selecionado: str, data_posicao: Any, regime: str) -> bytes:
    buf, styles, page_w = BytesIO(), _estilos(), _page_width()
    nome_plano = _nome_plano(plano_selecionado)
    doc = _criar_documento(buf, title=f"Enquadramento - {nome_plano}")
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
    return buf.getvalue()


def _formatar_valor_risco(value: Any, column_name: str) -> str:
    if pd.isna(value): return "—"
    col = str(column_name).upper()
    if any(x in col for x in ["R$", "PATRIM", "EXPOSI"]): return fmt_br(value)
    if any(x in col for x in ["%", "PERC"]): return formatar_percentual_br(value)
    return str(value)


def gerar_pdf_limites_operacionais(df_limites: pd.DataFrame, data_posicao: Any, titulo_relatorio: str = "Limites Operacionais -",
                                  subtitulo_relatorio: str = " Instituições Financeiras", disponivel_alocacao_26=None,
                                  total_exposicao=None, total_exposicao_26=None, alocado_26=None, df_risco: pd.DataFrame | None = None) -> bytes:
    buf, styles, page_w = BytesIO(), _estilos(), _page_width()
    doc = _criar_documento(buf)
    elements = [
        Paragraph(f'{titulo_relatorio}<font face="{_fonte("SourceSerif", "Times-Italic")}"><i>{subtitulo_relatorio}</i></font>', styles["Titulo"]),
        Spacer(1, 4 * mm), Paragraph(f"Data de posição: {_date_to_br(data_posicao)}", styles["DataPos"]), Spacer(1, 4 * mm),
    ]
    for label, val in [("Disponível 2026", disponivel_alocacao_26), ("Alocado 2026", alocado_26), 
                       ("Exposição Geral", total_exposicao), ("Exposição 2026", total_exposicao_26)]:
        if val is not None: elements.append(Paragraph(f"<b>{label}:</b> {fmt_br(val)}", styles["CorpoTexto"]))
    
    spec_lim = _limites_spec(page_w)
    rows_lim = [[_p(r.get("INSTITUICAO_FINANCEIRA"), styles["TdCell"]), _p(fmt_br(r.get("EXPOSICAO")), styles["TdCellRight"]),
                 _p(fmt_br(r.get("EXPOSICAO_2026")), styles["TdCellRight"]), _p(fmt_br(r.get("FINANCEIRO_AQUISICAO")), styles["TdCellRight"]),
                 _p(fmt_br(r.get("LIMITE_ALOCACAO_2026")), styles["TdCellRight"])] for _, r in df_limites.iterrows()]
    
    elements.extend([Paragraph("Limites Operacionais", styles["Subtitulo"]), 
                     _construir_tabela(spec_lim.headers, rows_lim, spec_lim.col_widths, set(), styles, spec_lim.header_aligns, spec_lim.col_aligns),
                     Paragraph(RODAPE_NAO_ELEGIVEIS, styles["RodaPe"])])

    if df_risco is not None and not df_risco.empty:
        elements.append(PageBreak())
        headers_r = list(df_risco.columns)
        rows_r = [[_p(_formatar_valor_risco(row.get(c), c), styles["TdCell"] if i==0 else styles["TdCellCenter"]) 
                   for i, c in enumerate(headers_r)] for _, row in df_risco.iterrows()]
        spec_r = _risco_spec(df_risco, page_w)
        elements.extend([Paragraph("Informações de Risco", styles["Subtitulo"]),
                         _construir_tabela(headers_r, rows_r, spec_r.col_widths, set(), styles, spec_r.header_aligns, spec_r.col_aligns),
                         Paragraph(RODAPE_NAO_ELEGIVEIS, styles["RodaPe"])])

    doc.build(elements, onFirstPage=_fundo_pagina, onLaterPages=_fundo_pagina)
    return buf.getvalue()

def _limites_spec(page_w: float) -> TableSpec:
    headers = ["Instituição Financeira", "Posição R$", "Posição 2026 R$", "Alocação 2026 R$", "Disp. Alocação"]
    return TableSpec(headers, [page_w*0.34] + [page_w*0.66/4]*4, ["ThCell"] + ["ThCellRight"]*4, ["LEFT"] + ["RIGHT"]*4)

def _risco_spec(df: pd.DataFrame, page_w: float) -> TableSpec:
    cols = list(df.columns)
    n = len(cols)
    return TableSpec(cols, [page_w*0.34] + [page_w*0.66/(n-1)]*(n-1), ["ThCell"] + ["ThCellCenter"]*(n-1), ["LEFT"] + ["CENTER"]*(n-1))