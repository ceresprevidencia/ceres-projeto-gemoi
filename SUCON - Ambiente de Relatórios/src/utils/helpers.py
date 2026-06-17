import pandas as pd
from datetime import date, timedelta
import streamlit as st

# ── FORMATAÇÃO ────────────────────────────────────────────────────────────────

def fmt_br(valor, decimais: int = 2) -> str:
    """Formata número para o padrão brasileiro (vírgula decimal, ponto de milhar)."""
    if pd.isna(valor) or valor == "-":
        return "—"
    try:
        # O formatador :.2f força exatamente o número de casas decimais
        # O formatador , (vírgula) coloca o separador de milhar americano (que trocaremos depois)
        formatado = f"{float(valor):,.{decimais}f}"
        return formatado.replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "—"

def formatar_percentual_br(valor) -> str:
    """Formata um percentual para o padrão brasileiro (ex: 12,50%)."""
    if pd.isna(valor) or valor == "-":
        return "—"
    try:
        # Aqui está o segredo: o :.2f garante as duas casas decimais como texto
        return f"{float(valor):.2f}".replace('.', ',') + "%"
    except (ValueError, TypeError):
        return "—"

# ── NOMES ─────────────────────────────────────────────────────────────────────

# Mapeamento de identificadores internos para nomes amigáveis dos planos
_NOMES_PLANOS = {
    "Ceres FlexCeres_CV":    "Ceres FlexCeres",
    "Epagri Saldado_BD":     "Epagri Saldado",
    "Epagri Básico_BD":      "Epagri Básico",
    "Epamig Básico_BD":      "Epamig Básico",
    "Embrapa FlexCeres_CV":  "Embrapa FlexCeres",
    "ABDI FlexCeres_CD":     "ABDI FlexCeres",
    "Cidasc FlexCeres_CV":   "Cidasc FlexCeres",
    "Epamig FlexCeres_CV":   "Epamig FlexCeres",
    "Emater DF FlexCeres_CV":"EmaterDF FlexCeres",
    "Ceres Básico_BD":       "Ceres Básico",
    "Emater MG Básico_BD":   "EmaterMG Básico",
    "Família Ceres_CD":      "Família Ceres",
    "Epagri FlexCeres_CV":   "Epagri FlexCeres",
    "Embrapa Básico_BD":     "Embrapa Básico",
    "Emater MG FlexCeres_CV":"EmaterMG FlexCeres",
    "Epamig Saldado_BD":     "Epamig Saldado",
    "Emater MG Saldado_BD":  "EmaterMG Saldado",
    "PGA":                   "PGA",
    "[CERES TOTAL]":         "Consolidado",
}

def nome_plano(valor_original: str) -> str:
    """Extrai a parte após 'Tesouraria=' (se existir) e mapeia para nome amigável."""
    chave = valor_original.split("=", 1)[-1] if "=" in valor_original else valor_original
    return _NOMES_PLANOS.get(chave, chave)


# ── LIMPEZA DE TEXTO ──────────────────────────────────────────────────────────

def limpar_texto(texto: str) -> str:
    """Remove o prefixo 'Art. XX - ' de descrições de regras."""
    return str(texto)[8:] if "Art." in texto else texto


def remove_grp(palavra: str) -> str:
    """Extrai o nome do grupo econômico após 'grupo=' em strings de agregação."""
    return palavra.split("=")[-1] if "grupo" in palavra.lower() else palavra


# ── CSS ───────────────────────────────────────────────────────────────────────

def get_css_responsivo() -> str:
    """
    CSS responsivo para o wrapper `.tabela-responsiva`.
    Deve ser injetado uma vez por página via st.markdown().
    """
    return """
    <style>
    .tabela-responsiva {
        width: 100%;
        overflow-x: auto;
        display: block;
    }
    .tabela-responsiva table {
        width: 100%;
        border-collapse: collapse;
    }
    .tabela-responsiva table td,
    .tabela-responsiva table th {
        padding: 12px;
        text-align: center;
        word-wrap: break-word;
        overflow-wrap: break-word;
        word-break: break-word;
    }
    @media (max-width: 1200px) {
        .tabela-responsiva table td,
        .tabela-responsiva table th { padding: 10px; font-size: 13px; }
    }
    @media (max-width: 768px) {
        .tabela-responsiva { font-size: 11px; }
        .tabela-responsiva table td,
        .tabela-responsiva table th { padding: 6px; }
    }
    @media (max-width: 480px) {
        .tabela-responsiva { font-size: 9px; }
        .tabela-responsiva table td,
        .tabela-responsiva table th { padding: 4px; }
    }
    </style>
    """


# ── TABELA HTML UNIFICADA ─────────────────────────────────────────────────────

