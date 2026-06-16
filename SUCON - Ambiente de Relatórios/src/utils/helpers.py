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
) -> str:

    """
    Gera uma tabela HTML no padrão visual do sistema (cabeçalho verde escuro,
    hover suave, bordas arredondadas).

    Parâmetros
    ----------
    df : pd.DataFrame
        Dados a exibir.
    nomes_colunas : dict, opcional
        Mapeamento {coluna_interna: label_exibido}. Se omitido, usa os nomes do df.
    primeira_coluna_larga : bool
        Se True, a primeira coluna recebe proporção 2fr; demais, 1fr.
    mask_destaque : pd.Series (bool), opcional
        Série booleana alinhada ao índice do df. Linhas True recebem fundo vermelho claro.
        Use para marcar linhas "Desenquadrado" ou qualquer outro destaque de atenção.
    formatar_valores : bool
        Se True, formata automaticamente números com fmt_br(). Desative se os valores
        já vierem pré-formatados como string.

    borda_inferior : bool
        Se True, exibe a borda inferior verde na última linha da tabela.
        Se False, remove essa borda.

    Retorna
    -------
    str : HTML completo da tabela, pronto para st.html().
    """
    if nomes_colunas is None:
        nomes_colunas = {col: col for col in df.columns}

    # Monta o grid CSS dinamicamente
    primeira = "2fr" if primeira_coluna_larga else "1fr"
    resto    = " ".join(["1fr"] * (len(df.columns) - 1))
    grid     = f"{primeira} {resto}" if len(df.columns) > 1 else "1fr"




    classe_borda = _classe_borda_inferior(borda_inferior)

    html = _CSS_TABELA
    html += f'<div class="tabela-custom-wrapper {classe_borda}">'



    # Cabeçalho
    html += f'<div class="th-custom" style="grid-template-columns:{grid};">'
    for col in df.columns:
        html += f'<div>{nomes_colunas.get(col, col)}</div>'
    html += '</div>'

    # Linhas
    for idx, row in df.iterrows():
        # Aplica classe de destaque se a máscara indicar
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

    html += '</div>'
    return html


# Aliases de compatibilidade — mantidos para não quebrar chamadas existentes
def gerar_tabela_estilizada(
    df,
    nomes_colunas=None,
    primeira_coluna_larga=True,
    borda_inferior="borda",
) -> str:
    return gerar_tabela_html(
        df,
        nomes_colunas=nomes_colunas,
        primeira_coluna_larga=primeira_coluna_larga,
        borda_inferior=borda_inferior,
    )

