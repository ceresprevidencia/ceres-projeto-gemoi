"""
Gerador de PDF do Relatório de Enquadramento Diário — Fundação Ceres
Usa reportlab para construir o documento página a página.
"""
from io import BytesIO
import os
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    HRFlowable,
    Flowable,

)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from svglib.svglib import svg2rlg


# ── FONTES ───────────────────────────────────────────────────────────────────────
_FONTS_DIR = "fonts"

def _registrar_fontes():
    """Registra as famílias de fontes no reportlab."""
    _fonts = {
        "Figtree": "Figtree-Regular.ttf",
        "Figtree-Bold": "Figtree-Bold.ttf",
        "Figtree-SemiBold": "Figtree-SemiBold.ttf",
        "SourceSerif": "SourceSerif4_36pt-SemiBoldItalic.ttf",
    }
    for nome, arquivo in _fonts.items():
        caminho = os.path.join(_FONTS_DIR, arquivo)
        if os.path.exists(caminho):
            pdfmetrics.registerFont(TTFont(nome, caminho))

    pdfmetrics.registerFontFamily(
        "Figtree",
        normal="Figtree",
        bold="Figtree-Bold",
        italic="Figtree",
        boldItalic="Figtree-Bold",
    )
_registrar_fontes()


# ── CORES ─────────────────────────────────────────────────────────────────────
VERDE_ESCURO = colors.HexColor("#016837")
VERDE_TITULO = colors.HexColor("#0B2F13")
VERDE_CLARO = colors.HexColor("#A8EC7D")  # Cor do texto do cabeçalho (mesmo da página)
VERDE_BORDA = colors.HexColor("#014d2a")
VERMELHO = colors.HexColor("#c0392b")
CINZA_BORDA = colors.HexColor("#dddddd")
VERMELHO_FUNDO = colors.HexColor("#ffcccc")
BRANCO = colors.white
FUNDO_PAGINA = colors.HexColor("#fafbeb")


# ── ESTILOS ───────────────────────────────────────────────────────────────────
def _estilos():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        "Titulo",
        fontName="Figtree-Bold",
        fontSize=18,
        textColor=VERDE_TITULO,
        spaceAfter=0,
        spaceBefore=1*cm,
        leading=22,
    ))
    styles.add(ParagraphStyle(
        "Subtitulo",
        fontName="Figtree-SemiBold",
        fontSize=13,
        textColor=VERDE_TITULO,
        spaceBefore=2*mm,
        spaceAfter=2*mm,
        leading=16,
    ))
    styles.add(ParagraphStyle(
        "SubtituloCentro",
        fontName="Figtree-SemiBold",
        fontSize=13,
        textColor=VERDE_TITULO,
        spaceBefore=2*mm,
        spaceAfter=2*mm,
        leading=16,
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "NomePlano",
        fontName="SourceSerif",
        fontSize=12,
        textColor=VERDE_TITULO,
        spaceBefore=0,
        spaceAfter=2*mm,
        leading=17,
    ))
    styles.add(ParagraphStyle(
        "CorpoTexto",
        fontName="Figtree",
        fontSize=9,
        leading=14,
        spaceAfter=1 * mm,
        textColor=colors.HexColor("#333333"),
    ))

    styles.add(ParagraphStyle(
        "RodaPe",
        fontName="SourceSerif",
        fontSize=8,
        leading=14,
        spaceAfter=1 * mm,
        textColor=colors.HexColor("#333333"),
        leftIndent=1*mm
    ))


    styles.add(ParagraphStyle(
        "DataPos",
        fontName="Figtree",
        fontSize=10,
        alignment=TA_RIGHT,
        textColor=VERDE_TITULO,
    ))
    # Estilos de células da tabela
    styles.add(ParagraphStyle(
        "ThCell",
        fontName="Figtree-Bold",
        fontSize=7,
        leading=9,
        textColor=VERDE_CLARO,
        alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        "ThCellRight",
        fontName="Figtree-Bold",
        fontSize=7,
        leading=9,
        textColor=VERDE_CLARO,
        alignment=TA_RIGHT,
    ))
    styles.add(ParagraphStyle(
        "ThCellCenter",
        fontName="Figtree-Bold",
        fontSize=7,
        leading=9,
        textColor=VERDE_CLARO,
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "TdCell",
        fontName="Figtree",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#222222"),
        alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        "TdCellRight",
        fontName="Figtree",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#222222"),
        alignment=TA_RIGHT,
    ))
    styles.add(ParagraphStyle(
        "TdCellCenter",
        fontName="Figtree",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#222222"),
        alignment=TA_CENTER,
    ))
    

    return styles


