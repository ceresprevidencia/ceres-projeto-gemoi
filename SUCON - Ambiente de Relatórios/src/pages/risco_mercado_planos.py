import streamlit as st
import pandas as pd
from utils.queries.risco_mercado_planos import buscar_dados as buscar_dados_planos
from utils.queries.risco_mercado_segmentos import buscar_dados as buscar_dados_segmentos
import os
import plotly.graph_objects as go
from utils.helpers import ( 
                           nome_plano,
                           card_geral,
                           formatar_numero,
                           fmt_br
                           )

# Carregar dados c

@st.cache_data(ttl="1h", show_time=True)
def carregar_dados() -> pd.DataFrame:
    return buscar_dados_planos()

 


df_planos = carregar_dados()

df_planos.columns = df_planos.columns.str.upper()

colunas_map = {
    'TESOURARIA': 'Planos',
    'POSICAO': 'Posição',
    'DATA_COTACAO': 'DATA_COTACAO',
    'RISCO': 'Value at Risk - VaR R$',
    'RISCO/POSICAO_%': 'Value at Risk - VaR %',
    'LIMITE_INTERNO_%': 'Limite Interno %',
    'STATUS_%':'Status %',
    'VARIACAO_POSICAO_STRESS_1': 'Posicação Stress (+) R$',
    'VARIACAO_POSICAO_STRESS_1/POSICAO_%': 'Posicação Stress (+) %',
    'VARIACAO_POSICAO_STRESS_2': 'Posicação Stress (-) R$',
    'VARIACAO_POSICAO_STRESS_2/POSICAO_%':'Posicação Stress (-) %',
    
}

# Seleciona e renomeia as colunas
df_planos = df_planos[list(colunas_map.keys())].rename(columns=colunas_map)

# Garante que DATA_COTACAO esteja como datetime
df_planos["DATA_COTACAO"] = pd.to_datetime(
    df_planos["DATA_COTACAO"],
    errors="coerce"
)

# Remove linhas sem data válida
df_planos = df_planos.dropna(subset=["DATA_COTACAO"])

# Inicializa a data selecionada como date, não Timestamp
if "data-selecionada" not in st.session_state:
    st.session_state["data-selecionada"] = df_planos["DATA_COTACAO"].max().date()


# __________________________ CABEÇALHO
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
            Risco de Mercado -
            <span style='color:#A8EC7D; font-family:"Source Serif 4",serif; font-style:italic; font-weight:600;'>
                Planos
            </span>
        </p>
    """, unsafe_allow_html=True)

st.space()

# ── DESCRIÇÃO + SELETOR DE DATA ───────────────────────────────────────────────
col1, _, col2 = st.columns([1, 0.5, 0.5])

with col1:
    opcoes_planos = df_planos["Planos"].dropna().unique().tolist()

    opcoes_planos = ["Todos os planos"] + opcoes_planos

    selected_plano = st.selectbox(
        "Selecione o plano:",
        options=opcoes_planos,
        format_func=lambda x: x if x == "Todos os planos" else nome_plano(x),
    )
with col2:
    primeira_data = df_planos["DATA_COTACAO"].min().date()
    ultima_data = df_planos["DATA_COTACAO"].max().date()

    st.date_input(
        "Selecione a data posição",
        value=st.session_state["data-selecionada"],
        format="DD/MM/YYYY",
        help=(
            f"Datas disponíveis: "
            f"{primeira_data.strftime('%d/%m/%Y')} a "
            f"{ultima_data.strftime('%d/%m/%Y')}."
        ),
        min_value=primeira_data,
        max_value=ultima_data,
        key="data-selecionada",
    )


# Aviso se a data selecionada não tiver dados disponíveis
datas_disponiveis = sorted(df_planos["DATA_COTACAO"].dt.date.unique())

data_selecionada = st.session_state["data-selecionada"]

if data_selecionada not in datas_disponiveis:
    data_ant = next(
        (d for d in reversed(datas_disponiveis) if d < data_selecionada),
        None
    )

    data_post = next(
        (d for d in datas_disponiveis if d > data_selecionada),
        None
    )

    msg = f"**Nenhum dado disponível para {data_selecionada.strftime('%d/%m/%Y')}.**\n\n"

    if data_ant:
        msg += f"Data anterior mais próxima: **{data_ant.strftime('%d/%m/%Y')}**\n"

    if data_post:
        msg += f"\nData posterior mais próxima: **{data_post.strftime('%d/%m/%Y')}**"

    st.warning(msg)

if selected_plano == "Todos os planos":
    df_planos_filtrado_dp = df_planos[df_planos["DATA_COTACAO"].dt.date == data_selecionada]

else:
    df_planos_filtrado_dp = df_planos[
        (df_planos["DATA_COTACAO"].dt.date == data_selecionada)
        & (df_planos["Planos"] == selected_plano)
    ]

c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    card_geral(
        titulo="Posição",
        valor=formatar_numero(df_planos_filtrado_dp['Posição'].sum(), prefixo="R$ "),
        valor_extenso=fmt_br(df_planos_filtrado_dp['Posição'].sum())
    )
with c2:
    card_geral(
        titulo="Risco Paramétrico",
        valor=formatar_numero(df_planos_filtrado_dp['Value at Risk - VaR R$'].sum(), prefixo="R$"),
        valor_extenso=fmt_br(df_planos_filtrado_dp['Value at Risk - VaR R$'].sum())
    )

with c3:
    parametrico_consolidado = (df_planos_filtrado_dp['Value at Risk - VaR R$'].sum() / df_planos_filtrado_dp['Posição'].sum() if df_planos_filtrado_dp['Posição'].sum() != 0 else 0) * 100

    card_geral(
        titulo="Risco Paramétrico %",
        valor=formatar_numero(parametrico_consolidado, sufixo="%")
    )

with c4:
    stress1 = df_planos_filtrado_dp['Posicação Stress (+) R$'].sum() + df_planos_filtrado_dp['Posição'].sum()
    card_geral(
        titulo="Stress (+)",
        valor=formatar_numero(stress1, prefixo="R$ "),
        delta=formatar_numero(df_planos_filtrado_dp['Posicação Stress (+) R$'].sum(), prefixo="R$ ")
    )

with c5:
    stress2 = df_planos_filtrado_dp['Posicação Stress (-) R$'].sum() + df_planos_filtrado_dp['Posição'].sum()

    card_geral(
        titulo="Stress (-)",
        valor=formatar_numero(stress2, prefixo="R$ "),
        delta=formatar_numero(df_planos_filtrado_dp['Posicação Stress (-) R$'].sum(), prefixo="R$ ")
    )

st.dataframe(df_planos_filtrado_dp, hide_index=True)  # Exibe as primeiras linhas para verificação
