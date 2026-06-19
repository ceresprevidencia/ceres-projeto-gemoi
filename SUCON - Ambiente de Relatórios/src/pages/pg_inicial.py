import streamlit as st


# ── COMPONENTE: CARD DE NAVEGAÇÃO ─────────────────────────────────────────────

# CSS compartilhado entre todos os cards — injetado uma única vez na página
_CSS_NAV_CARD = """
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">
<style>
  .nav-card {
    background: transparent;
    border: 0.5px solid rgba(128,128,128,0.3);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    transition: border-color .2s, background .2s, box-shadow .2s;
    height: 200px;
    display: flex;
    flex-direction: column;
  }
  .nav-card:hover {
  background: linear-gradient(
    135deg,
    rgba(168, 236, 125, 0.08),
    rgba(128, 128, 128, 0.04)
  );
  border-color: rgba(168, 236, 125, 0.45);
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.14);
  transform: translateY(-4px);
}

  .card-title { font-size: 20px; font-weight: 600; margin: 0 0 6px; }
  .card-desc  { font-size: 16px; opacity: .65; margin: 0 0 1rem; line-height: 1.5; flex: 1; }
  .badges     { display: flex; flex-wrap: wrap; gap: 6px; margin-top: auto; }

  /* Badge / link de navegação */
  .badge {
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
    background: #A8EC7D;
    color: #0B2F13;
    transition: background .15s, border-color .15s;
    cursor: pointer;
  }
  .badge:hover, .badge:focus {
    background: rgba(128,128,128,0.12);
    border-color: rgba(128,128,128,0.6);
    outline: none;
  }

  /* Tooltip — esconde quando data-tooltip está vazio */
  .badge[data-tooltip=""]:hover::after,
  .badge[data-tooltip=""]:focus::after,
  .badge[data-tooltip=""]:hover::before,
  .badge[data-tooltip=""]:focus::before { display: none; }

  /* Balão do tooltip */
  .badge::after {
    content: attr(data-tooltip);
    position: absolute;
    bottom: 140%;
    left: 50%;
    transform: translateX(-50%) scale(0.8);
    background-color: #A8EC7D;
    color: #0B2F13;
    padding: 7px 12px;
    border-radius: 8px;
    font-size: 13px;
    white-space: nowrap;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.15s ease, transform 0.15s ease;
    box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    z-index: 10;
  }

  /* Seta do tooltip */
  .badge::before {
    content: "";
    position: absolute;
    bottom: 140%;
    left: 50%;
    transform: translateX(-50%) translateY(100%) scale(0.8);
    border: 6px solid transparent;
    border-top-color: #1e1e1e;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.15s ease, transform 0.15s ease;
    z-index: 10;
  }

  /* Ativa tooltip ao hover/foco */
  .badge:hover::after,  .badge:focus::after  { opacity: 1; transform: translateX(-50%) scale(1); }
  .badge:hover::before, .badge:focus::before { opacity: 1; transform: translateX(-50%) translateY(100%) scale(1); }
</style>
"""

def nav_card(title: str, description: str, badges: list) -> str:
    """
    Gera o HTML de um card de navegação com badges clicáveis.

    Parâmetros
    ----------
    title       : Título do card.
    description : Texto descritivo exibido abaixo do título.
    badges      : Lista de dicts com as chaves:
                    - label   : texto do badge
                    - icon    : nome do ícone Tabler (sem o prefixo 'ti-')
                    - url     : destino do link
                    - tooltip : texto do balão ao passar o mouse (opcional)
    """
    badges_html = "".join(
        f'<a class="badge" href="{b["url"]}" target="_self" data-tooltip="{b.get("tooltip", "")}">'
        f'<i class="ti ti-{b["icon"]}"></i> {b["label"]}</a>'
        for b in badges
    )
    return f"""
    {_CSS_NAV_CARD}
    <div class="nav-card">
      <p class="card-title">{title}</p>
      <p class="card-desc">{description}</p>
      <div class="badges">{badges_html}</div>
    </div>
    """


# ── CSS DA PÁGINA ─────────────────────────────────────────────────────────────

st.html("""
<style>
    .block-container { padding-top: 4rem; }
    .st-key-meu-container {
        background-color: #0B2F13;
        border-radius: 8px;
        padding: 20px;
    }
</style>
""")


# ── CABEÇALHO ─────────────────────────────────────────────────────────────────

with st.container(key="meu-container", horizontal=True):
    st.markdown("""
        <div style="padding: 30px 0 45px 0;">
            <p style="color:#FAFBEB; font-family:Figtree,sans-serif; font-size:50px; font-weight:400; margin:0; line-height:0.9;">
                Bem-vindo
            </p>
            <p style="color:#FAFBEB; font-family:Figtree,sans-serif; font-size:50px; font-weight:400; margin:0;">
                ao
                <span style='color:#A8EC7D; font-family:"Source Serif 4",serif; font-style:italic; font-weight:600;'>
                    Controle Ceres
                </span>
            </p>
            <p style="color:#FAFBEB; font-family:Figtree,sans-serif; font-size:16px; font-weight:400; margin:20px 0 0; line-height:1.4;">
                Nesta página, você pode acessar os painéis produzidos pelas supervisões de monitoramento
                de investimentos, risco e <i>compliance</i>.
            </p>
        </div>
    """, unsafe_allow_html=True)

st.space("small")


# ── CARDS DE NAVEGAÇÃO ────────────────────────────────────────────────────────

# Definição centralizada dos cards — adicione, remova ou reordene aqui
CARDS = [
    {
        "col": 0,
        "title": "Enquadramento",
        "description": "Informações sobre o enquadramento dos planos, fundos e limites operacionais à luz da política de investimentos vigente.",
        "badges": [
            {"label": "Planos",               "icon": "file-text",             "url": "/enquadramento-planos",   "tooltip": "Enquadramento segundo a CMN n° 4994 e P.I."},
            {"label": "Limites Operacionais", "icon": "adjustments-horizontal", "url": "/limites-operacionais",  "tooltip": "Relatório de limites operacionais das instituições financeiras."},
        ],
    },
    {
        "col": 1,
        "title": "Rentabilidade",
        "description": "Acompanhamento diário dos retornos dos planos.",
        "badges": [
            {"label": "Rentabilidade", "icon": "file-text", "url": "/rentabilidade", "tooltip": "Histórico e metas de rentabilidade"},
        ],
    },
    # Para adicionar o card de Risco, descomente e ajuste:
    # {
    #     "col": 1,
    #     "title": "Risco",
    #     "description": "Avaliação e gerenciamento dos riscos associados aos planos e fundos.",
    #     "badges": [
    #         {"label": "Risco dos Planos",  "icon": "file-text", "url": "/risco-planos",  "tooltip": "Análise de risco por plano"},
    #         {"label": "Risco dos Ativos",  "icon": "coin",      "url": "/risco-ativos",  "tooltip": "Volatilidade e exposição de ativos"},
    #     ],
    # },
]

cols = st.columns(3)
for card in CARDS:
    with cols[card["col"]]:
        st.html(nav_card(card["title"], card["description"], card["badges"]))