import streamlit as st
import pandas as pd
from utils.gerar_pdf import gerar_pdf_risco_planos
from utils.queries.risco_mercado_planos import buscar_dados as buscar_dados_planos
from utils.queries.risco_mercado_segmentos import buscar_dados as buscar_dados_segmentos
import os
import plotly.graph_objects as go
from utils.helpers import ( 
                           nome_plano,
                           renderizar_tabela_estilizada,
                           card_geral,
                           formatar_numero,
                           fmt_br,
                           card_limites_excedidos
                           )

# Carregar dados c

@st.cache_data(ttl="1h", show_time=True)
def carregar_dados() -> pd.DataFrame:
    return buscar_dados_planos()

 


df_planos = carregar_dados()

df_planos.columns = df_planos.columns.str.upper()

colunas_map = {
    'TESOURARIA': 'Planos',
    'POSICAO': 'Posição R$',
    'DATA_COTACAO': 'DATA_COTACAO',
    'RISCO': 'VaR R$',
    'RISCO/POSICAO_%': 'VaR %',
    'LIMITE_INTERNO_%': 'Lim. Interno %',
    'STATUS_%':'Status %',
    'VARIACAO_POSICAO_STRESS_1': 'Stress (+) R$',
    'VARIACAO_POSICAO_STRESS_1/POSICAO_%': 'Stress (+) %',
    'VARIACAO_POSICAO_STRESS_2': 'Stress (-) R$',
    'VARIACAO_POSICAO_STRESS_2/POSICAO_%':'Stress (-) %',
    
}

# Seleciona e renomeia as colunas
df_planos = df_planos[list(colunas_map.keys())].rename(columns=colunas_map)

# Garante que DATA_COTACAO esteja como datetime
df_planos["DATA_COTACAO"] = pd.to_datetime(
    df_planos["DATA_COTACAO"],
    errors="coerce"
)
df_historico = df_planos.copy()
# Remove linhas sem data válida
df_planos = df_planos.dropna(subset=["DATA_COTACAO"])

# Inicializa a data selecionada como date, não Timestamp
if "data-selecionada-risco" not in st.session_state:
    st.session_state["data-selecionada-risco"] = df_planos["DATA_COTACAO"].max().date()



from html import escape


def _escape_html(valor) -> str:
    if valor is None:
        return ""

    return escape(str(valor), quote=True)


def titulo_section(
    titulo: str,
    subtitulo: str = None,
    help: str = None,
    mostrar_linha: bool = True,
    tamanho_titulo: int = 18,
    peso_titulo: int = 900,
    cor_titulo: str = "#0B2F13",
    cor_linha: str = "rgba(11, 47, 19, 0.22)",
    margem_topo: int = 8,
    margem_baixo: int = 1,
):
    """
    Renderiza um título de seção genérico com:
    - título;
    - subtítulo opcional;
    - tooltip opcional;
    - linha horizontal opcional à direita.

    Exemplo:
        titulo_section(
            "Resumo de Risco por Plano",
            subtitulo="Visão consolidada dos limites internos",
            help="Possibilidade"
        )
    """

    titulo_html = _escape_html(titulo)
    subtitulo_html = _escape_html(subtitulo)
    help_html_texto = _escape_html(help)

    tooltip_html = ""

    if help:
        tooltip_html = f"""
        <span class="section-title-help" aria-label="{help_html_texto}">
            ?
            <span class="section-title-tooltip">{help_html_texto}</span>
        </span>
        """

    linha_html = ""

    if mostrar_linha:
        linha_html = '<div class="section-title-line"></div>'

    subtitulo_bloco = ""

    if subtitulo:
        subtitulo_bloco = f"""
        <div class="section-subtitle-text">
            {subtitulo_html}
        </div>
        """

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

        .section-title-help {{
            position: relative;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 15px;
            height: 15px;
            border-radius: 999px;
            font-size: 10px;
            font-weight: 700;
            line-height: 1;
            cursor: pointer;
            color: #0B2F13;
            background: #A8EC7D;
            border: none;
            text-transform: none;
            letter-spacing: 0;
            flex-shrink: 0;
        }}

        .section-title-help:hover {{
            color: #0B2F13;
            background: #c7f7a8;
        }}

        .section-title-tooltip {{
            visibility: hidden;
            opacity: 0;
            position: absolute;
            bottom: 130%;
            left: 0;
            background-color: #0B2F13;
            color: #FAFBEB;
            text-align: left;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 400;
            font-style: normal;
            font-family: 'Figtree', sans-serif;
            white-space: normal;
            width: 200px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
            transition: opacity 0.2s ease-in-out;
            z-index: 9999;
            line-height: 1.35;
            letter-spacing: 0;
            pointer-events: none;
        }}

        .section-title-help:hover .section-title-tooltip {{
            visibility: visible;
            opacity: 1;
        }}

        .section-title-line {{
            flex: 1;
            height: 1px;
            background: {cor_linha};
            margin-left: 4px;
        }}

        .section-subtitle-text {{
            margin-top: 4px;
            color: #5a5a5a;
            font-size: 13px;
            font-weight: 500;
            line-height: 1.35;
        }}
    </style>

    <div class="section-title-container">
        <div class="section-title-row">
            <span class="section-title-text">{titulo_html}</span>
            {tooltip_html}
            {linha_html}
        </div>
        {subtitulo_bloco}
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

    .st-key-meu-container {
        background-color: #0B2F13;
        border-radius: 0px;
        padding: 30px 20px 30px 20px;
        width: 100%;
        box-sizing: border-box;
    }
    
    /* Container do conteúdo COM padding lateral */
    .st-key-conteudo {
        padding-left: 3rem;
        padding-right: 3rem;
    }
        
