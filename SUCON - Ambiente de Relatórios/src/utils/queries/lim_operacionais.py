import pandas as pd
from utils.db_oracle import get_connection

def buscar_dados() -> pd.DataFrame:
    query = """
    WITH alocacao AS (
    SELECT
        RME.COD_REL_APURACAO_FORM,
        RME.TESOURARIA,
        RME.EMISSOR,
        RME.PRODUTO,
        RME.VENCIMENTO,
        RME.DATA_AQUISICAO,
        RME.CODIGO_ISIN,
        RAF.DATA_COTACAO,
        RME.INDEXADOR_ATIVO_AQUISICAO AS INDEXADOR,
        RME.CUPOM_ATIVO_AQUISICAO AS TAXA_AQUISICAO,
        RME.POSICAO_DF as EXPOSICAO,
        RME.FINANCEIRO_AQUISICAO,
        DENSE_RANK() OVER(
                        PARTITION BY TRUNC(RAF.DATA_COTACAO)
                        ORDER BY RAF.COD_REL_APURACAO_FORM DESC
                        ) AS RN
    FROM REL_MULTI_ESTRATEGIA RME
    INNER JOIN REL_APURACAO_FORMS RAF 
        ON RME.COD_REL_APURACAO_FORM = RAF.COD_REL_APURACAO_FORM
    INNER JOIN REL_APURACAO RA 
        ON RAF.COD_REL_APURACAO = RA.CODIGO
    WHERE RA.NOME LIKE '[SUCON] LIMITES OPERACIONAIS - IFS%' 
    AND RME.NIVEL_AGREGACAO = 'Analítico'
    AND RME.EMISSOR IN (
                      'BANCO ABC BRASIL S.A.',
                      'BANCO VOTORANTIM S.A.',
                      'BANCO COOPEREATIVO SICREDI S.A.',
                      'BANCO BTG PACTUAL S.A.',
                      'BANCO DAYCOVAL S/A',
                      'ITAU UNIBANCO S.A.',
                      'BANCO MERCANTIL DO BRASIL SA',
                      'Banco Safra S.A.',
                      'BANCO SANTANDER (BRASIL) S.A.',
                      'BANCO SOFISA SA',
                      'Banco Cooperativo do Brasil S.A.',
                      'BANCO BRADESCO SA',
                      'PARANA BANCO S/A',
                      'BANCO PAN S.A.'
                    )
 
    )

    SELECT *
    FROM alocacao
    WHERE RN = 1
    ORDER BY TESOURARIA 
    """
    
    with get_connection().connect() as conn:
        df=  pd.read_sql(query, conn)

    df.columns = df.columns.str.upper()
    return df