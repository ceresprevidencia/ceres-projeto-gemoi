import pandas as pd
from utils.db_oracle import get_connection

def buscar_dados() -> pd.DataFrame:
    query = """
        WITH ranked_posicao AS (
    -- CONSULTA 2: Posição DF
    SELECT
        RAF.DATA_COTACAO,
        RME.TESOURARIA,
        RME.GRUPO,
        RME.PRODUTO,
        RME.POSICAO_DF,
        ROW_NUMBER() OVER(                            
            PARTITION BY TRUNC(RAF.DATA_COTACAO), RME.TESOURARIA, RME.GRUPO, RME.CARTEIRA, RME.PRODUTO
            ORDER BY RAF.COD_REL_APURACAO_FORM DESC     
        ) AS rn                                         
    FROM REL_MULTI_ESTRATEGIA RME
    INNER JOIN REL_APURACAO_FORMS RAF ON
        RME.COD_REL_APURACAO_FORM = RAF.COD_REL_APURACAO_FORM
    INNER JOIN REL_APURACAO RA ON
        RAF.COD_REL_APURACAO = RA.CODIGO
    WHERE RME.NIVEL_AGREGACAO = 'Sintético Nível 4' 
    AND RA.NOME LIKE '[RESULTADO] FUNDAÇÃO CERES DIARIO OFICIAL#%'
)
-- SELECT FINAL: Junta as duas CTEs
SELECT 
    *
FROM ranked_posicao  
WHERE rn = 1
ORDER BY DATA_COTACAO DESC


            

    """
    with get_connection().connect() as conn:
        df=  pd.read_sql(query, conn)

    df.columns = df.columns.str.upper()
    return df