</style>
""")

with st.container(key="meu-container"):
    st.html("""
        <p style="text-align:center; color:#FAFBEB; margin:0 0; font-size: clamp(20px, 3vw, 29px); font-weight:400;">
            Risco de Mercado - 
            <span style='color:#A8EC7D; font-family:"Source Serif 4",serif; font-style:italic; font-weight:600;'>
                Planos
            </span>
        </p>
    """)

with st.container(horizontal_alignment="center", gap=None, key="conteudo"):
    with st.container(width=1200):

            # ── DESCRIÇÃO + SELETOR DE DATA ───────────────────────────────────────────────
            col1, _, col2 = st.columns([1, 0.1, 0.5])
            with col1:
                st.markdown(
                    """
                    <div style="padding-left:20px; text-align:justify;; color:#5a5a5a; margin:0; font-size:16px; font-weight:400;">
                        Este painel apresenta uma visão do risco de mercado dos planos, com base no VaR (Value at Risk) paramétrico e diretrizes definidas
                        no Manual de Riscos de Investimento. 
                        O VaR é uma medida estatística que estima a perda potencial máxima em um determinado horizonte de tempo e nível de confiança.
                    </div>
                    """,
                    unsafe_allow_html=True
                )




            with col2:
                primeira_data = df_planos["DATA_COTACAO"].min().date()
                ultima_data = df_planos["DATA_COTACAO"].max().date()

                st.date_input(
                    "Selecione a data posição",
                    value=st.session_state["data-selecionada-risco"],
                    format="DD/MM/YYYY",
                    help=(
                        f"Datas disponíveis: "
                        f"{primeira_data.strftime('%d/%m/%Y')} a "
                        f"{ultima_data.strftime('%d/%m/%Y')}."
                    ),
                    min_value=primeira_data,
                    max_value=ultima_data,
                    key="data-selecionada-risco",
                )


            # Aviso se a data selecionada não tiver dados disponíveis
            datas_disponiveis = sorted(df_planos["DATA_COTACAO"].dt.date.unique())

            data_selecionada = st.session_state["data-selecionada-risco"]

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
                st.stop()


            df_planos_filtrado_dp = df_planos[df_planos["DATA_COTACAO"].dt.date == data_selecionada]

            pdf_bytes = gerar_pdf_risco_planos(
                df_planos_original=carregar_dados(),
                data_selecionada=st.session_state["data-selecionada-risco"],
            )

            _,  col3 = st.columns([0.85, 0.15])
            with col3:
                st.download_button(
                    label="Baixar relatório em PDF",
                    data=pdf_bytes,
                    file_name=f"risco_mercado_planos_{st.session_state['data-selecionada-risco'].strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary",
                )
            st.space()

            #-----------------CARDS
            with st.container():
                    
                titulo_section(
                    "Métricas de Risco Consolidado",
                    help=None
                )


                c1, c2, c3, c4, c5, c6 = st.columns(6)
                with c1:
                    card_geral(
                        titulo="Posição",
                        valor=formatar_numero(df_planos_filtrado_dp.loc[df_planos_filtrado_dp['Planos'] == '[CERES TOTAL]', 'Posição R$'].sum(), prefixo="R$ "),
                        valor_extenso=fmt_br(df_planos_filtrado_dp.loc[df_planos_filtrado_dp['Planos'] == '[CERES TOTAL]', 'Posição R$'].sum()),
                        help="Posição consolidada dos planos."
                    )
                with c2:
                    card_geral(
                        titulo="Risco Paramétrico",
                        valor=formatar_numero(df_planos_filtrado_dp.loc[df_planos_filtrado_dp['Planos'] == '[CERES TOTAL]', 'VaR R$'].sum(), prefixo="R$"),
                        valor_extenso=fmt_br(df_planos_filtrado_dp.loc[df_planos_filtrado_dp['Planos'] == '[CERES TOTAL]', 'VaR R$'].sum()),
                        help="VaR Paramétrico consolidado dos planos com 95% de confiança."
                    )
                with c3:
                    parametrico_consolidado = df_planos_filtrado_dp.loc[df_planos_filtrado_dp['Planos'] == '[CERES TOTAL]', 'VaR %'].sum()

                    card_geral(
                        titulo="Risco Paramétrico %",
                        valor=formatar_numero(parametrico_consolidado, sufixo="%"),
                        help="VaR Paramétrico consolidado dos planos com 95% de confiança, expresso em percentual da posição consolidada."
                    )
                with c4:
                    stress1 = df_planos_filtrado_dp.loc[df_planos_filtrado_dp['Planos'] == '[CERES TOTAL]', 'Posição R$'].sum()
                    card_geral(
                        titulo="Stress (+)",
                        valor=formatar_numero(stress1, prefixo="R$ "),
                        delta=formatar_numero(df_planos_filtrado_dp.loc[df_planos_filtrado_dp['Planos'] == '[CERES TOTAL]', 'Stress (+) R$'].sum(), prefixo="R$ "),
                        help="Posição após cenário favorável."
                    )
                with c5:
                    stress2 = df_planos_filtrado_dp.loc[df_planos_filtrado_dp['Planos'] == '[CERES TOTAL]', 'Stress (-) R$'].sum() + df_planos_filtrado_dp.loc[df_planos_filtrado_dp['Planos'] == '[CERES TOTAL]', 'Posição R$'].sum()

                    card_geral(
                        titulo="Stress (-)",
                        valor=formatar_numero(stress2, prefixo="R$ "),
                        delta=formatar_numero(df_planos_filtrado_dp.loc[df_planos_filtrado_dp['Planos'] == '[CERES TOTAL]', 'Stress (-) R$'].sum(), prefixo="R$ "),
                        help="Posição após cenário adverso."
                    )
                with c6:
                    execedido = df_planos_filtrado_dp.loc[(df_planos_filtrado_dp['Planos'] != '[CERES TOTAL]') & (df_planos_filtrado_dp["Status %"] > 100), 'Planos'].count()
                    n_execedido = df_planos_filtrado_dp.loc[(df_planos_filtrado_dp['Planos'] != '[CERES TOTAL]') & (df_planos_filtrado_dp["Status %"] <= 100), 'Planos'].count()

                    card_limites_excedidos(
                        titulo="Status dos Limites VAR",
                        qtd_ok=n_execedido,
                        qtd_excedido=execedido,
                        help="Quantidade de planos com o VaR paramétrico dentro e fora do limite estabelecido no Manual de Risco."
                    )
                    
                df_planos_exbir = df_planos_filtrado_dp.drop(columns=["DATA_COTACAO"])
                df_planos_exbir['Planos'] = df_planos_exbir['Planos'].apply(nome_plano)

                ultimos_12_meses = pd.to_datetime(data_selecionada) - pd.DateOffset(months=12)
                df_historico = df_historico[(df_historico['DATA_COTACAO'] >= ultimos_12_meses) & (df_historico['DATA_COTACAO'] <= pd.to_datetime(data_selecionada))]


            #______________________________GRÁFICO LINHAS
            titulo_section(
                    "Histórico VaR Paramétrico",
                    help=None
                )
            with st.container(border=True):
                
                st.markdown(
                    """
                    <div style="
                        margin: 0;
                        padding: 0;
                        height: 38px;
                        display: flex;
                        align-items: center;
                    ">
                        <p style="
                            margin: 0;
                            padding: 0;
                            font-family: Figtree, sans-serif;
                            font-size: 16px;
                            font-weight: 900;
                            color: #333333;
                        ">
                            VaR % Mensal
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                mostrar_limite = st.checkbox(
                    "Mostrar Limite Interno",
                    value=True,
                    key="mostrar_limite_var"
                )

                df_plot = df_historico.dropna(subset=["VaR %", "Planos"]).copy()
                df_plot["Planos"] = df_plot["Planos"].apply(nome_plano)
                df_plot["DATA_COTACAO"] = pd.to_datetime(df_plot["DATA_COTACAO"])

                # Ordenação real por data para montar o eixo corretamente
                df_plot = df_plot.sort_values(["DATA_COTACAO", "Planos"])

                if not df_plot.empty:

                    meses_pt = {
                        1: "Jan",
                        2: "Fev",
                        3: "Mar",
                        4: "Abr",
                        5: "Mai",
                        6: "Jun",
                        7: "Jul",
                        8: "Ago",
                        9: "Set",
                        10: "Out",
                        11: "Nov",
                        12: "Dez",
                    }

                    # ----------------------------
                    # EIXO X ESTÁVEL
                    # ----------------------------
                    df_plot["MES"] = df_plot["DATA_COTACAO"].dt.to_period("M")

                    # Chave real de ordenação do eixo
                    # Ex.: 2026-01, 2026-02, 2026-03...
                    df_plot["EIXO_X"] = df_plot["DATA_COTACAO"].dt.strftime("%Y-%m")

                    df_plot["MES_LABEL"] = (
                        df_plot["DATA_COTACAO"]
                        .dt.month
                        .map(meses_pt)
                    )

                    df_plot["ANO"] = (
                        df_plot["DATA_COTACAO"]
                        .dt.strftime("%Y")
                    )

                    df_eixo_x = (
                        df_plot
                        .sort_values("DATA_COTACAO")
                        .drop_duplicates(subset=["EIXO_X"])
                        [["EIXO_X", "ANO", "MES_LABEL", "DATA_COTACAO"]]
                        .copy()
                        .reset_index(drop=True)
                    )

                    ordem_x = df_eixo_x["EIXO_X"].tolist()

                    # ----------------------------
                    # LABEL DO EIXO X:
                    # MÊS EM CIMA + ANO CENTRALIZADO
                    # ----------------------------
                    ticktext_x = [""] * len(df_eixo_x)

                    for ano, df_ano in df_eixo_x.groupby("ANO", sort=False):
                        indices_ano = df_ano.index.tolist()
                        indice_central = indices_ano[len(indices_ano) // 2]

                        for idx in indices_ano:
                            mes = df_eixo_x.loc[idx, "MES_LABEL"]

                            if idx == indice_central:
                                ticktext_x[idx] = f"{mes}<br>{ano}"
                            else:
                                ticktext_x[idx] = f"{mes}<br>"

                    # ----------------------------
                    # POSIÇÕES DO "|" ENTRE OS ANOS
                    # ----------------------------
                    separadores_ano = []

                    for idx in range(1, len(df_eixo_x)):
                        ano_atual = df_eixo_x.loc[idx, "ANO"]
                        ano_anterior = df_eixo_x.loc[idx - 1, "ANO"]

                        if ano_atual != ano_anterior:
                            # Em eixo category, as posições são 0, 1, 2...
                            # O meio entre duas categorias fica em idx - 0.5
                            separadores_ano.append(idx - 0.5)

                    # ----------------------------
                    # RANGE DO EIXO Y
                    # ----------------------------
                    y_min = df_plot["VaR %"].min()
                    y_max = df_plot["VaR %"].max()

                    if mostrar_limite and "Lim. Interno %" in df_plot.columns:
                        y_min = min(y_min, df_plot["Lim. Interno %"].min())
                        y_max = max(y_max, df_plot["Lim. Interno %"].max())

                    padding_y = (y_max - y_min) * 0.2

                    if padding_y == 0:
                        padding_y = abs(y_max) * 0.2 if y_max != 0 else 1

                    # ----------------------------
                    # CORES FIXAS POR PLANO
                    # ----------------------------
                    paleta_padrao = [
                        "#0B2F13",  # verde escuro - Renda Fixa
                        "#D64550",  # vermelho coral - Renda Variável
                        "#A8EC7D",  # verde claro - Estruturado
                        "#2DC25F",  # verde vivo - Operações com Participantes
                        "#174C25",  # verde floresta
                        "#CCF1DF",  # verde muito claro - Imobiliário
                        "#6D597A",  # roxo acinzentado - Exterior
                        "#B83A45",  # vermelho escuro
                        "#8FD76A",  # verde lima suave
                        "#24A850",  # verde médio
                        "#B3E6D0",  # verde água claro
                        "#5A4967",  # roxo escuro
                        "#256B36",  # verde folha escuro
                        "#E0666F",  # coral claro
                        "#C2F29E",  # verde pastel
                        "#4FD17A",  # verde fresco
                        "#DDF7EC",  # menta clara
                        "#806A8C",  # lavanda escura
                        "#030704",  # verde profundo
                        "#F08A91",  # rosé coral
                    ]

                    planos_ordenados = sorted(df_plot["Planos"].unique())

                    cores_planos = {
                        plano: paleta_padrao[i % len(paleta_padrao)]
                        for i, plano in enumerate(planos_ordenados)
                    }

                    fig = go.Figure()

                    # ----------------------------
                    # LINHAS POR PLANO
                    # ----------------------------
                    for plano, df_p in df_plot.groupby("Planos"):

                        df_p = df_p.sort_values("DATA_COTACAO").copy()

                        visivel = True if plano == "Consolidado" else "legendonly"
                        cor_plano = cores_planos[plano]

                        # Linha do VaR %
                        fig.add_trace(
                            go.Scatter(
                                x=df_p["EIXO_X"],
                                y=df_p["VaR %"],
                                mode="lines",
                                name=plano,
                                visible=visivel,
                                legendgroup=plano,
                                line=dict(
                                    color=cor_plano,
                                    width=2,
                                    shape="spline",
                                    smoothing=1.1,
                                ),
                                cliponaxis=False,
                                customdata=df_p["DATA_COTACAO"].dt.strftime("%d/%m/%Y"),
                                hovertemplate=(
                                    f"<b>{plano}</b><br>"
                                    "Data: %{customdata}<br>"
                                    "VaR: %{y:.2f}%"
                                    "<extra></extra>"
                                ),
                            )
                        )

                        # Linha do Lim. Interno %
                        if "Lim. Interno %" in df_p.columns:
                            fig.add_trace(
                                go.Scatter(
                                    x=df_p["EIXO_X"],
                                    y=df_p["Lim. Interno %"],
                                    mode="lines",
                                    name=f"{plano} - Lim. Interno",
                                    visible=visivel if mostrar_limite else False,
                                    showlegend=False,
                                    legendgroup=plano,
                                    line=dict(
                                        color=cor_plano,
                                        width=2,
                                        dash="dash",
                                        shape="spline",
                                        smoothing=1.3,
                                    ),
                                    cliponaxis=False,
                                    customdata=df_p["DATA_COTACAO"].dt.strftime("%d/%m/%Y"),
                                    hovertemplate=(
                                        f"<b>{plano} - Lim. Interno</b><br>"
                                        "Data: %{customdata}<br>"
                                        "Limite: %{y:.2f}%"
                                        "<extra></extra>"
                                    ),
                                )
                            )

                    # ----------------------------
                    # "|" EXATAMENTE ENTRE OS ANOS
                    # ----------------------------
                    for x_sep in separadores_ano:
                        fig.add_annotation(
                            x=x_sep,
                            y=-0.145,
                            xref="x",
                            yref="paper",
                            text="|",
                            showarrow=False,
                            font=dict(
                                family="Figtree",
                                size=13,
                                color="#333333",
                            ),
                            xanchor="center",
                            yanchor="middle",
                        )

                    fig.update_layout(
                        height=320,
                        autosize=True,
                        separators=",.",

                        font=dict(
                            family="Figtree",
                            size=16,
                            color="#333333",
                        ),

                        xaxis=dict(
                            type="category",
                            categoryorder="array",
                            categoryarray=ordem_x,
                            tickvals=ordem_x,
                            ticktext=ticktext_x,
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
                            visible=True,
                            showgrid=True,
                            gridcolor="rgba(90, 90, 90, 0.12)",
                            zeroline=False,
                            showticklabels=True,
                            ticksuffix="%",
                            tickfont=dict(
                                family="Figtree",
                                size=11,
                                color="#5a5a5a",
                            ),
                            range=[
                                y_min - padding_y * 0.1,
                                y_max + padding_y,
                            ],
                        ),

                        hovermode="x unified",

                        hoverlabel=dict(
                            bgcolor="#FBFCEC",
                            bordercolor="#0B2F13",
                            font=dict(
                                family="Figtree",
                                size=14,
                                color="#0B2F13",
                            ),
                        ),

                        legend=dict(
                            groupclick="togglegroup",
                            orientation="h",
                            yanchor="bottom",
                            y=1.08,
                            xanchor="center",
                            x=0.5,
                            font=dict(
                                family="Figtree",
                                size=14,
                                color="#333333",
                            ),
                        ),

                        margin=dict(
                            r=20,
                            t=0,
                            b=0,
                            l=0,
                        ),

                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                    )

                    st.plotly_chart(
                        fig,
                        config={
                            "displayModeBar": False,
                            "scrollZoom": False,
                        },
                        width="stretch",
                        key="grafico_risco_planos",
                    )

                else:
                    st.info("Não há dados disponíveis para o período selecionado.")





            with st.container():
                titulo_section(
                "VaR. Paramétrico % por Plano",
                help=None
            )
                # ____________________________ Var por plano grafico de barras
                df_planos_exbir = df_planos_exbir[df_planos_exbir['Planos'] != 'Consolidado'].copy()
                df_grafico = df_planos_exbir.sort_values("VaR %", ascending=False).copy()

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
                            x=df_grafico["Planos"],
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
                                line=dict(width=0)
                            ),
                            textfont=dict(
                                family="Figtree",
                                size=14,
                                color="#0B2F13"
                            ),
                            cliponaxis=False,
                        )
                    )

                    fig.update_layout(
                        bargap=0.12,
                        height=300,
                        autosize=True,
                        separators=",.",
                        font=dict(
                            family="Figtree",
                            size=14,
                            color="#333333"
                        ),
                        xaxis=dict(
                            categoryorder="total descending",
                            showline=False,
                            showgrid=False,
                            automargin=True,
                            tickfont=dict(
                                family="Figtree",
                                size=14,
                                color="#333333"
                            )
                        ),
                        yaxis=dict(
                            showgrid=False,
                            zeroline=False,
                            showticklabels=False,
                            range=[0, max_exp * 1.18]
                        ),
                        hoverlabel=dict(
                            font=dict(
                                family="Figtree",
                                size=14,
                                color="#0B2F13"
                            )
                        ),
                        margin=dict(
                            r=5,
                            t=8,
                            b=20,
                            l=5
                        ),
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                    )

                    st.plotly_chart(
                        fig,
                        config={"displayModeBar": False},
                        width="stretch"
                    )

            with st.container():
                titulo_section(
                "Resumo de Risco por Plano",
                help=None
            )

                from numbers import Number
                from html import escape


                _JS_TABELA_ORDENAVEL = """
                export default function(component) {
                    const { parentElement } = component;
                    const data = component.data || {};

                    const root = parentElement.querySelector("#tabela-root");

                    if (!root) {
                        return;
                    }

                    if (!data.html) {
                        root.innerHTML = "";
                        return;
                    }

                    root.innerHTML = data.html;

                    if (!data.ordenacao) {
                        return;
                    }

                    const wrapper = root.querySelector(".tabela-custom-wrapper");

                    if (!wrapper) {
                        return;
                    }

                    const body = wrapper.querySelector(".tabela-body-custom");
                    const headers = Array.from(wrapper.querySelectorAll(".header-cell-custom"));

                    if (!body || headers.length === 0) {
                        return;
                    }

                    const linhasOriginais = Array.from(body.querySelectorAll(".row-custom"));

                    let estado = {
                        coluna: null,
                        direcao: null
                    };

                    function normalizarNumero(valor) {
                        if (valor === null || valor === undefined || valor === "") {
                            return Number.NEGATIVE_INFINITY;
                        }

                        const numero = Number(valor);

                        if (Number.isNaN(numero)) {
                            return Number.NEGATIVE_INFINITY;
                        }

                        return numero;
                    }

                    function compararTexto(a, b) {
                        const textoA = String(a || "").toLocaleLowerCase("pt-BR");
                        const textoB = String(b || "").toLocaleLowerCase("pt-BR");

                        return textoA.localeCompare(textoB, "pt-BR", {
                            numeric: true,
                            sensitivity: "base"
                        });
                    }

                    function atualizarIcones() {
                        headers.forEach((header, index) => {
                            const indicador = header.querySelector(".sort-indicator-custom");

                            if (!indicador) {
                                return;
                            }

                            if (estado.coluna !== index || estado.direcao === null) {
                                indicador.textContent = "↕";
                            } else if (estado.direcao === "asc") {
                                indicador.textContent = "▲";
                            } else {
                                indicador.textContent = "▼";
                            }
                        });
                    }

                    function restaurarOrdemOriginal() {
                        linhasOriginais.forEach((linha) => body.appendChild(linha));
                    }

                    function ordenarPorColuna(colunaIndex, direcao) {
                        const header = headers[colunaIndex];
                        const tipo = header.dataset.sortType || "text";

                        const linhas = Array.from(body.querySelectorAll(".row-custom"));

                        linhas.sort((linhaA, linhaB) => {
                            const celulaA = linhaA.children[colunaIndex];
                            const celulaB = linhaB.children[colunaIndex];

                            const valorA = celulaA ? celulaA.dataset.orderValue : "";
                            const valorB = celulaB ? celulaB.dataset.orderValue : "";

                            let resultado;

                            if (tipo === "number") {
                                resultado = normalizarNumero(valorA) - normalizarNumero(valorB);
                            } else {
                                resultado = compararTexto(valorA, valorB);
                            }

                            return direcao === "asc" ? resultado : -resultado;
                        });

                        linhas.forEach((linha) => body.appendChild(linha));
                    }

                    const cleanups = [];

                    headers.forEach((header, colunaIndex) => {
                        header.classList.add("ordenavel");

                        const onClick = (event) => {
                            if (event.target && event.target.closest(".help-coluna-custom")) {
                                event.stopPropagation();
                                return;
                            }

                            if (estado.coluna !== colunaIndex) {
                                estado = {
                                    coluna: colunaIndex,
                                    direcao: "asc"
                                };
                            } else if (estado.direcao === "asc") {
                                estado = {
                                    coluna: colunaIndex,
                                    direcao: "desc"
                                };
                            } else if (estado.direcao === "desc") {
                                estado = {
                                    coluna: null,
                                    direcao: null
                                };
                            } else {
                                estado = {
                                    coluna: colunaIndex,
                                    direcao: "asc"
                                };
                            }

                            if (estado.direcao === null) {
                                restaurarOrdemOriginal();
                            } else {
                                ordenarPorColuna(estado.coluna, estado.direcao);
                            }

                            atualizarIcones();
                        };

                        header.addEventListener("click", onClick);
                        cleanups.push(() => header.removeEventListener("click", onClick));
                    });

                    atualizarIcones();

                    return () => {
                        cleanups.forEach((cleanup) => cleanup());
                    };
                }
                """


                def _get_componente_tabela_ordenavel():
                    """
                    Registra o componente v2 apenas uma vez por sessão.
                    Evita o warning:
                    Component tabela_ordenavel_custom is already registered.
                    """

                    chave = "_componente_tabela_ordenavel_custom_v1"

                    if chave not in st.session_state:
                        st.session_state[chave] = st.components.v2.component(
                            name="tabela_ordenavel_custom_v1",
                            html='<div id="tabela-root"></div>',
                            js=_JS_TABELA_ORDENAVEL,
                            isolate_styles=True,
                        )

                    return st.session_state[chave]


                def _escape_html(valor) -> str:
                    if valor is None:
                        return ""

                    return escape(str(valor), quote=True)


                def fmt_br(valor, casas=2) -> str:
                    """
                    Formata número no padrão brasileiro.
                    Exemplo:
                        1234.56 -> 1.234,56
                    """

                    try:
                        return f"{float(valor):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    except Exception:
                        return str(valor)


                def _classe_borda_inferior(borda_inferior: str) -> str:
                    if borda_inferior == "borda":
                        return "com-borda-inferior"

                    return "sem-borda-inferior"


                def _tipo_coluna_ordenacao(serie: pd.Series) -> str:
                    try:
                        serie_sem_nulos = serie.dropna()

                        if len(serie_sem_nulos) == 0:
                            return "text"

                        if pd.api.types.is_numeric_dtype(serie_sem_nulos):
                            return "number"

                        return "text"
                    except Exception:
                        return "text"


                def _valor_ordenacao(valor) -> str:
                    if pd.isna(valor):
                        return ""

                    if isinstance(valor, Number):
                        return str(float(valor))

                    return str(valor)


                def _formatar_numero_resumo_risco(valor, col) -> str:
                    if pd.isna(valor):
                        return "—"

                    if isinstance(valor, Number):
                        col_lower = str(col).lower()

                        if "r$" in col_lower:
                            return f"R$ {fmt_br(valor, 2)}"

                        if "%" in col_lower:
                            return f"{fmt_br(valor, 2)}%"

                        return fmt_br(valor, 2)

                    return str(valor)


                def _formatar_status_resumo_risco(valor) -> str:
                    if pd.isna(valor):
                        return "—"

                    try:
                        numero = float(valor)
                    except Exception:
                        return str(valor)

                    if numero <= 100:
                        return "✓ Dentro"

                    return "⚠ Acima"


                _CSS_TABELA_RESUMO_RISCO_PLANOS = """
                <style>
                .tabela-custom-wrapper {
                    font-family: 'Figtree', sans-serif;
                    width: 100%;
                    overflow: visible;
                    border-radius: 14px;
                    background: transparent;
                }

                .tabela-custom-wrapper.com-borda-inferior {
                    border-bottom: 1px solid rgba(11, 47, 19, 0.14);
                }

                .tabela-custom-wrapper.sem-borda-inferior {
                    border-bottom: none;
                }

                .th-custom {
                    display: grid;
                    align-items: center;
                    background: #0B2F13;
                    border-bottom: 1px solid rgba(168, 236, 125, 0.35);
                    border-radius: 14px 14px 0 0;
                    overflow: visible;
                    position: relative;
                    z-index: 20;
                }

                .header-cell-custom {
                    min-height: 42px;
                    padding: 10px 12px;
                    font-size: 12px;
                    font-weight: 700;
                    color: #A8EC7D;
                    letter-spacing: 0.02em;
                    display: flex;
                    align-items: center;
                    justify-content: flex-start;
                    gap: 6px;
                    box-sizing: border-box;
                    user-select: none;
                    text-align: left;
                    border-right: none;
                    position: relative;
                    overflow: visible;
                }

                .header-cell-custom.ordenavel {
                    cursor: pointer;
                }

                .header-cell-custom.ordenavel:hover {
                    background: transparent;
                }

                .header-cell-custom:first-child {
                    border-top-left-radius: 14px;
                }

                .header-cell-custom:last-child {
                    border-top-right-radius: 14px;
                    border-right: none;
                }

                .sort-indicator-custom {
                    font-size: 10px;
                    color: #A8EC7D;
                    opacity: 0.85;
                    line-height: 1;
                    margin-left: auto;
                }

                .tabela-body-custom {
                    width: 100%;
                    overflow: visible;
                    background: transparent;
                    position: relative;
                    z-index: 1;
                }

                .row-custom {
                    display: grid;
                    align-items: stretch;
                    border-bottom: 1px solid rgba(11, 47, 19, 0.14);
                    background: transparent;
                }

                .row-custom:last-child {
                    border-bottom: none;
                }

                .row-custom:last-child .col-custom:first-child {
                    border-bottom-left-radius: 14px;
                }

                .row-custom:last-child .col-custom:last-child {
                    border-bottom-right-radius: 14px;
                }

                .row-custom:hover {
                    background: rgba(11, 47, 19, 0.03);
                }

                .row-custom.destaque {
                    background: rgba(168, 236, 125, 0.08);
                }

                .row-custom.destaque:hover {
                    background: rgba(168, 236, 125, 0.12);
                }

                .col-custom {
                    min-height: 40px;
                    padding: 10px 12px;
                    font-size: 13px;
                    font-weight: 500;
                    color: #0B2F13;
                    display: flex;
                    align-items: center;
                    justify-content: flex-start;
                    box-sizing: border-box;
                    word-break: break-word;
                    text-align: left;
                    background: transparent;
                    border-right: none;
                }

                .col-custom:last-child {
                    border-right: none;
                }

                .col-custom.col-planos {
                    justify-content: flex-start;
                    text-align: left;
                    font-weight: 600;
                }

                .col-custom.col-numero {
                    justify-content: flex-start;
                    text-align: left;
                }

                .tabela-borda-final {
                    height: 1px;
                    background: rgba(11, 47, 19, 0.14);
                    width: 100%;
                }

                .tabela-sem-borda-final {
                    height: 0;
                    width: 100%;
                }

                /* Cores somente nos valores */
                .valor-var {
                    color: #B45309;
                    font-weight: 700;
                }

                .valor-status-ok {
                    color: #22C55E;
                    font-weight: 700;
                }

                .valor-status-alerta {
                    color: #EF4444;
                    font-weight: 700;
                }

                .valor-stress-positivo {
                    color: #22C55E;
                    font-weight: 700;
                }

                .valor-stress-negativo {
                    color: #EF4444;
                    font-weight: 700;
                }

                .help-coluna-custom {
                    position: relative;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    width: 15px;
                    height: 15px;
                    border-radius: 999px;
                    font-size: 10px;
                    font-weight: 700;
                    line-height: 1;
                    cursor: pointer;
                    color: #0B2F13;
                    background: #A8EC7D;
                    border: none;
                    text-transform: none;
                    letter-spacing: 0;
                    flex-shrink: 0;
                }

                .help-coluna-custom:hover {
                    color: #0B2F13;
                    background: #c7f7a8;
                }

                .tooltip-coluna-custom {
                    visibility: hidden;
                    opacity: 0;
                    position: absolute;

                    top: calc(100% + 8px);
                    right: 0;

                    background-color: #0B2F13;
                    color: #FAFBEB;
                    text-align: left;
                    padding: 8px 12px;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 400;
                    font-style: normal;
                    font-family: 'Figtree', sans-serif;
                    white-space: normal;
                    width: 200px;
                    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
                    transition: opacity 0.2s ease-in-out;
                    z-index: 99999;
                    line-height: 1.35;
                    letter-spacing: 0;
                    pointer-events: none;
                }

                .help-coluna-custom:hover .tooltip-coluna-custom {
                    visibility: visible;
                    opacity: 1;
                }
                </style>
                """


                def gerar_html_tabela_resumo_risco_planos(
                    df: pd.DataFrame,
                    nomes_colunas: dict = None,
                    primeira_coluna_larga: bool = True,
                    mask_destaque: pd.Series = None,
                    formatar_valores: bool = True,
                    borda_inferior="borda",
                    config_colunas: dict = None,
                    ordenacao: bool = True,
                ) -> str:
                    """
                    Gera apenas o HTML da tabela.

                    Use esta função se quiser capturar o HTML como string.
                    Para renderizar no Streamlit com ordenação, use tabela_resumo_risco_planos().
                    """

                    if df is None:
                        df = pd.DataFrame()

                    if config_colunas is None:
                        config_colunas = {}

                    colunas_padrao = [
                        "Planos",
                        "Posição R$",
                        "VaR R$",
                        "VaR %",
                        "Lim. Interno %",
                        "Status %",
                        "Stress (+) R$",
                        "Stress (+) %",
                        "Stress (-) R$",
                        "Stress (-) %",
                    ]

                    colunas_existentes = [col for col in colunas_padrao if col in df.columns]
                    colunas_extras = [col for col in df.columns if col not in colunas_padrao]

                    if len(colunas_existentes) > 0:
                        df = df[colunas_existentes + colunas_extras]

                    if nomes_colunas is None:
                        nomes_colunas = {col: col for col in df.columns}

                    qtd_colunas = len(df.columns)

                    if qtd_colunas == 0:
                        return """
                        <div style="font-family: 'Figtree', sans-serif; padding: 12px;">
                            Nenhum dado para exibir.
                        </div>
                        """

                    larguras_padrao = {
                        "Planos": "1.7fr",
                        "Posição R$": "1.1fr",
                        "VaR R$": "1.05fr",
                        "VaR %": "0.9fr",
                        "Lim. Interno %": "1fr",
                        "Status %": "0.9fr",
                        "Stress (+) R$": "1.1fr",
                        "Stress (+) %": "0.9fr",
                        "Stress (-) R$": "1.1fr",
                        "Stress (-) %": "0.9fr",
                    }

                    helps_padrao = {
                        "Planos": None,
                        "Posição R$": None,
                        "VaR R$": None,
                        "VaR %": None,
                        "Lim. Interno %": None,
                        "Status %": None,
                        "Stress (+) R$": None,
                        "Stress (+) %": None,
                        "Stress (-) R$": None,
                        "Stress (-) %": None,
                    }

                    grid_partes = []

                    for i, col in enumerate(df.columns):
                        cfg = config_colunas.get(col, {})

                        if "largura" in cfg:
                            grid_partes.append(str(cfg["largura"]))
                        elif col in larguras_padrao:
                            grid_partes.append(larguras_padrao[col])
                        elif i == 0 and primeira_coluna_larga:
                            grid_partes.append("2fr")
                        else:
                            grid_partes.append("1fr")

                    grid = " ".join(grid_partes)
                    classe_borda = _classe_borda_inferior(borda_inferior)

                    html_tabela = _CSS_TABELA_RESUMO_RISCO_PLANOS
                    html_tabela += f'<div class="tabela-custom-wrapper {classe_borda}">'

                    # Cabeçalho
                    html_tabela += f'<div class="th-custom" style="grid-template-columns:{_escape_html(grid)};">'

                    for col_index, col in enumerate(df.columns):
                        cfg = config_colunas.get(col, {})

                        nome_coluna = _escape_html(nomes_colunas.get(col, col))
                        help_coluna = cfg.get("help", helps_padrao.get(col))
                        tipo_ordenacao = _tipo_coluna_ordenacao(df[col])

                        html_tabela += (
                            f'<div class="header-cell-custom" '
                            f'data-col-index="{col_index}" '
                            f'data-sort-type="{_escape_html(tipo_ordenacao)}">'
                            f'<span>{nome_coluna}</span>'
                        )

                        if help_coluna:
                            help_html = _escape_html(help_coluna)
                            html_tabela += (
                                f'<span class="help-coluna-custom" aria-label="{help_html}">'
                                f'?'
                                f'<span class="tooltip-coluna-custom">{help_html}</span>'
                                f'</span>'
                            )

                        if ordenacao:
                            html_tabela += '<span class="sort-indicator-custom">↕</span>'

                        html_tabela += '</div>'

                    html_tabela += '</div>'

                    # Corpo sem rolagem
                    html_tabela += '<div class="tabela-body-custom">'

                    for idx, row in df.iterrows():
                        classe_destaque = ""

                        if mask_destaque is not None and idx in mask_destaque.index and bool(mask_destaque.loc[idx]):
                            classe_destaque = " destaque"

                        html_tabela += f'<div class="row-custom{classe_destaque}" style="grid-template-columns:{_escape_html(grid)};">'

                        for col in df.columns:
                            valor = row[col]
                            cfg = config_colunas.get(col, {})

                            classe_coluna = ""
                            classe_valor = ""

                            if col == "Planos":
                                classe_coluna += " col-planos"

                            if col in [
                                "Posição R$",
                                "VaR R$",
                                "VaR %",
                                "Lim. Interno %",
                                "Status %",
                                "Stress (+) R$",
                                "Stress (+) %",
                                "Stress (-) R$",
                                "Stress (-) %",
                            ]:
                                classe_coluna += " col-numero"

                            formatador_custom = cfg.get("format")

                            if callable(formatador_custom):
                                try:
                                    valor_fmt = formatador_custom(valor)
                                except Exception:
                                    valor_fmt = "—"

                            elif col == "Status %":
                                valor_fmt = _formatar_status_resumo_risco(valor)

                                try:
                                    numero_status = float(valor)
                                    if numero_status <= 100:
                                        classe_valor = "valor-status-ok"
                                    else:
                                        classe_valor = "valor-status-alerta"
                                except Exception:
                                    classe_valor = ""

                            elif col in ["Stress (+) R$"]:
                                valor_fmt = f"↑ {_formatar_numero_resumo_risco(valor, col)}"
                                classe_valor = "valor-stress-positivo"
                            
                            elif col in ["Stress (+) %"]:
                                valor_fmt = f"{_formatar_numero_resumo_risco(valor, col)}"
                                classe_valor = "valor-stress-positivo"

                            elif col in ["Stress (-) R$"]:
                                valor_fmt = f"↓ {_formatar_numero_resumo_risco(valor, col)}"
                                classe_valor = "valor-stress-negativo"

                            elif col in ["Stress (-) %"]:
                                valor_fmt = f"{_formatar_numero_resumo_risco(valor, col)}"
                                classe_valor = "valor-stress-negativo"

                            elif formatar_valores:
                                valor_fmt = _formatar_numero_resumo_risco(valor, col)

                                if col in ["VaR R$", "VaR %"]:
                                    classe_valor = "valor-var"

                            else:
                                valor_fmt = str(valor) if pd.notna(valor) else "—"

                                if col in ["VaR R$", "VaR %"]:
                                    classe_valor = "valor-var"

                            valor_fmt_html = _escape_html(valor_fmt)
                            valor_ordem_html = _escape_html(_valor_ordenacao(valor))

                            classe_extra = cfg.get("classe", "")
                            style_extra = cfg.get("style", "")

                            classe_coluna = f"{classe_coluna} {classe_extra}".strip()

                            html_tabela += (
                                f'<div class="col-custom {_escape_html(classe_coluna)}" '
                                f'data-order-value="{valor_ordem_html}" '
                                f'style="{_escape_html(style_extra)}">'
                            )

                            if classe_valor:
                                html_tabela += f'<span class="{_escape_html(classe_valor)}">{valor_fmt_html}</span>'
                            else:
                                html_tabela += valor_fmt_html

                            html_tabela += '</div>'

                        html_tabela += '</div>'

                    html_tabela += '</div>'

                    if borda_inferior == "borda":
                        html_tabela += '<div class="tabela-borda-final"></div>'
                    else:
                        html_tabela += '<div class="tabela-sem-borda-final"></div>'

                    html_tabela += '</div>'

                    return html_tabela


                def tabela_resumo_risco_planos(
                    df: pd.DataFrame,
                    nomes_colunas: dict = None,
                    primeira_coluna_larga: bool = True,
                    mask_destaque: pd.Series = None,
                    formatar_valores: bool = True,
                    borda_inferior="borda",
                    config_colunas: dict = None,
                    ordenacao: bool = True,
                ):
                    """
                    Renderiza a tabela no Streamlit usando componente v2.

                    Esta é a função que você deve chamar na tela.
                    """

                    html = gerar_html_tabela_resumo_risco_planos(
                        df=df,
                        nomes_colunas=nomes_colunas,
                        primeira_coluna_larga=primeira_coluna_larga,
                        mask_destaque=mask_destaque,
                        formatar_valores=formatar_valores,
                        borda_inferior=borda_inferior,
                        config_colunas=config_colunas,
                        ordenacao=ordenacao,
                    )

                    componente = _get_componente_tabela_ordenavel()

                    # Altura com folga extra para o tooltip aparecer dentro do componente.
                    altura = 58 + max(len(df), 1) * 44 + 80

                    return componente(
                        data={
                            "html": html,
                            "ordenacao": ordenacao,
                        },
                        height=altura,
                    )


                tabela_resumo_risco_planos(
                    df_planos_exbir,
                    ordenacao=True,
                    config_colunas={
                        "VaR R$": {
                            "help": "VaR Paramétrico calculado pela volatilidade de 252 dias úteis"
                        },
                        "VaR %": {
                            "help": "% do VaR Paramétrico sobre patrimônio total do plano"
                        },
                        "Lim. Interno %": {
                            "help": "Limite máximo de VaR Paramétrico permitido conforme o Manual de Risco do Plano"
                        }
                    }
                )