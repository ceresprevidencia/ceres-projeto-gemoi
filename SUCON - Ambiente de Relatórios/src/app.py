import streamlit as st
from PIL import Image
from utils.helpers import get_css_global

# ── CONFIG ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Relatório de Enquadramento - Fundação Ceres",
    page_icon="images\\c2.svg",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── FONTE GLOBAL ──────────────────────────────────────────────────────────────
get_css_global = get_css_global()
st.markdown(get_css_global, unsafe_allow_html=True)

# ── LOGO ──────────────────────────────────────────────────────────────────────
img_path = "images\\logo_escuro.png"
try:
    img = Image.open(img_path)
    st.logo(image=img, size='large')
except FileNotFoundError:
    st.error("Arquivo de imagem não encontrado!")

# ── FLUXO ─────────────────────────────────────────────────────────────────────

enquadramento_planos = st.Page("pages/s1_enquadramento_planos.py", title="Planos", icon=":material/analytics:")
enquadramento_fundos = st.Page("pages/s1_enquadramento_fundos.py", title="Fundos", icon=":material/analytics:")
lim_op = st.Page("pages/s1_lim_op.py", title="Limites Operacionais", icon=":material/analytics:")
risco_planos = st.Page("pages/s2_risco_planos.py", title="Risco Planos", icon=":material/analytics:")
risco_ativos = st.Page("pages/s2_risco_ativos.py", title="Risco Ativos", icon=":material/analytics:")
rent = st.Page("pages/s4_rentabilidade.py", title="Rentabilidade", icon=":material/analytics:")
teste = st.Page("pages/p0_teste.py", title="Teste", icon=":material/analytics:")

pg = st.navigation(
    {
        "Enquadramento": [enquadramento_planos, enquadramento_fundos, lim_op], 
        "Risco": [risco_planos, risco_ativos], 
        "Rentabilidade": [rent],
        "Teste": [teste]
    },
    position='hidden'
        
    )

# Menu customizado reutilizando os objetos st.Page
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

pg.run()