# CSS compartilhado entre todas as tabelas HTML do sistema
_CSS_TABELA = """
<style>
    .tabela-custom-wrapper {
        overflow: hidden;
        width: 100%;
        border-radius: 10px;
    }

    /* Cabeçalho verde escuro */
    .th-custom {
        background-color: #0B2F13;
        color: #A8EC7D;
        display: grid;
        align-items: center;
        padding-left: 12px;
    }
    .th-custom div {
        padding: 12px;
        text-align: center;
        font-family: 'Figtree', sans-serif;
        font-size: 14px;
        word-break: break-word;
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 43px;
    }
    .th-custom div:first-child {
        justify-content: flex-start;
        padding-left: 20px;
        border-top-left-radius: 10px;
    }
    
    /* Modo: borda */
    .tabela-custom-wrapper.com-borda-inferior .row-custom:last-child {
        border-bottom: 14px solid #0B2F13;
    }

    /* Modo: ultima-linha */
    .tabela-custom-wrapper.ultima-linha-verde .row-custom:last-child {
        background-color: #0B2F13 !important;
        border-bottom: none;
    }

    .tabela-custom-wrapper.ultima-linha-verde .row-custom:last-child:hover {
        background-color: #0B2F13 !important;
    }

    .tabela-custom-wrapper.ultima-linha-verde .row-custom:last-child .col-custom {
        color: #FAFBEB !important;
        font-weight: 600;
    }

    /* Linhas de dados */
    .row-custom {
        display: grid;
        align-items: center;
        background-color: transparent;
        transition: background-color 0.15s ease;
        padding-left: 15px;
    }
    .row-custom:hover {
        background-color: rgba(11, 47, 19, 0.04);
    }


    /* Linha destacada (ex: desenquadrado) */
    .row-custom.destaque {
        background-color: #ffcccc !important;
    }
    .row-custom.destaque:hover {
        background-color: #ffb3b3 !important;
    }

    /* Células de dados */
    .col-custom {
        padding: 10px 14px;
        font-family: 'Figtree', sans-serif;
        font-size: 13px;
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 42px;
        word-break: break-word;
    }
    .col-custom:first-child {
        justify-content: flex-start;
        padding-left: 20px;
        font-weight: normal;
    }

    /* Responsividade */
    @media (max-width: 768px) {
        .th-custom div, .col-custom {
            font-size: 11px;
            padding: 8px;
            min-height: 35px;
        }
        .th-custom div:first-child, .col-custom:first-child {
            padding-left: 10px;
        }
    }
    @media (max-width: 480px) {
        .th-custom div, .col-custom {
            font-size: 9px;
            padding: 6px;
            min-height: 30px;
        }
    }
</style>
"""


def gerar_tabela_html(
    df: pd.DataFrame,
    nomes_colunas: dict = None,
    primeira_coluna_larga: bool = True,
    mask_destaque: pd.Series = None,
    formatar_valores: bool = True,
    borda_inferior="borda",
    rolagem: bool = False,
    altura_max: str = "420px",
) -> str:
    """
    Gera uma tabela HTML no padrão visual do sistema.

    Quando rolagem=False:
        - tabela fica expandida conforme o tamanho dos dados.

    Quando rolagem=True:
        - corpo da tabela recebe barra de rolagem;
        - cabeçalho fica congelado;
        - borda inferior fica congelada.
    """

    if nomes_colunas is None:
        nomes_colunas = {col: col for col in df.columns}

    primeira = "2fr" if primeira_coluna_larga else "1fr"
    resto = " ".join(["1fr"] * (len(df.columns) - 1))
    grid = f"{primeira} {resto}" if len(df.columns) > 1 else "1fr"

    classe_borda = _classe_borda_inferior(borda_inferior)

    html = _CSS_TABELA

    html += """
    <style>
        .tabela-scroll-body {
            overflow-y: auto;
            overflow-x: hidden;
        }

        .tabela-scroll-body::-webkit-scrollbar {
            width: 8px;
        }

        .tabela-scroll-body::-webkit-scrollbar-track {
            background: rgba(219, 208, 178, 0.20);
            border-radius: 999px;
        }

        .tabela-scroll-body::-webkit-scrollbar-thumb {
            background: rgba(11, 47, 19, 0.35);
            border-radius: 999px;
        }

        .tabela-scroll-body::-webkit-scrollbar-thumb:hover {
            background: rgba(11, 47, 19, 0.55);
        }

        .tabela-borda-final {
            height: 4px;
            background-color: #0B2F13;
            border-radius: 0 0 8px 8px;
        }

        .tabela-sem-borda-final {
            height: 0;
            background-color: transparent;
        }
    </style>
    """

    # Wrapper principal
    html += f'<div class="tabela-custom-wrapper {classe_borda}">'

    # Cabeçalho fora da área rolável
    html += f'<div class="th-custom" style="grid-template-columns:{grid};">'
    for col in df.columns:
        html += f'<div>{nomes_colunas.get(col, col)}</div>'
    html += '</div>'

    # Corpo com ou sem rolagem
    if rolagem:
        html += f'<div class="tabela-scroll-body" style="max-height:{altura_max};">'
    else:
        html += '<div>'

    # Linhas
    for idx, row in df.iterrows():
        classe_destaque = ""
        if mask_destaque is not None and idx in mask_destaque.index and mask_destaque.loc[idx]:
            classe_destaque = " destaque"

        html += f'<div class="row-custom{classe_destaque}" style="grid-template-columns:{grid};">'

        for col in df.columns:
            valor = row[col]

            if formatar_valores and isinstance(valor, (int, float)) and not pd.isna(valor):
                col_lower = col.lower()

                if "r$" in col_lower or "%" in col_lower:
                    valor_fmt = fmt_br(valor, 2)
                else:
                    valor_fmt = f"{valor:.2f}"
            else:
                valor_fmt = str(valor) if pd.notna(valor) else "—"

            html += f'<div class="col-custom">{valor_fmt}</div>'

        html += '</div>'

    html += '</div>'  # fecha corpo

    # Borda inferior congelada
    if borda_inferior == "borda":
        html += '<div class="tabela-borda-final"></div>'
    else:
        html += '<div class="tabela-sem-borda-final"></div>'

    html += '</div>'  # fecha wrapper

    return html

def gerar_tabela_estilizada(
    df,
    nomes_colunas=None,
    primeira_coluna_larga=True,
    borda_inferior="borda",
    rolagem: bool = False,
    altura_max: str = "420px",
) -> str:
    return gerar_tabela_html(
        df,
        nomes_colunas=nomes_colunas,
        primeira_coluna_larga=primeira_coluna_larga,
        borda_inferior=borda_inferior,
        rolagem=rolagem,
        altura_max=altura_max,
    )


def aplicar_destaque(
    df_exibir: pd.DataFrame,
    mask_desenquadrado: pd.Series,
    borda_inferior="borda",
    rolagem: bool = False,
    altura_max: str = "420px",
) -> str:
    return gerar_tabela_html(
        df_exibir,
        mask_destaque=mask_desenquadrado,
        formatar_valores=False,
        borda_inferior=borda_inferior,
        rolagem=rolagem,
        altura_max=altura_max,
    )
# ── UTILITÁRIOS DE DATA ───────────────────────────────────────────────────────

