import pandas as pd
from utils.db_oracle import get_connection

def buscar_dados() -> pd.DataFrame:
    query = """
                
WITH ENQUADRAMENTO AS (
                                        SELECT
                                            AGREGACAO,
                                            ESTRUTURA_ASSOCIADA,
                                            DATA_COTACAO,
                                            VALOR_REFERENCIA_MOEDA_VISUAL AS VALOR_REFERENCIA,
                                            CASE
                                                WHEN CONJUNTO_LIMITE LIKE '%[LUZ][v7.8] Resolução Bacen 4994%' THEN 'Resolução 4994'
                                                WHEN CONJUNTO_LIMITE LIKE '[CERES] Política de Investimentos%' THEN 'Política de Investimentos'
                                            ELSE CONJUNTO_LIMITE END AS CONJUNTO,
                                            DESCRICAO,
                                            AGREGACAO_COMPARACAO,
                                            ROUND(VALOR_LIMITE_REGRA, 4) AS VALOR_LIMITE_REGRA,
                                            ROUND(VALOR_LIMITE, 2) AS LIMITE_PERCENTUAL,
                                            ROUND(UTILIZADO, 4) AS VALOR_ATUAL,
                                            ROUND(NVL(PERCENTUAL_UTILIZADO,0), 4) AS PERCENTUAL_UTILIZADO,
                                            ROUND(NVL(PERCENTUAL_ULTRAPASSADO_REF, 0)*10, 4) AS PERCENTUAL_ULTRAPASSADO,
                                            ROUND(NVL(PERCENTUAL_TOTAL, 0), 4) AS PERCENTUAL_TOTAL,
                                            STATUS,
                                            CASE 
                                                WHEN DESCRICAO LIKE 'Art. 21%' THEN 'Renda Fixa (Art. 21)'
                                                WHEN DESCRICAO LIKE 'Renda Fixa' THEN 'Renda Fixa'   
                                                WHEN DESCRICAO LIKE '%Títulos da dívida pública mobiliária federal%' THEN 'Renda Fixa'
                                                WHEN DESCRICAO LIKE '%Cotas de classes de ETF de RF composto exclusivamente por títulos públicos%' THEN 'Renda Fixa'
                                                WHEN DESCRICAO LIKE '%Ativos financeiros RF de instituições financeiras autorizadas pelo Bacen%' THEN 'Renda Fixa'
                                                WHEN DESCRICAO LIKE '%Ativos financeiros RF de sociedade por ações cap aberto e cias securitizadoras%' THEN 'Renda Fixa'
                                                WHEN DESCRICAO LIKE '%Cotas de classes de ETF de RF%' THEN 'Renda Fixa'
                                                WHEN DESCRICAO LIKE '%Títulos das dívidas públicas mobiliárias estaduais e municipais%' THEN 'Renda Fixa'
                                                WHEN DESCRICAO LIKE '%Obrigações de organismos multilaterais emitidas no País%' THEN 'Renda Fixa'
                                                WHEN DESCRICAO LIKE '%Ativos financeiros RF de inst. financeiras não bancárias e cooperativas de crédito%' THEN 'Renda Fixa'
                                                WHEN DESCRICAO LIKE '%Debêntures Incentivadas - Lei 12.431 e Debêntures de Infraestrutura - Lei 14.801%' THEN 'Renda Fixa'
                                                WHEN DESCRICAO LIKE '%Cotas de classe FIDC e cotas de classes de cotas de FIDCs, CCBs e CCCBs%' THEN 'Renda Fixa'
                                                WHEN DESCRICAO LIKE '%CPRs, CRAs, CDCAs e Was%' THEN 'Renda Fixa'
                                                WHEN DESCRICAO LIKE '%Demais ativos%' THEN 'Renda Fixa'
                                               
                                                WHEN DESCRICAO LIKE 'Art. 22%' THEN 'Renda Variável (Art. 22)'
                                                WHEN DESCRICAO LIKE 'Renda Variável' THEN 'Renda Variável'
                                                WHEN DESCRICAO LIKE '%Ações e cotas de classes de fundos de índice segmento especial%' THEN 'Renda Variável'
                                                WHEN DESCRICAO LIKE '%Ações e cotas de classe de fundos de índice segmento não especial%' THEN 'Renda Variável'
                                                WHEN DESCRICAO LIKE '%Brazilian Depositary Receipts (BDR) e ETF internacional%' THEN 'Renda Variável'
                                                WHEN DESCRICAO LIKE '%Certificado de Ouro físico padrão negociado em bolsa de mercadorias e de futuros%' THEN 'Renda Variável'                                                                     
                                                
                                                WHEN DESCRICAO LIKE 'Art. 23%' THEN 'Estruturado (Art. 23)'
                                                WHEN DESCRICAO LIKE 'Estruturado' THEN 'Estruturado'
                                                WHEN DESCRICAO LIKE '%Cotas de classes Fundos de Investimento em Participações - FIP%' THEN 'Estruturado'
                                                WHEN DESCRICAO LIKE '%Cotas de classes Fundos de Invest. nas Cadeias Produtivas Agroindustriais - FIAGRO%' THEN 'Estruturado'
                                                WHEN DESCRICAO LIKE '%Certificado de Operações Estruturadas - COE%' THEN 'Estruturado'
                                                WHEN DESCRICAO LIKE '%Cotas de classes de fundos de investimento "Ações - Mercado de Acesso"%' THEN 'Estruturado'
                                                WHEN DESCRICAO LIKE '%Cotas de classes de Fundos tipificadas como Multimercado%' THEN 'Estruturado'
                                                WHEN DESCRICAO LIKE '%Créditos de descarbonização – CBIO e Créditos de Carbono%' THEN 'Estruturado'
                                                
                                                WHEN DESCRICAO LIKE 'Art. 24%' THEN 'Imobiliário (Art. 24)'
                                                WHEN DESCRICAO LIKE '%Imobiliário%' THEN 'Imobiliário'
                                                WHEN DESCRICAO LIKE '%Cotas de classes Fundo de Invest. Imobiliário (FII) e Cotas de Classes em Cotas de FII%' THEN 'Imobiliário'
                                                WHEN DESCRICAO LIKE '%Certificados de recebíveis imobiliários - CRI%' THEN 'Imobiliário'
                                                WHEN DESCRICAO LIKE '%Células de crédito imobiliário - CCI%' THEN 'Imobiliário'
                                                WHEN DESCRICAO LIKE '%Imóveis%' THEN 'Imobiliário'
                                                
                                                WHEN DESCRICAO LIKE 'Art. 25%' THEN 'Operações com Participantes (Art. 25)'
                                                WHEN DESCRICAO LIKE 'Operações com Participantes' THEN 'Operações com Participantes'
                                                WHEN DESCRICAO LIKE 'Empréstimo Simples' THEN 'Operações com Participantes'
                                                WHEN DESCRICAO LIKE 'Financiamento Imobiliário' THEN 'Operações com Participantes'
                                                
                                                WHEN DESCRICAO LIKE 'Art. 26%' THEN 'Exterior (Art. 26)'
                                                WHEN DESCRICAO LIKE 'Exterior' THEN 'Exterior'
                                                WHEN DESCRICAO LIKE '%Cotas de classes de fundos e cotas de classe de FICs Renda Fixa - Dívida Externa%' THEN 'Exterior'
                                                WHEN DESCRICAO LIKE '%Cotas de classes de fundos e cotas de classe de FICs Renda Fixa - Dívida Externa%' THEN 'Exterior'
                                                WHEN DESCRICAO LIKE '%Cotas de classes de FI, destinados a investidores qualificados e Offshore%' THEN 'Exterior'
                                                WHEN DESCRICAO LIKE '%Cotas de classes de FI, destinados a investidores qualificados e ativos no exterior%' THEN 'Exterior'
                                                WHEN DESCRICAO LIKE '%Cotas de classes de FI, destinados ao público em geral e Offshore%' THEN 'Exterior'
                                                WHEN DESCRICAO LIKE '%Ativos financeiros no exterior pertencentes às carteiras dos fundos locais%' THEN 'Exterior'
                                                
                                                WHEN DESCRICAO LIKE 'Art. 27%' THEN 'Emissores (Art. 27)'
                                                WHEN DESCRICAO LIKE 'Art. 28%' THEN 'Emissores (Art. 28)'
                                                WHEN DESCRICAO LIKE 'Art. 30%' THEN 'Derivativos (Art. 30)'
                                                WHEN DESCRICAO LIKE 'Art. 36%' THEN 'Vedações (Art. 36)'
                                                
                                                ELSE 'Não identificado' END AS SEGMENTO,                         
                                            CASE 
                                                WHEN DESCRICAO LIKE '%V)%' OR DESCRICAO LIKE '%V,%' THEN '7'
                                                WHEN DESCRICAO LIKE '%IV)%' OR DESCRICAO LIKE '%IV,%' THEN '6'
                                                WHEN DESCRICAO LIKE '%III)%' OR DESCRICAO LIKE '%III,%' THEN '5'
                                                WHEN DESCRICAO LIKE '%II)%' OR DESCRICAO LIKE '%II,%' THEN '4'
                                                WHEN DESCRICAO LIKE '%I)%' OR DESCRICAO LIKE '%I,%' THEN '3'
                                                WHEN DESCRICAO LIKE '%§1%' THEN '2'
                                                WHEN NOT REGEXP_LIKE(DESCRICAO, '§1|III[),]|II[),]|I[),]|IV[),]|V[),]') THEN '1'
                                                ELSE 'Não identificado'
                                            END AS ORDEM,
                                            ROW_NUMBER() OVER(
                                                PARTITION BY TRUNC(RAF.DATA_COTACAO), AGREGACAO, ESTRUTURA_ASSOCIADA, CONJUNTO_LIMITE, DESCRICAO
                                                ORDER BY RAF.COD_REL_APURACAO_FORM DESC
                                                ) AS RN
                                        FROM   
                                            REL_LIMITE RL 
                                            inner join REL_APURACAO_FORMS RAF on RAF.COD_REL_APURACAO_FORM = RL.COD_REL_APURACAO_FORM 
                                            inner join REL_APURACAO RA on RA.CODIGO = RAF.COD_REL_APURACAO
                                
                                        WHERE
                                            RA.NOME LIKE '[ENQUADRAMENTO] FUNDAÇÃO CERES#%' AND
                                            AGREGACAO_COMPARACAO IS NOT NULL AND
                                            VALOR_LIMITE_REGRA !=0  
                                    )
                                SELECT 
                                    AGREGACAO,
                                    ESTRUTURA_ASSOCIADA,                        
                                    DATA_COTACAO,
                                    CONJUNTO,                        
                                    DESCRICAO,
                                    AGREGACAO_COMPARACAO,
                                    VALOR_LIMITE_REGRA,
                                    VALOR_REFERENCIA,
                                    LIMITE_PERCENTUAL,
                                    VALOR_ATUAL,
                                    PERCENTUAL_UTILIZADO,
                                    PERCENTUAL_ULTRAPASSADO,
                                    PERCENTUAL_TOTAL,
                                    STATUS,
                                    SEGMENTO,
                                    ORDEM
                                FROM 
                                    ENQUADRAMENTO 
                                WHERE
                                    RN = 1
                                ORDER BY 
                                    DESCRICAO   

    """
    with get_connection().connect() as conn:
        df=  pd.read_sql(query, conn)

    df.columns = df.columns.str.upper()
    return df