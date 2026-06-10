import streamlit as st
import streamlit.components.v1 as components

def nav_card(title, description, badges):
    """
    badges: lista de dicts {"label": str, "icon": str, "url": str, "tooltip": str (opcional)}
    """
    badges_html = "".join([
        f'<a class="badge" href="{b["url"]}" target="_self" data-tooltip="{b.get("tooltip", "")}">'
        f'<i class="ti ti-{b["icon"]}"></i> {b["label"]}</a>'
        for b in badges
    ])

    return f"""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">
    <style>
      .nav-card {{
        background: transparent;
        border: 0.5px solid rgba(128,128,128,0.3);
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        transition: border-color .2s, background .2s, box-shadow .2s;
        height: 200px;
        display: flex;
        flex-direction: column;
       
      }}
      
      .card-title {{ 
        font-size: 20px; 
        font-weight: 600; 
        margin: 0 0 6px; 
      }}

      .card-desc {{ 
        font-size: 16px; 
        opacity: .65; 
        margin: 0 0 1rem; 
        line-height: 1.5;
        flex: 1;
      }}

      .badges {{ 
        display: flex; 
        flex-wrap: wrap; 
        gap: 6px;
        margin-top: auto;
      }}

      .badge {{
        position: relative;
        display: inline-flex; 
        align-items: center; 
        gap: 5px;
        font-size: 14px; 
        font-weight: 500;
        border: 0.5px solid rgba(128,128,128,0.35);
        border-radius: 999px; 
        padding: 4px 10px;
        text-decoration: none; 
        color: inherit;
        transition: background .15s, border-color .15s;
        cursor: pointer;
      }}

      .badge:hover, .badge:focus {{ 
        background: rgba(128,128,128,0.12); 
        border-color: rgba(128,128,128,0.6); 
        outline: none;
      }}

      /* ==================== BALÃO DE DIÁLOGO  ==================== */
      
      /* Se não houver texto, esconde o balão e a seta */
      .badge[data-tooltip=""]:hover::after, .badge[data-tooltip=""]:focus::after,
      .badge[data-tooltip=""]:hover::before, .badge[data-tooltip=""]:focus::before {{
        display: none;
      }}

      /* Corpo do Balão */
      .badge::after {{
        content: attr(data-tooltip);
        position: absolute;
        bottom: 140%; /* Ajustado um pouco mais para cima para dar espaço à seta */
        left: 50%;
        transform: translateX(-50%) scale(0.8);
        background-color: #1e1e1e; /* Cor escura do balão */
        color: #fff;
        padding: 7px 12px;
        border-radius: 8px; /* Cantos levemente arredondados estilo caixa de diálogo */
        font-size: 13px;
        white-space: nowrap;
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.15s ease, transform 0.15s ease;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        z-index: 10;
      }}

      /* A Seta do Balão (O "biquinho" do quadrinho) */
      .badge::before {{
        content: "";
        position: absolute;
        bottom: 140%;
        left: 50%;
        transform: translateX(-50%) translateY(100%) scale(0.8); /* Fica logo abaixo do balão */
        border-width: 6px;
        border-style: solid;
        /* Cria o triângulo apontando para baixo */
        border-color: #1e1e1e transparent transparent transparent; 
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.15s ease, transform 0.15s ease;
        z-index: 10;
      }}

      /* Efeito de ativação: Mostra o balão e a seta juntos */
      .badge:hover::after, .badge:focus::after {{
        opacity: 1;
        transform: translateX(-50%) scale(1);
      }}

      .badge:hover::before, .badge:focus::before {{
        opacity: 1;
        transform: translateX(-50%) translateY(100%) scale(1);
      }}
    </style>

    <div class="nav-card">
      <p class="card-title">{title}</p>
      <p class="card-desc">{description}</p>
      <div class="badges">{badges_html}</div>
    </div>
    """



st.html("""
    <style>
        .st-key-meu-container {
            background-color: #0B2F13;
            border-radius: 8px;
            padding: 20px;
        }
    </style>
    """)


with st.container(key="meu-container", horizontal=True):
    st.markdown(
        """
        <div style="padding: 30px 0 45px 0;">
            <p style='color: #FAFBEB; font-family: Figtree, sans-serif; font-size: 50px; font-weight: 400; margin: 0; line-height: 0.9;'>
                Bem-vindo
            </p>
            <p style='color: #FAFBEB; font-family: Figtree, sans-serif; font-size: 50px; font-weight: 400; margin: 0 0 0 0;'>
                ao
                <span style='color: #A8EC7D; font-family: "Source Serif 4", serif; font-style: italic; font-size: 50px; font-weight: 600;'>
                    Controle Ceres
                </span>
            </p>
            <p style='color: #FAFBEB; font-family: Figtree, sans-serif; font-size: 16px; font-weight: 400; margin: 20px 0 0 0; line-height: 1.4;'>
                Nesta página, você pode acessar os painéis produzidos pelas supervisões de monitoramento de investimentos, risco e <i>compliance</i>.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
st.space('small')


col1, col2, col3 = st.columns(3)



with col1:
    st.html(nav_card(
        title="Enquadramento",
        description="Informações sobre o enquadramento dos planos, fundos e limites operacionais à luz da política de investimentos vigente.",
        badges=[
            {"label": "Planos", "icon": "file-text", "url": "/enquadramento-planos", "tooltip": "Enquadramento segundo a CMN n° 4994 e P.I."},
            {"label": "Limites Operacionais", "icon": "adjustments-horizontal", "url": "/limites-operacionais", "tooltip": "Relatório de limites operacionais das instituições financeiras."},
           
        ]
    ))


#  {"label": "Fundos", "icon": "coin", "url": "/enquadramento-fundos", "tooltip": "Verificar limites de fundos"},
#             {"label": "Limites Operacionais", "icon": "adjustments-horizontal", "url": "/limites-operacionais", "tooltip": "Acessar painel de limites"},
# with col2:
#     st.html(nav_card(
#         title="Risco",
#         description="Avaliação e gerenciamento dos riscos associados aos planos, fundos.",
#         badges=[
#             {"label": "Risco dos Planos", "icon": "file-text", "url": "/risco-planos", "tooltip": "Análise de risco por plano"},
#             {"label": "Risco dos Ativos", "icon": "coin", "url": "/risco-ativos", "tooltip": "Volatilidade e exposição de ativos"},
#         ]
#     ))

# with col3:
#     st.html(nav_card(
#         title="Rentabilidade",
#         description="Acompanhamento diário dos retornos dos planos.",
#         badges=[
#             {"label": "Rentabilidade", "icon": "file-text", "url": "/rentabilidade", "tooltip": "Histórico e metas de rentabilidade"},
#         ]
#     ))