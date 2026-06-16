import pandas as pd
from utils.db_sqlserver import get_connection

def buscar_dados() -> pd.DataFrame:
    query = """
        WITH rentabilidade_ajustada AS (
            SELECT *,
                CASE
                    WHEN DS_PLANO_MITRA = 'RENTABILIDADE CONSOLIDADA' THEN 'CERES CONSOLIDADA' 
                    ELSE DS_PLANO_MITRA
                END AS DS_PLANO_CORRIGIDO
                FROM [BI_CERES].[dbo].[VW_RENTABILIDADE]
                WHERE DS_SEGMENTO_APLICACAO IN ('RENTABILIDADE CONSOLIDADA', 'PERFORMANCE CONSOLIDADA')
            )
            SELECT 

                CASE
                    WHEN re.DS_PLANO_CORRIGIDO = 'CERES CONSOLIDADA' THEN '[CERES TOTAL]' 
                    ELSE re.DS_PLANO_CORRIGIDO
                 END AS PLANO,
                DATEFROMPARTS(re.CO_EXERCICIO, re.NR_MES, 1) AS DATA,
                re.PERC_MES AS RENTABILIDADE,
                ma.PERC_MES AS BENCH
            FROM VW_META_ATUARIAL AS ma
            RIGHT JOIN rentabilidade_ajustada as re
            ON ma.DS_PLANO_MITRA = re.DS_PLANO_CORRIGIDO
            AND ma.CO_EXERCICIO = re.CO_EXERCICIO
            AND ma.NR_MES = re.NR_MES
    """
    with get_connection().connect() as conn:
        df=  pd.read_sql(query, conn)

    df.columns = df.columns.str.upper()
    return df