# ── HELPERS ───────────────────────────────────────────────────────────────────
def _formatar_percentual_br(valor):
    if valor is None:
        return "—"
    return f"{str(valor).replace('.', ',')}%"


def _formatar_moeda_br(valor):
    try:
        return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return str(valor)


def _limpar_texto(texto):
    if 'Art.' in texto:
        return str(texto)[8:]
    else:
        return texto


def _nome_plano(valor_original):
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
    chave = valor_original.split("=", 1)[-1] if "=" in valor_original else valor_original
    return NOMES_PLANOS.get(chave, chave)


def _remove_grp(palavra):
    if "grupo" in palavra.lower():
        return palavra.split("=")[-1]
    return palavra


def _p(text, style):
    """Atalho para criar Paragraph — garante que o texto nunca é cortado."""
    return Paragraph(str(text), style)


class TabelaArredondada(Flowable):
    """Flowable que desenha uma tabela com bordas arredondadas."""

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
        w, h = self._tabela.wrap(availWidth, availHeight)
        self.width = w
        self.height = h
        return w, h

    def split(self, availWidth, availHeight):
        parts = self._tabela.split(availWidth, availHeight)
        if not parts:
            return []
        result = []
        for i, part in enumerate(parts):
            wrapped = TabelaArredondada(
                part,
                raio=self._raio,
                cor_borda=self._cor_borda,
                espessura=self._espessura,
                cor_header=self._cor_header,
                is_continuation=(i > 0 or self._is_continuation),
            )
            result.append(wrapped)
        return result

    def draw(self):
        canvas = self.canv
        w, h = self.width, self.height
        r = self._raio

        # ── Fundo arredondado do cabeçalho ──
        # Calcula a altura da primeira linha (cabeçalho)
        row_heights = self._tabela._rowHeights or []
        if row_heights and row_heights[0] is not None:
            header_h = row_heights[0]
        else:
            header_h = 22
            if hasattr(self._tabela, '_rowpositions') and len(self._tabela._rowpositions) > 1:
                header_h = self._tabela._rowpositions[0] - self._tabela._rowpositions[1]

        canvas.saveState()
        # Clip com retângulo arredondado
        clip = canvas.beginPath()
        clip.roundRect(0, 0, w, h, r)
        canvas.clipPath(clip, stroke=0)

        # Background do cabeçalho (topo arredondado)
        canvas.setFillColor(self._cor_header)
        canvas.rect(0, h - header_h, w, header_h, stroke=0, fill=1)

        # Desenha a tabela dentro do clip
        self._tabela.drawOn(canvas, 0, 0)
        canvas.restoreState()

        # ── Borda arredondada por cima da tabela ──
        canvas.setStrokeColor(self._cor_borda)
        canvas.setLineWidth(self._espessura)
        canvas.roundRect(0, 0, w, h, r, stroke=1, fill=0)


