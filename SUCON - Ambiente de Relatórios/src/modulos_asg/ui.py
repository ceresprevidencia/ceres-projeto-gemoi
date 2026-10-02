"""
Identidade visual do Painel de Controle Ceres aplicada ao Streamlit.

Reproduz o padrão das telas existentes (ex.: Rentabilidade - Planos):
barra superior com navegação, faixa verde-escura com título em duas
fontes, cards de indicador em bege com ícone de informação, painéis com
borda fina e cards de segmento com barra lateral colorida e anel.
"""
from __future__ import annotations

from html import escape

import plotly.graph_objects as go
import streamlit as st

# Paleta Ceres
VERDE = "#016837"
VERDE_ESCURO = "#0B2F13"
VERDE_VIVO = "#2DC25F"
VERDE_CLARO = "#A8EC7D"
OFF_WHITE = "#FAFBEB"
CARD = "#F3F4E3"
LINHA = "#DDE0CC"
TINTA = "#16210F"
TINTA_SUAVE = "#55624A"
CINZA_VERDE = "#5F7566"   # mesma cor das barras de benchmark
ALERTA = "#C0392B"
ATENCAO = "#D69E2E"

COR_NIVEL = {"ok": VERDE_VIVO, "atencao": ATENCAO, "alerta": ALERTA, "neutro": CINZA_VERDE}
COR_DIM = {"A": VERDE_VIVO, "S": VERDE, "G": CINZA_VERDE}

FONT_STACK = "'Figtree', -apple-system, 'Segoe UI', Roboto, sans-serif"
SERIF_STACK = "'Source Serif 4', Georgia, serif"

_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700;800&family=Source+Serif+4:ital,wght@0,600;0,700;1,600;1,700&display=swap');

html, body, [class*="css"], .stApp, .stMarkdown, button, input, textarea, select {{
  font-family: {FONT_STACK} !important;
}}
.stApp {{ background: {OFF_WHITE}; color: {TINTA}; }}

/* ---------- barra superior ---------- */
.ceres-nav {{
  width: 100vw; position: relative; left: 50%; margin-left: -50vw;
  background: {OFF_WHITE}; border-bottom: 1px solid {LINHA};
  display: flex; align-items: center; gap: 26px; padding: 10px 28px; height: 46px;
}}
.ceres-logo {{ font-weight: 800; font-size: 25px; color: {VERDE}; letter-spacing: -0.04em; margin-right: 10px; }}
.ceres-nav .item {{ font-size: 12.5px; color: {VERDE}; font-weight: 500; display: inline-flex; align-items: center; gap: 5px; }}
.ceres-nav .item::after {{ content: ''; width: 5px; height: 5px; border-right: 1.5px solid {VERDE};
  border-bottom: 1.5px solid {VERDE}; transform: rotate(45deg) translateY(-2px); }}
.ceres-nav .item.sem-menu::after {{ display: none; }}
.ceres-nav .item.ativo {{ font-weight: 700; color: {VERDE_ESCURO}; border-bottom: 2px solid {VERDE_VIVO}; padding-bottom: 2px; }}

