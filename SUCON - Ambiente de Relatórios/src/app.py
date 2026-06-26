import streamlit as st
from PIL import Image
from utils.helpers import get_css_global
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "images"))

# ── FONTE GLOBAL ──────────────────────────────────────────────────────────────
get_css_global = get_css_global()
st.html(get_css_global)

# ── LOGO ──────────────────────────────────────────────────────────────────────
icon_img = os.path.join(IMAGES_DIR, "c2.svg")
icon_img_side = os.path.join(IMAGES_DIR, "c1.png")
img_path = os.path.join(IMAGES_DIR, "logo_escuro_adj.png")
try:
    img = Image.open(img_path)
    st.logo(image=img, size="medium", icon_image=img)
except FileNotFoundError:
    st.error("Arquivo de imagem não encontrado!")
    st.error(f"Arquivo de imagem não encontrado no caminho: {img_path}")

# ── FLUXO ─────────────────────────────────────────────────────────────────────
pg_inicial = st.Page("pages/pg_inicial.py", title="Home", url_path="home", visibility="hidden")
enquadramento_planos = st.Page("pages/s1_enquadramento_planos.py", title="Planos",  url_path="enquadramento-planos")
enquadramento_fundos = st.Page("pages/s1_enquadramento_fundos.py", title="Fundos",  url_path="enquadramento-fundos", visibility="hidden")
lim_op = st.Page("pages/s1_lim_op.py", title="Limites Operacionais",  url_path="limites-operacionais")
risco_mercado_planos = st.Page("pages/risco_mercado_planos.py", title="Planos",  url_path="risco-mercado-planos")
risco_mercado_ativos = st.Page("pages/risco_mercado_ativos.py", title="Risco Mercado Ativos",  url_path="risco-mercado-ativos", visibility="hidden")
rent = st.Page("pages/s4_rentabilidade.py", title="Planos",  url_path="rentabilidade-planos")


current_page = st.navigation(
    {
        "Início": [pg_inicial],
        "Enquadramento": [enquadramento_planos, enquadramento_fundos],
        "Risco de Crédito": [lim_op],
        "Risco de Mercado": [risco_mercado_planos, risco_mercado_ativos],
        "Rentabilidade": [rent],
    
    },
    position="top"
)

# ── CONFIG (dinâmico) ─────────────────────────────────────


st.set_page_config(
    page_title=f"Controle Ceres | {current_page.title}",
    page_icon=icon_img,
    layout="wide",)


current_page.run()