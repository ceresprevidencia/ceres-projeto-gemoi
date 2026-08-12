import pandas as pd
from utils.db_sqlserver import get_connection
import streamlit as st

@st.cache_data(ttl="24h")
def buscar_dados() -> pd.DataFrame:
    query = """
       select 
        DS_PLANO_MITRA AS TESOURARIA,
        CO_EXERCICIO AS ANO,
        NR_MES AS MES,
        PERC_ANO,
        PERC_MES 
        FROM [BI_CERES].[dbo].[VW_META_ATUARIAL]
        order by co_exercicio, nr_mes desc

    """
    with get_connection().connect() as conn:
        df=  pd.read_sql(query, conn)

    df.columns = df.columns.str.upper()
    return df