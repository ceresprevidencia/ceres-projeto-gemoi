import io
import os
import zipfile
import tempfile

import pandas as pd
import streamlit as st

from utils.gerar_pdf import gerar_pdf
from utils.queries.enquadramento import buscar_dados
from utils.helpers import (
    aplicar_destaque,
    formatar_percentual_br,
    fmt_br,
    limpar_texto,
    nome_plano,
    remove_grp,
)


# ── CONSTANTES ────────────────────────────────────────────────────────────────

# Ordem canônica dos segmentos exibidos nas tabelas
ORDEM_SEGMENTOS = [
    "Renda Fixa",
    "Renda Variável",
    "Imobiliário",
    "Estruturado",
    "Operações com Participantes",
    "Exterior",
]

# Ordem das descrições de regras dentro de cada segmento (Política de Investimentos)
ORDEM_REGRAS_PI = [
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
    'Cotas de classes de fundos de investimento "Ações - Mercado de Acesso"',
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

# Colunas brutas → nomes amigáveis para a tabela padrão de segmentos
COLUNAS_SEGMENTO = {
    "DESCRICAO": "Descrição",
    "LIMITE_PERCENTUAL": "Limite %",
    "VALOR_LIMITE_REGRA": "Limite R$",
    "VALOR_ATUAL": "Posição R$",
    "PERCENTUAL_UTILIZADO": "Limite Utilizado %",
    "PERCENTUAL_ULTRAPASSADO": "% Ultrapassado",
    "PERCENTUAL_TOTAL": "% Total",
    "STATUS": "Status",
}


# ── HELPERS LOCAIS ────────────────────────────────────────────────────────────

def formatar_brl(valor) -> str:
    """Formata um número float no padrão monetário brasileiro (1.234,56)."""
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def preparar_df_segmento(df: pd.DataFrame) -> pd.DataFrame:
    """
    Seleciona, renomeia e formata as colunas padrão de um segmento,
    removendo as colunas auxiliares de percentual ultrapassado/total.
    """
    df_exibir = df[list(COLUNAS_SEGMENTO.keys())].copy().rename(columns=COLUNAS_SEGMENTO)

    df_exibir["Limite %"] = df_exibir["Limite %"].apply(formatar_percentual_br)
    df_exibir["Limite Utilizado %"] = df_exibir["Limite Utilizado %"].apply(formatar_percentual_br)
    df_exibir["% Ultrapassado"] = df_exibir["% Ultrapassado"].apply(formatar_percentual_br)
    df_exibir["% Total"] = df_exibir["% Total"].apply(formatar_percentual_br)
    df_exibir["Posição R$"] = df_exibir["Posição R$"].apply(formatar_brl)
    df_exibir["Limite R$"] = df_exibir["Limite R$"].apply(formatar_brl)

    return df_exibir.drop(columns=["% Total", "% Ultrapassado"])


def exibir_tabela(df_exibir: pd.DataFrame, borda_inferior: bool = True):
    """Aplica destaque nas linhas desenquadradas e renderiza a tabela no padrão do sistema."""
    mask = df_exibir["Status"].str.upper() == "DESENQUADRADO"
    st.html(aplicar_destaque(df_exibir, mask, borda_inferior=borda_inferior))


# ── SESSION STATE: valores iniciais ──────────────────────────────────────────

# Regime selecionado (PI ou Resolução 4994)
if "regime_ativo" not in st.session_state:
    st.session_state["regime_ativo"] = "Política de Investimentos"

if "pills_desenq" not in st.session_state:
    st.session_state["pills_desenq"] = None


# ── DADOS ─────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_time=True)
def carregar_dados() -> pd.DataFrame:
    """Carrega e cacheia o DataFrame principal por 1 hora."""
    return buscar_dados()


df = carregar_dados()
df.columns = df.columns.str.upper()

if df.empty:
    st.warning("Nenhum dado encontrado para o filtro selecionado.")
    st.stop()


# ── CSS ───────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    /* Reduz padding do topo da página */
    .block-container { padding-top: 3rem; }

    /* Container do cabeçalho verde */
    .st-key-meu-container {
        background-color: #0B2F13;
        border-radius: 8px;
        padding: 30px 20px 45px 20px;
        width: 100%;
        box-sizing: border-box;
    }

    /* Oculta ícone duplicado gerado pelo bug do Expander */
    [data-testid="stExpanderToggleIcon"] { display: none !important; }
    [data-testid="stExpanderSummary"] span:not(:first-child) { display: none !important; }
    [data-testid="stExpanderSummary"] p {
        font-family: 'Figtree', sans-serif !important;
        width: 100% !important;
    }

    /* Pills – estado base */
    [data-testid="stMainBlockContainer"] [data-testid="stButtonGroup"] button[kind="pills"] {
        background-color: transparent !important;
        border-color: #c0392b !important;
        color: #c0392b !important;
        border-radius: 6px !important;
        font-family: 'Figtree', sans-serif !important;
        transition: none !important;
    }

    /* Pills – hover */
    [data-testid="stMainBlockContainer"] [data-testid="stButtonGroup"] button[kind="pills"]:hover {
        background-color: rgba(192, 57, 43, 0.15) !important;
        border-color: #a93226 !important;
        color: #a93226 !important;
    }

    /* Pills – selecionado */
    [data-testid="stMainBlockContainer"] [data-testid="stButtonGroup"] button[kind="pills"][aria-checked="true"] {
        background-color: #c0392b !important;
        border-color: #c0392b !important;
        color: white !important;
    }

    /* Botão PRIMARY */
    [data-testid="stMainBlockContainer"] [data-testid="stBaseButton-primary"],
    [data-testid="stMainBlockContainer"] [data-testid="stBaseButton-primary"]:hover,
    [data-testid="stMainBlockContainer"] [data-testid="stBaseButton-primary"]:focus {
        background-color: #0b2f13 !important;
        color: white !important;
        border: 2px solid #0b2f13 !important;
    }

    /* Botão SECONDARY */
    [data-testid="stMainBlockContainer"] [data-testid="stBaseButton-secondary"],
    [data-testid="stMainBlockContainer"] [data-testid="stBaseButton-secondary"]:hover,
    [data-testid="stMainBlockContainer"] [data-testid="stBaseButton-secondary"]:focus {
        background-color: transparent !important;
        color: #0b2f13 !important;
        border: 2px solid #0b2f13 !important;
    }

    /* Radio */
    [data-testid="stMainBlockContainer"] [data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child {
        background-color: transparent !important;
        border: 2px solid #0b2f13 !important;
    }
    [data-testid="stMainBlockContainer"] [data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child > div {
        background-color: transparent !important;
    }
    [data-testid="stMainBlockContainer"] [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) > div:first-child > div {
        background-color: #0b2f13 !important;
    }

    /* Multiselect – tag e item selecionado */
    [data-testid="stMainBlockContainer"] [data-testid="stMultiSelect"] span[data-baseweb="tag"] {
        background-color: #0b2f13 !important;
    }
    [data-testid="stMainBlockContainer"] [data-testid="stMultiSelect"] li[aria-selected="true"] {
        background-color: rgba(11, 47, 19, 0.2) !important;
    }

    /* Selectbox e Multiselect – remove borda colorida no foco */
    [data-testid="stMainBlockContainer"] [data-testid="stSelectbox"] [data-baseweb="select"] > div:first-child,
    [data-testid="stMainBlockContainer"] [data-testid="stMultiSelect"] [data-baseweb="select"] > div:first-child {
        border-color: rgba(0, 0, 0, 0.2) !important;
        box-shadow: none !important;
    }

    :root { --primary-color: #014d2a !important; }
</style>
""", unsafe_allow_html=True)



# ── CABEÇALHO ─────────────────────────────────────────────────────────────────

# Container verde escuro com título estilizado
with st.container(key="meu-container"):
    st.markdown("""
        <p style="text-align:center; color:#FAFBEB; margin:0; font-size:40px; font-weight:400; white-space:nowrap;">
            Enquadramento Diário -
            <span style='color:#A8EC7D; font-family:"Source Serif 4",serif; font-style:italic; font-weight:600;'>
                Planos
            </span>
        </p>
    """, unsafe_allow_html=True)

st.space()


# ── TEXTO DESCRITIVO + SELETOR DE DATA ───────────────────────────────────────

col1, _, col3 = st.columns([0.7, 0.05, 0.25])

with col1:
    st.space()
    st.markdown("""
        <div style="padding-left:20px; text-align:justify;">
            O Relatório tem como objetivo verificar a aderência dos investimentos do plano às diretrizes de
            aplicações estabelecidas pela Política de Investimentos vigente e pela Resolução CMN N° 4.994 vigente.
        </div>
    """, unsafe_allow_html=True)

with col3:
    primeira_data = df["DATA_COTACAO"].min().date()
    ultima_data = df["DATA_COTACAO"].max().date()

    # Inicializa a data de posição com o máximo disponível na primeira carga
    if "data_posicao" not in st.session_state:
        st.session_state["data_posicao"] = ultima_data

    def armazena_data():
        """Callback: persiste o valor do date_input temporário na chave permanente."""
        st.session_state["data_posicao"] = st.session_state["_data_posicao"]

    # Sincroniza chave temporária com a permanente antes de renderizar o widget
    st.session_state["_data_posicao"] = st.session_state["data_posicao"]

    data_posicao = st.date_input(
        "Selecione a data posição",
        format="DD/MM/YYYY",
        help=f"Datas disponíveis: {primeira_data.strftime('%d/%m/%Y')} a {ultima_data.strftime('%d/%m/%Y')}.",
        min_value=primeira_data,
        max_value=ultima_data,
        key="_data_posicao",
        on_change=armazena_data,
    )

st.divider()


# ── SELETOR DE REGIME ─────────────────────────────────────────────────────────

def set_regime(nome: str):
    """Callback: troca o regime ativo (PI ou Resolução 4994)."""
    st.session_state["regime_ativo"] = nome


col1, col2, col3 = st.columns([4, 1.5, 1.5])
with col2:
    st.markdown("**Regime:**")
    st.button(
        "Política de Investimentos",
        type="primary" if st.session_state["regime_ativo"] == "Política de Investimentos" else "secondary",
        use_container_width=True,
        on_click=set_regime,
        args=("Política de Investimentos",),
    )
with col3:
    st.markdown("&nbsp;", unsafe_allow_html=True)
    st.button(
        "Resolução 4994",
        type="primary" if st.session_state["regime_ativo"] == "Resolução 4994" else "secondary",
        use_container_width=True,
        on_click=set_regime,
        args=("Resolução 4994",),
    )


# ── FILTRAGEM PRINCIPAL ───────────────────────────────────────────────────────

# Filtra por data selecionada e pelo regime ativo
df_filtrado_data = df[df["DATA_COTACAO"] == pd.to_datetime(data_posicao)]
df_filtrado = df_filtrado_data[df_filtrado_data["CONJUNTO"] == st.session_state["regime_ativo"]]


# ── PILLS DE PLANOS DESENQUADRADOS ────────────────────────────────────────────

planos = sorted(df_filtrado["ESTRUTURA_ASSOCIADA"].unique())
planos_desenquadrados = sorted(
    df_filtrado.loc[df_filtrado["STATUS"] == "Desenquadrado", "ESTRUTURA_ASSOCIADA"].unique()
)

# Dicionários de conversão entre nome amigável e valor original do plano
nome_para_orig = {nome_plano(p): p for p in planos_desenquadrados}


def on_pills_change():
    """Ao clicar em um pill, seleciona o plano correspondente no selectbox."""
    sel = st.session_state.get("pills_desenq")
    if sel:
        st.session_state["selectbox_plano"] = nome_para_orig[sel]
        st.session_state["pills_desenq"] = None


def on_selectbox_change():
    """Ao trocar o selectbox, desmarca qualquer pill ativo."""
    st.session_state["pills_desenq"] = None


if planos_desenquadrados:
    st.pills(
        "Planos desenquadrados:",
        list(nome_para_orig.keys()),
        key="pills_desenq",
        on_change=on_pills_change,
    )


# ── SELETOR DE PLANO ──────────────────────────────────────────────────────────

try:
    # Inicializa ou valida o plano salvo; reseta para o primeiro se não existir mais
    if "selectbox_plano" not in st.session_state or st.session_state["selectbox_plano"] not in planos:
        st.session_state["selectbox_plano"] = planos[0]

    plano = st.selectbox(
        "Plano",
        options=planos,
        format_func=nome_plano,
        key="selectbox_plano",
        on_change=on_selectbox_change,
    )

except Exception:
    # Nenhum plano encontrado: sugere as datas mais próximas disponíveis
    datas_disponiveis = df["DATA_COTACAO"].sort_values().unique()
    data_posicao_ts = pd.Timestamp(data_posicao)

    for idx, data in enumerate(datas_disponiveis[:-1]):
        data_ts = pd.Timestamp(data)
        proxima_ts = pd.Timestamp(datas_disponiveis[idx + 1])
        if data_ts < data_posicao_ts < proxima_ts:
            st.warning(
                f"Nenhum plano encontrado para a data selecionada. "
                f"Considere: {data_ts.strftime('%d/%m/%Y')} ou {proxima_ts.strftime('%d/%m/%Y')}."
            )
            break

    st.stop()


# ── DATAFRAME DO PLANO SELECIONADO ────────────────────────────────────────────

df_plano = df_filtrado[df_filtrado["ESTRUTURA_ASSOCIADA"] == plano].copy()

if df_plano.empty:
    st.warning("Nenhum dado encontrado para o plano selecionado.")
    st.stop()


# ── EXPORTAÇÃO (PDF / CSV) ────────────────────────────────────────────────────

def gerar_nome_arquivo(plano_sel, extensao: str) -> str:
    """Gera nome padronizado para o arquivo exportado."""
    data_str = data_posicao.strftime("%d-%m-%Y")
    return f"enquadramento_{nome_plano(plano_sel).replace(' ', '_')}_{data_str}_{st.session_state['regime_ativo']}.{extensao}"


def gerar_zip_pdfs(planos_sel: list) -> bytes:
    """Gera um ZIP contendo um PDF por plano selecionado."""
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "enquadramento_planos.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            for p in planos_sel:
                pdf = gerar_pdf(df_filtrado_data, p, data_posicao, st.session_state["regime_ativo"])
                zf.writestr(gerar_nome_arquivo(p, "pdf"), pdf)
        return open(zip_path, "rb").read()


def gerar_zip_csvs(planos_sel: list) -> bytes:
    """Gera um ZIP contendo um CSV por plano selecionado."""
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "enquadramento_planos_csv.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            for p in planos_sel:
                df_csv = df_filtrado_data[
                    (df_filtrado_data["ESTRUTURA_ASSOCIADA"] == p)
                    & (df_filtrado_data["CONJUNTO"] == st.session_state["regime_ativo"])
                ]
                zf.writestr(gerar_nome_arquivo(p, "csv"), df_csv.to_csv(index=False))
        return open(zip_path, "rb").read()


_, col_export = st.columns([3, 1])
with col_export:
    with st.expander("Exportar dados (PDF ou CSV)", icon=None, key="exportar_dados_expander"):
        tipo_export = st.radio("Formato de exportação:", ["PDF", "CSV"], horizontal=True, key="tipo_exportacao_radio")

        # Pré-seleciona o plano que está sendo visualizado no momento
        planos_multiplos = st.multiselect(
            "Selecione os planos para exportar:",
            options=planos,
            format_func=nome_plano,
            default=[st.session_state["selectbox_plano"]],
            key="multiplos_planos_export",
        )

        if planos_multiplos:
            data_str = data_posicao.strftime("%d-%m-%Y")
            regime = st.session_state["regime_ativo"]

            if tipo_export == "PDF":
                if len(planos_multiplos) == 1:
                    pdf_bytes = gerar_pdf(df_filtrado_data, planos_multiplos[0], data_posicao, regime)
                    st.download_button("Exportar PDF", data=pdf_bytes, file_name=gerar_nome_arquivo(planos_multiplos[0], "pdf"), mime="application/pdf")
                else:
                    st.download_button("Exportar ZIP com PDFs", data=gerar_zip_pdfs(planos_multiplos), file_name=f"enquadramento_planos_{data_str}_{regime}.zip", mime="application/zip")

            else:  # CSV
                if len(planos_multiplos) == 1:
                    df_csv = df_filtrado_data[
                        (df_filtrado_data["ESTRUTURA_ASSOCIADA"] == planos_multiplos[0])
                        & (df_filtrado_data["CONJUNTO"] == regime)
                    ]
                    st.download_button("Exportar CSV", data=df_csv.to_csv(index=False).encode("utf-8-sig"), file_name=gerar_nome_arquivo(planos_multiplos[0], "csv"), mime="text/csv")
                else:
                    st.download_button("Exportar ZIP com CSVs", data=gerar_zip_csvs(planos_multiplos), file_name=f"enquadramento_planos_{data_str}_{regime}.zip", mime="application/zip")


# ── TABELA AGREGADA (somente Política de Investimentos) ───────────────────────

if st.session_state["regime_ativo"] == "Política de Investimentos":
    st.subheader("Limites de Alocação e Concentração", text_alignment="center")
    st.space(size="xxsmall")

    # Filtra apenas as linhas que representam os totais por segmento
    df_agregado = df_plano[df_plano["DESCRICAO"].isin(ORDEM_SEGMENTOS)].copy()
    df_agregado["DESCRICAO"] = pd.Categorical(df_agregado["DESCRICAO"], categories=ORDEM_SEGMENTOS, ordered=True)
    df_agregado = df_agregado.sort_values("DESCRICAO")

    # Calcula o percentual de posição atual em relação ao valor de referência
    df_agregado["PCT_ATUAL"] = (df_agregado["VALOR_ATUAL"] / df_agregado["VALOR_REFERENCIA"]) * 100

    # Seleciona e renomeia colunas para exibição
    colunas_map = {
        "DESCRICAO": "Segmento de Aplicação",
        "LIMITE_PERCENTUAL": "Limite %",
        "VALOR_LIMITE_REGRA": "Limite R$",
        "PCT_ATUAL": "Posição %",
        "VALOR_ATUAL": "Posição R$",
        "PERCENTUAL_UTILIZADO": "Limite Utilizado %",
        "STATUS": "Status",
    }
    df_agregado = df_agregado[list(colunas_map.keys())].rename(columns=colunas_map)

    # Adiciona linha de totais (calculada antes da formatação)
    linha_total = pd.DataFrame({
        "Segmento de Aplicação": ["Total de Recursos Garantidores"],
        "Posição %": [df_agregado["Posição %"].sum()],
        "Posição R$": [df_agregado["Posição R$"].sum()],
    })
    df_agregado = pd.concat([df_agregado, linha_total], ignore_index=True)

    # Formatação dos valores (feita após o cálculo dos totais)
    # Colunas de Percentual
    df_agregado["Limite %"] = df_agregado["Limite %"].apply(formatar_percentual_br)
    df_agregado["Limite Utilizado %"] = df_agregado["Limite Utilizado %"].apply(formatar_percentual_br)
    df_agregado["Posição %"] = df_agregado["Posição %"].apply(formatar_percentual_br)

    # Colunas de Dinheiro (R$)
    df_agregado["Posição R$"] = df_agregado["Posição R$"].apply(fmt_br)
    df_agregado["Limite R$"] = df_agregado["Limite R$"].apply(fmt_br)
    df_agregado = df_agregado.fillna("-")

    exibir_tabela(df_agregado, borda_inferior='ultima-linha')


st.divider()


# ── TABELAS POR SEGMENTO ──────────────────────────────────────────────────────

# Ordena os segmentos do plano conforme a ordem canônica definida em ORDEM_SEGMENTOS
segmentos = sorted(
    df_plano["SEGMENTO"].unique(),
    key=lambda x: ORDEM_SEGMENTOS.index(x) if x in ORDEM_SEGMENTOS else len(ORDEM_SEGMENTOS),
)

for segmento in segmentos:
    df_segmento = (
        df_plano[df_plano["SEGMENTO"] == segmento]
        .sort_values("ORDEM")
        .copy()
    )
    df_segmento["DESCRICAO"] = df_segmento["DESCRICAO"].apply(limpar_texto)

    st.subheader(segmento)

    # ── Resolução 4994 ────────────────────────────────────────────────────────
    if st.session_state["regime_ativo"] == "Resolução 4994":

        if segmento not in ["Emissores (Art. 27)", "Emissores (Art. 28)"]:
            # Tabela padrão de segmento
            df_exibir = preparar_df_segmento(df_segmento)

        else:
            # Tabela de emissores: inclui coluna de Grupo Econômico e merge visual por descrição
            df_segmento["GRP_ECONOMICO"] = df_segmento["AGREGACAO"].apply(remove_grp)
            df_segmento = df_segmento.sort_values(["ORDEM", "DESCRICAO"])

            df_exibir = df_segmento[[
                "DESCRICAO", "GRP_ECONOMICO", "VALOR_LIMITE_REGRA", "VALOR_ATUAL",
                "PERCENTUAL_UTILIZADO", "PERCENTUAL_ULTRAPASSADO", "PERCENTUAL_TOTAL", "STATUS",
            ]].copy()
            df_exibir.columns = [
                "Descrição", "Grupo Econômico", "Limite R$", "Posição R$",
                "Limite Utilizado %", "% Ultrapassado", "% Total", "Status",
            ]

            df_exibir["Limite Utilizado %"] = df_exibir["Limite Utilizado %"].apply(formatar_percentual_br)
            df_exibir["% Ultrapassado"] = df_exibir["% Ultrapassado"].apply(formatar_percentual_br)
            df_exibir["% Total"] = df_exibir["% Total"].apply(formatar_percentual_br)
            df_exibir["Posição R$"] = df_exibir["Posição R$"].apply(formatar_brl)
            df_exibir["Limite R$"] = df_exibir["Limite R$"].apply(formatar_brl)

            # Merge visual: oculta repetições consecutivas na coluna Descrição
            df_exibir["Descrição"] = df_exibir["Descrição"].where(
                df_exibir["Descrição"] != df_exibir["Descrição"].shift(), ""
            )

            df_exibir = df_exibir.drop(columns=["% Total", "% Ultrapassado"])

    # ── Política de Investimentos ─────────────────────────────────────────────
    else:
        if segmento not in ORDEM_SEGMENTOS:
            st.warning(f"Segmento '{segmento}' não está na lista de segmentos esperados.")
            continue

        # Ordena as descrições conforme a ordem canônica de regras
        df_segmento["DESCRICAO"] = pd.Categorical(df_segmento["DESCRICAO"], categories=ORDEM_REGRAS_PI, ordered=True)
        df_segmento = df_segmento.sort_values("DESCRICAO")

        df_exibir = preparar_df_segmento(df_segmento)

        # Remove a primeira linha (cabeçalho de segmento duplicado vindo da query)
        df_exibir = df_exibir.iloc[1:]

    exibir_tabela(df_exibir, borda_inferior=False)