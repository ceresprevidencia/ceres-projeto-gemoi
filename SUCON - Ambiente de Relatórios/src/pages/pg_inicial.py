import streamlit as st


# ── COMPONENTE: CARD DE NAVEGAÇÃO ─────────────────────────────────────────────

_CSS_NAV_CARD = """
<style>
  @import url("https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/dist/tabler-icons.min.css");

  .nav-card {
    background: transparent;
    border: 0.5px solid rgba(128,128,128,0.3);
    border-radius: 12px;
    padding: 1.5rem 1.75rem;
    transition: border-color .2s, background .2s, box-shadow .2s, transform .2s;
    height: 260px;
    display: flex;
    flex-direction: column;
    position: relative;

   
    container-type: inline-size;
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

  .card-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 0 0 10px;
    min-width: 0;
  }

  .card-icon {
    font-size: 34px;
    line-height: 1;
    color: #A8EC7D;
    flex-shrink: 0;
  }

  .card-title {
    font-size: 26px;
    font-weight: 600;
    margin: 0;
    line-height: 1.15;
    min-width: 0;
  }

  .card-desc {
    font-size: 16px;
    opacity: .65;
    margin: 0;
    line-height: 1.5;
    flex: 1;
  }

  .card-divider {
    width: 100%;
    height: 1px;
    background: rgba(128, 128, 128, 0.25);
    margin: 2rem 0 0.85rem;
  }


  .badges-desktop {
    display: flex;
    flex-wrap: nowrap;
    gap: 6px;
    min-width: 0;
    overflow: hidden;
  }

  .badge {
    position: relative;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    min-width: 0;
    max-width: 100%;
    font-size: 14px;
    font-weight: 600;
    border: 0.5px solid rgba(128,128,128,0.35);
    border-radius: 999px;
    padding: 4px 10px;
    text-decoration: none;
    background: #A8EC7D;
    color: #0B2F13;
    transition: background .15s, border-color .15s, color .15s;
    cursor: pointer;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    flex-shrink: 1;
  }

  .badge span {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .badge:hover,
  .badge:focus {
    background: rgba(128,128,128,0.12);
    border-color: rgba(128,128,128,0.6);
    outline: none;
  }

  .badge.disabled {
    background: rgba(128, 128, 128, 0.18);
    color: rgba(128, 128, 128, 0.95);
    border-color: rgba(128, 128, 128, 0.35);
    cursor: not-allowed;
    pointer-events: auto;
  }

  .badge.disabled:hover,
  .badge.disabled:focus {
    background: rgba(128, 128, 128, 0.22);
    color: rgba(128, 128, 128, 1);
    border-color: rgba(128, 128, 128, 0.45);
    outline: none;
  }



  .badge[data-tooltip=""]:hover::after,
  .badge[data-tooltip=""]:focus::after,
  .badge[data-tooltip=""]:hover::before,
  .badge[data-tooltip=""]:focus::before {
    display: none;
  }

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
    font-weight: 500;
    white-space: nowrap;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.15s ease, transform 0.15s ease;
    box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    z-index: 30;
  }

  .badge::before {
    content: "";
    position: absolute;
    bottom: 140%;
    left: 50%;
    transform: translateX(-50%) translateY(100%) scale(0.8);
    border: 6px solid transparent;
    border-top-color: #A8EC7D;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.15s ease, transform 0.15s ease;
    z-index: 30;
  }

  .badge:hover::after,
  .badge:focus::after {
    opacity: 1;
    transform: translateX(-50%) scale(1);
  }

  .badge:hover::before,
  .badge:focus::before {
    opacity: 1;
    transform: translateX(-50%) translateY(100%) scale(1);
  }

  .badge.disabled::after {
    background-color: #3A3A3A;
    color: #F1F1F1;
  }

  .badge.disabled::before {
    border-top-color: #3A3A3A;
  }


  .badges-mobile {
    display: none;
    position: relative;
  }

  .badges-mobile summary {
    list-style: none;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    width: fit-content;
    font-size: 14px;
    font-weight: 600;
    border: 0.5px solid rgba(128,128,128,0.35);
    border-radius: 999px;
    padding: 4px 10px;
    background: #A8EC7D;
    color: #0B2F13;
    cursor: pointer;
    user-select: none;
  }

  .badges-mobile summary::-webkit-details-marker {
    display: none;
  }

  .badges-mobile summary .ti-chevron-down {
    transition: transform .15s ease;
  }

  .badges-mobile[open] summary .ti-chevron-down {
    transform: rotate(180deg);
  }

  .badges-mobile-list {
    position: absolute;
    left: 0;
    bottom: 34px;
    z-index: 40;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
    min-width: 220px;
    max-width: min(280px, 80vw);
    padding: 10px;
    border: 0.5px solid rgba(128,128,128,0.35);
    border-radius: 12px;
    background: #0B2F13;
    box-shadow: 0 10px 28px rgba(0,0,0,0.22);
  }

  .badges-mobile-list .badge {
    width: 100%;
    justify-content: flex-start;
    white-space: normal;
  }

  .badges-mobile-list .badge span {
    white-space: normal;
  }

 
  @container (max-width: 420px) {
    .nav-card.needs-menu .badges-desktop {
      display: none;
    }

    .nav-card.needs-menu .badges-mobile {
      display: block;
    }
  }


  
  @media (max-width: 520px) {
    .nav-card {
      height: auto;
      min-height: 260px;
      padding: 1.25rem 1.25rem;
    }

    .card-title {
      font-size: 22px;
    }

    .card-desc {
      font-size: 15px;
    }

    .badges-mobile-list {
      min-width: 200px;
      max-width: calc(100vw - 48px);
    }
  }
</style>
"""


