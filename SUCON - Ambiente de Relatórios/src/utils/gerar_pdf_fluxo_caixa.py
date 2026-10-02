"""
PDF do painel Risco de Liquidez - Fluxo de Caixa.

Recebe o dict de `utils.fluxo_caixa.calcular_painel` e monta um relatório A4
paisagem no padrão visual dos demais relatórios (gerar_pdf.py). Os gráficos são
desenhados com reportlab.graphics, sem dependência de Kaleido/Chrome.
"""

from __future__ import annotations

from io import BytesIO
from xml.sax.saxutils import escape

import pandas as pd
from reportlab.graphics.shapes import Drawing, Line, PolyLine, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

try:  # reaproveita fontes e logo do módulo principal de PDFs
    from utils.gerar_pdf import FONTES, LOGO_RELATIVE_PATH, _resolve_asset_path, svg_arquivo_para_flowable
except Exception:  # pragma: no cover - ambiente isolado
    class _Fontes:
        regular, bold, italic_serif = "Helvetica", "Helvetica-Bold", "Times-Italic"
    FONTES, LOGO_RELATIVE_PATH = _Fontes(), None
    _resolve_asset_path = svg_arquivo_para_flowable = None

VERDE_TITULO = colors.HexColor("#0B2F13")
VERDE_ESCURO = colors.HexColor("#016837")
VERDE_CLARO = colors.HexColor("#A8EC7D")
VERDE_OK = colors.HexColor("#2DC25F")
AMBAR = colors.HexColor("#E8A33D")
VERMELHO = colors.HexColor("#D64550")
CINZA = colors.HexColor("#5a5a5a")
CINZA_BORDA = colors.HexColor("#dddddd")
FUNDO = colors.HexColor("#FAFBEB")
ZEBRA = colors.HexColor("#F1F2DE")
TEXTO = colors.HexColor("#333333")

MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
LARGURA_UTIL = landscape(A4)[0] - 2.4 * cm


# ── FORMATAÇÃO ───────────────────────────────────────────────────────────────

def _br(valor, casas=2):
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _brl_curto(v):
    if pd.isna(v):
        return "—"
    a = abs(v)
    for lim, suf in [(1e9, " Bi"), (1e6, " Mi"), (1e3, " Mil")]:
        if a >= lim:
            return f"R$ {_br(v / lim, 1)}{suf}"
    return f"R$ {_br(v)}"


def _brl(v):
    return "—" if pd.isna(v) else f"R$ {_br(v)}"


def _pct(v, casas=0):
    return "—" if pd.isna(v) else f"{_br(v * 100, casas)}%"


def _anos(v):
    return "—" if pd.isna(v) else _br(v, 1)


def _liq(v):
    return "Sem necessidade" if not v else _brl_curto(v)


def _dur(a, p):
    return f"{_anos(a)} | {_anos(p)}"


def _eixo_curto(v):
    a = abs(v)
    for lim, suf in [(1e9, "B"), (1e6, "M"), (1e3, "k")]:
        if a >= lim:
            casas = 1 if a / lim < 10 else 0
            return f"{_br(v / lim, casas)}{suf}"
    return _br(v, 0)


# ── ESTILOS ──────────────────────────────────────────────────────────────────

def _estilos():
    return {
        "titulo": ParagraphStyle("t", fontName=FONTES.regular, fontSize=20, textColor=VERDE_TITULO, alignment=TA_CENTER, leading=24),
        "secao": ParagraphStyle("s", fontName=FONTES.bold, fontSize=12.5, textColor=VERDE_TITULO, spaceBefore=4, spaceAfter=6),
        "texto": ParagraphStyle("x", fontName=FONTES.regular, fontSize=9.5, textColor=TEXTO, leading=13, alignment=TA_JUSTIFY),
        "nota": ParagraphStyle("n", fontName=FONTES.regular, fontSize=8.3, textColor=CINZA, leading=11.5, alignment=TA_JUSTIFY),
        "kpi_rot": ParagraphStyle("kr", fontName=FONTES.regular, fontSize=8, textColor=CINZA, alignment=TA_CENTER, leading=10),
        "kpi_val": ParagraphStyle("kv", fontName=FONTES.bold, fontSize=13, textColor=VERDE_TITULO, alignment=TA_CENTER, leading=16),
    }


