import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from html import escape
from utils.queries.risco_mercado_ativos import buscar_dados_risco_mercado_ativos
from utils.helpers import (
    nome_plano,
    card_geral,
    formatar_numero,
    fmt_br,
    renderizar_tabela_estilizada,
)

# Carregar dados


@st.cache_data(ttl="1h", show_time=True)
def carregar_dados() -> pd.DataFrame:
    return buscar_dados_risco_mercado_ativos()


df_ativos = carregar_dados()
df_ativos.columns = df_ativos.columns.str.upper()

colunas_map = {
    "FUNDOS": "Fundos",
    "POSICAO": "Posição R$",
    "VAR": "VaR R$",
    "VAR/POSICAO_%": "VaR %",
    "PARAMETRICO": "Contrib. Marginal %",
    "BVAR": "BVaR R$",
    "BVAR/POSICAO_%": "BVaR %",
    "NOMEBVAR": "Índice",
}

de_para_nome_fundo = {"AGUAS EMENDADAS FUNDO DE INVESTIMENTO EM ACOES": "SERRA DO CIPÓ FIA"}
df_ativos["FUNDOS"] = df_ativos["FUNDOS"].replace(de_para_nome_fundo)

colunas_existentes = [col for col in colunas_map if col in df_ativos.columns]

# Seleciona e renomeia as colunas
df_ativos = df_ativos[colunas_existentes].rename(columns=colunas_map)

# Remove eventual prefixo "Tesouraria=" e aplica nome amigável quando conhecido
df_ativos["Fundos"] = df_ativos["Fundos"].apply(nome_plano)


def _escape_html(valor) -> str:
    if valor is None:
        return ""

    return escape(str(valor), quote=True)


def _fmt_var_pct_vs_bvar(row) -> str:
    """
    Exibe o VaR % com uma seta comparando-o ao BVaR %:
    seta vermelha para cima quando o VaR % é maior que o BVaR %
    (fundo com mais risco corrente do que em estresse),
    seta verde para baixo quando o VaR % é menor que o BVaR %
    (fundo com menos risco corrente do que em estresse).
    """

    var_pct = row["VaR %"]
    bvar_pct = row["BVaR %"]

    texto = f"{fmt_br(var_pct, 2)}%" if pd.notna(var_pct) else "—"

    if pd.isna(var_pct) or pd.isna(bvar_pct):
        return _escape_html(texto)

    if var_pct > bvar_pct:
        return f'<span style="color:#EF4444; font-weight:700;">{_escape_html(texto)} ▲</span>'

    if var_pct < bvar_pct:
        return f'<span style="color:#22C55E; font-weight:700;">{_escape_html(texto)} ▼</span>'

    return _escape_html(texto)


def titulo_section(
    titulo: str,
    mostrar_linha: bool = True,
    tamanho_titulo: int = 18,
    peso_titulo: int = 900,
    cor_titulo: str = "#0B2F13",
    cor_linha: str = "rgba(11, 47, 19, 0.22)",
    margem_topo: int = 8,
    margem_baixo: int = 1,
):
    """
    Renderiza um título de seção com linha horizontal opcional à direita.
    """

    titulo_html = _escape_html(titulo)

    linha_html = ""

    if mostrar_linha:
        linha_html = '<div class="section-title-line"></div>'

    html = f"""
    <style>
        .section-title-container {{
            width: 100%;
            margin: {margem_topo}px 0 {margem_baixo}px 0;
            font-family: 'Figtree', sans-serif;
        }}

        .section-title-row {{
            display: flex;
            align-items: center;
            gap: 8px;
            width: 100%;
        }}

        .section-title-text {{
            color: {cor_titulo};
            font-size: {tamanho_titulo}px;
            font-weight: {peso_titulo};
            line-height: 1.2;
            white-space: nowrap;
        }}

        .section-title-line {{
            flex: 1;
            height: 1px;
            background: {cor_linha};
            margin-left: 4px;
        }}
    </style>

    <div class="section-title-container">
        <div class="section-title-row">
            <span class="section-title-text">{titulo_html}</span>
            {linha_html}
        </div>
    </div>
    """

    st.html(html)


st.set_page_config(layout="wide")

st.html("""
<style>
    /* Remove o padding lateral e superior do bloco principal */
    .block-container {
        padding-top: 3.8rem;
        padding-left: 0rem;
        padding-right: 0rem;
    }

    .st-key-meu-container-ativos {
        background-color: #0B2F13;
        border-radius: 0px;
        padding: 30px 20px 30px 20px;
        width: 100%;
        box-sizing: border-box;
    }

    /* Container do conteúdo COM padding lateral */
    .st-key-conteudo-ativos {
        padding-left: 3rem;
        padding-right: 3rem;
    }

</style>
""")

with st.container(key="meu-container-ativos"):
    st.html("""
        <p style="text-align:center; color:#FAFBEB; margin:0 0; font-size: clamp(20px, 3vw, 29px); font-weight:400;">
            Risco de Mercado -
            <span style='color:#A8EC7D; font-family:"Source Serif 4",serif; font-style:italic; font-weight:600;'>
                Ativos
            </span>
        </p>
    """)

