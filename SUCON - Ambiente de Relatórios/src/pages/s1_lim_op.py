import zipfile
from io import BytesIO
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.gerar_pdf import gerar_pdf_limites_operacionais
from utils.helpers import fmt_br, gerar_tabela_estilizada, nome_plano
from utils.queries.lim_operacionais import buscar_dados


# ── CONSTANTES ────────────────────────────────────────────────────────────────

# Limite de alocação vigente para 2026 (R$)
LIMITE_ALOCACAO_2026 = 100_000_000.00

# Data de corte para classificar alocações como "2026"
DATA_CORTE_2026 = pd.to_datetime("2026-01-01")

# Colunas a exibir na tabela principal (mapeamento interno → amigável)
COLUNAS_EXIBIR = {
    "EXPOSICAO": "Posição R$",
    "EXPOSICAO_2026": "Posição 2026 R$",
    "FINANCEIRO_AQUISICAO": "Alocação 2026 R$",
    "LIMITE_ALOCACAO_2026": "Limite Operacional R$",
}

# Dados estáticos das instituições financeiras e seus limites
DADOS_LIMITES = [
    ["BANCO COOPEREATIVO SICREDI S.A.",        "SICREDI",            None, None, None, LIMITE_ALOCACAO_2026],
    ["Banco Cooperativo do Brasil S.A.",        "BANCO SICOOB",       None, None, None, LIMITE_ALOCACAO_2026],
    ["Banco Safra S.A.",                        "SAFRA",              None, None, None, LIMITE_ALOCACAO_2026],
    ["ITAU UNIBANCO S.A.",                      "ITAÚ UNIBANCO",      None, None, None, LIMITE_ALOCACAO_2026],
    ["BANCO ABC BRASIL S.A.",                   "ABC BRASIL",         None, None, None, LIMITE_ALOCACAO_2026],
    ["BANCO BTG PACTUAL S.A.",                  "BTG PACTUAL",        None, None, None, LIMITE_ALOCACAO_2026],
    ["BANCO DAYCOVAL S/A",                      "DAYCOVAL",           None, None, None, LIMITE_ALOCACAO_2026],
    ["BANCO MERCANTIL DO BRASIL SA",            "MERCANTIL",          None, None, None, LIMITE_ALOCACAO_2026],
    ["BANCO SANTANDER (BRASIL) S.A.",           "SANTANDER (BRASIL)", None, None, None, LIMITE_ALOCACAO_2026],
    ["BANCO VOTORANTIM S.A.",                   "BANCO BV",           None, None, None, LIMITE_ALOCACAO_2026],
    ["BANCO SOFISA SA",                         "SOFISA",             None, None, None, LIMITE_ALOCACAO_2026],
    ["BANCO BRADESCO SA",                       "BRADESCO (*)",       None, None, None, None],
    ["PARANA BANCO S/A",                        "PARANA BANCO (*)",   None, None, None, None],
    ["BANCO PAN S.A.",                          "PAN (**)",           None, None, None, None],
]

# Dados estáticos de classificação de risco das IFs
DADOS_RISCO = [
    ["ABC BRASIL",         "Médio Porte",  11.02, None, 6_604_060.00,   "Até 5 anos",  "BRLP 3"],
    ["BANCO BV",           "Grande Porte",  9.77, None, 13_397_130.00,  "Até 5 anos",  "BRLP 3"],
    ["SOFISA",             "Médio Porte",   9.19, None, 1_144_639.00,   "Até 3 anos",  "BRMP 1"],
    ["SICREDI",            "Grande Porte", 11.35, None, 5_432_089.00,   "Até 5 anos",  "BRLP 3"],
    ["BANCO SICOOB",       "Grande Porte", 11.25, None, 5_505_854.00,   "Até 5 anos",  "BRLP 3"],
    ["BTG PACTUAL",        "Grande Porte", 10.68, None, 69_335_302.00,  "Até 5 anos",  "BRLP 3"],
    ["DAYCOVAL",           "Médio Porte",  10.44, None, 7_666_905.00,   "Até 5 anos",  "BRLP 3"],
    ["ITAÚ UNIBANCO",      "Grande Porte", 11.17, None, 209_552_000.00, "Até 10 anos", "BRLP 1"],
    ["MERCANTIL",          "Médio Porte",  10.07, None, 2_106_362.00,   "Até 3 anos",  "BRMP 1"],
    ["SAFRA",              "Grande Porte", 11.25, None, 19_777_134.00,  "Até 5 anos",  "BRLP 3"],
    ["SANTANDER (BRASIL)", "Grande Porte",  9.91, None, 94_089_614.00,  "Até 10 anos", "BRLP 1"],
    ["BRADESCO (*)",       "Médio Porte",   9.19, "CI", 1_144_639.00,   "Até 3 anos",  "BRMP 1"],
    ["PARANA BANCO (*)",   "Médio Porte",   9.19, "A",  1_144_639.00,   "Até 3 anos",  "BRMP 1"],
    ["PAN (**)",           "Médio Porte",   9.19, None, 1_144_639.00,   "Até 3 anos",  "BRMP 1"],
]