def aplicar_destaque(
    df_exibir: pd.DataFrame,
    mask_desenquadrado: pd.Series,
    borda_inferior="borda",
) -> str:
    return gerar_tabela_html(
        df_exibir,
        mask_destaque=mask_desenquadrado,
        formatar_valores=False,
        borda_inferior=borda_inferior,
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


import streamlit as st
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
    tipo: str = "barra",
    help: str = None,
    mostrar_status: bool = True
):
    """
    Renderiza um card de acompanhamento de rentabilidade versus meta.

    Parâmetros:
    - titulo: título do card
    - rentabilidade_atual: rentabilidade atual. Ex: 8.5, "8,5%" ou 0.085
    - rentabilidade_alvo: rentabilidade alvo. Ex: 10, "10%" ou 0.10
    - tipo: "barra" ou "velocimetro"
    - help: tooltip opcional
    - mostrar_status: exibe texto de atingimento da meta
    """

    atual = _parse_percentual(rentabilidade_atual)
    alvo = _parse_percentual(rentabilidade_alvo)

    if alvo == 0:
        percentual_meta = 0
    else:
        percentual_meta = atual / alvo

    percentual_meta_exibicao = percentual_meta * 100
    percentual_barra = max(0, min(percentual_meta_exibicao, 100))

    atual_fmt = f"{atual:.2f}%".replace('.', ',')
    alvo_fmt = f"{alvo:.2f}%".replace('.', ',')
    atingimento_fmt = f"{percentual_meta_exibicao:.1f}%".replace('.', ',')

    if percentual_meta >= 1:
        cor_principal = "#016837"
        cor_fundo = "rgba(1, 104, 55, 0.14)"
        status = "Meta atingida"
    elif percentual_meta >= 0.85:
        cor_principal = "#B7791F"
        cor_fundo = "rgba(183, 121, 31, 0.14)"
        status = "Próximo da meta"
    else:
        cor_principal = "#c0392b"
        cor_fundo = "rgba(192, 57, 43, 0.14)"
        status = "Abaixo da meta"

    help_html = ""
    if help:
        help_html = f"""
        <div class="rent-card-help">
            ℹ
            <span class="rent-card-tooltip">{help}</span>
        </div>
        """

    status_html = ""
    if mostrar_status:
        status_html = f"""
        <div class="rent-status" style="color:{cor_principal}; background-color:{cor_fundo};">
            {status} · {atingimento_fmt} do alvo
        </div>
        """

    if tipo.lower() == "velocimetro":
        # Escala visual: até 130% da meta para permitir ultrapassar o alvo.
        escala_max = max(alvo * 1.30, atual, 1)
        proporcao_gauge = max(0, min(atual / escala_max, 1))

        # Ângulo do ponteiro no semicírculo: 180 graus à esquerda, 0 graus à direita
        angulo = 180 - (proporcao_gauge * 180)
        rad = math.radians(angulo)

        cx, cy, r = 130, 118, 82
        x2 = cx + r * math.cos(rad)
        y2 = cy - r * math.sin(rad)

        # Marcador da meta
        proporcao_alvo = max(0, min(alvo / escala_max, 1))
        angulo_alvo = 180 - (proporcao_alvo * 180)
        rad_alvo = math.radians(angulo_alvo)

        x_meta_1 = cx + (r - 10) * math.cos(rad_alvo)
        y_meta_1 = cy - (r - 10) * math.sin(rad_alvo)
        x_meta_2 = cx + (r + 8) * math.cos(rad_alvo)
        y_meta_2 = cy - (r + 8) * math.sin(rad_alvo)

        grafico_html = f"""
        <div class="rent-gauge-area">
            <svg width="260" height="150" viewBox="0 0 260 150">
                <path d="M 48 118 A 82 82 0 0 1 212 118"
                      fill="none"
                      stroke="rgba(90, 90, 90, 0.16)"
                      stroke-width="18"
                      stroke-linecap="round"/>

                <path d="M 48 118 A 82 82 0 0 1 212 118"
                      fill="none"
                      stroke="{cor_principal}"
                      stroke-width="18"
                      stroke-linecap="round"
                      stroke-dasharray="{proporcao_gauge * 258} 258"/>

                <line x1="{x_meta_1:.2f}" y1="{y_meta_1:.2f}"
                      x2="{x_meta_2:.2f}" y2="{y_meta_2:.2f}"
                      stroke="#0B2F13"
                      stroke-width="3"
                      stroke-linecap="round"/>

                <line x1="{cx}" y1="{cy}"
                      x2="{x2:.2f}" y2="{y2:.2f}"
                      stroke="#0B2F13"
                      stroke-width="4"
                      stroke-linecap="round"/>

                <circle cx="{cx}" cy="{cy}" r="7" fill="#0B2F13"/>

                <text x="48" y="143" text-anchor="middle"
                      font-size="11" fill="#5a5a5a"
                      font-family="Figtree, sans-serif">0%</text>

                <text x="212" y="143" text-anchor="middle"
                      font-size="11" fill="#5a5a5a"
                      font-family="Figtree, sans-serif">{escala_max:.1f}%</text>

                <text x="{x_meta_2:.2f}" y="{y_meta_2 - 8:.2f}"
                      text-anchor="middle"
                      font-size="10" fill="#0B2F13"
                      font-weight="700"
                      font-family="Figtree, sans-serif">Meta</text>
            </svg>
        </div>
        """

    else:
        grafico_html = f"""
        <div class="rent-bar-area">
            <div class="rent-bar-labels">
                <span>Atual: <strong>{atual_fmt}</strong></span>
                <span>Alvo: <strong>{alvo_fmt}</strong></span>
            </div>

            <div class="rent-bar-track">
                <div class="rent-bar-fill"
                     style="width:{percentual_barra:.2f}%; background-color:{cor_principal};">
                </div>
                <div class="rent-bar-target"></div>
            </div>

            <div class="rent-bar-footer">
                <span>0%</span>
                <span>100% da meta</span>
            </div>
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

        .rent-main-value {{
            color: #0B2F13;
            font-size: 30px;
            font-weight: 900;
            margin-top: 8px;
            font-family: 'Figtree', sans-serif;
            text-align: center;
        }}

        .rent-sub-value {{
            color: #5a5a5a;
            font-size: 12px;
            font-weight: 500;
            text-align: center;
            margin-top: -2px;
            font-family: 'Figtree', sans-serif;
        }}

        .rent-status {{
            display: table;
            margin: 10px auto 2px auto;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 700;
            font-family: 'Figtree', sans-serif;
        }}

        .rent-bar-area {{
            margin-top: 14px;
        }}

        .rent-bar-labels {{
            display: flex;
            justify-content: space-between;
            color: #5a5a5a;
            font-size: 12px;
            margin-bottom: 6px;
            font-family: 'Figtree', sans-serif;
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

        .rent-bar-target {{
            position: absolute;
            right: 0;
            top: -3px;
            height: 20px;
            width: 3px;
            background-color: #0B2F13;
            border-radius: 3px;
        }}

        .rent-bar-footer {{
            display: flex;
            justify-content: space-between;
            color: #5a5a5a;
            font-size: 11px;
            margin-top: 5px;
            font-family: 'Figtree', sans-serif;
        }}

        .rent-gauge-area {{
            display: flex;
            justify-content: center;
            margin-top: 6px;
            margin-bottom: -4px;
        }}
    </style>

    <div class="rent-card-container">
        <div class="rent-card-custom">
            {help_html}

            <span class="rent-card-title">
                {titulo}
            </span>

            <div class="rent-main-value">
                {atual_fmt}
            </div>

            <div class="rent-sub-value">
                Alvo: {alvo_fmt}
            </div>

            {grafico_html}

            {status_html}
        </div>
    </div>
    """

    st.html(html_final)