def _fundo_rodape(canvas, doc):
    largura, altura = landscape(A4)
    canvas.saveState()
    canvas.setFillColor(FUNDO)
    canvas.rect(0, 0, largura, altura, stroke=0, fill=1)
    canvas.setFont(FONTES.regular, 7)
    canvas.setFillColor(TEXTO)
    canvas.drawCentredString(largura / 2, 0.75 * cm, f"Risco de Liquidez - Fluxo de Caixa | Página {doc.page}")
    canvas.restoreState()


def _cabecalho(est, plano_nome):
    titulo = Paragraph(
        f"Risco de Liquidez - <font name='{FONTES.italic_serif}'><i>Fluxo de Caixa</i></font>"
        f"<br/><font size='11' color='#5a5a5a'>{escape(plano_nome)}</font>",
        est["titulo"],
    )
    logo = ""
    if _resolve_asset_path and LOGO_RELATIVE_PATH:
        caminho = _resolve_asset_path(LOGO_RELATIVE_PATH)
        if caminho:
            try:
                logo = svg_arquivo_para_flowable(caminho, width=3.2 * cm, height=0.9 * cm, h_align="RIGHT")
            except Exception:
                logo = ""
    t = Table([["", titulo, logo]], colWidths=[3.2 * cm, LARGURA_UTIL - 6.4 * cm, 3.2 * cm], rowHeights=[1.9 * cm])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (2, 0), (2, 0), "RIGHT")]))
    return t


# ── BLOCOS ───────────────────────────────────────────────────────────────────

def _cards(est, itens):
    """Linha de cards: lista de (rótulo, valor)."""
    celulas = [[Paragraph(escape(r), est["kpi_rot"]), Spacer(1, 3), Paragraph(escape(v), est["kpi_val"])] for r, v in itens]
    largura = LARGURA_UTIL / len(itens)
    t = Table([celulas], colWidths=[largura] * len(itens), rowHeights=[1.55 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F1E4")),
        ("LINEAFTER", (0, 0), (-2, -1), 3, FUNDO),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEABOVE", (0, 0), (-1, 0), 1.2, VERDE_ESCURO),
    ]))
    return t


def _tabela(df: pd.DataFrame, larguras=None, destacar_linha=None, compacta=False):
    dados = [list(df.columns)] + df.astype(str).values.tolist()
    larguras = larguras or [LARGURA_UTIL / len(df.columns)] * len(df.columns)
    t = Table(dados, colWidths=larguras, repeatRows=1)
    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), VERDE_TITULO),
        ("TEXTCOLOR", (0, 0), (-1, 0), VERDE_CLARO),
        ("FONTNAME", (0, 0), (-1, 0), FONTES.bold),
        ("FONTNAME", (0, 1), (-1, -1), FONTES.regular),
        ("FONTSIZE", (0, 0), (-1, -1), 7.2 if compacta else 8),
        ("TEXTCOLOR", (0, 1), (-1, -1), TEXTO),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, CINZA_BORDA),
        ("TOPPADDING", (0, 0), (-1, -1), 1.6 if compacta else 3.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6 if compacta else 3.2),
    ]
    for i in range(2, len(dados), 2):
        cmds.append(("BACKGROUND", (0, i), (-1, i), ZEBRA))
    if destacar_linha is not None:
        cmds += [("FONTNAME", (0, destacar_linha + 1), (-1, destacar_linha + 1), FONTES.bold),
                 ("BACKGROUND", (0, destacar_linha + 1), (-1, destacar_linha + 1), colors.HexColor("#E3F5D6"))]
    t.setStyle(TableStyle(cmds))
    return t


