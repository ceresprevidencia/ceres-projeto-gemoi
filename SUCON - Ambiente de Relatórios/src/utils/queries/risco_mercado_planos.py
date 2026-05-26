import pandas as pd
from utils.db_oracle import get_connection

def buscar_dados() -> pd.DataFrame:

    query=  """
                    WITH PLANOS AS (
                        SELECT
                            RME.TESOURARIA,
                            DATA_COTACAO,
                            ROUND(RME.POSICAO_DF, 2) AS POSICAO,
                            ROUND(RME.RISCO_PAR, 2) AS RISCO,
                            ROUND((RME.RISCO_PAR / NULLIF(RME.POSICAO_DF, 0)), 4)*100 AS "RISCO/POSICAO_%",
                            ROUND(RME.DIF_POSICAO_DF_STRESS_1, 2) AS VARIACAO_POSICAO_STRESS_1,
                            ROUND((RME.DIF_POSICAO_DF_STRESS_1/ NULLIF(RME.POSICAO_DF , 0)), 4)*100 AS "VARIACAO_POSICAO_STRESS_1/POSICAO_%",
                            ROUND(RME.DIF_POSICAO_DF_STRESS_2, 2) AS VARIACAO_POSICAO_STRESS_2,
                            ROUND((RME.DIF_POSICAO_DF_STRESS_2/ NULLIF(RME.POSICAO_DF , 0)), 4)*100 AS "VARIACAO_POSICAO_STRESS_2/POSICAO_%",
                            1.00 AS "LIMITE_INTERNO_%",
                            ROUND(((((RME.RISCO_PAR / NULLIF(RME.POSICAO_DF, 0))/ 0.01 ))), 4)*100 AS "STATUS_%",
                            DENSE_RANK() OVER(
                                PARTITION BY TRUNC(RAF.DATA_COTACAO), RME.TESOURARIA
                                ORDER BY RAF.COD_REL_APURACAO_FORM DESC
                            ) AS RN
                        FROM REL_MULTI_ESTRATEGIA RME
                        INNER JOIN REL_APURACAO_FORMS RAF 
                            ON RME.COD_REL_APURACAO_FORM = RAF.COD_REL_APURACAO_FORM
                        INNER JOIN REL_APURACAO RA 
                            ON RAF.COD_REL_APURACAO = RA.CODIGO
                        WHERE RME.NIVEL_AGREGACAO = 'Sintético Nível 1'
                        AND RA.NOME LIKE '[RISCO] FUNDAÇÃO CERES#%'
                    )
                    SELECT *
                    FROM PLANOS
                    ORDER BY DATA_COTACAO DESC, TESOURARIA, RN"""
    
    with get_connection().connect() as conn:
        df=  pd.read_sql(query, conn)

    df.columns = df.columns.str.upper()
    return df