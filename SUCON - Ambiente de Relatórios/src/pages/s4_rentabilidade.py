import streamlit as st
import pandas as pd
from utils.queries.ipca import buscar_dados as buscar_ipca
from utils.queries.rent_mensal_planos import buscar_dados as buscar_rent_mensal_planos
from utils.queries.rent_grupos import buscar_dados as buscar_grupos
from utils.queries.rent_planos import buscar_dados as buscar_planos
from utils.queries.rent_produtos import buscar_dados as buscar_dados_produtos
import plotly.graph_objects as go


# Carregar dados c
#@st.cache_data(ttl="1h", show_time=True)
#def carregar_ipca() -> pd.DataFrame:
#    try:
#        return buscar_ipca()
#    except Exception as e:
#        st.error(f"Erro ao carregar dados do IPCA: {e}")
#        st.stop()

@st.cache_data(ttl="1h", show_time=True)
def carregar_planos() -> pd.DataFrame:
    try:
        return buscar_planos()
    except Exception as e:
        st.error(f"Erro ao carregar dados dos planos: {e}")
        st.stop()

@st.cache_data(ttl="1h", show_time=True)
def carregar_grupos() -> pd.DataFrame:
    try:
        return buscar_grupos()
    except Exception as e:
        st.error(f"Erro ao carregar dados dos grupos: {e}")
        st.stop()

@st.cache_data(ttl="1h", show_time=True)
def carregar_produtos() -> pd.DataFrame:
    try:
        return buscar_dados_produtos()
    except Exception as e:
        st.error(f"Erro ao carregar dados dos produtos: {e}")
        st.stop()

@st.cache_data(ttl="1h", show_time=True)
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


#df_ipca = carregar_ipca()
df_grupos = carregar_grupos()
df_planos = carregar_planos()
df_produtos = carregar_produtos()
df_rent_mensal_planos = carregar_rent_mensal_planos()


#df_ipca['PLANO'] = 'PGA'
#df_ipca['DATA'] = pd.to_datetime(df_ipca['DATA']).dt.to_period('M').dt.to_timestamp()
#df_ipca = df_ipca.set_index(['PLANO', 'DATA'])

#df_rent_mensal_planos['DATA'] = pd.to_datetime(df_rent_mensal_planos['DATA']).dt.to_period('M').dt.to_timestamp()
#               df_rent_mensal_planos = df_rent_mensal_planos.set_index(['PLANO', 'DATA'])

# separa o update do set_index
#df_rent_mensal_planos.update(df_ipca)

df_rent_mensal_planos = df_rent_mensal_planos.reset_index()
#st.dataframe(df_ipca)
st.dataframe(df_rent_mensal_planos)

st.dataframe(df_planos)

st.dataframe(df_grupos)

st.dataframe(df_produtos)



