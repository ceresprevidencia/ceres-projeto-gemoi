import pandas as pd
from data.db_oracle import get_connection
import streamlit as st

def buscar_produtos() -> pd.DataFrame:
    query = """

SELECT 
    RME.COD_REL_APURACAO_FORM, 
    RAF.DATA_COTACAO,
    RME.TESOURARIA,
    RME.GRUPO,
    RME.CARTEIRA,
    RME.PRODUTO,
    RME.POSICAO_DF

FROM REL_MULTI_ESTRATEGIA RME
INNER JOIN REL_APURACAO_FORMS RAF ON
    RME.COD_REL_APURACAO_FORM = RAF.COD_REL_APURACAO_FORM
INNER JOIN REL_APURACAO RA ON
    RAF.COD_REL_APURACAO = RA.CODIGO
WHERE RME.NIVEL_AGREGACAO = 'Sintético Nível 4' 
AND RA.NOME LIKE '[RESULTADO] FUNDAÇÃO CERES DIARIO OFICIAL#%'
AND RAF.DATA_COTACAO >= '23/07/26'


            

    """
    with get_connection().connect() as conn:
        df=  pd.read_sql(query, conn)

    df.columns = df.columns.str.upper()
    return df