def _grafico(rotulos, publicos, privados, necessidade, linha2=None, linha2_nome="", linha2_pct=False,
             largura=LARGURA_UTIL, altura=7.2 * cm, caixa=None):
    """Barras empilhadas (público/privado) + necessidade tracejada + linha opcional no eixo direito."""
    d = Drawing(largura, altura)
    esq, dir_, base, topo = 48, 48 if linha2 is not None else 12, 34, altura - 22
    area_l, area_a = largura - esq - dir_, topo - base
    n = len(rotulos)
    if n == 0:
        return d

    caixa = list(caixa) if caixa is not None else [0.0] * n
    totais = [p + q + c for p, q, c in zip(publicos, privados, caixa)]
    vmax = max(max(totais), max(necessidade) if necessidade else 0) * 1.1 or 1
    passo = area_l / n
    larg_barra = passo * 0.7

    for i in range(5):  # grade + eixo esquerdo
        y = base + area_a * i / 4
        d.add(Line(esq, y, esq + area_l, y, strokeColor=CINZA_BORDA, strokeWidth=0.4))
        d.add(String(esq - 4, y - 3, _eixo_curto(vmax * i / 4), fontName=FONTES.regular, fontSize=6.5, fillColor=CINZA, textAnchor="end"))

    salto = max(1, n // 30)
    for i, (rot, p, q, cx) in enumerate(zip(rotulos, publicos, privados, caixa)):
        x = esq + i * passo + (passo - larg_barra) / 2
        hp, hq, hc = area_a * p / vmax, area_a * q / vmax, area_a * cx / vmax
        if hc > 0:
            d.add(Rect(x, base + hp + hq, larg_barra, hc, fillColor=colors.HexColor("#E8D9A8"), strokeColor=None))
        if hp > 0:
            d.add(Rect(x, base, larg_barra, hp, fillColor=VERDE_ESCURO, strokeColor=None))
        if hq > 0:
            d.add(Rect(x, base + hp, larg_barra, hq, fillColor=VERDE_CLARO, strokeColor=None))
        if i % salto == 0:
            d.add(String(x + larg_barra / 2, base - 11, rot, fontName=FONTES.regular, fontSize=6.3, fillColor=TEXTO, textAnchor="middle"))

    centro = lambda i: esq + i * passo + passo / 2  # noqa: E731
    if necessidade and max(necessidade) > 0:
        pts = []
        for i, v in enumerate(necessidade):
            pts += [centro(i), base + area_a * v / vmax]
        d.add(PolyLine(pts, strokeColor=VERMELHO, strokeWidth=1.6, strokeDashArray=[4, 2.5]))

    if linha2 is not None and len(linha2):
        vals = [0 if pd.isna(v) else (min(v, 3.0) if linha2_pct else v) for v in linha2]  # cobertura limitada a 300%
        lo, hi = min(min(vals), 0), max(max(vals), 0)
        hi = hi if hi != lo else lo + 1
        norm = lambda v: base + area_a * (v - lo) / (hi - lo)  # noqa: E731
        pts = []
        for i, v in enumerate(vals):
            pts += [centro(i), norm(v)]
        d.add(PolyLine(pts, strokeColor=colors.HexColor("#6D597A") if linha2_pct else CINZA, strokeWidth=1.2))
        for i in range(5):
            v = lo + (hi - lo) * i / 4
            d.add(String(esq + area_l + 4, base + area_a * i / 4 - 3, _pct(v) if linha2_pct else _eixo_curto(v),
                         fontName=FONTES.regular, fontSize=6.5, fillColor=CINZA))

    legenda = [(VERDE_ESCURO, "Títulos públicos", False), (VERDE_CLARO, "Títulos privados", False)]
    if any(caixa):
        legenda.append((colors.HexColor("#E8D9A8"), "Fundos caixa D0", False))
    if necessidade and max(necessidade) > 0:
        legenda.append((VERMELHO, "Necessidade líquida", True))
    if linha2 is not None:
        legenda.append((colors.HexColor("#6D597A") if linha2_pct else CINZA, linha2_nome, True))
    x = esq
    for cor, nome, linha in legenda:
        if linha:
            d.add(Line(x, altura - 8, x + 14, altura - 8, strokeColor=cor, strokeWidth=1.6))
        else:
            d.add(Rect(x, altura - 12, 9, 8, fillColor=cor, strokeColor=None))
        d.add(String(x + 18, altura - 11, nome, fontName=FONTES.regular, fontSize=7.5, fillColor=TEXTO))
        x += 30 + len(nome) * 4.2
    return d


def _tabela_fluxo(df, rotulos, tem_passivo, com_caixa=False):
    f = _brl_curto
    out = pd.DataFrame({"Período": rotulos, "Públicos": df["PUBLICOS"].map(f),
                        "Privados": df["PRIVADOS"].map(f), "Recebimentos": df["RECEBIMENTOS"].map(f)})
    if com_caixa:
        out["Caixa D0"] = df["CAIXA"].map(f)
    if tem_passivo:
        out["Necessidade"] = df["NECESSIDADE"].map(f)
        out["Saldo"] = df["SALDO"].map(f)
        out["Saldo acumulado"] = df["SALDO_ACUM"].map(f)
        out["Cobertura"] = df["COBERTURA"].map(_pct)
    return out


# ── RELATÓRIO ────────────────────────────────────────────────────────────────

def gerar_pdf_fluxo_caixa(res: dict, nome_exibicao=lambda x: x) -> bytes:
    est = _estilos()
    k, mensal, anual_df = res["kpis"], res["mensal"], res["anual"]
    db, plano, ano_fim = res["data_base"], res["plano"], res["ano_fim"]
    tem_passivo = k["tem_passivo"]
    nome = nome_exibicao(plano)
    prem, com_caixa = res["premissas"], res["com_caixa"]
    base = "fluxo nominal" if res["base"] == "nominal" else "valor presente (curva implícita nos títulos públicos)"
    distrib = "13 parcelas (dezembro em dobro)" if res["treze_parcelas"] else "média ÷ 12"
    passivo_txt = (f"real de {prem['data_referencia_passivo']:%d/%m/%Y} corrigido por IPCA {_pct(res['ipca_aa'], 2)} a.a."
                   if prem["passivo_em_valores_reais"] else "nominal")
    if res["deduzir_contrib_ativos"]:
        passivo_txt += ", líquido de contribuições de ativos"

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=1.2 * cm, rightMargin=1.2 * cm,
                            topMargin=1.0 * cm, bottomMargin=1.3 * cm, title=f"Fluxo de Caixa - {nome}")
    el = [_cabecalho(est, nome), Spacer(1, 0.2 * cm)]

    el.append(Paragraph(
        "Confronto entre os recebimentos programados da carteira de renda fixa (cupons e vencimentos de títulos "
        "públicos e privados)" + (", somados aos fundos caixa D0," if com_caixa else "") +
        " e a necessidade líquida de caixa previdencial — pagamentos de benefícios menos contribuições de assistidos, "
        "conforme a avaliação atuarial.", est["texto"]))
    el.append(Spacer(1, 0.15 * cm))
    el.append(Paragraph(
        f"<b>Data-base:</b> {db:%d/%m/%Y} &nbsp;&nbsp; <b>Horizonte:</b> até {ano_fim} &nbsp;&nbsp; "
        f"<b>Base:</b> {base} &nbsp;&nbsp; <b>Passivo:</b> {passivo_txt}, {distrib}", est["texto"]))
    if not tem_passivo:
        el.append(Spacer(1, 0.15 * cm))
        el.append(Paragraph("<b>Plano sem fluxo previdencial na avaliação atuarial:</b> exibidos apenas os recebimentos.", est["texto"]))
    el.append(Spacer(1, 0.35 * cm))

    sem = (lambda v: v) if tem_passivo else (lambda v: "—")
    el.append(Paragraph("Próximos 12 meses", est["secao"]))
    el.append(_cards(est, [
        ("Recebimentos + caixa" if com_caixa else "Recebimentos", _brl_curto(k["recursos_12m"])),
        ("Necessidade líquida", sem(_brl_curto(k["nec_12m"]))),
        ("Cobertura", _pct(k["cobertura_12m"])),
        ("Saldo líquido", sem(_brl_curto(k["saldo_12m"]))),
        ("Necessidade de liquidez 12m", sem(_liq(k["liquidez_12m"]))),
    ]))
    el.append(Spacer(1, 0.3 * cm))
    el.append(Paragraph("Liquidez e prazos", est["secao"]))
    el.append(_cards(est, [
        ("Necessidade de liquidez 24m", sem(_liq(k["liquidez_24m"]))),
        ("Cobertura em 5 anos", _pct(k["cobertura_5a"])),
        ("1º ano em déficit", sem(str(k["primeiro_ano_deficit"] or "Nenhum"))),
        ("Duration ativo | passivo (anos)", _dur(k["duration_ativo"], k["duration_passivo"])),
        (f"Passivo após {k['ultimo_ano_receb']}", sem(_pct(k["nec_pos_receb_pct"], 1))),
    ]))
    el.append(Spacer(1, 0.45 * cm))

    rot_anual = [f"{a}*" if a == db.year else str(a) for a in anual_df["ANO"]]
    el.append(KeepTogether([
        Paragraph("Recursos × necessidade líquida — anual", est["secao"]),
        _grafico(rot_anual, anual_df["PUBLICOS"].tolist(), anual_df["PRIVADOS"].tolist(),
                 anual_df["NECESSIDADE"].tolist() if tem_passivo else [],
                 linha2=anual_df["COBERTURA"].tolist() if tem_passivo else None, linha2_nome="Cobertura (eixo dir.)",
                 linha2_pct=True, altura=6.6 * cm, caixa=anual_df["CAIXA"].tolist()),
    ]))

    # Página 2: mensal 24 meses + comparativo
    el.append(PageBreak())
    m24 = mensal.head(24)
    rot_m = [f"{MESES[m - 1]}/{str(a)[2:]}" for a, m in zip(m24["ANO"], m24["MES"])]
    el.append(KeepTogether([
        Paragraph("Recursos × necessidade líquida — próximos 24 meses", est["secao"]),
        _grafico(rot_m, m24["PUBLICOS"].tolist(), m24["PRIVADOS"].tolist(),
                 m24["NECESSIDADE"].tolist() if tem_passivo else [],
                 linha2=m24["SALDO_ACUM"].tolist() if tem_passivo else None, linha2_nome="Saldo acumulado (eixo dir.)",
                 altura=5.6 * cm, caixa=m24["CAIXA"].tolist()),
    ]))
    el.append(Spacer(1, 0.25 * cm))

    rk = res["ranking"].copy()
    rk["_o"] = rk["nec_12m"].where(rk["tem_passivo"], -1)
    rk = rk.sort_values(["_o", "receb_12m"], ascending=False).reset_index(drop=True)
    tp = rk["tem_passivo"]
    tabela_rk = pd.DataFrame({
        "Plano": rk["TESOURARIA"].map(nome_exibicao),
        "Receb. 12m": rk["receb_12m"].map(_brl_curto),
        "Necess. 12m": [_brl_curto(v) if t else "sem fluxo" for v, t in zip(rk["nec_12m"], tp)],
        "Cobert. 12m": rk["cobertura_12m"].map(_pct),
        "Liquidez 12m": [_liq(v) if t else "—" for v, t in zip(rk["liquidez_12m"], tp)],
        "Liquidez 24m": [_liq(v) if t else "—" for v, t in zip(rk["liquidez_24m"], tp)],
        "Cobert. 5 anos": rk["cobertura_5a"].map(_pct),
        "1º ano déficit": [str(int(v)) if pd.notna(v) else ("Nenhum" if t else "—") for v, t in zip(rk["primeiro_ano_deficit"], tp)],
        "Duration A | P": [_dur(a, b) for a, b in zip(rk["duration_ativo"], rk["duration_passivo"])],
    })
    destaque = rk.index[rk["TESOURARIA"] == plano]
    larg = [4.6 * cm] + [(LARGURA_UTIL - 4.6 * cm) / 8] * 8
    el.append(Paragraph("Comparativo por plano", est["secao"]))
    el.append(_tabela(tabela_rk, larg, destaque[0] if len(destaque) else None, compacta=len(tabela_rk) > 12))

    # Página 3: tabela anual + nota
    el.append(PageBreak())
    el.append(Paragraph("Fluxo anual do horizonte", est["secao"]))
    el.append(_tabela(_tabela_fluxo(anual_df, rot_anual, tem_passivo, com_caixa), compacta=len(anual_df) > 15))
    el.append(Spacer(1, 0.3 * cm))
    planos_calc = ", ".join(nome_exibicao(p) for p in res["planos_calculo"])
    el.append(KeepTogether([
        Paragraph("Nota metodológica", est["secao"]),
        Paragraph(
            "<b>Ativo:</b> recebimentos programados da consulta [SUCON] Projeção Rendimentos na data-base; títulos públicos "
            "federais identificados pelo nome do produto (NTN, LTN, LFT)"
            + ("; fundos caixa D0 somados como recurso disponível no mês da data-base. " if com_caixa else ". ")
            + "<b>Passivo:</b> linha \"Fluxos de seguridade para o cálculo da duration (Fi)\" da avaliação atuarial com sinal "
            f"invertido (benefícios − contribuições de assistidos), {passivo_txt}. "
            f"<b>Base:</b> {base}; ativo e passivo sempre na mesma base. Duration de ambos pela curva implícita nos títulos públicos. "
            f"<b>Necessidade de liquidez:</b> maior déficit acumulado na janela. "
            f"<b>Distribuição mensal:</b> ano da data-base pro rata (marcado com *); demais anos {distrib}. "
            "<b>Limitações:</b> não considera ativos líquidos sem fluxo programado, reinvestimento, renda variável, imóveis e "
            "fundos. EROS FIM fora do consolidado para evitar dupla contagem. "
            f"<b>Planos no cálculo:</b> {escape(planos_calc)}.", est["nota"]),
    ]))

    doc.build(el, onFirstPage=_fundo_rodape, onLaterPages=_fundo_rodape)
    return buffer.getvalue()