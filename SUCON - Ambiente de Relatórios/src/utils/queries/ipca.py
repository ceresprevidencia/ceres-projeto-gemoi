import pandas as pd
from utils.db_sqlserver import get_connection

def buscar_dados() -> pd.DataFrame:
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