def _construir_tabela(headers_text, rows_para, col_widths, linhas_desenquadradas, styles,
                      header_aligns=None, col_aligns=None):
    """
    Monta uma Table do reportlab com Paragraphs em todas as células.
    headers_text: lista de strings para o cabeçalho
    rows_para: lista de listas de Paragraphs (corpo)
    header_aligns: lista de estilos para cada header (ThCell, ThCellRight, ThCellCenter)
    col_aligns: lista de alinhamentos por coluna (LEFT, RIGHT, CENTER) aplicados via TableStyle
    """
    linhas_desenquadradas = linhas_desenquadradas or set()

    if header_aligns is None:
        header_aligns = ["ThCell"] * len(headers_text)
    header_row = [_p(h, styles[a]) for h, a in zip(headers_text, header_aligns)]
    data = [header_row] + rows_para

    tabela = Table(data, colWidths=col_widths, repeatRows=1)

    estilo_cmds = [
        # Cabeçalho
        ("BACKGROUND", (0, 0), (-1, 0), VERDE_TITULO),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("LEFTPADDING", (0, 1), (-1, -1), 20),
        ("RIGHTPADDING", (0, 1), (-1, -1), 6),
        # Corpo
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ("TOPPADDING", (0, 1), (-1, -1), 5),
        ("LEFTPADDING", (0, 1), (-1, -1), 12),
        ("RIGHTPADDING", (0, 1), (-1, -1), 6),
        # Linhas
        ("LINEBELOW", (0, 0), (-1, 0), 1.5, VERDE_BORDA),
        ("LINEBELOW", (0, 1), (-1, -1), 0.5, CINZA_BORDA),
        # Alinhamento vertical
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]

    # Alinhamento horizontal por coluna
    if col_aligns:
        for col_idx, align in enumerate(col_aligns):
            estilo_cmds.append(("ALIGN", (col_idx, 0), (col_idx, -1), align))

    # Zebra (linhas pares com fundo cinza claro, exceto desenquadradas)
    desenq_rows = {idx + 1 for idx in linhas_desenquadradas}
    for r in range(2, len(data), 2):
        if r not in desenq_rows:
            estilo_cmds.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#f7f7f7")))

    # Destaque vermelho nas linhas desenquadradas
    for idx in linhas_desenquadradas:
        row = idx + 1
        estilo_cmds.append(("BACKGROUND", (0, row), (-1, row), VERMELHO_FUNDO))

    tabela.setStyle(TableStyle(estilo_cmds))
    return TabelaArredondada(tabela)


