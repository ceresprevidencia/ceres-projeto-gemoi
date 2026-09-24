import pandas as pd
import streamlit as st
from utils.db_oracle import get_connection


def buscar_dados_risco_mercado_ativos() -> pd.DataFrame:
    query="""
                SELECT
RME.TESOURARIA AS FUNDOS,      
ROUND(RME.POSICAO_DF, 2) AS POSICAO,   
ROUND(RME.RISCO_PAR, 2) AS VaR,  
ROUND(RME.RISCO_PAR / RME.POSICAO_DF,4)*100 AS "VaR/POSICAO_%",
RME.PORCENTAGEM_MARGINAL_PAR AS PARAMETRICO, 
ROUND(RME.RISCO_BVAR_PAR, 2) as BVaR,
ROUND(RME.RISCO_BVAR_PAR / RME.POSICAO_DF,4)*100 AS "BVaR/POSICAO_%",
RME.NOME_BVAR_PAR as NOMEBVaR

FROM REL_MULTI_ESTRATEGIA RME
INNER JOIN REL_APURACAO_FORMS RAF 
    ON RME.COD_REL_APURACAO_FORM = RAF.COD_REL_APURACAO_FORM
INNER JOIN REL_APURACAO RA 
    ON RAF.COD_REL_APURACAO = RA.CODIGO      
    
    
WHERE  RA.NOME = 'Relatório #125736 11/08/2026 11:57:50' 

AND RME.NIVEL_AGREGACAO = 'Sintético Nível 1'
                
                """
    with get_connection().connect() as conn:
        df=  pd.read_sql(query, conn)

    df.columns = df.columns.str.upper()
    return df