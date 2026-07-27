import streamlit as st

from modulos_exportaveis import renderizar_rras


# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================

st.set_page_config(
    page_title="Exportáveis",
    layout="wide",
)


# =========================================================
# CSS DA PÁGINA
# =========================================================

st.html(
    """
    <style>
        /*
        Container principal da página:
        - largura máxima de 1200px;
        - centralização horizontal;
        - espaço lateral em telas menores.
        */
        [data-testid="stMainBlockContainer"] {
            width: 100%;
            max-width: 1200px;
            margin-left: auto !important;
            margin-right: auto !important;
            padding-top: 3rem;
            padding-left: 24px;
            padding-right: 24px;
            padding-bottom: 48px;
            box-sizing: border-box;
        }

        /*
        Compatibilidade com outras versões do Streamlit.
        */
        .block-container {
            width: 100%;
            max-width: 1200px !important;
            margin-left: auto !important;
            margin-right: auto !important;
            padding-top: 3rem;
            padding-left: 24px;
            padding-right: 24px;
            padding-bottom: 48px;
            box-sizing: border-box;
        }

        .cabecalho-exportaveis {
            width: 100%;
            background-color: #0B2F13;
            border-radius: 14px;
            padding: 26px 24px;
            box-sizing: border-box;
            margin-bottom: 28px;
            text-align: center;
        }

        .cabecalho-exportaveis p {
            color: #FAFBEB;
            margin: 0;
            font-family: "Figtree", sans-serif;
            font-size: clamp(22px, 3vw, 30px);
            font-weight: 400;
        }

        .cabecalho-exportaveis span {
            color: #A8EC7D;
            font-family: "Source Serif 4", serif;
            font-style: italic;
            font-weight: 600;
        }

        .descricao-exportaveis {
            color: #5A5A5A;
            font-family: "Figtree", sans-serif;
            font-size: 15px;
            line-height: 1.5;
            margin: 0 0 16px 0;
        }

        /*
        Impede que elementos internos ultrapassem o container.
        */
        [data-testid="stVerticalBlock"],
        [data-testid="stHorizontalBlock"],
        [data-testid="stColumn"],
        [data-testid="stSelectbox"],
        [data-testid="stDateInput"],
        [data-testid="stDownloadButton"] {
            max-width: 100%;
            box-sizing: border-box;
        }

        @media (max-width: 768px) {
            [data-testid="stMainBlockContainer"],
            .block-container {
                padding-left: 14px;
                padding-right: 14px;
            }

            .cabecalho-exportaveis {
                padding: 22px 16px;
            }
        }
    </style>
    """
)


# =========================================================
# CABEÇALHO
# =========================================================

st.html(
    """
    <div class="cabecalho-exportaveis">
        <p>
            Central de
            <span>Exportáveis</span>
        </p>
    </div>
    """
)


# =========================================================
# SELEÇÃO DO VISUAL
# =========================================================

st.html(
    """
    <div class="descricao-exportaveis">
        Selecione o visual que deseja consultar e exportar.
    </div>
    """
)


visuais_disponiveis = {
    "RRAS": renderizar_rras,

    # Próximos módulos:
    # "Limites Operacionais": renderizar_limites_operacionais,
    # "Risco por Segmento": renderizar_risco_segmentos,
}


visual_selecionado = st.selectbox(
    "Qual visual deseja exportar?",
    options=list(visuais_disponiveis.keys()),
    key="visual_exportavel_selecionado",
)


st.divider()


# =========================================================
# RENDERIZAÇÃO DO MÓDULO SELECIONADO
# =========================================================

funcao_visual = visuais_disponiveis.get(
    visual_selecionado
)

if funcao_visual:
    funcao_visual()

else:
    st.warning(
        "O visual selecionado não está disponível."
    )