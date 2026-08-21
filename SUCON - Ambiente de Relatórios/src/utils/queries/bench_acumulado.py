import pandas as pd
from utils.db_sqlserver import get_connection
from utils.diagnostico import registrar_consulta
import streamlit as st

@st.cache_data(ttl="24h")
@registrar_consulta("bench_acumulado")
def buscar_dados_bench_acumulado() -> pd.DataFrame:
    query = """
        
            select 
            DS_PLANO_MITRA AS TESOURARIA,
            CO_EXERCICIO AS ANO,
            NR_MES,
            PERC_ANO AS YTD,
            PERC_MES AS MTD
            FROM [BI_CERES].[dbo].[VW_META_ATUARIAL]
            order by co_exercicio, nr_mes desc

    """
    with get_connection().connect() as conn:
        df=  pd.read_sql(query, conn)

    df.columns = df.columns.str.upper()
    return df