with st.container(horizontal_alignment="center", gap=None, key="conteudo-ativos"):
    with st.container(width=1200):

        # ── DESCRIÇÃO ────────────────────────────────────────────────────────
        st.markdown(
            """
            <div style="padding-left:20px; text-align:justify; color:#5a5a5a; margin:0; font-size:16px; font-weight:400;">
                Este painel apresenta uma visão do risco de mercado por fundo, com base no VaR (Value at Risk)
                paramétrico e no BVaR (Value at Risk do Benchmark), conforme diretrizes definidas no
                Manual de Riscos de Investimento. O VaR é uma medida estatística que estima a perda potencial
                máxima em um determinado horizonte de tempo e nível de confiança.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.space()

        # ── CARDS ────────────────────────────────────────────────────────────
        with st.container():

            titulo_section("Métricas de Risco Consolidado")

            posicao_total = df_ativos["Posição R$"].sum()
            var_total = df_ativos["VaR R$"].sum()
            bvar_total = df_ativos["BVaR R$"].sum()

            var_pct_total = (var_total / posicao_total * 100) if posicao_total else 0
            bvar_pct_total = (bvar_total / posicao_total * 100) if posicao_total else 0

            c1, c2, c3, c4, c5 = st.columns(5)

            with c1:
                card_geral(
                    titulo="Posição",
                    valor=formatar_numero(posicao_total, prefixo="R$ "),
                    valor_extenso=fmt_br(posicao_total),
                    help="Posição consolidada dos fundos.",
                )
            with c2:
                card_geral(
                    titulo="Risco Paramétrico",
                    valor=formatar_numero(var_total, prefixo="R$ "),
                    valor_extenso=fmt_br(var_total),
                    help="VaR Paramétrico consolidado dos fundos.",
                )
            with c3:
                card_geral(
                    titulo="Risco Paramétrico %",
                    valor=formatar_numero(var_pct_total, sufixo="%"),
                    help="VaR Paramétrico consolidado, expresso em percentual da posição total.",
                )
            with c4:
                card_geral(
                    titulo="BVaR",
                    valor=formatar_numero(bvar_total, prefixo="R$ "),
                    valor_extenso=fmt_br(bvar_total),
                    help="BVaR consolidado dos fundos.",
                )
            with c5:
                card_geral(
                    titulo="BVaR %",
                    valor=formatar_numero(bvar_pct_total, sufixo="%"),
                    help="BVaR consolidado, expresso em percentual da posição total.",
                )

        # ── GRÁFICO DE BARRAS ────────────────────────────────────────────────
        titulo_section("VaR Paramétrico % por Fundo")

        with st.container(border=True):

            df_grafico = df_ativos.sort_values("VaR %", ascending=False).copy()

            if df_grafico.empty:
                st.info("Não há dados disponíveis para exibir.")
            else:
                df_grafico["VALOR_BARRA"] = df_grafico["VaR %"].map(
                    lambda v: f"{v:,.2f}%".replace(".", "_").replace(",", ".").replace("_", ",")
                )

                max_exp = df_grafico["VaR %"].max()

                fig = go.Figure()

                fig.add_trace(
                    go.Bar(
                        x=df_grafico["Fundos"],
                        y=df_grafico["VaR %"],
                        text=df_grafico["VALOR_BARRA"],
                        textposition="outside",
                        customdata=df_grafico["VALOR_BARRA"],
                        hovertemplate=(
                            "<b>%{x}</b><br>"
                            "VaR: %{customdata}"
                            "<extra></extra>"
                        ),
                        marker=dict(
                            color="#0B2F13",
                            cornerradius=5,
                            line=dict(width=0),
                        ),
                        textfont=dict(
                            family="Figtree",
                            size=14,
                            color="#0B2F13",
                        ),
                        cliponaxis=False,
                    )
                )

                fig.update_layout(
                    bargap=0.12,
                    height=340,
                    autosize=True,
                    separators=",.",
                    font=dict(
                        family="Figtree",
                        size=14,
                        color="#333333",
                    ),
                    xaxis=dict(
                        categoryorder="total descending",
                        showline=False,
                        showgrid=False,
                        automargin=True,
                        tickfont=dict(
                            family="Figtree",
                            size=13,
                            color="#333333",
                        ),
                    ),
                    yaxis=dict(
                        showgrid=False,
                        zeroline=False,
                        showticklabels=False,
                        range=[0, max_exp * 1.18] if max_exp else None,
                    ),
                    hoverlabel=dict(
                        bgcolor="#FBFCEC",
                        bordercolor="#0B2F13",
                        font=dict(
                            family="Figtree",
                            size=14,
                            color="#0B2F13",
                        ),
                    ),
                    margin=dict(r=5, t=8, b=20, l=5),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                )

                st.plotly_chart(
                    fig,
                    config={"displayModeBar": False},
                    width="stretch",
                    key="grafico_risco_ativos",
                )

        # ── TABELA ───────────────────────────────────────────────────────────
        titulo_section("Resumo de Risco por Fundo")

        with st.container():
            renderizar_tabela_estilizada(
                df_ativos.sort_values("VaR %", ascending=False),
                primeira_coluna_larga=True,
                ordenacao=True,
                key="tabela_resumo_risco_ativos",
                colunas_html={"VaR %": _fmt_var_pct_vs_bvar},
            )