def primeiro_dia_util(ano: int) -> date:
    """Retorna o primeiro dia útil do ano, pulando fins de semana e 1º de janeiro."""
    feriados_fixos = {(1, 1)}
    dia = date(ano, 1, 1)
    while True:
        if dia.weekday() >= 5 or (dia.day, dia.month) in feriados_fixos:
            dia += timedelta(days=1)
            continue
        return dia
    



# CSS GLOBAL

def get_css_global():
    """
    CSS GLOBAL - Estrutura base do site
    Use no início de cada página.
    """
    return """
    <style>
     
        /* ============================================================================
           RESPONSIVE - TABLETS (≤ 1200px)
           ============================================================================ */
        @media (max-width: 1200px) {
            .th-custom div, .col-custom {
                padding: 10px;
                font-size: 13px;
                min-height: 38px;
            }

            .col-custom:first-child {
                padding-left: 15px;
            }
        }

        /* ============================================================================
           RESPONSIVE - MOBILE (≤ 768px)
           ============================================================================ */
        @media (max-width: 768px) {
            .th-custom div, .col-custom {
                padding: 8px;
                font-size: 11px;
                min-height: 35px;
            }

            .col-custom:first-child {
                padding-left: 10px;
            }
        }

        /* ============================================================================
           RESPONSIVE - SMALL MOBILE (≤ 480px)
           ============================================================================ */
        @media (max-width: 480px) {
            .th-custom div, .col-custom {
                padding: 6px;
                font-size: 9px;
                min-height: 32px;
            }

            .col-custom:first-child {
                padding-left: 6px;
            }
        }
    </style>
    """


_BORDA_INFERIOR_CLASSES = {
    "borda": "com-borda-inferior",
    "sem-borda": "sem-borda-inferior",
    "ultima-linha": "ultima-linha-verde",
}


def _normalizar_borda_inferior(borda_inferior="borda") -> str:
    if isinstance(borda_inferior, bool):
        return "borda" if borda_inferior else "sem-borda"

    if borda_inferior is None:
        return "borda"

    import unicodedata

    modo = str(borda_inferior).strip().lower()
    modo = "".join(
        char for char in unicodedata.normalize("NFKD", modo)
        if not unicodedata.combining(char)
    )
    modo = modo.replace("_", "-").replace(" ", "-")

    aliases = {
        "com-borda": "borda",
        "com-borda-inferior": "borda",
        "sem-borda-inferior": "sem-borda",
        "ultima": "ultima-linha",
        "ultima-linha-da-tabela": "ultima-linha",
        "ultima-linha-verde": "ultima-linha",
    }

    modo = aliases.get(modo, modo)

    if modo not in _BORDA_INFERIOR_CLASSES:
        opcoes = "borda, sem-borda, ultima-linha"
        raise ValueError(f"borda_inferior deve ser uma das opções: {opcoes}.")

    return modo


def _classe_borda_inferior(borda_inferior="borda") -> str:
    modo = _normalizar_borda_inferior(borda_inferior)
    return _BORDA_INFERIOR_CLASSES[modo]

def card_geral(titulo: str, valor: str, delta: str = None, help: str = None):
    """
    Renderiza um card de métrica seguindo o Manual de Marca Ceres.
    O delta e o help são opcionais. Se 'help' for informado, exibe um
    ícone 'i' no canto superior direito com tooltip ao passar o mouse.
    """

    # 1. Lógica do Delta Opcional
    delta_html = ""
    if delta:
        numero_delta = float(delta.replace(',', '.').replace('%', '').strip())

        if numero_delta > 0:
            cor_delta = "#016837"
            fundo_delta = "rgba(1, 104, 55, 0.12)"
            texto_delta = f"↑{delta}"
        elif numero_delta < 0:
            cor_delta = "#c0392b"
            fundo_delta = "rgba(192, 57, 43, 0.12)"
            texto_delta = f"↓{delta}"
        else:
            cor_delta = "#5a5a5a"
            fundo_delta = "rgba(90, 90, 90, 0.12)"
            texto_delta = delta

        delta_html = (
            f'<div style="display:inline-block; background-color:transparent; '
            f'color:{cor_delta}; font-size:12px; font-weight:400; '
           
            f'font-family: \'Figtree\', sans-serif;">{texto_delta}</div>'
        )

    # 2. Lógica do ícone de help (opcional)
    help_html = ""
    if help:
        help_html = f"""
        <div class="meu-card-help">
            ℹ
            <span class="meu-card-tooltip">{help}</span>
        </div>
        """

    html_final = f"""
    <style>
        .meu-card-custom {{
            background-color: rgba(219, 208, 178, 0.14);
            padding: 15px;
            border-radius: 8px;
            margin-top: 6px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.08);
            transition: all 0.3s ease-in-out;
            text-align: left;
            position: relative;
        }}
        .meu-card-custom:hover {{
            transform: translateY(-4px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.18);
        }}
        .meu-card-help {{
            position: absolute;
            top: 10px;
            right: 10px;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background-color: transparent;
            border: 1.5px solid #0B2F13;
            color: #0B2F13;
            font-size: 11px;
            font-weight: 700;
            font-style: italic;
            font-family: 'Figtree', sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
        }}
        .meu-card-tooltip {{
            visibility: hidden;
            opacity: 0;
            position: absolute;
            bottom: 130%;
            right: 0;
            background-color: #0B2F13;
            color: #FAFBEB;
            text-align: left;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 400;
            font-style: normal;
            font-family: 'Figtree', sans-serif;
            white-space: normal;
            width: 200px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
            transition: opacity 0.2s ease-in-out;
            z-index: 999;
        }}
        .meu-card-help:hover .meu-card-tooltip {{
            visibility: visible;
            opacity: 1;
        }}
    </style>
    <div class="meu-card-container">
        <div class="meu-card-custom">
            {help_html}
            <span style="color:#5a5a5a; font-size:16px;
                         padding:2px 8px; border-radius:6px; font-weight:900; display:inline-block;
                         font-family: 'Figtree', sans-serif;">
                {titulo}
            </span>
            <div style="color: #0b2f13; font-size: 30px; font-weight: 900;
                        margin-top: 8px; font-family: 'Figtree', sans-serif; text-align: center;">
                {valor}
            <span style="font-size: 12px; font-weight: 400; margin-left: 8px;">
                {delta_html}
            </span>
            </div>
        </div>
    </div>
    """

    st.html(html_final)




