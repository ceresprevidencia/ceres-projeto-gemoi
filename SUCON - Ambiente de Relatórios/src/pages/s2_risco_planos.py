import streamlit as st
import pandas as pd
from utils.queries.risco_mercado_planos import buscar_dados as buscar_dados_planos
from utils.queries.risco_mercado_segmentos import buscar_dados as buscar_dados_segmentos
import os
import plotly.graph_objects as go

# Carregar dados c

@st.cache_data(ttl="1h", show_time=True)
def carregar_dados() -> pd.DataFrame:
    return buscar_dados_planos()
    

@st.cache_data(ttl="1h", show_time=True)
def carregar_dados_segmentos() -> pd.DataFrame:
    return buscar_dados_segmentos()

def limpar_cache():
    carregar_dados.clear()
    carregar_dados_segmentos.clear()
 

df_planos = carregar_dados()
st.dataframe(df_planos, hide_index=True)  # Exibe as primeiras linhas para verificação
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


df_planos = df_planos[list(colunas_map.keys())].rename(columns=colunas_map)



df_segmentos = carregar_dados_segmentos()
df_segmentos.columns = df_segmentos.columns.str.upper()


# Título da página
st.title("Risco de Mercado - Planos")

# Espaçamento
st.space("medium")

col1, col2 = st.columns([3, 1])
with col1:
    with st.container(border=True):
        st.write("Metodologia "*60)
        
#_Espaçamento
st.space("medium")

# Seleção de data e validação
texto_data = ""
with col2:
    ultima_data_disponivel = df_planos['DATA_COTACAO'].max().date()
    primeira_data_disponivel = df_planos['DATA_COTACAO'].min().date()
    ajuda_data_input = f"As datas disponíveis estão entre {primeira_data_disponivel.strftime('%d/%m/%Y')} e {ultima_data_disponivel.strftime('%d/%m/%Y')}."
    data_posicao = st.date_input("Selecione a data posição", format="DD/MM/YYYY", value=ultima_data_disponivel, help=ajuda_data_input)

    if data_posicao not in df_planos['DATA_COTACAO'].dt.date.unique():
        datas_disponiveis = df_planos["DATA_COTACAO"].sort_values().unique()
        data_posicao_ts = pd.Timestamp(data_posicao)
        

        for idx, data in enumerate(datas_disponiveis[:-1]):
            data_ts = pd.Timestamp(data)
            proxima_ts = pd.Timestamp(datas_disponiveis[idx + 1])

            if data_posicao_ts < pd.Timestamp(primeira_data_disponivel):

                texto_data = (f"A data selecionada é anterior à primeira data disponível. Por favor, selecione uma data a partir de {primeira_data_disponivel.strftime('%d/%m/%Y')}")
                break
            
            elif data_posicao_ts > pd.Timestamp(ultima_data_disponivel):
                texto_data = (f"A data selecionada é posterior à última data disponível. Por favor, selecione uma data até {ultima_data_disponivel.strftime('%d/%m/%Y')}")
                break

            elif data_ts < data_posicao_ts < proxima_ts:
                texto_data = (
                    f'A data selecionada não possui dados disponíveis, considere selecionar a data mais próxima: '
                    f'{data_ts.strftime("%d/%m/%Y")} ou {proxima_ts.strftime("%d/%m/%Y")}.'
                )
                break


#--------------------GRÁFICO LINHAS VaR --------------------------
if texto_data != "":
    st.warning(texto_data)

df_planos_filtrado_data = df_planos[df_planos['DATA_COTACAO'] == pd.to_datetime(data_posicao)].copy()


# Iniciando session_state para armazenar os planos selecionados
if "plano_selecionado" not in st.session_state:
    st.session_state.plano_selecionado = []



if st.session_state.plano_selecionado:
    df_grafico_planos = df_planos[df_planos['Planos'].isin(st.session_state.plano_selecionado)]
else:
    df_grafico_planos = df_planos.iloc[0:0]  # DataFrame vazio para o gráfico quando nenhum plano é selecionado

container_grafico_linhas = st.container(border=True)
with container_grafico_linhas:
    fig = go.Figure()
    for plano in df_grafico_planos.Planos.unique():
        df_temp = df_grafico_planos[df_grafico_planos['Planos'] == plano]
        fig.add_trace(
            go.Scatter(
                x=df_temp['DATA_COTACAO'],
                y=df_temp['Value at Risk - VaR %'],
                name=plano,
                mode='lines'
            )
        )
    fig.update_layout(title='VaR % Mensal',
                    xaxis_title='Data',
                    yaxis_title='VaR (%)',
                    showlegend=True)
    st.plotly_chart(fig, config = {'scrollZoom': False}, key="grafico_risco_planos")