# ── GERADOR PRINCIPAL ─────────────────────────────────────────────────────────
def gerar_pdf(df, plano_selecionado, data_posicao, regime):
    """
    Gera o PDF do relatório de enquadramento para um plano.

    Parâmetros
    ----------
    df : pd.DataFrame  — dados completos de enquadramento
    plano_selecionado : str — ESTRUTURA_ASSOCIADA do plano
    regime: str - Política de Investimentos ou Resolução 4994 (definido na coluna CONJUNTO)
    data_posicao : str — data dd/mm/aaaa

    Retorna
    -------
    bytes — conteúdo do PDF
    """
    buf = BytesIO()
    styles = _estilos()

    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=1 * cm,
        rightMargin=1 * cm,
        topMargin=1 * cm,
        bottomMargin=1 * cm,
        title=f"Enquadramento - {_nome_plano(plano_selecionado)}",
    )

    def _fundo_pagina(canvas, doc):
        """Pinta o fundo de cada página com a cor #fafbeb e adiciona logo apenas na primeira página."""
        canvas.saveState()
        canvas.setFillColor(FUNDO_PAGINA)
        canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], stroke=0, fill=1)
        
        # Adiciona logo apenas na primeira página
        if doc.page == 1:
            logo_path = "images/c1_fundo_claro.svg"
            if os.path.exists(logo_path):
                try:
                    logo_width = 22 
                    logo_height = 22 
                    x = doc.pagesize[0] - logo_width - 1.2 * cm  # Margem direita
                    y = doc.pagesize[1] - logo_height - 1.2 * cm  # Margem topo
                    
                    if logo_path.lower().endswith('.svg'):
                        # Renderiza SVG
                        drawing = svg2rlg(logo_path)
                        if drawing:
                            # Escala o SVG para o tamanho desejado
                            drawing.scale(logo_width / drawing.width, logo_height / drawing.height)
                            # Desenha o SVG renderizado no canvas
                            drawing.drawOn(canvas, x, y)
                    else:
                        # Renderiza PNG/JPG
                        logo = ImageReader(logo_path)
                        canvas.drawImage(logo, x, y, width=logo_width, height=logo_height)
                except Exception as e:
                    print(f"Erro ao carregar logo: {e}")
        
        canvas.restoreState()

    elements = []
    page_w = landscape(A4)[0] - 2.4 * cm

    # ── Título, Plano e Data ──
    elements.append(Paragraph("Enquadramento Diário - Fundação Ceres", styles["Titulo"]))

    elements.append(Paragraph(
        f"Plano: {_nome_plano(plano_selecionado)}", styles["NomePlano"],
    ))
    elements.append(Paragraph(f"Data de posição: {data_posicao.strftime('%d/%m/%Y')}", styles["DataPos"]))
    elements.append(Spacer(1, 3 * mm))

    # ── Texto descritivo ──
    elements.append(Paragraph(
        "O Relatório tem como objetivo verificar a aderência dos investimentos do plano às "
        f"diretrizes de aplicações estabelecidas pela <b>{regime}</b> vigente.",
        styles["CorpoTexto"],
    ))

    elements.append(HRFlowable(
        width="100%", thickness=0.4, color=VERDE_ESCURO,
        spaceAfter=4 * mm, spaceBefore=1 * mm,
    ))

    # ── Dados do plano ──
    df_plano = df[(df["ESTRUTURA_ASSOCIADA"] == plano_selecionado) & (df['CONJUNTO'] == regime)].copy()
    
    # ── TABELA AGREGADA (apenas para Política de Investimentos) ──
    if regime == "Política de Investimentos":
        elementos_agregado = []
        elementos_agregado.append(Paragraph("Limites de Alocação e Concentração", styles["SubtituloCentro"]))
        elementos_agregado.append(Spacer(1, 1 * mm))
        
        agregado = ["Renda Fixa", "Renda Variável", "Imobiliário", "Estruturado", "Operações com Participantes", "Exterior"]
        df_agregado = df_plano[df_plano['DESCRICAO'].isin(agregado)].copy()
        df_agregado['DESCRICAO'] = pd.Categorical(df_agregado['DESCRICAO'], categories=agregado, ordered=True)
        df_agregado = df_agregado.sort_values('DESCRICAO')
        
        # Cálculo de totais e posição %
        total_rs = df_agregado["VALOR_ATUAL"].sum()
        df_agregado["PCT_ATUAL"] = (df_agregado["VALOR_ATUAL"] / df_agregado["VALOR_REFERENCIA"] * 100).round(2) if df_agregado["VALOR_REFERENCIA"].sum() > 0 else 0
        total_perc = df_agregado["PCT_ATUAL"].sum()
        
        rows_agregado = []
        desenquadradas_agregado = set()
        for i, (_, row) in enumerate(df_agregado.iterrows()):
            rows_agregado.append([
                _p(row["DESCRICAO"], styles["TdCell"]),
                _p(_formatar_percentual_br(row["LIMITE_PERCENTUAL"]), styles["TdCellCenter"]),
                _p(_formatar_moeda_br(row["VALOR_LIMITE_REGRA"]), styles["TdCellCenter"]),
                _p(_formatar_percentual_br(row["PCT_ATUAL"]), styles["TdCellCenter"]),
                _p(_formatar_moeda_br(row["VALOR_ATUAL"]), styles["TdCellCenter"]),
                _p(_formatar_percentual_br(row["PERCENTUAL_UTILIZADO"]), styles["TdCellCenter"]),
                _p(str(row["STATUS"]), styles["TdCellCenter"]),
            ])
            if str(row["STATUS"]).upper() == "DESENQUADRADO":
                desenquadradas_agregado.add(i)
        
        # Linha de total
        rows_agregado.append([
            _p("Total de Recursos Garantidores", styles["TdCell"]),
            _p("-", styles["TdCellCenter"]),
            _p("-", styles["TdCellCenter"]),
            _p(_formatar_percentual_br(total_perc), styles["TdCellCenter"]),
            _p(_formatar_moeda_br(total_rs), styles["TdCellCenter"]),
            _p("-", styles["TdCellCenter"]),
            _p("-", styles["TdCellCenter"]),
        ])
        
        headers_agregado = [
            "Segmento de Aplicação", "Limite %", "Limite R$", "Posição %", "Posição R$", "Limite Utilizado %", "Status"
        ]
        col_widths_agregado = [
            page_w * 0.22,
            page_w * 0.12,
            page_w * 0.13,
            page_w * 0.13,
            page_w * 0.13,
            page_w * 0.13,
            page_w * 0.14,
        ]
        
        header_aligns_agregado = [
            "ThCellCenter", "ThCellCenter", "ThCellCenter", "ThCellCenter", "ThCellCenter", "ThCellCenter", "ThCellCenter"
        ]
        col_aligns_agregado = ["LEFT", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER"]
        
        tabela_agregado = _construir_tabela(headers_agregado, rows_agregado, col_widths_agregado, 
                                            desenquadradas_agregado, styles, header_aligns_agregado, col_aligns_agregado)
        elementos_agregado.append(tabela_agregado)
        
        elements.extend(elementos_agregado)
        elements.append(HRFlowable(
            width="60%", thickness=0.05, color=VERDE_ESCURO,
            spaceAfter=4 * mm,
            spaceBefore=8 * mm,
        ))
    
    # Define a ordem esperada dos segmentos
    ordem_segmentos_politica = ['Renda Fixa', 'Renda Variável', 'Imobiliário', 'Estruturado', 'Operações com Participantes', 'Exterior']
    
    # Ordena os segmentos de acordo com a lista de ordem
    segmentos = df_plano["SEGMENTO"].unique()
    segmentos = sorted(segmentos, key=lambda x: ordem_segmentos_politica.index(x) if x in ordem_segmentos_politica else len(ordem_segmentos_politica))

    for segmento in segmentos:
        df_seg = df_plano[df_plano["SEGMENTO"] == segmento].copy()
        df_seg = df_seg.sort_values(by="ORDEM")
        df_seg["DESCRICAO"] = df_seg["DESCRICAO"].apply(_limpar_texto)
        
        # Remove a primeira linha que é igual ao segmento (já está na tabela agregada)
        if regime == "Política de Investimentos":
            df_seg = df_seg[df_seg["DESCRICAO"] != segmento].copy()

        seg_elements = []
        seg_elements.append(Paragraph(segmento, styles["Subtitulo"]))
        seg_elements.append(Spacer(1, 1 * mm))

        if segmento not in ["Emissores (Art. 27)", "Emissores (Art. 28)"]:
            # Define headers e col_widths conforme o regime
            if regime == "Política de Investimentos":
                headers = [
                    "Descrição", "Limite %", "Limite R$", "Posição R$", "Limite Utilizado %", "Status",
                ]
                col_widths = [
                    page_w * 0.30,
                    page_w * 0.14,
                    page_w * 0.14,
                    page_w * 0.14,
                    page_w * 0.14,
                    page_w * 0.14,
                ]
            else:
                headers = [
                    "Descrição", "Limite %", "Limite R$", "Posição R$", "Limite Utilizado %", "Status"
                ]
                col_widths = [
                    page_w * 0.25,
                    page_w * 0.15,
                    page_w * 0.15,
                    page_w * 0.15,
                    page_w * 0.15,
                    page_w * 0.15,
                ]

            # Se for Política de Investimentos, ordena pelas regras definidas
            if regime == "Política de Investimentos":
                ordem_regras = [
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
                    "Ativos financeiros no exterior pertencentes às carteiras dos fundos locais"
                ]
                
                df_seg["DESCRICAO"] = pd.Categorical(df_seg["DESCRICAO"], categories=ordem_regras, ordered=True)
                df_seg = df_seg.sort_values(by="DESCRICAO")

            rows = []
            desenquadradas = set()
            for i, (_, row) in enumerate(df_seg.iterrows()):
                desc = row["DESCRICAO"] if isinstance(row["DESCRICAO"], str) else str(row["DESCRICAO"])
                if regime == "Política de Investimentos":
                    rows.append([
                        _p(desc, styles["TdCell"]),
                        _p(_formatar_percentual_br(row["LIMITE_PERCENTUAL"]), styles["TdCellCenter"]),
                        _p(_formatar_moeda_br(row["VALOR_LIMITE_REGRA"]), styles["TdCellCenter"]),
                        _p(_formatar_moeda_br(row["VALOR_ATUAL"]), styles["TdCellCenter"]),
                        _p(_formatar_percentual_br(row["PERCENTUAL_UTILIZADO"]), styles["TdCellCenter"]),
                        _p(str(row["STATUS"]), styles["TdCellCenter"]),
                    ])
                else:
                    rows.append([
                        _p(desc, styles["TdCell"]),
                        _p(_formatar_percentual_br(row["LIMITE_PERCENTUAL"]), styles["TdCellCenter"]),
                        _p(_formatar_moeda_br(row["VALOR_LIMITE_REGRA"]), styles["TdCellCenter"]),
                        _p(_formatar_moeda_br(row["VALOR_ATUAL"]), styles["TdCellCenter"]),
                        _p(_formatar_percentual_br(row["PERCENTUAL_UTILIZADO"]), styles["TdCellCenter"]),
                        _p(str(row["STATUS"]), styles["TdCellCenter"]),
                    ])
                if str(row["STATUS"]).upper() == "DESENQUADRADO":
                    desenquadradas.add(i)

            if regime == "Política de Investimentos":
                header_aligns = [
                    "ThCellCenter", "ThCellCenter", "ThCellCenter",
                    "ThCellCenter", "ThCellCenter", "ThCellCenter",
                ]
                col_aligns = ["LEFT", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER"]
            else:
                header_aligns = [
                    "ThCellCenter", "ThCellCenter", "ThCellCenter",
                    "ThCellCenter", "ThCellCenter", "ThCellCenter",
                ]
                col_aligns = ["LEFT", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER"]
            tabela = _construir_tabela(headers, rows, col_widths, desenquadradas, styles, header_aligns, col_aligns)
            seg_elements.append(tabela)
        else:
            df_seg["DESCRICAO"] = df_seg["DESCRICAO"].str.strip()
            df_seg["GRP_ECONOMICO"] = df_seg["AGREGACAO"].apply(_remove_grp)
            df_seg = df_seg.sort_values(by=["ORDEM", "DESCRICAO"])

            # Define headers e col_widths conforme o regime
            if regime == "Política de Investimentos":
                headers = [
                    "Descrição", "Grupo Econômico", "Limite %", "Limite R$", "Posição R$",
                    "Limite Utilizado %", "Status"
                ]
                col_widths = [
                    page_w * 0.22,
                    page_w * 0.15,
                    page_w * 0.12,
                    page_w * 0.12,
                    page_w * 0.12,
                    page_w * 0.12,
                    page_w * 0.15,
                ]
            else:
                headers = [
                    "Descrição", "Grupo Econômico", "Limite R$", "Posição R$", "Limite Utilizado %", "Status"
                ]
                col_widths = [
                    page_w * 0.20,
                    page_w * 0.15,
                    page_w * 0.15,
                    page_w * 0.15,
                    page_w * 0.15,
                    page_w * 0.20,
                ]

            rows = []
            desenquadradas = set()
            prev_desc = None
            for i, (_, row) in enumerate(df_seg.iterrows()):
                desc = row["DESCRICAO"]
                show_desc = desc if desc != prev_desc else ""
                prev_desc = desc
                if regime == "Política de Investimentos":
                    rows.append([
                        _p(show_desc, styles["TdCell"]),
                        _p(str(row["GRP_ECONOMICO"]), styles["TdCell"]),
                        _p(_formatar_percentual_br(row["LIMITE_PERCENTUAL"]), styles["TdCellCenter"]),
                        _p(_formatar_moeda_br(row["VALOR_LIMITE_REGRA"]), styles["TdCellCenter"]),
                        _p(_formatar_moeda_br(row["VALOR_ATUAL"]), styles["TdCellCenter"]),
                        _p(_formatar_percentual_br(row["PERCENTUAL_UTILIZADO"]), styles["TdCellCenter"]),
                        _p(str(row["STATUS"]), styles["TdCellCenter"]),
                    ])
                else:
                    rows.append([
                        _p(show_desc, styles["TdCell"]),
                        _p(str(row["GRP_ECONOMICO"]), styles["TdCell"]),
                        _p(_formatar_moeda_br(row["VALOR_LIMITE_REGRA"]), styles["TdCellCenter"]),
                        _p(_formatar_moeda_br(row["VALOR_ATUAL"]), styles["TdCellCenter"]),
                        _p(_formatar_percentual_br(row["PERCENTUAL_UTILIZADO"]), styles["TdCellCenter"]),
                        _p(str(row["STATUS"]), styles["TdCellCenter"]),
                    ])
                if str(row["STATUS"]).upper() == "DESENQUADRADO":
                    desenquadradas.add(i)

            if regime == "Política de Investimentos":
                header_aligns = [
                    "ThCellCenter", "ThCellCenter", "ThCellCenter", "ThCellCenter",
                    "ThCellCenter", "ThCellCenter", "ThCellCenter",
                ]
                col_aligns = ["LEFT", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER"]
            else:
                header_aligns = [
                    "ThCellCenter", "ThCellCenter", "ThCellCenter", "ThCellCenter",
                    "ThCellCenter", "ThCellCenter",
                ]
                col_aligns = ["LEFT", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER"]
            tabela = _construir_tabela(headers, rows, col_widths, desenquadradas, styles, header_aligns, col_aligns)
            seg_elements.append(tabela)

        # Adiciona título e tabela do segmento diretamente, sem KeepTogether
        elements.extend(seg_elements)
        # Adiciona espaçamento após cada segmento
        elements.append(Spacer(1, 4 * mm))

    doc.build(elements, onFirstPage=_fundo_pagina, onLaterPages=_fundo_pagina)
    buf.seek(0)
    return buf.getvalue()


# ── EXPORTADOR LIMITES OPERACIONAIS ───────────────────────────────────────────
def gerar_pdf_limites_operacionais(df_limites, plano_nome, data_posicao, titulo_relatorio="Limites Operacionais - Instituições Financeiras",
                                   total_alocacao_26=None, total_exposicao_ceres=None, total_exposicao_plano=None, total_alocacao_plano=None, total_alocacao_ceres=None, total_exposicao_26_plano=None):
    """
    Gera PDF da tabela de Limites Operacionais.

    Parâmetros
    ----------
    df_limites : pd.DataFrame — dados da tabela de limites
    plano_nome : str — nome do plano
    data_posicao : date — data da posição
    titulo_relatorio : str — título do relatório
    total_alocacao_26 : float — disponível para 2026 (Ceres)
    total_exposicao_ceres : float — exposição total (Ceres)
    total_exposicao_plano : float — exposição do plano selecionado
    total_alocacao_plano : float — alocação 2026 do plano selecionado
    total_alocacao_ceres : float — alocação 2026 (Plano)
    total_exposicao_26_plano : float — exposição 2026 do plano selecionado
    total_exposicao_26_plano : float — exposição 2026 do plano selecionado

    Retorna
    -------
    bytes — conteúdo do PDF
    """
    buf = BytesIO()
    styles = _estilos()

    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=1 * cm,
        rightMargin=1 * cm,
        topMargin=1 * cm,
        bottomMargin=1 * cm,
        title=f"Limites Operacionais - {plano_nome}",
    )

    def _fundo_pagina(canvas, doc):
        """Pinta o fundo de cada página e adiciona logo apenas na primeira página."""
        canvas.saveState()
        canvas.setFillColor(FUNDO_PAGINA)
        canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], stroke=0, fill=1)
        
        if doc.page == 1:
            logo_path = "images/c1_fundo_claro.svg"
            if os.path.exists(logo_path):
                try:
                    logo_width = 22 
                    logo_height = 22 
                    x = doc.pagesize[0] - logo_width - 1.2 * cm
                    y = doc.pagesize[1] - logo_height - 1.2 * cm
                    
                    if logo_path.lower().endswith('.svg'):
                        drawing = svg2rlg(logo_path)
                        if drawing:
                            drawing.scale(logo_width / drawing.width, logo_height / drawing.height)
                            drawing.drawOn(canvas, x, y)
                    else:
                        logo = ImageReader(logo_path)
                        canvas.drawImage(logo, x, y, width=logo_width, height=logo_height)
                except Exception:
                    pass
        
        canvas.restoreState()

    elements = []
    page_w = landscape(A4)[0] - 2.4 * cm

    # ── Títulos e Metadados ──
    elements.append(Paragraph(titulo_relatorio, styles["Titulo"]))


    elements.append(Paragraph(f"Plano: <font face=\"SourceSerif\"><i>{plano_nome}</i></font>", styles["Subtitulo"]))
    elements.append(Paragraph(f"Data de posição: {data_posicao.strftime('%d/%m/%Y')}", styles["DataPos"]))
    elements.append(Spacer(1, 2 * mm))
    
    # ── Informações dos Cards ──
    if total_alocacao_26 is not None or total_exposicao_ceres is not None or total_alocacao_ceres is not None or total_exposicao_plano is not None or total_alocacao_plano is not None or total_exposicao_26_plano is not None:
        card_info = []
        if total_alocacao_26 is not None:
            card_info.append(f"<b>Ceres - Disponível para 2026:</b> R$ {_formatar_moeda_br(total_alocacao_26)}")
        if total_alocacao_ceres is not None:
            card_info.append(f"<b>Ceres - Alocado em 2026:</b> R$ {_formatar_moeda_br(total_alocacao_ceres)}")
        if total_exposicao_ceres is not None:
            card_info.append(f"<b>Ceres - Exposição:</b> R$ {_formatar_moeda_br(total_exposicao_ceres)}")
        if total_exposicao_plano is not None:
            card_info.append(f"<b>{plano_nome} - Exposição:</b> R$ {_formatar_moeda_br(total_exposicao_plano)}")
        if total_exposicao_26_plano is not None:
            card_info.append(f"<b>{plano_nome} - Exposição 2026:</b> R$ {_formatar_moeda_br(total_exposicao_26_plano)}")
        if total_alocacao_plano is not None:
            card_info.append(f"<b>{plano_nome} - Alocação 2026:</b> R$ {_formatar_moeda_br(total_alocacao_plano)}")
        
        if card_info:
            elementos_info = []
            for info in card_info:
                elementos_info.append(Paragraph(info, styles["CorpoTexto"]))
            elements.extend(elementos_info)
            elements.append(Spacer(1, 2 * mm))
    
    elements.append(HRFlowable(width="60%", thickness=0.4, color=VERDE_ESCURO))
    elements.append(Spacer(1, 4 * mm))

    # ── Cabeçalho da tabela ──
    headers = [
        "Instituição", "Porte", "RiskBank", "Alerta", "Patrimônio R$", 
        "Prazo Máximo", "Classificação", "Exposição R$", "Exposição 26 R$"
    ]
    
    # Calcular largura das colunas dinamicamente
    num_colunas = len(headers)
    col_width = page_w / num_colunas
    col_widths = [col_width] * num_colunas

    # Preparar dados da tabela
    rows = []
    for _, row in df_limites.iterrows():
        def safe_get(col, default="—"):
            try:
                val = row[col]
                return val if pd.notna(val) else default
            except:
                return default
        
        rows.append([
            _p(str(safe_get("INSTITUICAO_FINANCEIRA")), styles["TdCell"]),
            _p(str(safe_get("PORTE_INSTITUICAO")), styles["TdCellCenter"]),
            _p(_formatar_moeda_br(safe_get("INDICE_RISKBANK")), styles["TdCellCenter"]),
            _p(str(safe_get("ALERTA")), styles["TdCellCenter"]),
            _p(_formatar_moeda_br(safe_get("PATRIMONIO_LIQUIDO_R_MIL")), styles["TdCellCenter"]),
            _p(str(safe_get("PRAZO_MAXIMO_APLICACAO")), styles["TdCellCenter"]),
            _p(str(safe_get("CLASSIFICACAO_RISCO")), styles["TdCellCenter"]),
            _p(_formatar_moeda_br(safe_get("EXPOSICAO")), styles["TdCellCenter"]),
            _p(_formatar_moeda_br(safe_get("ALOCAÇÃO 2026")), styles["TdCellCenter"]),
        ])

    # Construir e adicionar tabela
    header_aligns = ["ThCell"] + ["ThCellCenter"] * (len(headers) - 1)
    header_aligns[0] = "ThCell"  # Primeira coluna esquerda
    col_aligns = ["LEFT"] + ["RIGHT"] * (len(headers) - 1)
    
    tabela = _construir_tabela(headers, rows, col_widths, set(), styles, header_aligns, col_aligns)
    elements.append(tabela)
    
    # Adicionar legenda dos asteriscos
    elements.append(Spacer(1, 2 * mm))
    elementos_legenda = [
    Paragraph(
        "<b>*</b> Não elegível desde maio/2026.<br/><b>**</b> Não elegível desde maio/2025.", 
        styles["RodaPe"]
    ),
]
    elements.extend(elementos_legenda)

    doc.build(elements, onFirstPage=_fundo_pagina, onLaterPages=_fundo_pagina)
    buf.seek(0)
    return buf.getvalue()
