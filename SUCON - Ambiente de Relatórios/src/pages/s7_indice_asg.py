"""Índice de Materialidade e Impacto ASG - Carteira Consolidada (SURIC)."""
import streamlit as st

from modulos_asg import pagina, ui

#==================CABEÇALHO=========================
st.set_page_config(layout="wide")

# Tema ASG sem esconder o header/menu do Controle Ceres
ui.aplicar_tema(integrado=True)

st.html("""
<style>
    /* Remove o padding lateral e superior do bloco principal */
    .block-container {
        padding-top: 3.8rem;
        padding-left: 0rem;
        padding-right: 0rem;
    }

    .st-key-meu-container {
        background-color: #0B2F13;
        border-radius: 0px;
        padding: 30px 20px 30px 20px;
        width: 100%;
        box-sizing: border-box;
    }

    /* Container do conteúdo COM padding lateral */
    .st-key-conteudo {
        padding-left: 3rem;
        padding-right: 3rem;
    }

</style>
""")

with st.container(key="meu-container"):
    st.html("""
        <p style="text-align:center; color:#FAFBEB; margin:0 0; font-size: clamp(20px, 3vw, 29px); font-weight:400;">
            Índice ASG -
            <span style='color:#A8EC7D; font-family:"Source Serif 4",serif; font-style:italic; font-weight:600;'>
                Carteira Consolidada
            </span>
        </p>
        <p style="text-align:center; color:#C9D8C2; margin:6px 0 0; font-size:13px;">
            Dupla materialidade nos investimentos · Portaria Previc nº 728/2026
        </p>
    """)

with st.container(horizontal_alignment="center", gap=None, key="conteudo"):
    with st.container(width=1200):
        pagina.render(mostrar_hero=False)
