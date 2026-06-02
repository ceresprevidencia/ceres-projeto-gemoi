import streamlit as st
import pandas as pd
from utils.queries.ipca import buscar_dados as buscar_ipca
from utils.queries.rent_mensal_planos import buscar_dados as buscar_rent_mensal_planos
from utils.queries.rent_grupos import buscar_dados as buscar_grupos
from utils.queries.rent_planos import buscar_dados as buscar_planos
from utils.queries.rent_produtos import buscar_dados as buscar_dados_produtos
import plotly.graph_objects as go
from utils.helpers import primeiro_dia_util


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

# Botão para atualizar todos os dados
if st.button("Atualizar dados", on_click=limpar_cache):
    pass


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

if 'plano-selecionado' not in st.session_state:
    st.session_state['plano-selecionado'] = '[CERES TOTAL]'

if 'data-selecionada' not in st.session_state:
    st.session_state['data-selecionada'] = df_planos['DATA_COTACAO'].max()

selected_plano = st.selectbox(
    "Selecione o plano:",
    options=df_planos['TESOURARIA'].unique(),
    index=df_planos['TESOURARIA'].unique().tolist().index(st.session_state['plano-selecionado'])
)


selected_data = st.date_input(
    "Selecione a data de cotação:",
    value=st.session_state['data-selecionada'],
    min_value=df_planos['DATA_COTACAO'].min(),
    max_value=df_planos['DATA_COTACAO'].max()
)


primeiro_dia_util_ano = primeiro_dia_util(selected_data.year)

st.write(primeiro_dia_util_ano)
pl_inicio = df_planos[
    (df_planos['TESOURARIA'] == selected_plano) &
    (df_planos['DATA_COTACAO'] == pd.to_datetime(primeiro_dia_util_ano))
]
st.dataframe(pl_inicio)

df_planos_filtrado = df_planos[
    (df_planos['TESOURARIA'] == selected_plano) &
    (df_planos['DATA_COTACAO'] == pd.to_datetime(selected_data))
]

delta_pl = round(((df_planos_filtrado['POSICAO_DF'].values[0]/pl_inicio['POSICAO_DF'].values[0])-1)*100, 2)

st.write(f"Rentabilidade acumulada no ano: {delta_pl:.2f}%")
st.metric(label='PL', value=df_planos_filtrado['POSICAO_DF'], delta=f' {delta_pl:.2f}%')
st.dataframe(df_planos_filtrado)








st.write("df_planos")
st.dataframe(df_planos)

st.write("df_rent_mensal_planos")
st.dataframe(df_rent_mensal_planos)

st.write("df_grupos")
st.dataframe(df_grupos)

st.dataframe(df_produtos)