def formatar_numero(valor: float, prefixo: str = "", sufixo: str = "", decimais: int = 2) -> str:
    """
    Formata um número grande em formato abreviado: Mil, Mi (milhão) ou Bi (bilhão).

    Exemplos:
        formatar_numero(1_500_000_000) -> "1.5 Bi"
        formatar_numero(2_300_000)     -> "2.3 Mi"
        formatar_numero(8_400)         -> "8.4 Mil"
        formatar_numero(950)           -> "950"
        formatar_numero(1_500_000, prefixo="R$ ") -> "R$ 1.5 Mi"
    """
    valor_abs = abs(valor)
    sinal = "-" if valor < 0 else ""

    if valor_abs >= 1_000_000_000:
        numero = valor_abs / 1_000_000_000
        unidade = " Bi"
    elif valor_abs >= 1_000_000:
        numero = valor_abs / 1_000_000
        unidade = " Mi"
    elif valor_abs >= 1_000:
        numero = valor_abs / 1_000
        unidade = " Mil"
    else:
        numero = valor_abs
        unidade = ""

    texto_numero = f"{numero:.{decimais}f}".rstrip("0").rstrip(".")
    if texto_numero == "" or texto_numero == "-":
        texto_numero = "0"
    texto_numero = texto_numero.replace(".", ",")  # padrão numérico brasileiro

    return f"{sinal}{prefixo}{texto_numero}{unidade}{sufixo}"


import math


def _parse_percentual(valor):
    """
    Aceita valores como:
    0.085
    8.5
    "8,5%"
    "8.5%"
    """
    if isinstance(valor, str):
        valor = valor.replace('%', '').replace(',', '.').strip()
        valor = float(valor)

    valor = float(valor)

    # Se vier como 0.085, entende como 8,5%
    if abs(valor) <= 1:
        valor = valor * 100

    return valor

def card_rentabilidade_meta(
    titulo: str,
    rentabilidade_atual,
    rentabilidade_alvo,
    help: str = None
):
    """
    Renderiza um card de acompanhamento de rentabilidade versus meta.
    Versão enxuta com barra de progresso.
    """

    atual = _parse_percentual(rentabilidade_atual)
    alvo = _parse_percentual(rentabilidade_alvo)

    percentual_meta = 0 if alvo == 0 else atual / alvo
    percentual_meta_exibicao = percentual_meta * 100
    percentual_barra = max(0, min(percentual_meta_exibicao, 100))

    atual_fmt = f"{atual:.2f}%".replace('.', ',')
    alvo_fmt = f"{alvo:.2f}%".replace('.', ',')
    avanco_fmt = f"{percentual_meta_exibicao:.1f}%".replace('.', ',')

    if percentual_meta >= 1.00:
        cor_principal = "#016837"
    elif percentual_meta >= 0.90:
        cor_principal = "#2E7D32"
    elif percentual_meta >= 0.80:
        cor_principal = "#558B2F"
    elif percentual_meta >= 0.70:
        cor_principal = "#827717"
    elif percentual_meta >= 0.60:
        cor_principal = "#B7791F"
    elif percentual_meta >= 0.50:
        cor_principal = "#C98A1A"
    elif percentual_meta >= 0.40:
        cor_principal = "#D97706"
    elif percentual_meta >= 0.30:
        cor_principal = "#C05621"
    elif percentual_meta >= 0.20:
        cor_principal = "#B83227"
    elif percentual_meta >= 0.10:
        cor_principal = "#A93226"
    else:
        cor_principal = "#c0392b"

    help_html = ""
    if help:
        help_html = f"""
        <div class="rent-card-help">
            ℹ
            <span class="rent-card-tooltip">{help}</span>
        </div>
        """

    html_final = f"""
    <style>
        .rent-card-custom {{
            background-color: rgba(219, 208, 178, 0.14);
            padding: 15px;
            border-radius: 8px;
            margin-top: 6px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.08);
            transition: all 0.3s ease-in-out;
            text-align: left;
            position: relative;
            font-family: 'Figtree', sans-serif;
        }}

        .rent-card-custom:hover {{
            transform: translateY(-4px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.18);
        }}

        .rent-card-title {{
            color: #5a5a5a;
            font-size: 16px;
            padding: 2px 8px;
            border-radius: 6px;
            font-weight: 900;
            display: inline-block;
            font-family: 'Figtree', sans-serif;
        }}

        .rent-card-help {{
            position: absolute;
            top: 10px;
            right: 10px;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background-color: transparent;
            border: 1.5px solid #0B2F13;
            color: #0B2F13;
            font-size: 11px;
            font-weight: 700;
            font-style: italic;
            font-family: 'Figtree', sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
        }}

        .rent-card-tooltip {{
            visibility: hidden;
            opacity: 0;
            position: absolute;
            bottom: 130%;
            right: 0;
            background-color: #0B2F13;
            color: #FAFBEB;
            text-align: left;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 400;
            font-style: normal;
            font-family: 'Figtree', sans-serif;
            white-space: normal;
            width: 220px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
            transition: opacity 0.2s ease-in-out;
            z-index: 999;
        }}

        .rent-card-help:hover .rent-card-tooltip {{
            visibility: visible;
            opacity: 1;
        }}

        .rent-values-row {{
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            gap: 12px;
            margin-top: 12px;
            margin-bottom: 8px;
            font-family: 'Figtree', sans-serif;
        }}

        .rent-value-box {{
            display: flex;
            flex-direction: column;
            line-height: 1.05;
        }}

        .rent-value-box.right {{
            text-align: right;
        }}

        .rent-value-label {{
            color: #5a5a5a;
            font-size: 11px;
            font-weight: 400;
            margin-bottom: 3px;
            font-family: 'Figtree', sans-serif;
        }}

        .rent-main-value {{
            color: #0B2F13;
            font-size: 30px;
            font-weight: 900;
            font-family: 'Figtree', sans-serif;
            white-space: nowrap;
        }}

        .rent-target-value {{
            color: #5a5a5a;
            font-size: 16px;
            font-weight: 600;
            font-family: 'Figtree', sans-serif;
            white-space: nowrap;
        }}

        .rent-bar-area {{
            margin-top: 8px;
        }}

        .rent-bar-track {{
            position: relative;
            width: 100%;
            height: 14px;
            background-color: rgba(90, 90, 90, 0.16);
            border-radius: 999px;
            overflow: hidden;
        }}

        .rent-bar-fill {{
            height: 100%;
            border-radius: 999px;
            transition: width 0.4s ease-in-out;
        }}

        .rent-bar-footer {{
            display: flex;
            justify-content: space-between;
            color: #5a5a5a;
            font-size: 11px;
            margin-top: 5px;
            font-family: 'Figtree', sans-serif;
        }}
    </style>

    <div class="rent-card-container">
        <div class="rent-card-custom">
            {help_html}

            <span class="rent-card-title">
                {titulo}
            </span>

            <div class="rent-values-row">
                <div class="rent-value-box">
                    <span class="rent-value-label">Atual</span>
                    <span class="rent-main-value">{atual_fmt}</span>
                </div>

                <div class="rent-value-box right">
                    <span class="rent-value-label">Projetada</span>
                    <span class="rent-target-value">{alvo_fmt}</span>
                </div>
            </div>

            <div class="rent-bar-area">
                <div class="rent-bar-track">
                    <div class="rent-bar-fill"
                         style="width:{percentual_barra:.2f}%; background-color:{cor_principal};">
                    </div>
                
                </div>

                <div class="rent-bar-footer">
                    <span>0%</span>
                    <span>{avanco_fmt} da meta</span>
                </div>
            </div>
        </div>
    </div>
    """

    st.html(html_final)



