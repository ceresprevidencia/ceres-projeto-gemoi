import pandas as pd
from utils.db_sqlserver import get_connection
import streamlit as st

@st.cache_data(ttl="24h")
def buscar_dados_ipca() -> pd.DataFrame:
    query = """
        SELECT 
            DATA,
            VALOR_MES AS BENCH
        FROM [BI_CERES].[dbo].[API_INDICADORES]
        WHERE TIPO_INDICADOR = 'IPCA'
        ORDER BY DATA DESC
    """
    with get_connection().connect() as conn:
        df=  pd.read_sql(query, conn)

    df.columns = df.columns.str.upper()
    return df