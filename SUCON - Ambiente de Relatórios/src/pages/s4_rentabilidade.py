import streamlit as st
import pandas as pd
from utils.queries.ipca import buscar_dados as buscar_ipca
from utils.queries.rent_mensal_planos import buscar_dados as buscar_rent_mensal_planos
from utils.queries.rent_grupos import buscar_dados as buscar_grupos
from utils.queries.rent_planos import buscar_dados as buscar_planos
from utils.queries.rent_produtos import buscar_dados as buscar_dados_produtos
import plotly.graph_objects as go
from utils.helpers import primeiro_dia_util, nome_plano, fmt_br, card_geral, formatar_numero, formatar_percentual_br, card_rentabilidade_meta
from pathlib import Path

# Carregar dados c
@st.cache_data(ttl="1h", show_time=True)
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

def limpar_cache():
    #carregar_ipca.clear()
    carregar_planos.clear()
    carregar_grupos.clear()
    carregar_produtos.clear()
    carregar_rent_mensal_planos.clear()


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
info_pl = 'A variação percentual do PL entre o primeiro dia útil do ano e a data selecionada.'

#___________________Cards
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
        card_geral('PL', formatar_numero(df_planos_filtrado_dp['POSICAO_DF'].iloc[0], prefixo="R$ "), formatar_percentual_br(delta_pl), help=info_pl)
with col2:
    card_geral('Mês', formatar_percentual_br(df_planos_filtrado_dp['MTD'].iloc[0]), formatar_percentual_br(df_planos_filtrado_dp['DIDF'].iloc[0]), help='Rentabilidade do dia')
with col3:
    
    card_rentabilidade_meta(
    titulo="Ano",
    rentabilidade_atual=formatar_percentual_br(df_planos_filtrado_dp['YTD'].iloc[0]),
    rentabilidade_alvo="10,0%",
    tipo="barra",
    help="Compara a rentabilidade acumulada atual com a rentabilidade alvo do plano."
)




st.dataframe(df_rent_projetada)

with col4:
     card_geral('12 meses', formatar_percentual_br(df_planos_filtrado_dp['MESES12'].iloc[0]))

with col5:
    if df_planos_filtrado_dp['REFERENCIA_BENCHMARK'].iloc[0] == 'CDI':
        card_geral('Benchmark', '-')
    else:
        card_geral('Benchmark', df_planos_filtrado_dp['REFERENCIA_BENCHMARK'].iloc[0])

#____________________GRAFICO DE LINHAS RENT