def card_segmento_rentabilidade(
    segmento: str,
    rentabilidade_atual,
    rentabilidade_alvo,
    posicao,
    posicao_pct,
    mtd,
    m12,
    cor_segmento: str = "#016837",
    help: str = None
):
    """
    Renderiza um card de segmento com:
    - Nome do segmento
    - Rentabilidade atual
    - Rentabilidade alvo/projetada
    - Posição
    - Posição %
    - MTD
    - 12 Meses
    - Barra de avanço contra a meta

    A cor do segmento é aplicada inline para evitar conflito de CSS
    quando vários cards são renderizados na mesma tela.
    """

    atual = _parse_percentual(rentabilidade_atual)
    alvo = _parse_percentual(rentabilidade_alvo)
    mtd_valor = _parse_percentual(mtd)
    m12_valor = _parse_percentual(m12)
    posicao_pct_valor = _parse_percentual(posicao_pct)

    percentual_meta = 0 if alvo == 0 else atual / alvo
    percentual_meta_exibicao = percentual_meta * 100
    percentual_barra = max(0, min(percentual_meta_exibicao, 100))

    atual_fmt = f"{atual:.2f}%".replace('.', ',')
    alvo_fmt = f"{alvo:.2f}%".replace('.', ',')
    avanco_fmt = f"{percentual_meta_exibicao:.1f}%".replace('.', ',')
    posicao_pct_fmt = f"{posicao_pct_valor:.2f}%".replace('.', ',')
    mtd_fmt = f"{mtd_valor:.2f}%".replace('.', ',')
    m12_fmt = f"{m12_valor:.2f}%".replace('.', ',')

    if isinstance(posicao, (int, float)):
        posicao_fmt = f"R$ {posicao:,.2f}"
        posicao_fmt = (
            posicao_fmt
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
    else:
        posicao_fmt = str(posicao)

    if percentual_meta >= 1.00:
        cor_principal = "#016837"
    elif percentual_meta >= 0.90:
        cor_principal = "#2E7D32"
    elif percentual_meta >= 0.80:
        cor_principal = "#558B2F"
    elif percentual_meta >= 0.70:
        cor_principal = "#827717"
    elif percentual_meta >= 0.60:
        cor_principal = "#B7791F"
    elif percentual_meta >= 0.50:
        cor_principal = "#C98A1A"
    elif percentual_meta >= 0.40:
        cor_principal = "#D97706"
    elif percentual_meta >= 0.30:
        cor_principal = "#C05621"
    elif percentual_meta >= 0.20:
        cor_principal = "#B83227"
    elif percentual_meta >= 0.10:
        cor_principal = "#A93226"
    else:
        cor_principal = "#c0392b"

    help_html = ""
    if help:
        help_html = f"""
        <div class="seg-card-help">
            ℹ
            <span class="seg-card-tooltip">{help}</span>
        </div>
        """

    html_final = f"""
    <style>
        .seg-card-custom {{
            background-color: rgba(219, 208, 178, 0.14);
            padding: 15px 15px 14px 17px;
            border-radius: 10px;
            margin-top: 6px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.08);
            transition: all 0.3s ease-in-out;
            text-align: left;
            position: relative;
            font-family: 'Figtree', sans-serif;
            overflow: hidden;
        }}

        .seg-card-custom:hover {{
            transform: translateY(-4px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.18);
        }}

        .seg-color-bar {{
            position: absolute;
            left: 0;
            top: 0;
            width: 5px;
            height: 100%;
        }}

        .seg-card-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            padding-right: 22px;
        }}

        .seg-card-title-wrap {{
            display: flex;
            align-items: center;
            gap: 8px;
            min-width: 0;
        }}

        .seg-color-dot {{
            width: 10px;
            height: 10px;
            min-width: 10px;
            border-radius: 999px;
        }}

        .seg-card-title {{
            color: #5a5a5a;
            font-size: 16px;
            font-weight: 900;
            font-family: 'Figtree', sans-serif;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .seg-card-help {{
            position: absolute;
            top: 10px;
            right: 10px;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background-color: transparent;
            border: 1.5px solid #0B2F13;
            color: #0B2F13;
            font-size: 11px;
            font-weight: 700;
            font-style: italic;
            font-family: 'Figtree', sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
        }}

        .seg-card-tooltip {{
            visibility: hidden;
            opacity: 0;
            position: absolute;
            bottom: 130%;
            right: 0;
            background-color: #0B2F13;
            color: #FAFBEB;
            text-align: left;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 400;
            font-style: normal;
            font-family: 'Figtree', sans-serif;
            white-space: normal;
            width: 220px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
            transition: opacity 0.2s ease-in-out;
            z-index: 999;
        }}

        .seg-card-help:hover .seg-card-tooltip {{
            visibility: visible;
            opacity: 1;
        }}

        .seg-values-row {{
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            gap: 12px;
            margin-top: 14px;
            margin-bottom: 10px;
        }}

        .seg-value-box {{
            display: flex;
            flex-direction: column;
            line-height: 1.05;
        }}

        .seg-value-box.right {{
            text-align: right;
        }}

        .seg-value-label {{
            color: #5a5a5a;
            font-size: 12px;
            font-weight: 400;
            margin-bottom: 3px;
            font-family: 'Figtree', sans-serif;
        }}

        .seg-main-value {{
            color: #0B2F13;
            font-size: 30px;
            font-weight: 900;
            font-family: 'Figtree', sans-serif;
            white-space: nowrap;
        }}

        .seg-target-value {{
            color: #5a5a5a;
            font-size: 18px;
            font-weight: 600;
            font-family: 'Figtree', sans-serif;
            white-space: nowrap;
        }}

        .seg-position-row {{
            display: flex;
            justify-content: space-between;
            gap: 10px;
            margin-top: 8px;
            padding: 9px 10px;
            border-radius: 8px;
            background-color: rgba(250, 251, 235, 0.55);
          
        }}

        .seg-position-item {{
            display: flex;
            flex-direction: column;
            line-height: 1.1;
        }}

        .seg-position-item.right {{
            text-align: right;
        }}

        .seg-small-label {{
            color: #5a5a5a;
            font-size: 11px;
            font-weight: 600;
            margin-bottom: 4px;
            font-family: 'Figtree', sans-serif;
        }}

        .seg-position-value {{
            color: #0B2F13;
            font-size: 14px;
            font-weight: 600;
            font-family: 'Figtree', sans-serif;
            white-space: nowrap;
        }}

        .seg-bar-area {{
            margin-top: 12px;
        }}

        .seg-bar-track {{
            position: relative;
            width: 100%;
            height: 14px;
            background-color: rgba(90, 90, 90, 0.16);
            border-radius: 999px;
            overflow: hidden;
        }}

        .seg-bar-fill {{
            height: 100%;
            border-radius: 999px;
            transition: width 0.4s ease-in-out;
        }}

        .seg-bar-footer {{
            display: flex;
            justify-content: space-between;
            color: #5a5a5a;
            font-size: 11px;
            margin-top: 5px;
            font-family: 'Figtree', sans-serif;
        }}

        .seg-period-row {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-top: 12px;
        }}

        .seg-period-box {{
            padding: 8px 10px;
            border-radius: 8px;
            background-color: transparent;
    
        }}

        .seg-period-label {{
            color: #5a5a5a;
            font-size: 11px;
            font-weight: 700;
            font-family: 'Figtree', sans-serif;
            margin-bottom: 4px;
        }}

        .seg-period-value {{
            color: #0B2F13;
            font-size: 16px;
            font-weight: 900;
            font-family: 'Figtree', sans-serif;
        }}
    </style>

    <div class="seg-card-container">
        <div class="seg-card-custom">

            <div class="seg-color-bar" style="background:{cor_segmento};"></div>

            {help_html}

            <div class="seg-card-header">
                <div class="seg-card-title-wrap">
                    <span class="seg-color-dot"
                          style="background-color:{cor_segmento}; box-shadow:0 0 0 4px {cor_segmento}22;">
                    </span>
                    <span class="seg-card-title">{segmento}</span>
                </div>
            </div>

            <div class="seg-values-row">
                <div class="seg-value-box">
                    <span class="seg-value-label">YTD</span>
                    <span class="seg-main-value">{atual_fmt}</span>
                </div>

                <div class="seg-value-box right">
                    <span class="seg-value-label">Projetada</span>
                    <span class="seg-target-value">{alvo_fmt}</span>
                </div>
            </div>

            <div class="seg-position-row">
                <div class="seg-position-item">
                    <span class="seg-small-label">Posição</span>
                    <span class="seg-position-value">{posicao_fmt}</span>
                </div>

                <div class="seg-position-item right">
                    <span class="seg-small-label">%</span>
                    <span class="seg-position-value">{posicao_pct_fmt}</span>
                </div>
            </div>

            <div class="seg-period-row">
                <div class="seg-period-box">
                    <div class="seg-period-label">MTD</div>
                    <div class="seg-period-value">{mtd_fmt}</div>
                </div>

                <div class="seg-period-box">
                    <div class="seg-period-label">12 Meses</div>
                    <div class="seg-period-value">{m12_fmt}</div>
                </div>
            </div>

            <div class="seg-bar-area">
                <div class="seg-bar-track">
                    <div class="seg-bar-fill"
                         style="width:{percentual_barra:.2f}%; background-color:{cor_principal};">
                    </div>
                </div>

                <div class="seg-bar-footer">
                    <span>0%</span>
                    <span>{avanco_fmt} da meta</span>
                </div>
            </div>

            
        </div>
    </div>
    """

    st.html(html_final)




def card_segmento_rentabilidade_sem_projetada(
    segmento: str,
    rentabilidade_atual,
    posicao,
    posicao_pct,
    mtd,
    m12,
    cor_segmento: str = "#016837",
    help: str = None
):
    """
    Renderiza um card de segmento com:
    - Nome do segmento
    - Rentabilidade atual
    - Posição
    - Posição %
    - MTD
    - 12 Meses

    A cor do segmento é aplicada inline para evitar conflito de CSS
    quando vários cards são renderizados na mesma tela.
    """

    atual = _parse_percentual(rentabilidade_atual)
    mtd_valor = _parse_percentual(mtd)
    m12_valor = _parse_percentual(m12)
    posicao_pct_valor = _parse_percentual(posicao_pct)

    atual_fmt = f"{atual:.2f}%".replace('.', ',')
    mtd_fmt = f"{mtd_valor:.2f}%".replace('.', ',')
    m12_fmt = f"{m12_valor:.2f}%".replace('.', ',')
    posicao_pct_fmt = f"{posicao_pct_valor:.2f}%".replace('.', ',')

    if isinstance(posicao, (int, float)):
        posicao_fmt = f"R$ {posicao:,.2f}"
        posicao_fmt = (
            posicao_fmt
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
    else:
        posicao_fmt = str(posicao)

    help_html = ""
    if help:
        help_html = f"""
        <div class="seg-card-help">
            ℹ
            <span class="seg-card-tooltip">{help}</span>
        </div>
        """

    html_final = f"""
    <style>
        .seg-card-custom {{
            background-color: rgba(219, 208, 178, 0.14);
            padding: 15px 15px 14px 17px;
            border-radius: 10px;
            margin-top: 6px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.08);
            transition: all 0.3s ease-in-out;
            text-align: left;
            position: relative;
            font-family: 'Figtree', sans-serif;
            overflow: hidden;
        }}

        .seg-card-custom:hover {{
            transform: translateY(-4px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.18);
        }}

        .seg-color-bar {{
            position: absolute;
            left: 0;
            top: 0;
            width: 5px;
            height: 100%;
        }}

        .seg-card-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            padding-right: 22px;
        }}

        .seg-card-title-wrap {{
            display: flex;
            align-items: center;
            gap: 8px;
            min-width: 0;
        }}

        .seg-color-dot {{
            width: 10px;
            height: 10px;
            min-width: 10px;
            border-radius: 999px;
        }}

        .seg-card-title {{
            color: #5a5a5a;
            font-size: 16px;
            font-weight: 900;
            font-family: 'Figtree', sans-serif;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .seg-card-help {{
            position: absolute;
            top: 10px;
            right: 10px;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background-color: transparent;
            border: 1.5px solid #0B2F13;
            color: #0B2F13;
            font-size: 11px;
            font-weight: 700;
            font-style: italic;
            font-family: 'Figtree', sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
        }}

        .seg-card-tooltip {{
            visibility: hidden;
            opacity: 0;
            position: absolute;
            bottom: 130%;
            right: 0;
            background-color: #0B2F13;
            color: #FAFBEB;
            text-align: left;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 400;
            font-style: normal;
            font-family: 'Figtree', sans-serif;
            white-space: normal;
            width: 220px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
            transition: opacity 0.2s ease-in-out;
            z-index: 999;
        }}

        .seg-card-help:hover .seg-card-tooltip {{
            visibility: visible;
            opacity: 1;
        }}

        .seg-main-area {{
            margin-top: 14px;
            margin-bottom: 10px;
        }}

        .seg-value-label {{
            color: #5a5a5a;
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 3px;
            font-family: 'Figtree', sans-serif;
        }}

        .seg-main-value {{
            color: #0B2F13;
            font-size: 32px;
            font-weight: 900;
            font-family: 'Figtree', sans-serif;
            white-space: nowrap;
            line-height: 1.05;
        }}

        .seg-position-row {{
            display: flex;
            justify-content: space-between;
            gap: 10px;
            margin-top: 8px;
            padding: 9px 10px;
            border-radius: 8px;
            background-color: rgba(250, 251, 235, 0.55);
        
        }}

        .seg-position-item {{
            display: flex;
            flex-direction: column;
            line-height: 1.1;
        }}

        .seg-position-item.right {{
            text-align: right;
        }}

        .seg-small-label {{
            color: #5a5a5a;
            font-size: 11px;
            font-weight: 600;
            margin-bottom: 4px;
            font-family: 'Figtree', sans-serif;
        }}

        .seg-position-value {{
            color: #0B2F13;
            font-size: 14px;
            font-weight: 900;
            font-family: 'Figtree', sans-serif;
            white-space: nowrap;
        }}

        .seg-period-row {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-top: 12px;
        }}

        .seg-period-box {{
            padding: 8px 10px;
            border-radius: 8px;
            background-color: transparent;
        }}

        .seg-period-label {{
            color: #5a5a5a;
            font-size: 11px;
            font-weight: 700;
            font-family: 'Figtree', sans-serif;
            margin-bottom: 4px;
        }}

        .seg-period-value {{
            color: #0B2F13;
            font-size: 16px;
            font-weight: 900;
            font-family: 'Figtree', sans-serif;
        }}
    </style>

    <div class="seg-card-container">
        <div class="seg-card-custom">

            <div class="seg-color-bar" style="background:{cor_segmento};"></div>

            {help_html}

            <div class="seg-card-header">
                <div class="seg-card-title-wrap">
                    <span class="seg-color-dot"
                          style="background-color:{cor_segmento}; box-shadow:0 0 0 4px {cor_segmento}22;">
                    </span>
                    <span class="seg-card-title">{segmento}</span>
                </div>
            </div>

            <div class="seg-main-area">
                <div class="seg-value-label">YTD</div>
                <div class="seg-main-value">{atual_fmt}</div>
            </div>

            <div class="seg-position-row">
                <div class="seg-position-item">
                    <span class="seg-small-label">Posição</span>
                    <span class="seg-position-value">{posicao_fmt}</span>
                </div>

                <div class="seg-position-item right">
                    <span class="seg-small-label">%</span>
                    <span class="seg-position-value">{posicao_pct_fmt}</span>
                </div>
            </div>

            <div class="seg-period-row">
                <div class="seg-period-box">
                    <div class="seg-period-label">MTD</div>
                    <div class="seg-period-value">{mtd_fmt}</div>
                </div>

                <div class="seg-period-box">
                    <div class="seg-period-label">12 Meses</div>
                    <div class="seg-period-value">{m12_fmt}</div>
                </div>
            </div>
        </div>
    </div>
    """

    st.html(html_final)


def de_para_produto(prod):
    """
    Faz o de/para do nome do produto.

    Regras:
    - Primeiro busca trechos contidos no texto, como códigos C000... e NTNB_...
    - Depois busca correspondência exata.
    - Se não encontrar correspondência, retorna o valor original.
    """

    if prod is None:
        return prod

    prod_str = str(prod).strip()

    mapa_contains = {
        # Produtos que contêm código Cxxxxxxxxxx
        "C0000213691": "4UM Small Caps FIA",
        "C0000194425": "Agrociência FIF Ações",
        "C0000272493": "BB Previd. Ref. DI LP Perfil FICFI",
        "C0000071171": "Bradesco FIRF Ref. DI Premium",
        "C0000698733": "Chapada Diamantina FIF",
        "C0000700606": "Chapada dos Guimarães FICFIM",
        "C0000602418": "Chapada dos Veadeiros FIF Ações",
        "C0000214019": "Guepardo Institucional FIC FIA",
        "C0000529478": "Trigono Flagship 60 Small Caps FICFIA",
        "C0000267066": "Eros FIF Multimercado CP",
        "C0000020435": "Itaú Institucional RF Ref. DI FIF",
        "C0000603384": "Oceana Serra da Capivara FIF Ações",
        "C0000331031": "Safra Cap. Market Prem. FICFI RF Ref. DI CP",
        "C0000289191": "Santander Ações Dividendos FICFI",
        "C0000604828": "Serra do Cipó FIF Ações",
        "C0000605859": "Tijuca FIF Ações",

        # NTN-B
        "NTNB_15/05/2033": "NTN-B 2033",
        "NTNB_15/05/2035": "NTN-B 2035",
        "NTNB_15/05/2045": "NTN-B 2045",
        "NTNB_15/05/2055": "NTN-B 2055",
        "NTNB_15/08/2026": "NTN-B 2026",
        "NTNB_15/08/2028": "NTN-B 2028",
        "NTNB_15/08/2030": "NTN-B 2030",
        "NTNB_15/08/2032": "NTN-B 2032",
        "NTNB_15/08/2040": "NTN-B 2040",
        "NTNB_15/08/2050": "NTN-B 2050",
        "NTNB_15/08/2060": "NTN-B 2060",

        # NTN-C
        "NTNC_01/01/2031": "NTN-C 2031",
    }

    mapa_exato = {
        "ABDI FlexCeres_CD_Emprestimos": "Empréstimos",
        "CENESP (BLOCO C)": "CENESP (BLOCO C)",
        "CENESP (BLOCO J)": "CENESP (BLOCO J)",
        "Ceres Básico_BD_Emprestimos": "Empréstimos Ceres Básico",
        "Ceres Básico_BD_Financiamentos": "Financiamento Imobiliário Ceres Básico",
        "Ceres FlexCeres_CV_Emprestimos": "Empréstimos Ceres FlexCeres",
        "Cidasc FlexCeres_CV_Emprestimos": "Empréstimos",
        "CORPORATE FINANCIAL CENTER (303)": "Corporate Financial Center (303)",
        "CORPORATE FINANCIAL CENTER (304)": "Corporate Financial Center (304)",
        "ED. JOSÉ GUERRA": "Ed. José Guerra",
        "EDIFICIO CERES": "Ed. Ceres",

        "Emater DF FlexCeres_CV_Emprestimos": "Empréstimos Emater-DF FlexCeres",
        "Emater MG Básico_BD_Emprestimos": "Empréstimos Emater-MG Básico",
        "Emater MG Básico_BD_Financiamentos": "Financiamento Imobiliário Emater-MG Básico",
        "Emater MG FlexCeres_CV_Emprestimos": "Empréstimos Emater-MG FlexCeres",
        "Emater MG Saldado_BD_Emprestimos": "Empréstimos Emater-MG Saldado",
        "Emater MG Saldado_BD_Financiamentos": "Financiamento Imobiliário Emater-MG Saldado",

        "Embrapa Básico_BD_Emprestimos": "Empréstimos Embrapa-Básico",
        "Embrapa Básico_BD_Financiamentos": "Financiamento Imobiliário Embrapa Básico",
        "Embrapa FlexCeres_CV_Emprestimos": "Empréstimos Embrapa FlexCeres",

        "Epagri Básico_BD_Emprestimos": "Empréstimos Epagri Básico",
        "Epagri Básico_BD_Financiamentos": "Financiamento Imobiliário Epagri Básico",
        "Epagri FlexCeres_CV_Emprestimos": "Empréstimos Epagri FlexCeres",
        "Epagri Saldado_BD_Emprestimos": "Empréstimos Epagri Saldado",
        "Epagri Saldado_BD_Financiamentos": "Financiamento Imobiliário Epagri Saldado",

        "Epamig Básico_BD_Emprestimos": "Empréstimos Epamig Básico",
        "Epamig Básico_BD_Financiamentos": "Financiamento Imobiliário Epamig Básico",
        "Epamig FlexCeres_CV_Emprestimos": "Empréstimos Epamig FlexCeres",
        "Epamig Saldado_BD_Emprestimos": "Empréstimos Epamig Saldado",
        "Epamig Saldado_BD_Financiamentos": "Financiamento Imobiliário Epamig Saldado",

        "FCAP3*": "FCAP3",
        "RB CAPITAL DESENV RESIDENCIAL II FII": "FII RB Capital Des. Residencial II",
        "SHOPPING CONJUNTO NACIONAL": "Shopping Conjunto Nacional",
        "SHOPPING RECIFE": "Shopping Recife",
    }

    for trecho, nome_final in mapa_contains.items():
        if trecho in prod_str:
            return nome_final

    return mapa_exato.get(prod_str, prod_str)