/* ---------- faixa de título ---------- */
.ceres-hero {{
  width: 100vw; position: relative; left: 50%; margin-left: -50vw;
  background: {VERDE_ESCURO}; padding: 26px 20px; text-align: center; margin-bottom: 22px;
}}
.ceres-hero h1 {{ margin: 0; padding: 0; color: #FFFFFF; font-family: {FONT_STACK}; font-weight: 500; font-size: 23px; }}
.ceres-hero h1 em {{ font-family: {SERIF_STACK}; font-style: italic; font-weight: 700; color: {VERDE_CLARO}; }}
.ceres-hero .sub {{ color: #C9D8C2; font-size: 12.5px; margin-top: 6px; }}

/* ---------- rótulos de widgets ---------- */
[data-testid="stWidgetLabel"] p {{ font-size: 12px !important; color: {TINTA} !important; font-weight: 500; }}
[data-testid="stFileUploaderDropzone"] {{ background: {CARD}; border: 1px dashed #C9CDB4; border-radius: 6px; padding: 8px 14px; }}
.stButton > button, .stDownloadButton > button {{
  border-radius: 6px; font-weight: 600; font-size: 13px; border: 1px solid {LINHA};
  background: {CARD}; color: {VERDE_ESCURO};
}}
.stButton > button:hover, .stDownloadButton > button:hover {{ border-color: {VERDE}; color: {VERDE}; }}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {{
  background: {VERDE}; color: #fff; border-color: {VERDE};
}}
.stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover {{
  background: {VERDE_ESCURO}; color: #fff;
}}

/* ---------- abas (seletores para as versões baseweb e react-aria do Streamlit) ---------- */
.stTabs [data-baseweb="tab-list"], .stTabs [role="tablist"] {{ gap: 6px; border-bottom: 1px solid {LINHA}; }}
.stTabs [role="tab"] p {{ font-size: 13px !important; font-weight: 600; color: {TINTA_SUAVE}; }}
.stTabs [role="tab"][aria-selected="true"] p {{ color: {VERDE_ESCURO}; }}
.stTabs [data-baseweb="tab-highlight"] {{ background: {VERDE_VIVO}; }}

/* ---------- painéis com borda (st.container(border=True, key="painel_...")) ---------- */
[class*="st-key-painel"] {{ background: transparent; border: 1px solid {LINHA} !important; border-radius: 6px !important; padding: 6px 4px; }}

.titulo-painel {{ font-size: 13.5px; font-weight: 700; color: {TINTA}; margin: 2px 0 2px; }}
.sub-painel {{ font-size: 11.5px; color: {TINTA_SUAVE}; margin-bottom: 6px; }}
.titulo-secao {{ font-size: 14px; font-weight: 700; color: {TINTA}; margin: 22px 0 10px; }}

/* ---------- cards de indicador ---------- */
.kpi-row {{ display: grid; grid-template-columns: repeat(var(--n), 1fr); gap: 12px; margin: 4px 0 14px; }}
.kpi {{ background: {CARD}; border-radius: 8px; padding: 14px 16px 12px; position: relative;
  box-shadow: 0 1px 2px rgba(11,47,19,.06), 0 2px 6px rgba(11,47,19,.05); min-height: 96px; }}
.kpi .l {{ font-size: 12px; font-weight: 600; color: {TINTA}; }}
.kpi .v {{ font-size: 19px; font-weight: 700; color: {VERDE_ESCURO}; text-align: center; margin-top: 12px; }}
.kpi .s {{ font-size: 10.5px; color: {TINTA_SUAVE}; text-align: center; margin-top: 3px; }}
.kpi .s.neg {{ color: {ALERTA}; }} .kpi .s.pos {{ color: {VERDE}; }}
.kpi .info {{ position: absolute; top: 10px; right: 12px; width: 14px; height: 14px; border-radius: 50%;
  border: 1.3px solid {TINTA_SUAVE}; color: {TINTA_SUAVE}; font-size: 9px; font-weight: 700;
  display: flex; align-items: center; justify-content: center; cursor: help; font-family: Georgia, serif; }}
.kpi .barra {{ height: 6px; background: #DADDC6; border-radius: 4px; margin: 8px 6px 0; overflow: hidden; }}
.kpi .barra > div {{ height: 100%; background: {VERDE}; border-radius: 4px; }}

/* ---------- cards de segmento (eixos da dupla materialidade) ---------- */
.seg-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 8px; }}
.seg {{ background: {CARD}; border-radius: 6px; border-left: 4px solid var(--cor); padding: 14px 18px 14px 16px;
  display: grid; grid-template-columns: 132px 1fr; gap: 14px; align-items: center; }}
.seg .nome {{ grid-column: 1 / -1; font-size: 12.5px; font-weight: 600; color: {TINTA}; margin-bottom: -4px; }}
.seg .nome span {{ font-weight: 400; color: {TINTA_SUAVE}; font-size: 11px; margin-left: 6px; }}
.seg .linhas {{ font-size: 11.5px; color: {TINTA_SUAVE}; }}
.seg .linha {{ display: grid; grid-template-columns: 78px 1fr 30px; align-items: center; gap: 8px; margin: 6px 0; }}
.seg .linha b {{ color: {TINTA}; font-weight: 700; text-align: right; font-size: 11.5px; }}
.seg .mini {{ height: 5px; background: #DADDC6; border-radius: 4px; overflow: hidden; }}
.seg .mini > div {{ height: 100%; border-radius: 4px; }}
.seg .leitura {{ font-size: 11px; margin-top: 8px; color: {TINTA_SUAVE}; }}
.seg .leitura b {{ color: var(--cor-nivel); }}

/* ---------- chips e estados ---------- */
.chips {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 2px 0 12px; }}
.chip {{ display: inline-flex; align-items: center; gap: 6px; background: {CARD}; border-radius: 100px;
  padding: 4px 12px; font-size: 11.5px; font-weight: 600; color: {VERDE_ESCURO}; }}
.chip i {{ width: 7px; height: 7px; border-radius: 50%; display: inline-block; }}
.vazio {{ background: {CARD}; border-radius: 8px; padding: 40px 30px; text-align: center; margin-top: 10px; }}
.vazio h3 {{ font-family: {SERIF_STACK}; color: {VERDE_ESCURO}; font-size: 20px; margin: 0 0 8px; }}
.vazio p {{ color: {TINTA_SUAVE}; font-size: 13px; max-width: 620px; margin: 0 auto 6px; line-height: 1.6; }}
.aviso {{ background: {CARD}; border-left: 3px solid {ATENCAO}; border-radius: 4px; padding: 10px 14px;
  font-size: 12px; color: {TINTA_SUAVE}; margin: 6px 0 12px; line-height: 1.55; }}
.aviso.ok {{ border-left-color: {VERDE_VIVO}; }}

@media (max-width: 900px) {{
  .kpi-row {{ grid-template-columns: repeat(2, 1fr); }}
  .seg-row {{ grid-template-columns: 1fr; }}
  .ceres-nav .item {{ display: none; }}
}}
</style>
"""


# Regras só para o app isolado: no Painel de Controle o menu (st.navigation) vive
# dentro do header e as páginas usam padding-top próprio.
_CSS_SOMENTE_ISOLADO = """
<style>
header[data-testid="stHeader"], #MainMenu, footer, [data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }
.block-container { padding-top: 0 !important; padding-bottom: 4rem; max-width: 1180px; }
</style>
"""


def aplicar_tema(integrado: bool = False) -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    if not integrado:
        st.markdown(_CSS_SOMENTE_ISOLADO, unsafe_allow_html=True)


def navbar(itens: list[str], ativo: str) -> None:
    html = "".join(
        f"<span class='item {'ativo sem-menu' if i == ativo else ''}'>{escape(i)}</span>" for i in itens)
    st.markdown(f"<div class='ceres-nav'><span class='ceres-logo'>Ceres</span>{html}</div>",
                unsafe_allow_html=True)


def hero(titulo: str, destaque: str, sub: str | None = None) -> None:
    sub_html = f"<div class='sub'>{escape(sub)}</div>" if sub else ""
    st.markdown(f"<div class='ceres-hero'><h1>{escape(titulo)} - <em>{escape(destaque)}</em></h1>{sub_html}</div>",
                unsafe_allow_html=True)


def kpis(cards: list[dict]) -> None:
    """cards: [{l, v, s?, s_cls?, info?, barra?(0-100)}]"""
    partes = []
    for c in cards:
        info = f"<span class='info' title='{escape(c['info'])}'>i</span>" if c.get("info") else ""
        sub = f"<div class='s {c.get('s_cls', '')}'>{c['s']}</div>" if c.get("s") else ""
        barra = (f"<div class='barra'><div style='width:{max(0, min(100, c['barra'])):.1f}%'></div></div>"
                 if c.get("barra") is not None else "")
        partes.append(f"<div class='kpi'>{info}<div class='l'>{escape(c['l'])}</div>"
                      f"<div class='v'>{c['v']}</div>{sub}{barra}</div>")
    st.markdown(f"<div class='kpi-row' style='--n:{len(cards)}'>{''.join(partes)}</div>", unsafe_allow_html=True)


def chips(itens: list[tuple[str, str]]) -> None:
    st.markdown("<div class='chips'>" + "".join(
        f"<span class='chip'><i style='background:{cor}'></i>{texto}</span>" for texto, cor in itens) + "</div>",
                unsafe_allow_html=True)


def _anel(valor: float | None, cor: str) -> str:
    """Anel em arco (mesmo desenho dos cards de segmento), escala 0-10."""
    r, cx, cy, esp = 50, 62, 62, 13
    import math
    abertura = 70  # graus abertos embaixo, como no painel de rentabilidade
    ini, fim = 90 + abertura / 2, 90 + 360 - abertura / 2

    def ponto(ang):
        a = math.radians(ang)
        return cx + r * math.cos(a), cy + r * math.sin(a)

    def arco(a0, a1):
        x0, y0 = ponto(a0)
        x1, y1 = ponto(a1)
        grande = 1 if (a1 - a0) > 180 else 0
        return f"M {x0:.2f} {y0:.2f} A {r} {r} 0 {grande} 1 {x1:.2f} {y1:.2f}"

    frac = 0 if valor is None else max(0.0, min(1.0, valor / 10))
    fundo = f"<path d='{arco(ini, fim)}' stroke='#DADDC6' stroke-width='{esp}' fill='none' stroke-linecap='round'/>"
    frente = (f"<path d='{arco(ini, ini + (fim - ini) * frac)}' stroke='{cor}' stroke-width='{esp}' fill='none' "
              f"stroke-linecap='round'/>") if frac > 0.005 else ""
    txt = "N/D" if valor is None else f"{valor:.1f}".replace(".", ",")
    return (f"<svg viewBox='0 0 124 118' width='124' height='118' role='img' aria-label='score {txt} de 10'>"
            f"{fundo}{frente}"
            f"<text x='62' y='64' text-anchor='middle' font-size='22' font-weight='700' fill='{TINTA}' "
            f"font-family=\"Figtree, sans-serif\">{txt}</text>"
            f"<text x='62' y='80' text-anchor='middle' font-size='9' fill='{TINTA_SUAVE}' "
            f"font-family=\"Figtree, sans-serif\">de 10</text></svg>")


def cards_eixos(eixos: list[dict]) -> None:
    """eixos: [{nome, sub, cor, scores{A,S,G,geral}, leitura, cor_nivel}]"""
    blocos = []
    for e in eixos:
        linhas = ""
        for d, rot in (("A", "Ambiental"), ("S", "Social"), ("G", "Governança")):
            v = e["scores"][d]
            w = 0 if v is None else v * 10
            vtxt = "N/D" if v is None else f"{v:.1f}".replace(".", ",")
            linhas += (f"<div class='linha'><span>{rot}</span><div class='mini'>"
                       f"<div style='width:{w:.0f}%;background:{COR_DIM[d]}'></div></div><b>{vtxt}</b></div>")
        blocos.append(
            f"<div class='seg' style='--cor:{e['cor']};--cor-nivel:{e['cor_nivel']}'>"
            f"<div class='nome'>{escape(e['nome'])}<span>{escape(e['sub'])}</span></div>"
            f"<div>{_anel(e['scores']['geral'], e['cor'])}</div>"
            f"<div class='linhas'>{linhas}<div class='leitura'>Leitura consolidada: <b>{e['leitura']}</b></div></div>"
            f"</div>")
    st.markdown(f"<div class='seg-row'>{''.join(blocos)}</div>", unsafe_allow_html=True)


def titulo_painel(titulo: str, sub: str | None = None) -> None:
    st.markdown(f"<div class='titulo-painel'>{escape(titulo)}</div>"
                + (f"<div class='sub-painel'>{sub}</div>" if sub else ""), unsafe_allow_html=True)


def titulo_secao(titulo: str) -> None:
    st.markdown(f"<div class='titulo-secao'>{escape(titulo)}</div>", unsafe_allow_html=True)


def aviso(texto: str, ok: bool = False) -> None:
    st.markdown(f"<div class='aviso {'ok' if ok else ''}'>{texto}</div>", unsafe_allow_html=True)


def layout_plotly(fig: go.Figure, altura: int = 360) -> go.Figure:
    fig.update_layout(
        height=altura, margin=dict(l=8, r=16, t=10, b=8),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Figtree, sans-serif", size=11.5, color=TINTA),
        hoverlabel=dict(bgcolor="#FFFFFF", font_size=12, font_family="Figtree, sans-serif",
                        bordercolor=LINHA),
        separators=",.", showlegend=False,
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=LINHA, tickfont=dict(color=TINTA_SUAVE))
    fig.update_yaxes(showgrid=False, zeroline=False, tickfont=dict(color=TINTA))
    return fig


PLOTLY_CONFIG = {"displayModeBar": False, "locale": "pt-BR"}

# Compatibilidade entre versões do Streamlit: a partir da 1.50 o parâmetro
# use_container_width foi substituído por width="stretch".
def _versao(v: str) -> tuple[int, int]:
    partes = (v.split(".") + ["0"])[:2]
    return tuple(int("".join(ch for ch in x if ch.isdigit()) or 0) for x in partes)


ESTICAR = {"width": "stretch"} if _versao(st.__version__) >= (1, 50) else {"use_container_width": True}


def embutir_html(html: str, altura: int = 900) -> None:
    if hasattr(st, "iframe"):
        st.iframe(html, height=altura)
    else:
        import streamlit.components.v1 as components
        components.html(html, height=altura, scrolling=True)
