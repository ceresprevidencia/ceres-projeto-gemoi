import streamlit as st
import pandas as pd
from utils.queries.ipca import buscar_dados as buscar_ipca
from utils.queries.rent_mensal_planos import buscar_dados as buscar_rent_mensal_planos
from utils.queries.rent_grupos import buscar_dados as buscar_grupos
from utils.queries.rent_planos import buscar_dados as buscar_planos
from utils.queries.rent_produtos import buscar_dados as buscar_dados_produtos
import plotly.graph_objects as go
from utils.helpers import (primeiro_dia_util, 
                           nome_plano, fmt_br, 
                           card_geral, 
                           formatar_numero, 
                           formatar_percentual_br, 
                           card_rentabilidade_meta, 
                           _NOMES_PLANOS,
                           card_segmento_rentabilidade,
                           card_segmento_rentabilidade_sem_projetada,
                           renderizar_tabela_estilizada,
                           de_para_produto,
                           CORES_SEGMENTOS)
from pathlib import Path

# Carregar dados c
@st.cache_data(ttl="12h", show_time=True)
def carregar_ipca() -> pd.DataFrame:
    try:
        return buscar_ipca()
    except Exception as e:
        st.error(f"Erro ao carregar dados do IPCA: {e}")
        st.stop()

@st.cache_data(ttl="12h", show_time=True)
def carregar_planos() -> pd.DataFrame:
    try:
        return buscar_planos()
    except Exception as e:
        st.error(f"Erro ao carregar dados dos planos: {e}")
        st.stop()

@st.cache_data(ttl="12h", show_time=True)
def carregar_grupos() -> pd.DataFrame:
    try:
        return buscar_grupos()
    except Exception as e:
        st.error(f"Erro ao carregar dados dos grupos: {e}")
        st.stop()

@st.cache_data(ttl="12h", show_time=True)
def carregar_produtos() -> pd.DataFrame:
    try:
        return buscar_dados_produtos()
    except Exception as e:
        st.error(f"Erro ao carregar dados dos produtos: {e}")
        st.stop()

@st.cache_data(ttl="12h", show_time=True)
def carregar_rent_mensal_planos() -> pd.DataFrame:
    try:
        return buscar_rent_mensal_planos()
    except Exception as e:
        st.error(f"Erro ao carregar dados de rentabilidade mensal: {e}")
        st.stop()


df_ipca = carregar_ipca()
df_grupos = carregar_grupos()
df_planos = carregar_planos()
df_produtos = carregar_produtos()
df_rent_mensal_planos = carregar_rent_mensal_planos()
df_ipca['PLANO'] = 'PGA'
df_ipca['DATA'] = pd.to_datetime(df_ipca['DATA']).dt.to_period('M').dt.to_timestamp()
df_ipca = df_ipca.set_index(['PLANO', 'DATA'])
df_rent_mensal_planos['DATA'] = pd.to_datetime(df_rent_mensal_planos['DATA']).dt.to_period('M').dt.to_timestamp()
df_rent_mensal_planos = df_rent_mensal_planos.set_index(['PLANO', 'DATA'])
# separa o update do set_index

df_rent_mensal_planos.update(df_ipca)
df_rent_mensal_planos = df_rent_mensal_planos.reset_index()



RAIZ_PROJETO = Path(__file__).resolve().parent.parent.parent
# 2. Constrói o caminho correto até o CSV
caminho_csv = RAIZ_PROJETO / "src" / "utils" / "rentabilidade_projetada.csv"
# 3. Lê o arquivo sem erros de caminho relativo
df_rent_projetada = pd.read_csv(caminho_csv)



if 'plano-selecionado' not in st.session_state:
    st.session_state['plano-selecionado'] = '[CERES TOTAL]'

if 'data-selecionada' not in st.session_state:
    st.session_state['data-selecionada'] = df_planos['DATA_COTACAO'].max()


