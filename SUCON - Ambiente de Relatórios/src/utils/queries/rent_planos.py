import pandas as pd
from utils.db_oracle import get_connection

def buscar_dados() -> pd.DataFrame:
    query = """
            WITH ranked_rentabilidade AS (
            -- CONSULTA 1: Rentabilidades
            SELECT 
                TO_CHAR(ra.DATA_INICIAL, 'DD/MM/YYYY') AS DATA_INICIAL,
                RAF.DATA_COTACAO,
                RME.TESOURARIA,
                RME.RENT_COTA_INICIO_MOEDA_NVAG AS INICIO,
                RME.RENT_COTA_MTD_MOEDA_NVAG AS MTD,
                RME.RENT_COTA_YTD_MOEDA_NVAG AS YTD,
                RME.RENT_COTA_DIDF_MOEDA_NVAG AS DIDF,
                RME.RENT_COTA_12M_MOEDA_NVAG AS MESES12,
                RME.COTA_NIVEL_AGREGACAO_DI AS DI,
                RME.COTA_NIVEL_AGREGACAO_DF AS DF,
                RME.REFERENCIA_BENCHMARK,
                RA.NOME,
                ROW_NUMBER() OVER (
                    PARTITION BY TRUNC(RAF.DATA_COTACAO), RME.TESOURARIA
                    ORDER BY RAF.COD_REL_APURACAO_FORM DESC
                ) AS rn
            FROM rel_multi_estrategia_cota_nvag RME
            INNER JOIN REL_APURACAO_FORMS RAF ON
                RME.COD_REL_APURACAO_FORM = RAF.COD_REL_APURACAO_FORM
            INNER JOIN REL_APURACAO RA ON
                RAF.COD_REL_APURACAO = RA.CODIGO
            WHERE RME.NIVEL_AGREGACAO = 'Rentabilidade Cota Nível Agregação 1' 
            AND RA.NOME LIKE '[RESULTADO] FUNDAÇÃO CERES DIARIO OFICIAL#%'
        ),
        ranked_posicao AS (
            -- CONSULTA 2: Posição DF
            SELECT
                RAF.DATA_COTACAO,
                RME.TESOURARIA,
                RME.POSICAO_DF,
                ROW_NUMBER() OVER(                            
                    PARTITION BY TRUNC(RAF.DATA_COTACAO), RME.TESOURARIA
                    ORDER BY RAF.COD_REL_APURACAO_FORM DESC     
                ) AS rn                                         
            FROM REL_MULTI_ESTRATEGIA RME
            INNER JOIN REL_APURACAO_FORMS RAF ON
                RME.COD_REL_APURACAO_FORM = RAF.COD_REL_APURACAO_FORM
            INNER JOIN REL_APURACAO RA ON
                RAF.COD_REL_APURACAO = RA.CODIGO
            WHERE RME.NIVEL_AGREGACAO = 'Sintético Nível 1' 
            AND RA.NOME LIKE '[RESULTADO] FUNDAÇÃO CERES DIARIO OFICIAL#%'
        )
        -- SELECT FINAL: Junta as duas CTEs
        SELECT 
            R1.DATA_INICIAL,
            R1.DATA_COTACAO,
            R1.TESOURARIA,
            R1.INICIO,
            R1.MTD,
            R1.YTD,
            R1.DIDF,
            R1.MESES12,
            R1.DI,
            R1.DF,
            R1.REFERENCIA_BENCHMARK,
            R1.NOME,
            R2.POSICAO_DF 
        FROM ranked_rentabilidade R1
        LEFT JOIN ranked_posicao R2 ON
            TRUNC(R1.DATA_COTACAO) = TRUNC(R2.DATA_COTACAO)
            AND R1.TESOURARIA = R2.TESOURARIA
        WHERE R1.rn = 1
        AND (R2.rn = 1 OR R2.rn IS NULL)  
        ORDER BY R1.DATA_COTACAO DESC, R1.TESOURARIA
    """
    with get_connection().connect() as conn:
        df=  pd.read_sql(query, conn)

    df.columns = df.columns.str.upper()
    return df