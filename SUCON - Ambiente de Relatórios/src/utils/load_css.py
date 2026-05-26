"""
Módulo para carregar CSS global de forma centralizada.
Evita CSS inline repetido e facilita manutenção.
"""

import streamlit as st
import os


def load_global_css():
    """
    Carrega o arquivo CSS global no app.
    Deve ser chamado uma única vez no app.py ou nas páginas.
    """
    css_path = os.path.join(os.path.dirname(__file__), "..", "style", "style.css")
    
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"❌ Arquivo CSS não encontrado: {css_path}")


def load_inline_css(css_string: str):
    """
    Injeta CSS inline diretamente.
    Use para CSS específico de uma página.
    
    Args:
        css_string: String com CSS a ser injetado
    """
    st.markdown(f"<style>{css_string}</style>", unsafe_allow_html=True)
