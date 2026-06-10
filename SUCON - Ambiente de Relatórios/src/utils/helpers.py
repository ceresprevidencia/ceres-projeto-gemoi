import pandas as pd
from datetime import date, timedelta


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