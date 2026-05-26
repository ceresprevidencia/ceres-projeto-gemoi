import pandas as pd
from utils.db_oracle import get_connection

def buscar_dados() -> pd.DataFrame:
    query="""
                /* CONSULTA RISCO MERCADO (ATIVOS)*/
                WITH ATIVOS_AGREGADOS AS (
                SELECT
                    PRODUTO,
                    RAF.COD_REL_APURACAO_FORM,
                    RA.NOME,
                    GRUPO,
                    DATA_COTACAO,
                    EXPOSICAO_INDIV_PAR AS POSICAO,
                    RISCO_INDIV_PAR AS PAR_$,
                    RISCO_INDIV_POR_EXPOSICAO_PAR AS PAR_PCT,
                    RISCO_INDIV_HIST AS HIST_$,
                    RISCO_INDIV_POR_EXPOSICAO_HIST AS HIST_PCT,
                    RISCO_INDIV_MC AS MC_$,
                    RISCO_INDIV_POR_EXPOSICAO_MC AS MC_PCT,
                    DENSE_RANK() OVER(
                    PARTITION BY TRUNC(RAF.DATA_COTACAO), PRODUTO
                    ORDER BY RAF.COD_REL_APURACAO_FORM DESC
                ) AS RN
                FROM REL_MULTI_ESTRATEGIA RME
                INNER JOIN REL_APURACAO_FORMS RAF ON RME.COD_REL_APURACAO_FORM = RAF.COD_REL_APURACAO_FORM
                INNER JOIN REL_APURACAO RA ON RAF.COD_REL_APURACAO = RA.CODIGO
                WHERE RME.NIVEL_AGREGACAO = 'Risco de Mercado Analítico'
                AND RA.NOME LIKE '[RISCO] FUNDAÇÃO CERES#%'
                AND PRODUTO IN (
                        '4UM SMALL CAPS FIF - CLASSE DE INVESTIMENTO EM AÇÕES - RESP - C0000213691',
                        'AZ QUEST LUCE INSTITUCIONAL FC FIF RF CRED PRIV LP RESP LI - C0000724173',
                        'BB PREVIDENCIÁRIO RENDA FIXA REFERENCIADO DI LONGO PRAZO PER - C0000272493',
                        'BNP PARIBAS CRÉDITO INSTITUCIONAL SUSTENTÁVEL IS CLASSE DE I - C0000494151',
                        'BOVA11',
                        'BOVV11',
                        'BRADESCO PERFORMANCE INSTITUCIONAL FUNDO DE INVESTIMENTO FIN - C0000672335',
                        'CHAPADA DIAMANTINA CIC DE FI MULT - RESP LIMITADA - C0000698733',
                        'CHAPADA DOS GUIMARÃES CLASSE ÚNICA DE INVESTIMENTO EM COTAS - C0000700606',
                        'CHAPADA DOS VEADEIROS CLASSE DE FIF AÇÕES - RESP LIMITADA - C0000602418',
                        'CLASSE ÚNICA DE COTAS DO BTG PACTUAL CRÉDITO CORPORATIVO I F - C0000293075',
                        'CLASSE ÚNICA DE COTAS DO GUEPARDO INSTITUCIOAL FUNDO DE INVE - C0000214019',
                        'CLASSE ÚNICA DE COTAS DO TRÍGONO FLAGSHIP 60 SMALL CAPS FUND - C0000529478',
                        'CRI_12L0033171',
                        'DEB_CBAN32',
                        'DEB_CBAN52',
                        'DEB_LCAMD3',
                        'DEB_LORTA7',
                        'GOLD11',
                        'ITAÚ INSTITUCIONAL RF REF DI FIF RES LIMITADA - C0000020435',
                        'IVVB11',
                        'NTNB_15/05/2033_760199',
                        'NTNB_15/05/2035_760199',
                        'NTNB_15/05/2045_760199',
                        'NTNB_15/05/2055_760199',
                        'NTNB_15/08/2026_760199',
                        'NTNB_15/08/2028_760199',
                        'NTNB_15/08/2030_760199',
                        'NTNB_15/08/2032_760199',
                        'NTNB_15/08/2040_760199',
                        'NTNB_15/08/2050_760199',
                        'NTNB_15/08/2060_760199',
                        'NTNC_01/01/2031_770100',
                        'OCEANA SERRA DA CAPIVARA CLASSE DE FIF AÇÕES - RESP LIMITADA - C0000603384',
                        'PORTO SEGURO IPÊ FIF DA CIC RF CRÉD PRIV LP RESP LIMITADA - C0000523666',
                        'RB CAPITAL DESENV RESIDENCIAL II FII',
                        'SAFRA CAPITAL MARKET PREMIUM CIC RF REFERENCIADA DI CRED PRI - C0000331031',
                        'SAFRA VITESSE CI RF CRED PRIV RESP LIMITADA - C0000284211',
                        'SANTANDER DIVIDENDOS AÇÕES - CIC FIF RESP LIMITADA - C0000289191',
                        'SERRA DO CIPÓ CLASSE DE FIF AÇÕES - RESP LIMITADA - C0000604828',
                        'SPARTA TOP FC FIF RF CRED PRIV LP - RESP LIMITADA - C0000296430',
                        'SULAMÉRICA CRÉDITO INSTITUCIONAL ESG CLASSE DE INVESTIMENTO - C0000578411',
                        'TIJUCA CLASSE DE FIF AÇÕES - RESP LIMITADA - C0000605859'
                    )
                )
                SELECT PRODUTO,
                GRUPO,
                DATA_COTACAO,
                SUM(POSICAO) AS POSICAO,
                SUM(PAR_$) AS PAR_$,
                AVG(PAR_PCT) AS PAR_PCT,
                SUM(HIST_$) AS HIST_$,
                AVG(HIST_PCT) AS HIST_PCT,
                SUM(MC_$) AS MC_$,
                AVG(MC_PCT) AS MC_PCT
                FROM ATIVOS_AGREGADOS
                WHERE RN = 1
                GROUP BY PRODUTO, GRUPO, DATA_COTACAO
                ORDER BY DATA_COTACAO DESC, PRODUTO
                
                """
    with get_connection().connect() as conn:
        df=  pd.read_sql(query, conn)

    df.columns = df.columns.str.upper()
    return df