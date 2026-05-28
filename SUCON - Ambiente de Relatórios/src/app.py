import streamlit as st
from PIL import Image
from utils.helpers import get_css_global
import os

# ── FONTE GLOBAL ──────────────────────────────────────────────────────────────
get_css_global = get_css_global()
st.markdown(get_css_global, unsafe_allow_html=True)

# ── LOGO ──────────────────────────────────────────────────────────────────────
img_path = os.path.join("..", "images", "logo_escuro.png")
try:
    img = Image.open(img_path)
    st.logo(image=img)
except FileNotFoundError:
    st.error("Arquivo de imagem não encontrado!")
    st.error(f"Arquivo de imagem não encontrado no caminho: {img_path}")

# ── FLUXO ─────────────────────────────────────────────────────────────────────
pg_inicial = st.Page("pages/pg_inicial.py", title="Home", url_path="home")
enquadramento_planos = st.Page("pages/s1_enquadramento_planos.py", title="Planos", icon=":material/analytics:", url_path="enquadramento-planos")
enquadramento_fundos = st.Page("pages/s1_enquadramento_fundos.py", title="Fundos", icon=":material/analytics:", url_path="enquadramento-fundos")
lim_op = st.Page("pages/s1_lim_op.py", title="Limites Operacionais", icon=":material/analytics:", url_path="limites-operacionais")
risco_planos = st.Page("pages/s2_risco_planos.py", title="Risco Planos", icon=":material/analytics:", url_path="risco-planos")
risco_ativos = st.Page("pages/s2_risco_ativos.py", title="Risco Ativos", icon=":material/analytics:", url_path="risco-ativos")
rent = st.Page("pages/s4_rentabilidade.py", title="Rentabilidade", icon=":material/analytics:", url_path="rentabilidade")
teste = st.Page("pages/p0_teste.py", title="Teste", icon=":material/analytics:", url_path="teste")

current_page = st.navigation(
    {
        "Início": [pg_inicial],
        "Enquadramento": [enquadramento_planos, enquadramento_fundos, lim_op],
        "Risco": [risco_planos, risco_ativos],
        "Rentabilidade": [rent],
        "Teste": [teste],
    },
    position="hidden"
)

# ── CONFIG (dinâmico, após st.navigation) ─────────────────────────────────────
icon_img = Image.open(os.path.join("images", "c2.svg"))

st.set_page_config(
    page_title=f"Controle Ceres | {current_page.title}",
    page_icon=icon_img,
    layout="wide",
    initial_sidebar_state="collapsed")

# ── MENU CUSTOMIZADO ──────────────────────────────────────────────────────────
st.sidebar.markdown("Enquadramento")
st.sidebar.page_link(enquadramento_planos)
st.sidebar.page_link(enquadramento_fundos, disabled=True)
st.sidebar.page_link(lim_op)

st.sidebar.markdown("Risco")
st.sidebar.page_link(risco_planos, disabled=True)
st.sidebar.page_link(risco_ativos, disabled=True)

st.sidebar.markdown("Rentabilidade")
st.sidebar.page_link(rent, disabled=True)

st.sidebar.markdown("Teste")
st.sidebar.page_link(teste, disabled=True)

current_page.run()