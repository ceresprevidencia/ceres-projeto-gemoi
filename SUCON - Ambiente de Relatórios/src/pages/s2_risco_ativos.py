import streamlit as st
import pandas as pd
from utils.queries.risco_mercado_ativos import buscar_dados as buscar_dados_ativos
import plotly.graph_objects as go


# Carregar dados c
@st.cache_data(ttl="1h", show_time=True)
def carregar_dados() -> pd.DataFrame:
    return buscar_dados_ativos()


st.dataframe(carregar_dados())