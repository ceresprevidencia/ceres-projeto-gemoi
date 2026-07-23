import streamlit as st
from utils.queries.tickerh_rent_planos import buscar_dados
from utils.helpers import _NOMES_PLANOS 
import pandas as pd
import html

@st.cache_data(ttl='24h', show_time=True)
def carregar_dados() -> pd.DataFrame:
    """Carrega e cacheia o DataFrame principal por 1 hora."""
    return buscar_dados()

tickerh_rent_planos = buscar_dados()

st.set_page_config(initial_sidebar_state="collapsed", layout="wide")

# ── MANUTENÇÃO / CACHE ────────────────────────────────────────────────────────

if "mostrar_senha_cache" not in st.session_state:
    st.session_state["mostrar_senha_cache"] = False

with st.sidebar:
    with st.expander("Manutenção", expanded=False):
        st.caption("Use apenas se precisar forçar a atualização do app.")

        if st.button("Limpar cache", key="abrir_limpeza_cache"):
            st.session_state["mostrar_senha_cache"] = True

        if st.session_state["mostrar_senha_cache"]:
            senha_cache = st.text_input(
                "Digite a senha",
                type="password",
                key="senha_cache",
            )

            col_confirmar, col_cancelar = st.columns(2)

            with col_confirmar:
                if st.button(
                    "Confirmar",
                    type="primary",
                    use_container_width=True,
                    key="confirmar_limpeza_cache",
                ):
                    if senha_cache == "sucon2026":
                        st.cache_data.clear()
                        st.cache_resource.clear()
                        st.session_state["mostrar_senha_cache"] = False
                        st.success("Cache limpo com sucesso!")
                        st.rerun()
                    else:
                        st.error("Senha incorreta!")

            with col_cancelar:
                if st.button(
                    "Cancelar",
                    use_container_width=True,
                    key="cancelar_limpeza_cache",
                ):
                    st.session_state["mostrar_senha_cache"] = False
                    st.rerun()

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
    overflow: visible;
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
    overflow: visible;
    flex-shrink: 0;
  }

    .badge .ti {
      font-size: 16px;
      line-height: 1;
    }

    .badge.maintenance {
      background: #F2C94C;
      color: #1B1B1B;
      border-color: rgba(0, 0, 0, 0.18);
      cursor: not-allowed;
      pointer-events: auto;
    }

    .badge.maintenance:hover,
    .badge.maintenance:focus {
      background: #F2C94C;
      color: #1B1B1B;
      border-color: rgba(0, 0, 0, 0.18);
      outline: none;
    }

    .badge.maintenance::after {
      background-color: #1B1B1B;
      color: #F2C94C;
    }

    .badge.maintenance::before {
      border-top-color: #1B1B1B;
    }

  .badge span {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .badge:hover,
  .badge:focus {
   background: #0B2F13;      /* fundo ao passar o mouse */
   color: #A8EC7D;           /* texto ao passar o mouse */
   border-color: #A8EC7D;    /* borda ao passar o mouse */
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

  .badges-mobile-button {
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

  .badges-mobile-button:hover,
  .badges-mobile-button:focus {
    background: #0B2F13;
    color: #A8EC7D;
    border-color: #A8EC7D;
    outline: none;
  }

  .badges-mobile-button .ti-chevron-down {
    transition: transform .15s ease;
  }

  .badges-mobile:has(.badges-mobile-list:popover-open)
  .badges-mobile-button .ti-chevron-down {
    transform: rotate(180deg);
  }

  .badges-mobile-list {
    margin: 0;
    padding: 10px;
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
    min-width: 220px;
    max-width: min(280px, 80vw);
    border: 0.5px solid rgba(128,128,128,0.35);
    border-radius: 12px;
    background: #0B2F13;
    box-shadow: 0 10px 28px rgba(0,0,0,0.22);
    overflow: visible;
  }

  .badges-mobile-list:popover-open {
    display: flex;
    opacity: 1;
    transform: translateY(0);
    transition: opacity .15s ease, transform .15s ease;
  }

  @starting-style {
    .badges-mobile-list:popover-open {
      opacity: 0;
      transform: translateY(-5px);
    }
  }

  .badges-mobile-list .badge {
    width: 100%;
    justify-content: flex-start;
    white-space: normal;
    box-sizing: border-box;
  }

  .badges-mobile-list .badge span {
    white-space: normal;
  }

 
  /* O limite para trocar as badges pelo menu é definido por card. */


  
  .nav-card {
    margin-bottom: 1.5rem;
  }

  .nav-card:hover,
  .nav-card:focus-within {
    z-index: 50;
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
    """Monta o card e troca as badges por um menu apenas quando faltar espaço."""
    badges_html = ""

    for b in badges:
        label = html.escape(str(b["label"]))
        tooltip = html.escape(str(b.get("tooltip", "")), quote=True)
        maintenance = b.get("maintenance", False)
        disabled = b.get("disabled", False)

        if maintenance:
            if not tooltip:
                tooltip = "Página em manutenção."

            badges_html += f"""
            <span
              class="badge maintenance"
              data-tooltip="{tooltip}"
              title="{tooltip}"
              tabindex="0"
              aria-disabled="true"
            >
              <i class="ti ti-lock"></i>
              <span>{label}</span>
            </span>
            """
        elif disabled:
            if not tooltip:
                tooltip = "Página em manutenção ou desenvolvimento."

            badges_html += f"""
            <span
              class="badge disabled"
              data-tooltip="{tooltip}"
              title="{tooltip}"
              tabindex="0"
              aria-disabled="true"
            >
              <span>{label}</span>
            </span>
            """
        else:
            url = html.escape(str(b["url"]), quote=True)
            badges_html += f"""
            <a
              class="badge"
              href="{url}"
              target="_self"
              data-tooltip="{tooltip}"
              title="{tooltip}"
            >
              <span>{label}</span>
            </a>
            """

    # Aproxima a largura real das badges: texto + padding/borda + espaços entre elas.
    # O pequeno acréscimo evita que a última badge seja comprimida ou cortada.
    largura_badges = sum(max(54, len(str(b["label"])) * 7.8 + 24) for b in badges)
    largura_badges += max(0, len(badges) - 1) * 6 + 8
    limite_menu = int(largura_badges)

    card_id = f"nav-card-{abs(hash((title, tuple(b['label'] for b in badges))))}"
    menu_id = f"{card_id}-menu"

    return f"""
    <style>
      @container (max-width: {limite_menu}px) {{
        #{card_id} .badges-desktop {{
          display: none;
        }}

        #{card_id} .badges-mobile {{
          display: block;
        }}
      }}
    </style>

    <div class="nav-card" id="{card_id}">
      <div class="card-header">
        <i class="ti ti-{html.escape(icon, quote=True)} card-icon"></i>
        <p class="card-title">{html.escape(title)}</p>
      </div>

      <p class="card-desc">{html.escape(description)}</p>

      <div class="card-divider"></div>

      <div class="badges-desktop">
        {badges_html}
      </div>

      <div class="badges-mobile">
        <button
              "maintenance": True,
          type="button"
          class="badges-mobile-button"
          id="{menu_id}-button"
          popovertarget="{menu_id}"
          aria-label="Abrir opções de {html.escape(title, quote=True)}"
          style="anchor-name: --{menu_id};"
        >
          <span>Opções</span>
          <i class="ti ti-chevron-down"></i>
        </button>

        <div
          id="{menu_id}"
          class="badges-mobile-list"
          popover="auto"
          style="
            position: fixed;
            position-anchor: --{menu_id};
            position-area: bottom span-right;
            margin-top: 8px;
          "
        >
          {badges_html}
        </div>
      </div>
    </div>
    """


# ── CSS DA PÁGINA ─────────────────────────────────────────────────────────────

st.html("""
<style>
    .block-container {
        padding-top: 3.8rem;
        padding-left: 0;
        padding-right: 0;
    }

    .st-key-meu-container {
        background-color: #0B2F13;
        border-radius: 0;
        padding: 18px 20px;
        width: 100%;
        box-sizing: border-box;
        justify-content: center;
    }

    .st-key-conteudo {
        padding-left: 3rem;
        padding-right: 3rem;
    }

    .cabecalho-conteudo {
        width: 100%;
        text-align: center;
        padding: 12px 0 18px 0;
    }
</style>
""")

# Injeta o CSS dos cards uma única vez
st.html(_CSS_NAV_CARD)

# ── CABEÇALHO ─────────────────────────────────────────────────────────────────

with st.container(key="meu-container"):
    st.html("""
    <div class="cabecalho-conteudo">
        <p style="
            color:#FAFBEB;
            font-family:Figtree,sans-serif;
            font-size:42px;
            font-weight:400;
            margin:0;
            line-height:1;
        ">
            Bem-vindo ao
            <span style='
                color:#A8EC7D;
                font-family:"Source Serif 4",serif;
                font-style:italic;
                font-weight:600;
            '>
                Controle Ceres
            </span>
        </p>

        <p style="
            color:#FAFBEB;
            font-family:Figtree,sans-serif;
            font-size:16px;
            font-weight:400;
            margin:14px auto 0 auto;
            line-height:1.4;
            max-width:850px;
        ">
            Nesta página, você pode acessar os painéis produzidos pelas
            supervisões de monitoramento de investimentos, risco e
            <i>compliance</i>.
        </p>
    </div>
    """)

# Seleciona apenas as colunas necessárias.
dados_ticker = tickerh_rent_planos[
    ["TESOURARIA", "YTD"]
].copy()

dados_ticker['TESOURARIA'] = dados_ticker['TESOURARIA'].replace(_NOMES_PLANOS) 
# Limpa e converte os dados.
dados_ticker["TESOURARIA"] = (
    dados_ticker["TESOURARIA"]
    .astype("string")
    .str.strip()
)

dados_ticker["YTD"] = pd.to_numeric(
    dados_ticker["YTD"],
    errors="coerce",
)

dados_ticker = dados_ticker.dropna(
    subset=["TESOURARIA", "YTD"]
)

dados_ticker = dados_ticker[
    dados_ticker["TESOURARIA"] != ""
]

itens_ticker = []

for _, linha in dados_ticker.iterrows():
    nome_plano = html.escape(
        str(linha["TESOURARIA"])
    )

    rentabilidade = float(linha["YTD"])

    # Use esta multiplicação se YTD vier como 0.085 para representar 8,5%.
    rentabilidade_percentual = rentabilidade 

    # Caso YTD já venha como 8.5 para representar 8,5%,
    # substitua a linha acima por:
    # rentabilidade_percentual = rentabilidade

    rentabilidade_formatada = (
        f"{rentabilidade_percentual:,.2f}%"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

    if rentabilidade_percentual > 0:
        indicador = "▲"
        classe = "ticker-positivo"

    elif rentabilidade_percentual < 0:
        indicador = "▼"
        classe = "ticker-negativo"

    else:
        indicador = "●"
        classe = "ticker-neutro"

    itens_ticker.append(
        f"""
        <span class="ticker-item">
            {nome_plano}
            <span class="{classe}">
                {rentabilidade_formatada} {indicador}
            </span>
        </span>
        """
    )

# Duplica os itens para criar o efeito de loop contínuo.
conteudo_ticker = "".join(
    itens_ticker + itens_ticker
)

st.html(
    f"""
    <style>

        /* Remove apenas a margem externa do ticker, sem alterar os demais blocos. */
            .ticker-wrapper {{
                /* Compensa apenas o gap padrão entre o cabeçalho e o ticker. */
                margin-top: -1rem;
                margin-bottom: 2rem;
            }}

        .ticker-wrapper {{
            width: 100%;
            overflow: hidden;
            background-color: #F5F5F5;
            padding: 10px 0;
            box-sizing: border-box;
        }}

        .ticker-content {{
            display: inline-block;
            white-space: nowrap;
            animation: ticker 120s linear infinite;
        }}

        .ticker-wrapper:hover .ticker-content {{
            animation-play-state: paused;
        }}

        .ticker-item {{
            display: inline-block;
            padding: 0 28px;
            color: #000000;
            font-size: 14px;
            font-weight: 600;
            border-right: 1px solid #000000;
        }}

        .ticker-item span {{
            margin-left: 6px;
       
            font-size: 14px;
            font-weight: 600;
        }}

        .ticker-positivo {{
            color: #038216;
        }}

        .ticker-negativo {{
            color: #FF9A9A;
        }}

        .ticker-neutro {{
            color: #FAFBEB;
        }}

        @keyframes ticker {{
            0% {{
                transform: translateX(0);
            }}

            100% {{
                transform: translateX(-50%);
            }}
        }}
    </style>

    <div class="ticker-wrapper">
        <div class="ticker-content">
            {conteudo_ticker}
        </div>
    </div>
    """
)


with st.container(horizontal_alignment="center", gap=None, key="conteudo"):
    with st.container(width=1200):

      
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
                    #"tooltip": "Enquadramento segundo a CMN n° 4994 e P.I.",
                    "tooltip": "Em manutenção.",
                    "maintenance": True,
                  },
                  {
                    "label": "Fundos",
                    "url": "/enquadramento-fundos",
                    "tooltip": "Página em desenvolvimento.",
                    "disabled": True,
                  },
                  # Exemplo 1: em manutenção, com cadeado amarelo.
                  # {
                  #     "label": "Outra fase",
                  #     "url": "/enquadramento-outra-fase",
                  #     "tooltip": "Página em manutenção.",
                  #     "maintenance": True,
                  # },
                  # Exemplo 2: habilitado, com tooltip informativo.
                  # {
                  #     "label": "Nova fase",
                  #     "url": "/enquadramento-nova-fase",
                  #     "tooltip": "Enquadramento segundo a CMN n° 4994 e P.I.",
                  # },
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
            {
                "col": 2,
                "title": "Due Diligence",
                "icon": "file-check",
                "description": "Ferramenta de Due Diligence para avaliação de riscos e conformidade.",
                "badges": [
                    {
                        "label": "Gestoras",
                        "url": "/due-diligence-questionario",
                        "tooltip": "Página em desenvolvimento.",
                        "disabled": True,
                    },
                ],
            },
          
      ]


      cols = st.columns(3, gap="medium")

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