import pandas as pd
from utils.db_sqlserver import get_connection
import streamlit as st

@st.cache_data(ttl="24h")
def buscar_dados_ticker() -> pd.DataFrame:
    query = """
       WITH ultima_competencia AS (
    SELECT TOP 1
        CO_EXERCICIO,
        NR_MES
    FROM [BI_CERES].[dbo].[VW_META_ATUARIAL]
    ORDER BY
        CO_EXERCICIO DESC,
        NR_MES DESC
),

meta_atuarial AS (
    SELECT 
        DS_PLANO_MITRA AS TESOURARIA,
        CO_EXERCICIO AS ANO,
        NR_MES AS MES,
        PERC_ANO,
        PERC_MES
    FROM [BI_CERES].[dbo].[VW_META_ATUARIAL]
),

rentabilidade AS (
    SELECT *
    FROM [BI_CERES].[dbo].[VW_RENTABILIDADE]
    WHERE DS_SEGMENTO_APLICACAO = 'PERFORMANCE CONSOLIDADA'
)

SELECT
    DS_PLANO_MITRA AS TESOURARIA,
    R.CO_EXERCICIO AS ANO,
    R.NR_MES AS MES,
    R.PERC_ANO AS YTD,
    M.PERC_ANO AS BENCH_YTD

FROM rentabilidade R

INNER JOIN ultima_competencia U
    ON R.CO_EXERCICIO = U.CO_EXERCICIO
   AND R.NR_MES = U.NR_MES

LEFT JOIN meta_atuarial M
    ON R.DS_PLANO_MITRA = M.TESOURARIA
   AND R.CO_EXERCICIO = M.ANO
   AND R.NR_MES = M.MES

ORDER BY
    R.CO_EXERCICIO DESC,
    R.NR_MES DESC,
    R.DS_PLANO_MITRA;

    """
    with get_connection().connect() as conn:
        df=  pd.read_sql(query, conn)

    df.columns = df.columns.str.upper()
    return df