with st.container(border=True):

    # Cabeçalho: título à esquerda e controle no canto direito
    col_titulo, col_controle = st.columns([2, 3])

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

    with col_controle:
        col_spacer, _, col_select = st.columns([8, 2, 2])

        with col_spacer:
            st.empty()

        with col_select:
            selecao_periodo = st.segmented_control(
                "Período:",
                options=['MTD', 'YTD'],
                selection_mode="single",
                default='YTD',
                key='rent',
                required=True,
                label_visibility="collapsed",
            )

    # Seleção do período
    if selecao_periodo == 'MTD':
        df_plot = df_planos_filtrado_ytd[
            (df_planos_filtrado_ytd['DATA_COTACAO'] >= inicio_mes) &
            (df_planos_filtrado_ytd['DATA_COTACAO'] <= selected_data)
        ].copy()
        col_y = 'MTD'
    else:
        df_plot = df_planos_filtrado_ytd.copy()
        col_y = 'YTD'

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
            df_plot['ROTULO'] = df_plot[col_y].apply(lambda v: f"{v:.2f}%")

        else:
            # No YTD, mostra:
            # primeiro ponto, início de cada mês e último ponto
            indices_rotulo = set()

            indices_rotulo.add(df_plot.index[0])

            indices_inicio_mes = df_plot.groupby('MES').head(1).index
            indices_rotulo.update(indices_inicio_mes)

            indices_rotulo.add(df_plot.index[-1])

            df_plot['ROTULO'] = [
                f"{v:.2f}%" if idx in indices_rotulo else ""
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

        # Linha principal
        fig.add_trace(go.Scatter(
            x=df_plot['DATA_COTACAO'],
            y=df_plot[col_y],
            mode='lines',
            name=selecao_periodo,
            fill='tozeroy',
            fillcolor='rgba(11, 47, 19, 0.08)',
            line=dict(
                color='#0B2F13',
                width=2,
                shape='spline',
                smoothing=1.3
            ),
            cliponaxis=False,
        ))

        # Rótulos como annotations
        for _, row in df_plot[df_plot['ROTULO'] != ""].iterrows():
            fig.add_annotation(
                x=row['DATA_COTACAO'],
                y=row[col_y],
                text=row['ROTULO'],
                showarrow=False,
                yshift=20,
                xshift=0,
                font=dict(
                    family='Figtree',
                    size=14,
                    color='#0B2F13'
                ),
                bgcolor='rgba(255,255,255,0)',
                bordercolor='rgba(255,255,255,0)',
            )

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
                    size=12,
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

        fig.update_traces(
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

    else:
        st.info("Não há dados disponíveis para o período selecionado.")

#__________________________GRAFICO BARRAS RENTABILIDADE MENSAL

with st.container(border=True):

    # Cabeçalho: título à esquerda e controle no canto direito
    col_titulo, col_controle = st.columns([2, 3])

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

    with col_controle:
        col_spacer, col_select = st.columns([7, 3])

        with col_spacer:
            st.empty()

        with col_select:
            opcao = ['6m', '12m', '18m', '24m']

            selecao_periodo_mensal = st.segmented_control(
                "Período:",
                options=opcao,
                selection_mode="single",
                default='12m',
                required=True,
                key='rent_mensal',
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

    # Remove valores vazios
    df_rent_mensal_planos_filtrado = df_rent_mensal_planos_filtrado.dropna(
        subset=['BENCH', 'RENTABILIDADE']
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
            df_rent_mensal_planos_filtrado['BENCH'].apply(lambda v: f"{v:.2f}%")
        )

        df_rent_mensal_planos_filtrado['ROTULO_RENTABILIDADE'] = (
            df_rent_mensal_planos_filtrado['RENTABILIDADE'].apply(lambda v: f"{v:.2f}%")
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
                    color='#0B2F13',
                    line=dict(
                        color='#0B2F13',
                        width=1
                    )
                ),
                text=df_rent_mensal_planos_filtrado['ROTULO_BENCH'],
                textposition='outside',
                textfont=dict(
                    family='Figtree',
                    size=14,
                    color='#0B2F13'
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
                    size=12,
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
                    size=12,
                    color='#333333'
                ),
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


#__________________________GRAFICO BARRAS DISTRIBUIÇÃO PL





#__________________________ROSCA SEGMENTOS

posicao_segmentos = df_grupos[
    (df_grupos['TESOURARIA'] == selected_plano) &
    (df_grupos['DATA_COTACAO'] == pd.to_datetime(selected_data))
]


col1, col2, col3, col4, col5 = st.columns(5)
col1.metric(label='Renda fixa', value=posicao_segmentos[posicao_segmentos['GRUPO'] == 'Renda Fixa']['POSICAO_DF'].iloc[0],  delta=None)
col2.metric(label='Ações', value=posicao_segmentos[posicao_segmentos['GRUPO'] == 'Renda Variável']['POSICAO_DF'].iloc[0], delta=None)
col3.metric(label='Multimercado', value=posicao_segmentos[posicao_segmentos['GRUPO'] == 'Estruturado']['POSICAO_DF'].iloc[0], delta=None)
col4.metric(label='Internacional', value=posicao_segmentos[posicao_segmentos['GRUPO'] == 'Imobiliário']['POSICAO_DF'].iloc[0], delta=None)
col5.metric(label='Outros', value=posicao_segmentos[posicao_segmentos['GRUPO'] == 'Operações com Participantes']['POSICAO_DF'].iloc[0], delta=None)

#___________________________RENT SEGMENTOS

df_grupos_filtrado_ytd = df_grupos[
    (df_grupos['TESOURARIA'] == selected_plano) &
    df_grupos['DATA_COTACAO'].between(primeiro_dia_util_ano, selected_data)
]

opcao = ['MTD', 'YTD']

selecao_periodo = st.segmented_control(
    "Selecione o período para o gráfico:", 
    options=opcao,
    selection_mode="single",
    default='YTD',
    required=True,
    key='rent_segmentos')

if selecao_periodo == 'MTD':
    df_mtd = df_grupos_filtrado_ytd[
        (df_grupos_filtrado_ytd['DATA_COTACAO'] >= inicio_mes) &
        (df_grupos_filtrado_ytd['DATA_COTACAO'] <= selected_data)
    ]

    fig = go.Figure()
    for grupo, df_g in df_mtd.groupby('GRUPO'):
        fig.add_trace(
            go.Scatter(
                x=df_g['DATA_COTACAO'],
                y=df_g['MTD'],
                mode='lines',
                name=grupo
            )
    )
    st.plotly_chart(fig, config = {'scrollZoom': False})
else:
        fig = go.Figure()
        for grupo, df_g in df_grupos_filtrado_ytd.groupby('GRUPO'):
            fig.add_trace(
                go.Scatter(
                    x=df_g['DATA_COTACAO'],
                    y=df_g['YTD'],
                    mode='lines+markers',
                    name=grupo
                )
    )
        st.plotly_chart(fig, config = {'scrollZoom': False})





#___________________________________TABELA PRODUTOS

df_produtos_filtrado = df_produtos[
    (df_produtos['TESOURARIA'] == selected_plano) &
    (df_produtos['DATA_COTACAO'] == pd.to_datetime(selected_data)).copy()
]

df_produtos_filtrado['%_POSICAO'] = (df_produtos_filtrado['POSICAO_DF'] / df_produtos_filtrado['POSICAO_DF'].sum()) * 100

st.dataframe(df_produtos_filtrado[['PRODUTO', 'POSICAO_DF', '%_POSICAO']])