#__________________________CABEÇALHO
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
            Rentabilidade - 
            <span style='color:#A8EC7D; font-family:"Source Serif 4",serif; font-style:italic; font-weight:600;'>
                Planos
            </span>
        </p>
    """, unsafe_allow_html=True)

st.space()
# ________________Seleção do plano e data
col1, _, col2 = st.columns([1, 0.5, 0.5])
with col1:
    selected_plano = st.selectbox(
        "Selecione o plano:",
        options=df_planos['TESOURARIA'].unique(),
        index=df_planos['TESOURARIA'].unique().tolist().index(st.session_state['plano-selecionado']),
        format_func=nome_plano, 
    )

with col2:

    primeira_data = df_planos["DATA_COTACAO"].min().date()
    ultima_data = df_planos["DATA_COTACAO"].max().date()

    selected_data = st.date_input(
    "Selecione a data de cotação:",
    value=st.session_state['data-selecionada'],
    format="DD/MM/YYYY",
    help=f"Datas disponíveis: {primeira_data.strftime('%d/%m/%Y')} a {ultima_data.strftime('%d/%m/%Y')}.",
    min_value=df_planos['DATA_COTACAO'].min(),
    max_value=df_planos['DATA_COTACAO'].max()
)

primeiro_dia_util_ano = primeiro_dia_util(selected_data.year)
inicio_mes = pd.Timestamp(selected_data).replace(day=1)

if pd.to_datetime(selected_data) not in df_planos['DATA_COTACAO'].values:
    st.warning("Data selecionada não é um dia útil ou não possui dados. Por favor, selecione uma data válida.")
    st.stop()

df_planos_filtrado_dp = df_planos[
    (df_planos['TESOURARIA'] == selected_plano) &
    (df_planos['DATA_COTACAO'] == pd.to_datetime(selected_data))
]

df_planos['DATA_COTACAO'] = pd.to_datetime(df_planos['DATA_COTACAO'])

primeiro_dia_util_ano = pd.to_datetime(primeiro_dia_util_ano)
selected_data = pd.to_datetime(selected_data)

df_planos_filtrado_ytd = df_planos[
    (df_planos['TESOURARIA'] == selected_plano) &
    df_planos['DATA_COTACAO'].between(primeiro_dia_util_ano, selected_data)
]


st.space()



#___________delta pl ytd
pl_ytd = df_planos[
    (df_planos['TESOURARIA'] == selected_plano) &
    (df_planos['DATA_COTACAO'] == pd.to_datetime(primeiro_dia_util_ano))
]


delta_pl = round(((df_planos_filtrado_dp['POSICAO_DF'].values[0]/pl_ytd['POSICAO_DF'].values[0])-1)*100, 2)
info_pl = 'A variação indica o delta percentual do Patrimônio Líquido entre a data inicial e a data final selecionadas'

#___________________Cards
plano_selecionado = selected_plano

for antigo, novo in _NOMES_PLANOS.items():
    plano_selecionado = plano_selecionado.replace(antigo, novo)
    

df_rent_projetada_filtro =(df_rent_projetada[
    (df_rent_projetada['SEGMENTO'] == 'Consolidado') 
    & (df_rent_projetada['PLANO'] == plano_selecionado)
    & (df_rent_projetada['ano'] == int(pd.to_datetime(selected_data).year))
    ])
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
        card_geral('PL', formatar_numero(df_planos_filtrado_dp['POSICAO_DF'].iloc[0], prefixo="R$ "), 
                   formatar_percentual_br(delta_pl),
                   valor_extenso=fmt_br(df_planos_filtrado_dp['POSICAO_DF'].iloc[0]), 
                   help=info_pl)
with col2:
    card_geral('Mês', formatar_percentual_br(df_planos_filtrado_dp['MTD'].iloc[0]), 
               formatar_percentual_br(df_planos_filtrado_dp['DIDF'].iloc[0]),
               
               help='A variação representa o delta da rentabilidade entre a data de posição e o dia útil anterior')
with col3:
    

    # if selected_plano == '[CERES TOTAL]':
    #     card_geral('Ano', formatar_percentual_br(df_planos_filtrado_dp['YTD'].iloc[0]))
    # else:
    card_rentabilidade_meta(
    titulo="Ano",
    rentabilidade_atual=formatar_percentual_br(df_planos_filtrado_dp['YTD'].iloc[0]),
    rentabilidade_alvo=df_rent_projetada_filtro['rentabilidade'].values[0],

    help="A rentabilidade projeteda reflete a expectativa de rentabilidade para o ano, definido na Política de Investimentos do plano.")
    


with col4:
     card_geral('12 meses', formatar_percentual_br(df_planos_filtrado_dp['MESES12'].iloc[0]))

with col5:
    if df_planos_filtrado_dp['REFERENCIA_BENCHMARK'].iloc[0] == 'CDI':
        card_geral('Benchmark', 'INPC + 4,78%', help='O benchmark é definido com base na média dos planos de benefício')
    else:
        card_geral('Benchmark', df_planos_filtrado_dp['REFERENCIA_BENCHMARK'].iloc[0])

#____________________GRAFICO DE LINHAS RENT

with st.container(border=True):

    # Cabeçalho: título à esquerda e controle à direita
    col_titulo, col_espaco, col_controle = st.columns(
        [2,9, .6],
        vertical_alignment="top"
    )

    with col_titulo:
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
                    Rentabilidade do Plano
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_espaco:
        st.empty()

    with col_controle:
        selecao_periodo = st.segmented_control(
            "Período:",
            options=["MTD", "YTD"],
            selection_mode="single",
            default="YTD",
            key="rent",
            required=True,
            label_visibility="collapsed",
        )

    # Seleção do período
    if selecao_periodo == "MTD":
        df_plot = df_planos_filtrado_ytd[
            (df_planos_filtrado_ytd["DATA_COTACAO"] >= inicio_mes) &
            (df_planos_filtrado_ytd["DATA_COTACAO"] <= selected_data)
        ].copy()
        col_y = "MTD"
    else:
        df_plot = df_planos_filtrado_ytd.copy()
        col_y = "YTD"


    # Garante datetime
    df_plot['DATA_COTACAO'] = pd.to_datetime(df_plot['DATA_COTACAO'])

    # Ordena por data
    df_plot = df_plot.sort_values('DATA_COTACAO').copy()

    # Remove valores vazios
    df_plot = df_plot.dropna(subset=[col_y])

    if not df_plot.empty:

        # Meses em português
        meses_pt = {
            1: 'Jan',
            2: 'Fev',
            3: 'Mar',
            4: 'Abr',
            5: 'Mai',
            6: 'Jun',
            7: 'Jul',
            8: 'Ago',
            9: 'Set',
            10: 'Out',
            11: 'Nov',
            12: 'Dez'
        }

        # Cria referência mensal
        df_plot['MES'] = df_plot['DATA_COTACAO'].dt.to_period('M')

        # ----------------------------
        # RÓTULOS DOS PONTOS
        # ----------------------------
        if selecao_periodo == 'MTD':
            # No MTD, mostra rótulo em todos os pontos
            df_plot['ROTULO'] = df_plot[col_y].apply(lambda x: f"{x:.2f}%".replace(".", ",")
)

        else:
            # No YTD, mostra:
            # primeiro ponto, início de cada mês e último ponto
            indices_rotulo = set()

            indices_rotulo.add(df_plot.index[0])

            indices_inicio_mes = df_plot.groupby('MES').head(1).index
            indices_rotulo.update(indices_inicio_mes)

            indices_rotulo.add(df_plot.index[-1])

            df_plot['ROTULO'] = [
                f"{v:.2f}%".replace(".", ",") if idx in indices_rotulo else ""
                for idx, v in zip(df_plot.index, df_plot[col_y])
            ]

        # ----------------------------
        # DATAS DO EIXO X
        # ----------------------------
        if selecao_periodo == 'YTD':
            # No YTD, mostra apenas o mês
            df_ticks = (
                df_plot
                .groupby('MES', as_index=False)
                .first()
            )

            tickvals_x = df_ticks['DATA_COTACAO']
            ticktext_x = df_ticks['DATA_COTACAO'].dt.month.map(meses_pt)

        else:
            # No MTD, mostra dia/mês
            tickvals_x = df_plot['DATA_COTACAO']
            ticktext_x = df_plot['DATA_COTACAO'].dt.strftime('%d/%m')

        # ----------------------------
        # RANGE DO EIXO Y
        # ----------------------------
        y_min = df_plot[col_y].min()
        y_max = df_plot[col_y].max()

        padding_y = (y_max - y_min) * 0.2

        if padding_y == 0:
            padding_y = abs(y_max) * 0.2 if y_max != 0 else 1

        # ----------------------------
        # RANGE DO EIXO X
        # ----------------------------
        x_min = df_plot['DATA_COTACAO'].min()
        x_max = df_plot['DATA_COTACAO'].max()

        if x_min == x_max:
            padding_x = pd.Timedelta(days=1)
        else:
            padding_x = (x_max - x_min) * 0.02

        fig = go.Figure()

        # ----------------------------------------------------
        # Sombra / blur em gradiente abaixo da linha
        # Mais intenso perto da linha
        # ----------------------------------------------------
        base_y = y_min - padding_y * 0.1

        gradiente_blur = [
        (0.07, 'rgba(168, 236, 125, 0.015)'),
        (0.14, 'rgba(168, 236, 125, 0.025)'),
        (0.20, 'rgba(168, 236, 125, 0.040)'),
        (0.26, 'rgba(168, 236, 125, 0.060)'),
        (0.32, 'rgba(168, 236, 125, 0.080)'),
        (0.38, 'rgba(168, 236, 125, 0.100)'),
        (0.44, 'rgba(168, 236, 125, 0.120)'),
        (0.50, 'rgba(168, 236, 125, 0.140)'),
        (0.56, 'rgba(168, 236, 125, 0.160)'),
        (0.62, 'rgba(168, 236, 125, 0.180)'),
        (0.68, 'rgba(168, 236, 125, 0.200)'),
        (0.74, 'rgba(168, 236, 125, 0.240)'),
        (0.80, 'rgba(168, 236, 125, 0.260)'),
        (0.84, 'rgba(168, 236, 125, 0.280)'),
        (0.88, 'rgba(168, 236, 125, 0.300)'),
        (0.91, 'rgba(168, 236, 125, 0.320)'),
        (0.94, 'rgba(168, 236, 125, 0.340)'),
        (0.96, 'rgba(168, 236, 125, 0.360)'),
        (0.98, 'rgba(168, 236, 125, 0.380)'),
        (1.00, 'rgba(168, 236, 125, 0.400)'),
    ]
        for fator, cor in gradiente_blur:
            y_grad = base_y + (df_plot[col_y] - base_y) * fator

            fig.add_trace(go.Scatter(
                x=df_plot['DATA_COTACAO'],
                y=y_grad,
                mode='lines',
                fill='tonexty',
                fillcolor=cor,
                line=dict(
                    width=0,
                    color='rgba(0,0,0,0)',
                    shape='spline',
                    smoothing=1.3
                ),
                hoverinfo='skip',
                showlegend=False,
                cliponaxis=False,
            ))

        # ----------------------------------------------------
        # Linha principal
        # ----------------------------------------------------
        fig.add_trace(go.Scatter(
            x=df_plot['DATA_COTACAO'],
            y=df_plot[col_y],
            mode='lines',
            name=selecao_periodo,
            showlegend=False,
            fill=None,
            line=dict(
                color='#A8EC7D',
                width=2,
                shape='spline',
                smoothing=1.3
            ),
            cliponaxis=False,
        ))

        # ----------------------------------------------------
        # Rótulos como annotations
        # ----------------------------------------------------
        for _, row in df_plot[df_plot['ROTULO'] != ""].iterrows():
            fig.add_annotation(
                x=row['DATA_COTACAO'],
                y=row[col_y],
                text=row['ROTULO'],
                showarrow=False,
                yshift=8,
                xshift=0,
                font=dict(
                    family='Figtree',
                    size=14,
                    color='#0B2F13'
                ),
                bgcolor='rgba(255,255,255,0)',
                bordercolor='rgba(255,255,255,0)',
            )

        # ----------------------------------------------------
        # Layout
        # ----------------------------------------------------
        fig.update_layout(
            height=320,
            autosize=True,
            separators=',.',
            font=dict(
                family='Figtree',
                size=14,
                color='#333333'
            ),
            xaxis=dict(
                showline=False,
                showgrid=False,
                automargin=True,
                tickvals=tickvals_x,
                ticktext=ticktext_x,
                tickfont=dict(
                    family='Figtree',
                    size=13,
                    color='#333333'
                ),
                range=[
                    x_min - padding_x,
                    x_max + padding_x
                ],
            ),
            yaxis=dict(
                visible=False,
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                range=[
                    y_min - padding_y * 0.1,
                    y_max + padding_y
                ],
            ),
            hovermode='x unified',
            hoverlabel=dict(
                bgcolor='#FBFCEC',
                bordercolor='#0B2F13',
                font=dict(
                    family='Figtree',
                    size=12,
                    color='#0B2F13'
                ),
            ),
            margin=dict(
                r=0,
                t=0,
                b=0,
                l=0
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        # ----------------------------------------------------
        # Hover da linha principal
        # ----------------------------------------------------
        fig.update_traces(
            selector=dict(name=selecao_periodo),
            hovertemplate='<b>%{x|%d/%m/%Y}</b><br>Rentabilidade: %{y:.2f}%<extra></extra>'
        )

        st.plotly_chart(
            fig,
            config={
                'displayModeBar': False,
                'scrollZoom': False
            },
            width="stretch"
        )

#__________________________GRAFICO BARRAS RENTABILIDADE MENSAL

with st.container(border=True):

    # Cabeçalho: título à esquerda e controle no canto direito
    col_titulo, col_espaco, col_controle = st.columns(
        [2, 9, 1],
        vertical_alignment="top"
    )

    with col_titulo:
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
                    Rentabilidade Mensal
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_espaco:
        st.empty()

    with col_controle:
        opcao = ["6m", "12m", "18m", "24m"]

        selecao_periodo_mensal = st.segmented_control(
            "Período:",
            options=opcao,
            selection_mode="single",
            default="12m",
            required=True,
            key="rent_mensal",
            label_visibility="collapsed",
        )
    # Filtro do plano
    df_rent_mensal_planos_filtrado = df_rent_mensal_planos[
        df_rent_mensal_planos['PLANO'] == selected_plano.upper()
    ].copy()

    # Garante datetime
    df_rent_mensal_planos_filtrado['DATA'] = pd.to_datetime(
        df_rent_mensal_planos_filtrado['DATA']
    )

    # Filtro do período selecionado
    if selecao_periodo_mensal:
        meses = int(selecao_periodo_mensal.replace('m', ''))
        data_inicio_meses = selected_data - pd.DateOffset(months=meses)

        df_rent_mensal_planos_filtrado = df_rent_mensal_planos_filtrado[
            df_rent_mensal_planos_filtrado['DATA'] >= data_inicio_meses
        ].copy()

    # Ordena por data
    df_rent_mensal_planos_filtrado = (
        df_rent_mensal_planos_filtrado
        .sort_values('DATA')
        .copy()
    )

    
    
    if not df_rent_mensal_planos_filtrado.empty:

        # Meses em português
        meses_pt = {
            1: 'Jan',
            2: 'Fev',
            3: 'Mar',
            4: 'Abr',
            5: 'Mai',
            6: 'Jun',
            7: 'Jul',
            8: 'Ago',
            9: 'Set',
            10: 'Out',
            11: 'Nov',
            12: 'Dez'
        }

        # Eixo X hierárquico:
        # primeira linha: mês
        # segunda linha: ano
        df_rent_mensal_planos_filtrado['MES_LABEL'] = (
            df_rent_mensal_planos_filtrado['DATA'].dt.month.map(meses_pt)
        )

        df_rent_mensal_planos_filtrado['ANO'] = (
            df_rent_mensal_planos_filtrado['DATA'].dt.strftime('%Y')
        )

        # Rótulos das barras
        df_rent_mensal_planos_filtrado['ROTULO_BENCH'] = (
            df_rent_mensal_planos_filtrado['BENCH'].apply(lambda v: f"{v:.2f}%".replace(".", ","))
        )

        df_rent_mensal_planos_filtrado['ROTULO_RENTABILIDADE'] = (
            df_rent_mensal_planos_filtrado['RENTABILIDADE'].apply(lambda v: f"{v:.2f}%".replace(".", ","))
        )

        # Range Y com respiro para não cortar rótulos
        y_min = min(
            df_rent_mensal_planos_filtrado['BENCH'].min(),
            df_rent_mensal_planos_filtrado['RENTABILIDADE'].min()
        )

        y_max = max(
            df_rent_mensal_planos_filtrado['BENCH'].max(),
            df_rent_mensal_planos_filtrado['RENTABILIDADE'].max()
        )

        padding_y = (y_max - y_min) * 0.35

        if padding_y == 0:
            padding_y = abs(y_max) * 0.35 if y_max != 0 else 1

        fig = go.Figure()

        # Barra Benchmark
        fig.add_trace(
            go.Bar(
                x=[
                    df_rent_mensal_planos_filtrado['ANO'],
                    df_rent_mensal_planos_filtrado['MES_LABEL']
                ],
                y=df_rent_mensal_planos_filtrado['BENCH'],
                name='Benchmark',
                marker=dict(
                    color="#6B7A6E",
                    line=dict(
                        color='#6B7A6E',
                        width=1
                    )
                ),
                text=df_rent_mensal_planos_filtrado['ROTULO_BENCH'],
                textposition='outside',
                textfont=dict(
                    family='Figtree',
                    size=14,
                    color="#354238"
                ),
                cliponaxis=False,
                hovertemplate='Benchmark: %{y:.2f}%<extra></extra>',
            )
        )

        # Barra Rentabilidade
        fig.add_trace(
            go.Bar(
                x=[
                    df_rent_mensal_planos_filtrado['ANO'],
                    df_rent_mensal_planos_filtrado['MES_LABEL']
                ],
                y=df_rent_mensal_planos_filtrado['RENTABILIDADE'],
                name='Rentabilidade',
                marker=dict(
                    color='#A8EC7D',
                    line=dict(
                        color='#A8EC7D',
                        width=1
                    )
                ),
                text=df_rent_mensal_planos_filtrado['ROTULO_RENTABILIDADE'],
                textposition='outside',
                textfont=dict(
                    family='Figtree',
                    size=14,
                    color='#0B2F13'
                ),
                cliponaxis=False,
                hovertemplate='Rentabilidade: %{y:.2f}%<extra></extra>',
            )
        )

        fig.update_layout(
            height=340,
            autosize=True,
            barmode='group',
            bargap=0.28,
            bargroupgap=0.08,
            separators=',.',
            font=dict(
                family='Figtree',
                size=14,
                color='#333333'
            ),
            xaxis=dict(
                type='multicategory',
                showline=False,
                showgrid=False,
                automargin=True,
                tickfont=dict(
                    family='Figtree',
                    size=13,
                    color='#333333'
                ),
            ),
            yaxis=dict(
                visible=False,
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                range=[
                min(0, y_min - padding_y * 0.20),
                y_max + padding_y
            ],
            ),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='left',
                x=0,
                font=dict(
                    family='Figtree',
                    size=14,
                    color='#333333'
                ),
            ),
            hovermode='x unified',
            hoverlabel=dict(
                bgcolor='#FBFCEC',
                bordercolor='#0B2F13',
                font=dict(
                    family='Figtree',
                    size=14,
                    color='#0B2F13'
                ),
            ),
            margin=dict(
                r=0,
                t=0,
                b=40,
                l=5
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        # Barras arredondadas
        fig.update_traces(
            marker_cornerradius=8
        )

        st.plotly_chart(
            fig,
            config={
                "displayModeBar": False,
                "scrollZoom": False
            },
            width="stretch"
        )

    else:
        st.info("Não há dados disponíveis para o período selecionado.")


#________________________________ SEGMENTOS
st.space()
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
                   Segmentos de Investimento do Plano
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

posicao_segmentos = df_grupos[
    (df_grupos['TESOURARIA'] == selected_plano) &
    (df_grupos['DATA_COTACAO'] == pd.to_datetime(selected_data))
]

df_rent_projetada_filtro_segmetos =(df_rent_projetada[
            (df_rent_projetada['PLANO'] == plano_selecionado)
            & (df_rent_projetada['ano'] == int(pd.to_datetime(selected_data).year))
            ])


col1, col2, col3 = st.columns(3)

segmentos_cards = [
    "Renda Fixa",
    "Renda Variável",
    "Estruturado",
    "Operações com Participantes",
    "Imobiliário",
    "Exterior",
]

col1, col2, col3 = st.columns(3)
col4, col5, col6 = st.columns(3)

colunas_segmentos = {
    "Renda Fixa": col1,
    "Renda Variável": col2,
    "Estruturado": col3,
    "Operações com Participantes": col4,
    "Imobiliário": col5,
    "Exterior": col6,
}

total_posicao = posicao_segmentos["POSICAO_DF"].sum()

for segmento in segmentos_cards:

    if segmento not in posicao_segmentos["GRUPO"].values:
        continue

    coluna = colunas_segmentos[segmento]

    with coluna:
        linha_segmento = posicao_segmentos[
            posicao_segmentos["GRUPO"] == segmento
        ].iloc[0]

        posicao_pct = (
            linha_segmento["POSICAO_DF"] / total_posicao
        ) * 100

        cor_segmento = CORES_SEGMENTOS.get(segmento, "#016837")

        # if selected_plano == "[CERES TOTAL]":
        #     card_segmento_rentabilidade_sem_projetada(
        #         segmento=segmento,
        #         rentabilidade_atual=linha_segmento["YTD"],
        #         posicao=linha_segmento["POSICAO_DF"],
        #         posicao_pct=f"{posicao_pct:.2f}%",
        #         mtd=linha_segmento["MTD"],
        #         m12=linha_segmento["MESES12"],
        #         cor_segmento=cor_segmento,
        #     )

    # else:
        rentabilidade_alvo = df_rent_projetada_filtro_segmetos[
            df_rent_projetada_filtro_segmetos["SEGMENTO"] == segmento
        ]["rentabilidade"].values[0]

        card_segmento_rentabilidade(
            segmento=segmento,
            rentabilidade_atual=linha_segmento["YTD"],
            rentabilidade_alvo=rentabilidade_alvo,
            posicao=linha_segmento["POSICAO_DF"],
            pct_posicao=f"{posicao_pct:.2f}%",
            mtd=linha_segmento["MTD"],
            m12=linha_segmento["MESES12"],
            cor_segmento=cor_segmento,
        )
#___________________________RENT SEGMENTOS
with st.container(border=True):

    # Cabeçalho: título à esquerda e controle à direita
    col_titulo, col_espaco, col_controle = st.columns(
        [2, 9, .6],
        vertical_alignment="top"
    )

    with col_titulo:
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
                    Rentabilidade por Segmento
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_espaco:
        st.empty()

    with col_controle:
        selecao_periodo = st.segmented_control(
            "Período:",
            options=["MTD", "YTD"],
            selection_mode="single",
            default="YTD",
            key="rent_segmentos",
            required=True,
            label_visibility="collapsed",
        )
    # Base filtrada
    df_grupos_filtrado_ytd = df_grupos[
        (df_grupos["TESOURARIA"] == selected_plano) &
        df_grupos["DATA_COTACAO"].between(primeiro_dia_util_ano, selected_data)
    ].copy()

    # Seleção do período
    if selecao_periodo == "MTD":
        df_plot = df_grupos_filtrado_ytd[
            (df_grupos_filtrado_ytd["DATA_COTACAO"] >= inicio_mes) &
            (df_grupos_filtrado_ytd["DATA_COTACAO"] <= selected_data)
        ].copy()
        col_y = "MTD"
    else:
        df_plot = df_grupos_filtrado_ytd.copy()
        col_y = "YTD"

    df_plot["MTD"] = df_plot["MTD"] * 100
    df_plot["YTD"] = df_plot["YTD"] * 100

    # Garante datetime
    df_plot["DATA_COTACAO"] = pd.to_datetime(df_plot["DATA_COTACAO"])

    # Ordena por grupo e data
    df_plot = df_plot.sort_values(["GRUPO", "DATA_COTACAO"]).copy()

    # Remove valores vazios
    df_plot = df_plot.dropna(subset=[col_y, "GRUPO"])

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

        df_plot["MES"] = df_plot["DATA_COTACAO"].dt.to_period("M")

        # ----------------------------
        # DATAS DO EIXO X
        # ----------------------------
        if selecao_periodo == "YTD":
            df_ticks = (
                df_plot
                .sort_values("DATA_COTACAO")
                .groupby("MES", as_index=False)
                .first()
            )

            tickvals_x = df_ticks["DATA_COTACAO"]
            ticktext_x = df_ticks["DATA_COTACAO"].dt.month.map(meses_pt)

        else:
            df_ticks = (
                df_plot
                .sort_values("DATA_COTACAO")
                .drop_duplicates(subset=["DATA_COTACAO"])
            )

            tickvals_x = df_ticks["DATA_COTACAO"]
            ticktext_x = df_ticks["DATA_COTACAO"].dt.strftime("%d/%m")

        # ----------------------------
        # RANGE DO EIXO Y
        # ----------------------------
        y_min = df_plot[col_y].min()
        y_max = df_plot[col_y].max()

        padding_y = (y_max - y_min) * 0.2

        if padding_y == 0:
            padding_y = abs(y_max) * 0.2 if y_max != 0 else 1

        # ----------------------------
        # RANGE DO EIXO X
        # ----------------------------
        x_min = df_plot["DATA_COTACAO"].min()
        x_max = df_plot["DATA_COTACAO"].max()

        if x_min == x_max:
            padding_x = pd.Timedelta(days=1)
        else:
            padding_x = (x_max - x_min) * 0.02

        fig = go.Figure()

        # ----------------------------
        # LINHAS POR SEGMENTO
        # ----------------------------
        for grupo, df_g in df_plot.groupby("GRUPO"):

            df_g = df_g.sort_values("DATA_COTACAO").copy()
            cor_linha = CORES_SEGMENTOS.get(grupo, "#5a5a5a")

            fig.add_trace(go.Scatter(
                x=df_g["DATA_COTACAO"],
                y=df_g[col_y],
                mode="lines",
                name=grupo,
                line=dict(
                    color=cor_linha,
                    width=2,
                    shape="spline",
                    smoothing=1.3,
                ),
                cliponaxis=False,
                hovertemplate=(
                    f"<b>{grupo}</b><br>"
                    "Rentabilidade: %{y:.2f}%"
                    "<extra></extra>"
                )
            ))

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
                showline=False,
                showgrid=False,
                automargin=True,
                tickvals=tickvals_x,
                ticktext=ticktext_x,
                tickfont=dict(
                    family="Figtree",
                    size=13,
                    color="#333333",
                ),
                range=[
                    x_min - padding_x,
                    x_max + padding_x,
                ],
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
                r=0,
                t=38,
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
        )

    else:
        st.info("Não há dados disponíveis para o período selecionado.")
#___________________________________TABELA PRODUTOS

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
                   Produtos do Plano
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

df_produtos_filtrado = df_produtos[
    (df_produtos['TESOURARIA'] == selected_plano) &
    (df_produtos['DATA_COTACAO'] == pd.to_datetime(selected_data)).copy()
]

df_produtos_filtrado['%_POSICAO'] = (df_produtos_filtrado['POSICAO_DF'] / df_produtos_filtrado['POSICAO_DF'].sum()) * 100
df_produtos_filtrado = df_produtos_filtrado.sort_values('POSICAO_DF', ascending=False).copy()

segmentos_tabs = {
    "Geral": None,
    "Renda Fixa": "Renda Fixa",
    "Renda Variável": "Renda Variável",
    "Estruturado": "Estruturado",
    "Imobiliário": "Imobiliário",
    "Exterior": "Exterior",
    "Op. Participantes": "Operações com Participantes",
}

segmentos_existentes = set(df_produtos_filtrado["GRUPO"].dropna().unique())

tabs_ativas = {
    nome_tab: segmento_df
    for nome_tab, segmento_df in segmentos_tabs.items()
    if segmento_df is None or segmento_df in segmentos_existentes
}

st.dataframe(df_produtos_filtrado)

tabs = st.tabs(list(tabs_ativas.keys()))

for tab, (nome_tab, segmento_df) in zip(tabs, tabs_ativas.items()):
    with tab:
        if segmento_df is None:
            df_base = df_produtos_filtrado.copy()
        else:
            df_base = df_produtos_filtrado[
                df_produtos_filtrado["GRUPO"] == segmento_df
            ].copy()

        df_plot_produtos = (
            df_base[["PRODUTO", "GRUPO", "POSICAO_DF", "%_POSICAO"]]
            .rename(
                columns={
                    "PRODUTO": "Produtos",
                    "GRUPO": "Segmento",
                    "POSICAO_DF": "Posição (R$)",
                    "%_POSICAO": "% Posição",
                }
            )
        )

        df_plot_produtos["Produtos"] = df_plot_produtos["Produtos"].apply(de_para_produto)
        df_plot_produtos["% Posição"] = df_plot_produtos["% Posição"].apply(formatar_percentual_br)

        renderizar_tabela_estilizada(df_plot_produtos, rolagem=True, altura_max='300px', ordenacao=True)
        

#____________________________PL POR PLANO
df_planos_pl = df_planos[(df_planos['DATA_COTACAO'] == pd.to_datetime(selected_data))]
df_planos_pl = df_planos_pl[df_planos_pl['TESOURARIA'] != '[CERES TOTAL]'].copy()

total_pl = df_planos_pl["POSICAO_DF"].sum()



df_planos_pl['TESOURARIA'] = df_planos_pl['TESOURARIA'].replace(_NOMES_PLANOS)


if total_pl > 0:
    df_planos_pl["PART_PL"] = df_planos_pl["POSICAO_DF"] / total_pl * 100
else:
    df_planos_pl["PART_PL"] = 0

with st.columns(1)[0].container(border=True):
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
                    % PL por Plano
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    df_grafico = df_planos_pl[
        (df_planos_pl["TESOURARIA"] != "[CERES TOTAL]") &
        (df_planos_pl["POSICAO_DF"] > 0)
    ].copy()

    df_grafico = df_grafico.sort_values("POSICAO_DF", ascending=False)

    if not df_grafico.empty:

        df_grafico["VALOR_BARRA"] = df_grafico["POSICAO_DF"].apply(
            lambda v: f"{v:,.2f}".replace(".", "_").replace(",", ".").replace("_", ",")
        )

        df_grafico["PCT_BARRA"] = df_grafico["PART_PL"].apply(
            lambda v: f"{v:.2f}%".replace(".", ",")
        )

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=df_grafico["TESOURARIA"],
            y=df_grafico["POSICAO_DF"],
            text=df_grafico["PCT_BARRA"],
            textposition="outside",
            customdata=df_grafico[["VALOR_BARRA", "PCT_BARRA"]],
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
        ))

        max_exp = df_grafico["POSICAO_DF"].max()

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
            hovermode="x unified",
            hoverlabel=dict(
                bgcolor="#FBFCEC",
                bordercolor="#0B2F13",
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

        fig.update_traces(
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Valor: R$ %{customdata[0]}<br>"
                "Participação: %{customdata[1]}"
                "<extra></extra>"
            )
        )

        st.plotly_chart(
            fig,
            config={"displayModeBar": False},
            width="stretch"
        )

    else:
        st.info("Não há dados disponíveis para exibir.")