COLUNAS_LIMITES = ["ID_MITRA", "INSTITUICAO_FINANCEIRA", "EXPOSICAO", "EXPOSICAO_2026", "FINANCEIRO_AQUISICAO", "LIMITE_ALOCACAO_2026"]
COLUNAS_RISCO   = ["Instituição Financeira", "Porte da Instituição", "Índice RiskBank", "Alerta", "Patrimônio Líquido (R$ Mil)", "Prazo Máximo de Aplicação", "Classificação de Risco"]


# ── HELPERS LOCAIS ────────────────────────────────────────────────────────────

def card_titulo(texto: str):
    """Renderiza um badge verde escuro com texto verde claro (padrão visual do sistema)."""
    st.markdown(
        f'<span style="background-color:#0b2f13; color:#a8ec7d; font-size:20px; '
        f'padding:1px 5px; border-radius:6px; font-weight:normal; display:inline-block;">{texto}</span>',
        unsafe_allow_html=True,
    )


def gasto_card(titulo: str, gasto: float, limite: float):
    """
    Renderiza um card de progresso com barra colorida (verde → laranja → vermelho)
    conforme o percentual do limite utilizado.
    """
    pct = min(max(gasto / limite * 100, 0), 100)

    # Interpolação de cor: verde(63,196,87) → laranja(186,117,23) → vermelho(226,75,74)
    def lerp(a, b, t): return a + (b - a) * t
    p = pct / 100
    if p <= 0.5:
        t = p / 0.5
        r, g, b = int(lerp(99, 186, t)), int(lerp(196, 117, t)), int(lerp(87, 23, t))
    else:
        t = (p - 0.5) / 0.5
        r, g, b = int(lerp(186, 226, t)), int(lerp(117, 75, t)), int(lerp(23, 74, t))

    color    = f"rgb({r},{g},{b})"
    card_bg  = f"rgba({r},{g},{b},{round(pct / 100 * 0.08, 4)})"

    # Cor do badge por faixa de percentual
    if    pct < 30: badge_bg, badge_fg = "#EAF3DE", "#3B6D11"
    elif  pct < 50: badge_bg, badge_fg = "#F3F7DE", "#557A18"
    elif  pct < 65: badge_bg, badge_fg = "#FFFBE6", "#8F7000"
    elif  pct < 75: badge_bg, badge_fg = "#FAEEDA", "#854F0B"
    elif  pct < 85: badge_bg, badge_fg = "#FCECD9", "#9C4E05"
    elif  pct < 95: badge_bg, badge_fg = "#FAECE7", "#993C1D"
    else:           badge_bg, badge_fg = "#FCEBEB", "#A32D2D"

    disponivel     = limite - gasto
    gasto_fmt      = fmt_br(gasto, 2)
    limite_fmt     = fmt_br(limite, 2)
    disponivel_fmt = fmt_br(disponivel, 2)

    st.markdown(f"""
    <div style="background:{card_bg}; border:1px solid {color}; border-radius:16px; padding:20px 24px; margin-bottom:12px; font-family:'Figtree',sans-serif;">
      <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;">
        <div style="flex:1; min-width:0;">
          <p style="background:#0b2f13; color:#a8ec7d; font-size:20px; font-weight:normal; display:inline-block; border-radius:6px; padding:1px 5px; margin:0 -8px 8px;">{titulo}</p>
          <div style="display:flex; align-items:baseline; gap:6px; flex-wrap:wrap;">
            <span style="font-size:36px; font-weight:400; color:{color}; white-space:nowrap;">R$ {gasto_fmt}</span>
            <span style="font-size:14px; color:#888; white-space:nowrap;">/ R$ {limite_fmt}</span>
          </div>
        </div>
        <span style="background:{badge_bg}; color:{badge_fg}; font-size:14px; font-weight:600; padding:4px 12px; border-radius:99px; white-space:nowrap; flex-shrink:0; margin-left:8px;">{pct:.0f}%</span>
      </div>
      <div style="background:rgba(255,255,255,0.08); border-radius:99px; height:8px; overflow:hidden; margin-bottom:10px;">
        <div style="width:{pct}%; height:100%; background:{color}; border-radius:99px; box-shadow:0 0 6px {color};"></div>
      </div>
      <div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px;">
        <span style="font-size:12px; color:#666;">Disponível</span>
        <span style="font-size:12px; font-weight:500; color:{color if pct >= 75 else '#888'}; white-space:nowrap;">R$ {disponivel_fmt}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


def preparar_df_exibir(df_filtrado: pd.DataFrame, df_base: pd.DataFrame) -> pd.DataFrame:
    """
    Cruza os dados filtrados por data com o DataFrame base de IFs,
    calculando exposição, exposição 2026, alocação 2026 e limite restante.
    """
    df = df_base.copy()

    # Agrega exposição total e somente de alocações a partir de 2026
    mascara_2026 = df_filtrado["DATA_AQUISICAO"] >= DATA_CORTE_2026

    grp_expo        = df_filtrado.groupby("EMISSOR")["EXPOSICAO"].sum()
    grp_expo_26     = df_filtrado[mascara_2026].groupby("EMISSOR")["EXPOSICAO"].sum()
    grp_aloc_26     = df_filtrado[mascara_2026].groupby("EMISSOR")["FINANCEIRO_AQUISICAO"].sum()

    df["EXPOSICAO"]            = df["EXPOSICAO"].fillna(df["ID_MITRA"].map(grp_expo)).astype("float64")
    df["EXPOSICAO_2026"]       = df["ID_MITRA"].map(grp_expo_26).fillna(0).astype("float64")
    df["FINANCEIRO_AQUISICAO"] = df["ID_MITRA"].map(grp_aloc_26).fillna(0).astype("float64")

    # Limite disponível = limite original menos o já alocado em 2026
    df["LIMITE_ALOCACAO_2026"] = df["LIMITE_ALOCACAO_2026"] - df["FINANCEIRO_AQUISICAO"]

    return df[["ID_MITRA", "INSTITUICAO_FINANCEIRA"] + list(COLUNAS_EXIBIR.keys())]


def formatar_data(valor) -> str:
    """Converte um Timestamp (ou None) para string no formato dd/mm/aaaa."""
    if pd.isna(valor):
        return "—"
    return valor.strftime("%d/%m/%Y") if hasattr(valor, "strftime") else str(valor)


# ── DADOS ─────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=21600, show_time=True)
def load_data() -> pd.DataFrame:
    """Carrega e cacheia os dados de limites operacionais por 6 horas."""
    return buscar_dados()


data = load_data()

# DataFrames estáticos
df_limites = pd.DataFrame(DADOS_LIMITES, columns=COLUNAS_LIMITES)
df_risco   = (
    pd.DataFrame(DADOS_RISCO, columns=COLUNAS_RISCO)
    .sort_values("Índice RiskBank", ascending=False)
    .reset_index(drop=True)
)
df_risco["Índice RiskBank"] = df_risco["Índice RiskBank"].apply(lambda x: fmt_br(x, 2))


# ── SESSION STATE ─────────────────────────────────────────────────────────────

if "data_selecionada" not in st.session_state:
    st.session_state.data_selecionada = data["DATA_COTACAO"].max().date()


# ── CSS + CABEÇALHO ───────────────────────────────────────────────────────────

st.html("""
<style>
    .block-container { padding-top: 4rem; }
    .st-key-meu-container {
        background-color: #0B2F13;
        border-radius: 8px;
        padding: 30px 20px 45px 20px;
        width: 100%;
        box-sizing: border-box;
    }
</style>
""")

with st.container(key="meu-container"):
    st.markdown("""
        <p style="text-align:center; color:#FAFBEB; margin:0; font-size:40px; font-weight:400; white-space:nowrap;">
            Limites Operacionais -
            <span style='color:#A8EC7D; font-family:"Source Serif 4",serif; font-style:italic; font-weight:600;'>
                Instituições Financeiras
            </span>
        </p>
    """, unsafe_allow_html=True)

st.space()


# ── DESCRIÇÃO + SELETOR DE DATA ───────────────────────────────────────────────

col1, _, col3 = st.columns([0.7, 0.05, 0.25])
with col1:
    st.space()
    st.markdown("""
        <div style="padding-left:20px; text-align:justify;">
            Este relatório tem por objetivo estabelecer e monitorar limites de aplicação em Títulos e Valores
            Mobiliários de Renda Fixa emitidos ou coobrigados por Instituições Financeiras, em conformidade
            com a legislação vigente e as diretrizes da Política de Investimentos da Ceres.
        </div>
    """, unsafe_allow_html=True)

with col3:
    primeira_data = data["DATA_COTACAO"].min().date()
    ultima_data   = data["DATA_COTACAO"].max().date()
    st.date_input(
        "Selecione a data posição",
        value=st.session_state.data_selecionada,
        format="DD/MM/YYYY",
        help=f"Datas disponíveis: {primeira_data.strftime('%d/%m/%Y')} a {ultima_data.strftime('%d/%m/%Y')}.",
        min_value=primeira_data,
        max_value=ultima_data,
        key="data_selecionada",
    )

# Aviso se a data selecionada não tiver dados disponíveis
datas_disponiveis = sorted(data["DATA_COTACAO"].dt.date.unique())
if st.session_state.data_selecionada not in datas_disponiveis:
    data_ant  = next((d for d in reversed(datas_disponiveis) if d < st.session_state.data_selecionada), None)
    data_post = next((d for d in datas_disponiveis          if d > st.session_state.data_selecionada), None)

    msg = f"**Nenhum dado disponível para {st.session_state.data_selecionada.strftime('%d/%m/%Y')}.**\n\n"
    if data_ant:  msg += f"Data anterior mais próxima: **{data_ant.strftime('%d/%m/%Y')}**\n"
    if data_post: msg += f"\nData posterior mais próxima: **{data_post.strftime('%d/%m/%Y')}**"
    st.warning(msg)


# ── FILTRAGEM E PREPARAÇÃO DOS DADOS ─────────────────────────────────────────

df_filtrado = (
    data[data["DATA_COTACAO"].dt.date == st.session_state.data_selecionada]
    .drop(columns=["TESOURARIA"])
    .copy()
)
df_filtrado["DATA_AQUISICAO"] = pd.to_datetime(df_filtrado["DATA_AQUISICAO"])

# DataFrame principal com limites calculados
df_principal = preparar_df_exibir(df_filtrado, df_limites)

# Totais para os cards e para o PDF
total_exposicao    = float(df_filtrado["EXPOSICAO"].sum() or 0)
total_exposicao_26 = float(df_filtrado[df_filtrado["DATA_AQUISICAO"] >= DATA_CORTE_2026]["EXPOSICAO"].sum() or 0)
total_alocacao     = float(df_filtrado[df_filtrado["DATA_AQUISICAO"] >= DATA_CORTE_2026]["FINANCEIRO_AQUISICAO"].sum() or 0)

# Agrupamento de produtos por emissor para a tabela expansível
grp_produto = (
    df_filtrado
    .groupby(["EMISSOR", "PRODUTO", "DATA_AQUISICAO", "VENCIMENTO"])
    .agg(FINANCEIRO_AQUISICAO=("FINANCEIRO_AQUISICAO", "sum"), EXPOSICAO=("EXPOSICAO", "sum"),
         TAXA_AQUISICAO=("TAXA_AQUISICAO", "mean"), INDEXADOR=("INDEXADOR", lambda x: x.mode()[0]))
    .reset_index()
    .sort_values("DATA_AQUISICAO")
)
grp_produto["Tx. Aquisição"] = grp_produto["INDEXADOR"] + " + " + grp_produto["TAXA_AQUISICAO"].apply(lambda x: f"{x:.2f}%")


# ── EXPORTAÇÃO PDF ────────────────────────────────────────────────────────────

_, _ , col_export = st.columns([3, 1, 1])
with col_export:
    df_grafico_pdf = df_principal[df_principal["EXPOSICAO"] > 0] if not df_principal.empty else pd.DataFrame()
    pdf_bytes = gerar_pdf_limites_operacionais(
        df_principal,
        data_posicao=st.session_state.data_selecionada,
        titulo_relatorio="Limites Operacionais -",
        disponivel_alocacao_26=LIMITE_ALOCACAO_2026,
        total_exposicao=total_exposicao,
        total_exposicao_26=total_exposicao_26,
        alocado_26=total_alocacao,
        df_risco=df_risco,
    )
    st.space()
    st.download_button(
        label="Baixar PDF",
        data=pdf_bytes,
        file_name=f"limites_operacionais_{st.session_state.data_selecionada.strftime('%d%m%Y')}.pdf",
        mime="application/pdf",
        width="stretch",
        type="primary",
        key="download_pdf_unico",
    )

st.divider()


# ── CARDS DE RESUMO ───────────────────────────────────────────────────────────

col1, col2 = st.columns(2)
with col1:
    with st.container(border=True):
        card_titulo("Posição")
        st.metric(label="Geral", value=f"R$ {fmt_br(total_exposicao, 2)}")
with col2:
    with st.container(border=True):
        card_titulo("Posição")
        st.metric(label="2026", value=f"R$ {fmt_br(total_exposicao_26, 2)}")

gasto_card("Plano de Alocação", total_alocacao, LIMITE_ALOCACAO_2026)


# ── ABAS: LIMITES E CLASSIFICAÇÃO DE RISCO ───────────────────────────────────

tab1, tab2 = st.tabs(["Limites Operacionais", "Classificação de Risco"])

with tab1:
    # ── CSS da tabela expansível ──────────────────────────────────────────────
    num_colunas     = len(COLUNAS_EXIBIR)
    grid_master     = " ".join(["1fr"] * num_colunas)   # colunas iguais para o cabeçalho principal
    grid_produtos   = "3fr 1fr 1fr 1fr 1fr 1fr"         # coluna Produto mais larga
    fonte_tabela    = "14px"

    st.html(f"""
    <style>
        .tabela-full {{
            width:100%; border:none; font-family:'Figtree',sans-serif; font-size:{fonte_tabela};
            border-collapse:separate; border-spacing:0; border-radius:10px;
            overflow:auto; background-color:transparent; min-width:0;
        }}
        @media (max-width:768px) {{ .tabela-full {{ font-size:11px; overflow-x:auto; }} }}

        /* Cabeçalho verde principal */
        .th-master {{
            background-color:#0B2F13; color:#A8EC7D;
            display:grid; grid-template-columns:2fr {grid_master}; padding-left:20px; align-items:center;
        }}
        .th-master div {{
            padding:12px; text-align:center; font-size:{fonte_tabela};
            display:flex; align-items:center; justify-content:center; min-height:40px;
            word-break:break-word;
        }}
        .th-master div:first-child {{ border-top-left-radius:10px; justify-content:flex-start; }}
        .th-master div:last-child  {{ border-top-right-radius:10px; }}

        /* Linha de totais */
        .th-totais {{
            background-color:#0B2F13; color:#A8EC7D; margin-top:10px;
            display:grid; grid-template-columns:2fr {grid_master}; align-items:center;
        }}
        .th-totais div {{
            padding:12px; text-align:center; font-weight:bold; font-size:{fonte_tabela};
            display:flex; align-items:center; justify-content:center; min-height:40px;
            word-break:break-word;
        }}
        .th-totais div:first-child {{ justify-content:flex-start; }}

        /* Estrutura geral */
        details {{ width:100%; }}
        details[open] {{ margin-bottom:15px; }}
        summary {{ list-style:none; cursor:pointer; }}
        summary::-webkit-details-marker {{ display:none; }}

        /* Coluna de valor */
        .col-val {{
            text-align:center; padding:10px; font-size:{fonte_tabela};
            display:flex; align-items:center; justify-content:center; min-height:40px;
            word-break:break-word;
        }}

        /* Label da instituição */
        .label-box {{
            display:flex; align-items:center; padding:10px 10px 10px 10px;
            font-size:13px; min-height:40px; word-break:break-word;
        }}
        .icon {{ width:25px; text-align:center; font-family:monospace; font-weight:bold; margin-right:5px; flex-shrink:0; }}

        /* Linha de instituição com produtos (expansível) */
        .row-inst {{ background-color:transparent; transition:background-color 0.2s; align-items:center; }}
        .row-inst:hover {{ background-color:rgba(1,104,55,0.05); }}
        details[open] > summary.row-inst {{ background-color:rgba(1,104,55,0.05); }}
        .row-inst.com-produtos .icon::before {{ content:'+'; color:#016837; }}
        details[open] > .row-inst.com-produtos .icon::before {{ content:'−'; }}

        /* Linha de instituição sem produtos */
        .row-inst.sem-produtos {{ background-color:transparent; cursor:pointer; transition:background-color 0.2s; }}
        .row-inst.sem-produtos:hover {{ background-color:rgba(1,104,55,0.05); }}
        .row-inst.sem-produtos:last-child, details:last-child > summary {{
            border-bottom:14px solid #0B2F13;
        }}

        /* Cabeçalho dos produtos */
        .th-produtos {{
            background-color:#FBFCEC; display:grid; grid-template-columns:{grid_produtos};
            margin-top:5px; border-bottom:1px solid #ddd; align-items:center;
        }}
        .th-produtos div {{
            padding:10px; text-align:center; font-style:italic; font-weight:bold;
            font-size:{fonte_tabela}; display:flex; align-items:center; justify-content:center; min-height:35px;
            word-break:break-word;
        }}
        .th-produtos div:first-child {{ justify-content:flex-start; padding-left:40px; }}

        /* Linha de produto */
        .row-prod {{
            background-color:transparent; display:grid; grid-template-columns:{grid_produtos};
            margin-top:1px; border-bottom:1px solid #eee; align-items:center; transition:background-color 0.2s;
        }}
        .row-prod div {{
            padding:8px; text-align:center; font-size:{fonte_tabela};
            border-right:1px solid #eee; display:flex; align-items:center; justify-content:center;
            min-height:35px; word-break:break-word;
        }}
        .row-prod div:last-child  {{ border-right:none; }}
        .row-prod div:first-child {{ justify-content:flex-start; padding-left:40px; }}
        .row-prod:hover {{ background-color:rgba(1,104,55,0.03); }}

        @media (max-width:768px) {{
            .th-master div, .th-totais div, .col-val, .label-box,
            .th-produtos div, .row-prod div {{ padding:6px; font-size:11px; min-height:30px; }}
        }}
    </style>
    """)

    # ── Montagem do HTML da tabela expansível ─────────────────────────────────

    # Cabeçalho
    html = '<div class="tabela-full"><div class="th-master"><div>Instituição</div>'
    for col, label in COLUNAS_EXIBIR.items():
        html += f"<div>{label}</div>"
    html += "</div>"

    for _, row in df_principal.iterrows():
        id_mitra  = row["ID_MITRA"]
        produtos  = grp_produto[grp_produto["EMISSOR"] == id_mitra]
        tem_prods = len(produtos) > 0

        # Linha da instituição (expansível ou estática)
        grid_row = f'style="display:grid; grid-template-columns:2fr {grid_master}; align-items:center;"'
        if tem_prods:
            html += f'<details><summary class="row-inst com-produtos" {grid_row}>'
            html += f'<div class="label-box"><span class="icon"></span> {row["INSTITUICAO_FINANCEIRA"]}</div>'
        else:
            html += f'<div class="row-inst sem-produtos" {grid_row}>'
            html += f'<div class="label-box"><span style="width:25px;"></span> {row["INSTITUICAO_FINANCEIRA"]}</div>'

        # Valores das colunas
        for col in COLUNAS_EXIBIR:
            valor = row[col]
            if pd.isna(valor) or valor == 0:
                valor_fmt = "—"
            elif col == "LIMITE_ALOCACAO_2026" and pd.notna(valor):
                # Negrito quando o limite foi parcialmente consumido
                valor_fmt = fmt_br(valor, 2) if valor == LIMITE_ALOCACAO_2026 else f"<strong>{fmt_br(valor, 2)}</strong>"
            else:
                valor_fmt = fmt_br(valor, 2)
            html += f'<div class="col-val">{valor_fmt}</div>'

        html += "</summary>" if tem_prods else "</div>"

        # Linhas de produtos (quando expandido)
        if tem_prods:
            html += '<div class="th-produtos"><div>Produto</div><div>Aquisição</div><div>Vencimento</div><div>Tx. Aquisição</div><div>Fin. Aquisição</div><div>Posição</div></div>'
            for _, prod in produtos.iterrows():
                html += f"""
                <div class="row-prod">
                    <div>{prod['PRODUTO']}</div>
                    <div>{formatar_data(prod['DATA_AQUISICAO'])}</div>
                    <div>{formatar_data(prod['VENCIMENTO'])}</div>
                    <div><strong>{prod['Tx. Aquisição']}</strong></div>
                    <div><strong>{fmt_br(prod['FINANCEIRO_AQUISICAO'], 2) if pd.notna(prod['FINANCEIRO_AQUISICAO']) else '—'}</strong></div>
                    <div><strong>{fmt_br(prod['EXPOSICAO'], 2) if pd.notna(prod['EXPOSICAO']) else '—'}</strong></div>
                </div>"""
            html += "</details>"

    html += "</div>"
    st.html(html)
    st.markdown(
        '<p style="font-family:\'Source Serif Pro\',serif; font-style:italic; margin-left:20px;">'
        "(*) Não Elegíveis desde maio/2026, (**) Não elegível desde maio/2025.</p>",
        unsafe_allow_html=True,
    )


with tab2:
    st.html(gerar_tabela_estilizada(df_risco))
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            '<p style="font-family:\'Source Serif Pro\',serif; font-style:italic; margin-left:20px;">'
            "(*) Não Elegíveis desde maio/2026, (**) Não elegível desde maio/2025.</p>",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            '<div style="display:flex; justify-content:flex-end;">'
            '<p style="font-family:\'Source Serif Pro\',serif; font-style:italic; margin:0;">'
            "Fonte: Riskbank - atualização Junho/2025.</p></div>",
            unsafe_allow_html=True,
        )
    st.space(size="stretch")


# ── GRÁFICO: EXPOSIÇÃO POR EMISSOR ───────────────────────────────────────────

with st.columns(1)[0].container(border=True):
    df_grafico = df_principal[df_principal["EXPOSICAO"] > 0].copy()
    total_exp  = df_grafico["EXPOSICAO"].sum()

    if total_exp > 0:
        df_grafico["VALOR_BARRA"] = df_grafico["EXPOSICAO"].apply(
            lambda v: f"{v:,.2f}".replace(".", "_").replace(",", ".").replace("_", ",")
        )
        df_grafico["PCT_BARRA"] = df_grafico["EXPOSICAO"].apply(
            lambda v: f"{(v / total_exp) * 100:.1f}%"
        )
    else:
        df_grafico["VALOR_BARRA"] = "0,00"
        df_grafico["PCT_BARRA"]   = "0,0%"

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_grafico["INSTITUICAO_FINANCEIRA"],
        y=df_grafico["EXPOSICAO"],
        customdata=df_grafico[["VALOR_BARRA", "PCT_BARRA"]],
        marker=dict(color="#0B2F13", cornerradius=7, line=dict(width=0)),
    ))

    # Anotações com valor absoluto e percentual acima de cada barra
    for _, row in df_grafico.iterrows():
        fig.add_annotation(
            x=row["INSTITUICAO_FINANCEIRA"], y=row["EXPOSICAO"],
            text=f"<b>{row['PCT_BARRA']}</b><br>{row['VALOR_BARRA']}",
            showarrow=False, yanchor="bottom",
            font=dict(family="Figtree", size=12, color="#0B2F13"),
        )

    max_exp = df_grafico["EXPOSICAO"].max() if not df_grafico.empty else 100
    fig.update_layout(
        title="Exposição por Emissor",
        bargap=0.04,
        height=max(200, len(df_grafico) * 70),
        autosize=True,
        separators=",.",
        font=dict(family="Figtree", size=14, color="#333333"),
        xaxis=dict(categoryorder="total descending", showline=False, showgrid=False, automargin=True),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, max_exp * 1.05]),
        hovermode="closest",
        hoverlabel=dict(bgcolor="#FBFCEC", bordercolor="#0B2F13", font=dict(family="Figtree", size=12, color="#0B2F13")),
        margin=dict(r=20, t=45, b=30, l=20),
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>Valor: R$ %{customdata[0]}<br>Participação: %{customdata[1]}<extra></extra>"
    )

    st.plotly_chart(fig, config={"displayModeBar": False}, width="stretch")