#-----------------------PLOT DATAFRAME----------------------
df_planos_filtrado_data.drop(columns=['DATA_COTACAO'], inplace=True)


planos = st.dataframe(df_planos_filtrado_data,
                        width='stretch',
                        hide_index=True,
                        on_select='rerun',
                        selection_mode='multi-row',
                        selection_default={"selection": {"rows": [0]}},
                        height=len(df_planos_filtrado_data)* 35 + 40  
                        )


planos_selecionados = planos.selection.rows
selecionados = df_planos_filtrado_data.iloc[planos_selecionados]['Planos'].tolist() if planos_selecionados else []
if selecionados != st.session_state.plano_selecionado:
    st.session_state.plano_selecionado = selecionados
    st.rerun()


#----------------- GRÁFICO COLUNAS SEGEMENTOS -----------------
df_segmentos_filtrado_data = df_segmentos[df_segmentos['DATA_COTACAO'] == pd.to_datetime(data_posicao)]
    
# Gráfico de barras para renda fixa+
fig_renda_fixa = go.Figure()
for plano in df_grafico_planos.Planos.unique():
    df_temp_segmentos = df_segmentos_filtrado_data[(df_segmentos_filtrado_data['TESOURARIA'] == plano) & (df_segmentos_filtrado_data['GRUPO'] == 'Renda Fixa')]
    fig_renda_fixa.add_trace(
        go.Bar(
            x=df_temp_segmentos['TESOURARIA'],
            y=df_temp_segmentos['RISCO/POSICAO_%'],
            name=plano,
            text=df_temp_segmentos['RISCO/POSICAO_%'],  # rótulos
            textposition='outside',
        )
    )
fig_renda_fixa.update_layout(
    title='Renda Fixa',
    showlegend=False,
    xaxis=dict(
        showticklabels=False,  # desativa rótulos do eixo x
        showgrid=False,        # desativa grades        
        zerolinecolor='black',
        title=None             # remove nome da categoria
    ),
    yaxis=dict(
        showgrid=False,
        showticklabels=True,
        tickvals=[0],
        zerolinecolor='black',

    )
)

# Gráfico de barras para renda variável
fig_renda_variavel = go.Figure()
for plano in df_grafico_planos.Planos.unique():
    df_temp_segmentos = df_segmentos_filtrado_data[(df_segmentos_filtrado_data['TESOURARIA'] == plano) & (df_segmentos_filtrado_data['GRUPO'] == 'Renda Variável')]
    fig_renda_variavel.add_trace(
        go.Bar(
            x=df_temp_segmentos['TESOURARIA'],
            y=df_temp_segmentos['RISCO/POSICAO_%'],
            name=plano,
            text=df_temp_segmentos['RISCO/POSICAO_%'],  
            textposition='outside',
        )
    )
fig_renda_variavel.update_layout(
    title='Renda Variável',
    showlegend=False,
    xaxis=dict(
        showticklabels=False,  
        showgrid=False,          
        zerolinecolor='black',
        title=None            
    ),
    yaxis=dict(
        showgrid=False,
        showticklabels=True,
        tickvals=[0],
        zerolinecolor='black',

    )
)
# Gráfico de barras para estruturados
fig_estruturado = go.Figure()
for plano in df_grafico_planos.Planos.unique():
    df_temp_segmentos = df_segmentos_filtrado_data[(df_segmentos_filtrado_data['TESOURARIA'] == plano) & (df_segmentos_filtrado_data['GRUPO'] == 'Estruturado')]
    fig_estruturado.add_trace(
        go.Bar(
            x=df_temp_segmentos['TESOURARIA'],
            y=df_temp_segmentos['RISCO/POSICAO_%'],
            text=df_temp_segmentos['RISCO/POSICAO_%'],  
            textposition='outside',
            name=plano
        )
    )

fig_estruturado.update_layout(
    title='Estruturado',
    showlegend=False,
    xaxis=dict(
        showticklabels=False,  
        showgrid=False,             
        zerolinecolor='black',
        title=None             
    ),
    yaxis=dict(
        showgrid=False,
        showticklabels=True,
        tickvals=[0],
        zerolinecolor='black',

    )
)

col1, col2, col3 = st.columns(3)
with col1.container(border=True):
    st.plotly_chart(fig_renda_fixa, key="grafico_segmento_renda_fixa")
with col2.container(border=True):
    st.plotly_chart(fig_renda_variavel, key="grafico_segmento_renda_variavel")
with col3.container(border=True):
    st.plotly_chart(fig_estruturado, key="grafico_segmento_estruturado")


#_Espaçamento
st.space("xxsmall")



#-----------------------CONCEITO----------------------
container_conceito = st.container(border=True)
with container_conceito:
    st.write("Conceito "*60)

