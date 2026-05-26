import pandas as pd
from utils.db_oracle import get_connection

def buscar_dados() -> pd.DataFrame:
    query="""
            /* RISCO MERCADO SEGMENTOS*/
            WITH RISCO_MERCADO_SEGMENTOS AS (
                SELECT
                    RME.TESOURARIA,
                    GRUPO,
                    DATA_COTACAO,
                    ROUND(RME.POSICAO_DF, 2) AS POSICAO,
                    ROUND(RME.RISCO_PAR, 2) AS RISCO,
                    ROUND((RME.RISCO_PAR / NULLIF(RME.POSICAO_DF, 0)), 4)*100 AS "RISCO/POSICAO_%",
                    DENSE_RANK() OVER(
                        PARTITION BY TRUNC(RAF.DATA_COTACAO), RME.TESOURARIA
                        ORDER BY RAF.COD_REL_APURACAO_FORM DESC
                    ) AS RN
                FROM REL_MULTI_ESTRATEGIA RME
                INNER JOIN REL_APURACAO_FORMS RAF 
                    ON RME.COD_REL_APURACAO_FORM = RAF.COD_REL_APURACAO_FORM
                INNER JOIN REL_APURACAO RA 
                    ON RAF.COD_REL_APURACAO = RA.CODIGO
                WHERE RME.NIVEL_AGREGACAO = 'Sintético Nível 2'
                AND RA.NOME LIKE '[RISCO] FUNDAÇÃO CERES#%'
            )
            SELECT *
            FROM RISCO_MERCADO_SEGMENTOS
            ORDER BY DATA_COTACAO DESC, TESOURARIA, RN
            """
    with get_connection().connect() as conn:
        df=  pd.read_sql(query, conn)

    df.columns = df.columns.str.upper()
    return df