def nav_card(title: str, icon: str, description: str, badges: list) -> str:
    badges_html = ""

    for b in badges:
        label = b["label"]
        tooltip = b.get("tooltip", "")
        disabled = b.get("disabled", False)

        if disabled:
            if not tooltip:
                tooltip = "Página em manutenção ou desenvolvimento."

            badges_html += f"""
            <span class="badge disabled" data-tooltip="{tooltip}">
              <span>{label}</span>
            </span>
            """
        else:
            badges_html += f"""
            <a class="badge" href="{b["url"]}" target="_self" data-tooltip="{tooltip}">
              <span>{label}</span>
            </a>
            """


    precisa_menu = len(badges) > 1 or any(len(b["label"]) > 24 for b in badges)
    menu_class = " needs-menu" if precisa_menu else ""

    return f"""
    <div class="nav-card{menu_class}">
      <div class="card-header">
        <i class="ti ti-{icon} card-icon"></i>
        <p class="card-title">{title}</p>
      </div>

      <p class="card-desc">{description}</p>

      <div class="card-divider"></div>

      <div class="badges-desktop">
        {badges_html}
      </div>

      <details class="badges-mobile">
        <summary>
          <span>Opções</span>
          <i class="ti ti-chevron-down"></i>
        </summary>

        <div class="badges-mobile-list">
          {badges_html}
        </div>
      </details>
    </div>
    """


# ── CSS DA PÁGINA ─────────────────────────────────────────────────────────────

st.html("""
<style>
    .block-container {
        padding-top: 4rem;
    }

    .st-key-meu-container {
        background-color: #0B2F13;
        border-radius: 8px;
        padding: 20px;
    }
</style>
""")


# Injeta o CSS dos cards uma única vez
st.html(_CSS_NAV_CARD)


# ── CABEÇALHO ─────────────────────────────────────────────────────────────────

with st.container(key="meu-container", horizontal=True):
    st.html("""
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
""")


st.space("small")


# ── CARDS DE NAVEGAÇÃO ────────────────────────────────────────────────────────

CARDS = [
    {
        "col": 0,
        "title": "Enquadramento",
        "icon": "scale",
        "description": "Informações sobre o enquadramento dos planos, fundos e limites operacionais à luz da política de investimentos vigente.",
        "badges": [
            {
                "label": "Planos",
                "url": "/enquadramento-planos",
                "tooltip": "Enquadramento segundo a CMN n° 4994 e P.I.",
            },
        ],
    },
    {
        "col": 1,
        "title": "Rentabilidade",
        "icon": "chart-line",
        "description": "Acompanhamento diário dos retornos dos planos.",
        "badges": [
            {
                "label": "Planos",
                "url": "/rentabilidade-planos",
                "tooltip": "Histórico e metas de rentabilidade",
            },
        ],
    },
    {
        "col": 2,
        "title": "Risco de Mercado",
        "icon": "chart-column",
        "description": "Apresentação dos Indicadores de Risco de Mercado dos planos e ativos da carteira.",
        "badges": [
            {
                "label": "Planos",
                "url": "/risco-mercado-planos",
                "tooltip": "Página em desenvolvimento.",
               
            },
            {
                "label": "Ativos",
                "url": "/risco-mercado-ativos",
                "tooltip": "Página em desenvolvimento.",
                "disabled": True,
            },
        ],
    },
    {
        "col": 0,
        "title": "Risco de Liquidez",
        "icon": "droplet",
        "description": "Apresentação dos Indicadores de Risco de Liquidez, fluxo de caixa e prazos de liquidação.",
        "badges": [
            {
                "label": "Fluxo de Caixa dos Planos",
                "url": "/risco-planos",
                "tooltip": "Página em desenvolvimento.",
                "disabled": True,
            },
            {
                "label": "Prazo de Liquidação dos Ativos",
                "url": "/risco-ativos",
                "tooltip": "Página em desenvolvimento.",
                "disabled": True,
            },
        ],
    },
    {
        "col": 1,
        "title": "Risco de Crédito",
        "icon": "credit-card",
        "description": "Apresentação do Risco de Crédito dos ativos da carteira, ratings e limites operacionais.",
        "badges": [
            {
                "label": "Limites Operacionais",
                "url": "/limites-operacionais",
                "tooltip": "Relatório de limites operacionais das instituições financeiras.",
            },
            {
                "label": "Fundos de Crédito Privado",
                "url": "/risco-planos",
                "tooltip": "Página em desenvolvimento.",
                "disabled": True,
            },
            {
                "label": "Rating dos Ativos",
                "url": "/risco-ativos",
                "tooltip": "Página em desenvolvimento.",
                "disabled": True,
            },
        ],
    },
]


cols = st.columns(3)

for card in CARDS:
    with cols[card["col"]]:
        st.html(
            nav_card(
                title=card["title"],
                icon=card["icon"],
                description=card["description"],
                badges=card["badges"],
            )
        )