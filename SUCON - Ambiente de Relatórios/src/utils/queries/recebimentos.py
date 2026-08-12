import streamlit as st
import pandas as pd
from utils.db_oracle import get_connection

@st.cache_data(ttl="24h")
def buscar_dados_recebimentos() -> pd.DataFrame:
    query = """
        WITH rendimentos AS (
            SELECT 
                RME_FC.COD_REL_APURACAO_FORM,
                RME_FC.TESOURARIA,
                RME_FC.PRODUTO,
                RME_FC.CODIGO,
                RME_FC.GRUPO,
                RAF.DATA_COTACAO,
                RME_FC.DATA AS DATA_PAGAMENTO,
                RME_FC.DF_VENCIM_DU AS PAGAMENTO_DU,
                RME_FC.FINANCEIRO_DF AS FINANCEIRO_PRESENTE,
                RME_FC.FIN_VAL_FINAL_PROJ AS FINANCEIRO_PROJETADO,
                DENSE_RANK() OVER(
                        PARTITION BY TRUNC(RAF.DATA_COTACAO), RME_FC.TESOURARIA
                        ORDER BY RAF.COD_REL_APURACAO_FORM DESC
                        ) AS RN
            FROM REL_MULTI_ESTRATEGIA_FC RME_FC
            INNER JOIN REL_APURACAO_FORMS RAF ON RME_FC.COD_REL_APURACAO_FORM = RAF.COD_REL_APURACAO_FORM
            INNER JOIN REL_APURACAO RA ON RAF.COD_REL_APURACAO = RA.CODIGO
            WHERE RA.NOME LIKE '[SUCON] PROJEÇÃO RENDIMENTOS%'
            AND RME_FC.NIVEL_AGREGACAO = 'Analítico'
            AND RME_FC.TESOURARIA IN (
                'ABDI FlexCeres_CD', 'Ceres Básico_BD', 'Ceres FlexCeres_CV', 'Cidasc FlexCeres_CV',
                'Emater DF FlexCeres_CV', 'Emater MG Básico_BD', 'Emater MG FlexCeres_CV',
                'Emater MG Saldado_BD', 'Embrapa Básico_BD', 'Embrapa FlexCeres_CV',
                'Epagri Básico_BD', 'Epagri FlexCeres_CV', 'Epagri Saldado_BD', 'Epamig Básico_BD',
                'Epamig FlexCeres_CV', 'Epamig Saldado_BD', 'EROS FIM CREDITO PRIVADO',
                'Família Ceres_CD', 'PGA'
            )
        ),
        dados_com_vencimento AS (
            SELECT 
                A.*,
                (
                    SELECT RME.VENCIMENTO 
                    FROM REL_MULTI_ESTRATEGIA RME 
                    WHERE RME.COD_REL_APURACAO_FORM = A.COD_REL_APURACAO_FORM 
                    AND RME.CODIGO = A.CODIGO 
                    AND ROWNUM = 1
                ) AS VENCIMENTO
            FROM rendimentos A
            WHERE A.RN = 1
        )
        SELECT *
        FROM dados_com_vencimento
        WHERE VENCIMENTO IS NOT NULL
        ORDER BY TESOURARIA, CODIGO, DATA_PAGAMENTO
        """
        
    with get_connection().connect() as conn:
        df=  pd.read_sql(query, conn)

    df.columns = df.columns.str.upper()
    return df