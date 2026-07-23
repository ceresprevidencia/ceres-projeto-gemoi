import pandas as pd
from datetime import date, timedelta
import streamlit as st
import math
import re

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

import html
from numbers import Number

import pandas as pd
import streamlit as st


# ── CSS RESPONSIVO ────────────────────────────────────────────────────────────

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


# ── HELPERS ───────────────────────────────────────────────────────────────────

def fmt_br(valor, casas=2):
    """
    Formata número no padrão brasileiro.
    Exemplo:
        1234.56 -> 1.234,56
    """
    try:
        valor_float = float(valor)
    except (TypeError, ValueError):
        return str(valor)

    texto = f"{valor_float:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _classe_borda_inferior(borda_inferior: str) -> str:
    """
    Define a classe visual da borda inferior.

    Valores aceitos:
        "borda"        -> borda verde fixa no final
        "ultima-linha" -> última linha verde
        qualquer outro -> sem modo especial
    """
    if borda_inferior == "borda":
        return "com-borda-inferior"

    if borda_inferior == "ultima-linha":
        return "ultima-linha-verde"

    return ""


def _escape_html(valor) -> str:
    """
    Evita que valores da tabela quebrem o HTML.
    """
    return html.escape(str(valor), quote=True)


def _tipo_coluna_ordenacao(serie: pd.Series) -> str:
    """
    Define se a coluna deve ordenar como número ou texto.
    """
    if pd.api.types.is_numeric_dtype(serie):
        return "number"

    return "text"


def _valor_ordenacao(valor) -> str:
    """
    Valor cru usado pelo JavaScript para ordenar.
    Não usa o valor formatado visualmente.
    """
    if pd.isna(valor):
        return ""

    if isinstance(valor, Number):
        return str(float(valor))

    if isinstance(valor, pd.Timestamp):
        return valor.isoformat()

    return str(valor)


# ── CSS COMPARTILHADO DA TABELA ───────────────────────────────────────────────

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

    /* Linha destacada */
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
        font-size: 15px;
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
        .th-custom div,
        .col-custom {
            font-size: 11px;
            padding: 8px;
            min-height: 35px;
        }

        .th-custom div:first-child,
        .col-custom:first-child {
            padding-left: 10px;
        }
    }

    @media (max-width: 480px) {
        .th-custom div,
        .col-custom {
            font-size: 9px;
            padding: 6px;
            min-height: 30px;
        }
    }
</style>
"""


_CSS_SCROLL_E_ORDENACAO = """
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

    .header-cell-custom {
        gap: 6px;
        user-select: none;
    }

    .header-cell-custom.ordenavel {
        cursor: pointer;
    }

    .header-cell-custom.ordenavel:hover {
        background-color: transparent;
    }

    .sort-indicator-custom {
        font-size: 10px;
        opacity: 0.75;
        min-width: 12px;
        display: inline-flex;
        justify-content: center;
    }
</style>
"""


# ── HTML DA TABELA ────────────────────────────────────────────────────────────

def gerar_tabela_html(
    df: pd.DataFrame,
    nomes_colunas: dict = None,
    primeira_coluna_larga: bool = True,
    mask_destaque: pd.Series = None,
    formatar_valores: bool = True,
    borda_inferior="borda",
    rolagem: bool = False,
    altura_max: str = "420px",
    ordenacao: bool = False,
) -> str:
    """
    Gera uma tabela HTML no padrão visual do sistema.

    Quando rolagem=False:
        - tabela fica expandida conforme o tamanho dos dados.

    Quando rolagem=True:
        - corpo da tabela recebe barra de rolagem;
        - cabeçalho fica congelado;
        - borda inferior fica congelada.

    Quando ordenacao=True:
        - cabeçalho fica clicável;
        - cada clique alterna entre:
            sem ordenação -> crescente -> decrescente -> sem ordenação
        - colunas numéricas ordenam numericamente;
        - demais colunas ordenam alfabeticamente.
    """

    if df is None:
        df = pd.DataFrame()

    if nomes_colunas is None:
        nomes_colunas = {col: col for col in df.columns}

    qtd_colunas = len(df.columns)

    if qtd_colunas == 0:
        return """
        <div style="font-family: 'Figtree', sans-serif; padding: 12px;">
            Nenhum dado para exibir.
        </div>
        """

    primeira = "2fr" if primeira_coluna_larga else "1fr"
    resto = " ".join(["1fr"] * (qtd_colunas - 1))
    grid = f"{primeira} {resto}" if qtd_colunas > 1 else "1fr"

    classe_borda = _classe_borda_inferior(borda_inferior)

    html_tabela = _CSS_TABELA
    html_tabela += _CSS_SCROLL_E_ORDENACAO

    html_tabela += f'<div class="tabela-custom-wrapper {classe_borda}">'

    # Cabeçalho fora da área rolável
    html_tabela += f'<div class="th-custom" style="grid-template-columns:{grid};">'

    for col_index, col in enumerate(df.columns):
        nome_coluna = _escape_html(nomes_colunas.get(col, col))
        tipo_ordenacao = _tipo_coluna_ordenacao(df[col])

        html_tabela += (
            f'<div class="header-cell-custom" '
            f'data-col-index="{col_index}" '
            f'data-sort-type="{tipo_ordenacao}">'
            f'<span>{nome_coluna}</span>'
        )

        if ordenacao:
            html_tabela += '<span class="sort-indicator-custom">↕</span>'

        html_tabela += '</div>'

    html_tabela += '</div>'

    # Corpo com ou sem rolagem
    if rolagem:
        html_tabela += (
            f'<div class="tabela-scroll-body tabela-body-custom" '
            f'style="max-height:{_escape_html(altura_max)};">'
        )
    else:
        html_tabela += '<div class="tabela-body-custom">'

    # Linhas
    for idx, row in df.iterrows():
        classe_destaque = ""

        if mask_destaque is not None and idx in mask_destaque.index and bool(mask_destaque.loc[idx]):
            classe_destaque = " destaque"

        html_tabela += f'<div class="row-custom{classe_destaque}" style="grid-template-columns:{grid};">'

        for col in df.columns:
            valor = row[col]

            if formatar_valores and isinstance(valor, Number) and not pd.isna(valor):
                col_lower = str(col).lower()

                if "r$" in col_lower or "%" in col_lower:
                    valor_fmt = fmt_br(valor, 2)
                else:
                    valor_fmt = f"{valor:.2f}"
            else:
                valor_fmt = str(valor) if pd.notna(valor) else "—"

            valor_fmt_html = _escape_html(valor_fmt)
            valor_ordem_html = _escape_html(_valor_ordenacao(valor))

            html_tabela += (
                f'<div class="col-custom" data-order-value="{valor_ordem_html}">'
                f'{valor_fmt_html}'
                f'</div>'
            )

        html_tabela += '</div>'

    html_tabela += '</div>'  # fecha corpo

    # Borda inferior congelada
    if borda_inferior == "borda":
        html_tabela += '<div class="tabela-borda-final"></div>'
    else:
        html_tabela += '<div class="tabela-sem-borda-final"></div>'

    html_tabela += '</div>'  # fecha wrapper

    return html_tabela


# ── FUNÇÃO ORIGINAL, MANTIDA ──────────────────────────────────────────────────

def gerar_tabela_estilizada(
    df,
    nomes_colunas=None,
    primeira_coluna_larga=True,
    borda_inferior="borda",
    rolagem: bool = False,
    altura_max: str = "420px",
    ordenacao: bool = False,
) -> str:
    """
    Mantém a função original retornando HTML.

    Use com st.html(...) quando ordenacao=False.
    Para ordenacao=True, prefira renderizar_tabela_estilizada(...).
    """
    return gerar_tabela_html(
        df,
        nomes_colunas=nomes_colunas,
        primeira_coluna_larga=primeira_coluna_larga,
        borda_inferior=borda_inferior,
        rolagem=rolagem,
        altura_max=altura_max,
        ordenacao=ordenacao,
    )


# ── FUNÇÃO COM DESTAQUE, MANTIDA ──────────────────────────────────────────────

def aplicar_destaque(
    df_exibir: pd.DataFrame,
    mask_desenquadrado: pd.Series,
    borda_inferior="borda",
    rolagem: bool = False,
    altura_max: str = "420px",
    ordenacao: bool = False,
) -> str:
    return gerar_tabela_html(
        df_exibir,
        mask_destaque=mask_desenquadrado,
        formatar_valores=False,
        borda_inferior=borda_inferior,
        rolagem=rolagem,
        altura_max=altura_max,
        ordenacao=ordenacao,
    )


# ── JS DO COMPONENTE ORDENÁVEL ────────────────────────────────────────────────

_COMPONENTE_TABELA_ORDENAVEL = None


_JS_TABELA_ORDENAVEL = """
export default function(component) {
    const { parentElement, data } = component;

    const root = parentElement.querySelector("#tabela-root");

    if (!root) {
        return;
    }

    root.innerHTML = data.html;

    if (!data.ordenacao) {
        return;
    }

    const wrapper = root.querySelector(".tabela-custom-wrapper");

    if (!wrapper) {
        return;
    }

    const body = wrapper.querySelector(".tabela-body-custom");
    const headers = Array.from(wrapper.querySelectorAll(".header-cell-custom"));

    if (!body || headers.length === 0) {
        return;
    }

    const linhasOriginais = Array.from(body.querySelectorAll(".row-custom"));

    let estado = {
        coluna: null,
        direcao: null
    };

    function normalizarNumero(valor) {
        if (valor === null || valor === undefined || valor === "") {
            return Number.NEGATIVE_INFINITY;
        }

        const numero = Number(valor);

        if (Number.isNaN(numero)) {
            return Number.NEGATIVE_INFINITY;
        }

        return numero;
    }

    function compararTexto(a, b) {
        const textoA = String(a || "").toLocaleLowerCase("pt-BR");
        const textoB = String(b || "").toLocaleLowerCase("pt-BR");

        return textoA.localeCompare(textoB, "pt-BR", {
            numeric: true,
            sensitivity: "base"
        });
    }

    function atualizarIcones() {
        headers.forEach((header, index) => {
            const indicador = header.querySelector(".sort-indicator-custom");

            if (!indicador) {
                return;
            }

            if (estado.coluna !== index || estado.direcao === null) {
                indicador.textContent = "↕";
            } else if (estado.direcao === "asc") {
                indicador.textContent = "▲";
            } else {
                indicador.textContent = "▼";
            }
        });
    }

    function restaurarOrdemOriginal() {
        linhasOriginais.forEach((linha) => body.appendChild(linha));
    }

    function ordenarPorColuna(colunaIndex, direcao) {
        const header = headers[colunaIndex];
        const tipo = header.dataset.sortType || "text";

        const linhas = Array.from(body.querySelectorAll(".row-custom"));

        linhas.sort((linhaA, linhaB) => {
            const celulaA = linhaA.children[colunaIndex];
            const celulaB = linhaB.children[colunaIndex];

            const valorA = celulaA ? celulaA.dataset.orderValue : "";
            const valorB = celulaB ? celulaB.dataset.orderValue : "";

            let resultado;

            if (tipo === "number") {
                resultado = normalizarNumero(valorA) - normalizarNumero(valorB);
            } else {
                resultado = compararTexto(valorA, valorB);
            }

            return direcao === "asc" ? resultado : -resultado;
        });

        linhas.forEach((linha) => body.appendChild(linha));
    }

    const cleanups = [];

    headers.forEach((header, colunaIndex) => {
        header.classList.add("ordenavel");

        const onClick = () => {
            if (estado.coluna !== colunaIndex) {
                estado = {
                    coluna: colunaIndex,
                    direcao: "asc"
                };
            } else if (estado.direcao === "asc") {
                estado = {
                    coluna: colunaIndex,
                    direcao: "desc"
                };
            } else if (estado.direcao === "desc") {
                estado = {
                    coluna: null,
                    direcao: null
                };
            } else {
                estado = {
                    coluna: colunaIndex,
                    direcao: "asc"
                };
            }

            if (estado.direcao === null) {
                restaurarOrdemOriginal();
            } else {
                ordenarPorColuna(estado.coluna, estado.direcao);
            }

            atualizarIcones();
        };

        header.addEventListener("click", onClick);
        cleanups.push(() => header.removeEventListener("click", onClick));
    });

    atualizarIcones();

    return () => {
        cleanups.forEach((cleanup) => cleanup());
    };
}
"""


def _get_componente_tabela_ordenavel():
    """
    Registra o componente v2 apenas uma vez.
    """
    global _COMPONENTE_TABELA_ORDENAVEL

    if _COMPONENTE_TABELA_ORDENAVEL is None:
        _COMPONENTE_TABELA_ORDENAVEL = st.components.v2.component(
            name="tabela_ordenavel_custom",
            html='<div id="tabela-root"></div>',
            js=_JS_TABELA_ORDENAVEL,
            isolate_styles=True,
        )

    return _COMPONENTE_TABELA_ORDENAVEL


# ── FUNÇÃO FINAL DE RENDERIZAÇÃO ──────────────────────────────────────────────

def renderizar_tabela_estilizada(
    df,
    nomes_colunas=None,
    primeira_coluna_larga=True,
    borda_inferior="borda",
    rolagem: bool = False,
    altura_max: str = "420px",
    ordenacao: bool = False,
    key: str | None = None,
):
    """
    Função simples para chamar no app.

    Quando ordenacao=False:
        usa st.html(...)

    Quando ordenacao=True:
        usa st.components.v2.component(...)
    """
    html_tabela = gerar_tabela_estilizada(
        df=df,
        nomes_colunas=nomes_colunas,
        primeira_coluna_larga=primeira_coluna_larga,
        borda_inferior=borda_inferior,
        rolagem=rolagem,
        altura_max=altura_max,
        ordenacao=ordenacao,
    )

    if ordenacao:
        componente = _get_componente_tabela_ordenavel()

        return componente(
            data={
                "html": html_tabela,
                "ordenacao": True,
            },
            key=key,
        )

    return st.html(html_tabela)
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
def card_geral(titulo: str, valor: str, delta: str = None, help: str = None, valor_extenso: str = None):
    import numpy as np
    """
    Renderiza um card de métrica seguindo o Manual de Marca Ceres.

    Parâmetros:
    - titulo: título do card
    - valor: valor resumido exibido no painel, ex: "1,3 bi"
    - delta: variação opcional
    - help: texto opcional do ícone de ajuda
    - valor_extenso: valor completo exibido ao passar o mouse, ex: "R$ 1.300.000.000,00"
    """

    # 1. Lógica do Delta Opcional
    delta_html = ""

    if delta is not None and not pd.isna(delta):
        if isinstance(delta, (int, float, np.number)):
            numero_delta = float(delta)
            delta_formatado = f"{numero_delta:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            delta_formatado = str(delta)
            numero_delta = float(
                delta_formatado
                .replace("R$", "")
                .replace("Mi", "")
                .replace("Bi", "")
                .replace(".", "")
                .replace(",", ".")
                .replace("%", "")
                .replace(" ", "")
                .strip()
            )

        if numero_delta > 0:
            cor_delta = "#016837"
            texto_delta = f"▲ {delta_formatado}"
        elif numero_delta < 0:
            cor_delta = "#c0392b"
            texto_delta = f"▼ {delta_formatado}"
        else:
            cor_delta = "#5a5a5a"
            texto_delta = delta_formatado
        delta_html = (
            f'<div style="background-color:transparent; '
            f'color:{cor_delta}; font-size:14px; font-weight:600; text-align:center; margin-top: -6px;'
            f'font-family: \'Figtree\', sans-serif;">{texto_delta}</div>'
        )

    # 2. Lógica do ícone de help opcional
    help_html = ""
    if help:
        help_html = f"""
        <div class="meu-card-help">
            i
            <span class="meu-card-tooltip">{help}</span>
        </div>
        """

    # 3. Lógica do hover no valor principal
    if valor_extenso:
        valor_html = f"""
        <div class="meu-card-valor">
            {valor}
            <span class="meu-card-valor-tooltip">{valor_extenso}</span>
        </div>
        """
    else:
        valor_html = f"""
        <div class="meu-card-valor">
            {valor}
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
            height: 130px;
            box-sizing: border-box;

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
            font-style: normal;
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

        .meu-card-valor {{
            color: #0b2f13;
            font-size: 25px;
            font-weight: 900;
            margin-top: 8px;
            font-family: 'Figtree', sans-serif;
            text-align: center;
            position: relative;
            cursor: default;
            width: fit-content;
            margin-left: auto;
            margin-right: auto;
        }}

        .meu-card-valor-tooltip {{
            visibility: hidden;
            opacity: 0;
            position: absolute;
            top: 120%;
            left: 50%;
            transform: translateX(-50%);
            background-color: #0B2F13;
            color: #FAFBEB;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 400;
            font-family: 'Figtree', sans-serif;
            white-space: nowrap;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
            transition: opacity 0.2s ease-in-out;
            z-index: 999;
        }}

        .meu-card-valor:hover .meu-card-valor-tooltip {{
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

            {valor_html}

            <span>
                {delta_html}
            </span>
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

    if percentual_meta >= 1.01:
        cor_principal = "#D3AF37"
    elif percentual_meta >= 1.00:
        cor_principal = "#016837"
    elif percentual_meta >= 0.90:
        cor_principal = "#016837"
    elif percentual_meta >= 0.80:
        cor_principal = "#016837"
    elif percentual_meta >= 0.70:
        cor_principal = "#016837"
    elif percentual_meta >= 0.60:
        cor_principal = "#016837"
    elif percentual_meta >= 0.50:
        cor_principal = "#016837"
    elif percentual_meta >= 0.40:
        cor_principal = "#016837"
    elif percentual_meta >= 0.30:
        cor_principal = "#016837"
    elif percentual_meta >= 0.20:
        cor_principal = "#016837"
    elif percentual_meta >= 0.10:
        cor_principal = "#016837"
    else:
        cor_principal = "#016837"

    help_html = ""
    if help:
        help_html = f"""
        <div class="rent-card-help">
            i
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
            height: 130px;
            box-sizing: border-box;

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
            font-style: normal;
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
            font-size: 25px;
            font-weight: 900;
            font-family: 'Figtree', sans-serif;
            white-space: nowrap;
        }}

        .rent-target-value {{
            color: #5a5a5a;
            font-size: 13px;
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


import math
import re
import html as html_lib
import streamlit as st


def _parse_percentual(valor):
    if valor is None:
        return 0.0

    if isinstance(valor, (int, float)):
        valor = float(valor)

        # Caso venha como fração: 0.082 = 8,2%
        if -1 < valor < 1 and valor != 0:
            return valor * 100

        return valor

    texto = str(valor).strip()
    texto = texto.replace("%", "").replace(" ", "")

    if not texto:
        return 0.0

    if "," in texto and "." in texto:
        if texto.rfind(",") > texto.rfind("."):
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", "")
    elif "," in texto:
        texto = texto.replace(",", ".")

    try:
        valor = float(texto)
    except ValueError:
        return 0.0

    if -1 < valor < 1 and valor != 0:
        return valor * 100

    return valor


def _safe_id(text):
    return re.sub(r"[^a-zA-Z0-9_-]", "_", str(text))


def _svg_point(cx, cy, r, deg):
    rad = math.radians(deg)
    return cx + r * math.cos(rad), cy + r * math.sin(rad)


def _svg_arc_path(cx, cy, r, start_deg, end_deg):
    x1, y1 = _svg_point(cx, cy, r, start_deg)
    x2, y2 = _svg_point(cx, cy, r, end_deg)

    diff = end_deg - start_deg
    large_arc = 1 if abs(diff) > 180 else 0
    sweep = 1 if diff > 0 else 0

    return (
        f"M {x1:.2f} {y1:.2f} "
        f"A {r:.2f} {r:.2f} 0 {large_arc} {sweep} {x2:.2f} {y2:.2f}"
    )


def _format_percentual(valor, casas=2):
    return f"{valor:.{casas}f}%".replace(".", ",")


def _parse_numero_brl(valor):
    if valor is None:
        return 0.0

    if isinstance(valor, (int, float)):
        return float(valor)

    texto = str(valor).strip()
    texto = texto.replace("R$", "").replace(" ", "")

    if "," in texto and "." in texto:
        if texto.rfind(",") > texto.rfind("."):
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", "")
    elif "," in texto:
        texto = texto.replace(",", ".")

    return float(texto)


def _format_brl_completo(valor):
    if valor is None:
        return "-"

    try:
        numero = _parse_numero_brl(valor)
    except Exception:
        return str(valor)

    return "R$ " + f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _format_brl_curto(valor):
    if valor is None:
        return "-"

    try:
        numero = _parse_numero_brl(valor)
    except Exception:
        return str(valor)

    abs_numero = abs(numero)

    if abs_numero >= 1_000_000_000:
        return "R$ " + f"{numero / 1_000_000_000:.2f}".replace(".", ",") + " Bi"

    if abs_numero >= 1_000_000:
        return "R$ " + f"{numero / 1_000_000:.2f}".replace(".", ",") + " Mi"

    if abs_numero >= 1_000:
        return "R$ " + f"{numero / 1_000:.2f}".replace(".", ",") + " Mil"

    return _format_brl_completo(numero)


def card_segmento_rentabilidade(
    segmento: str,
    rentabilidade_atual,
    rentabilidade_alvo,
    posicao,
    mtd,
    m12,
    pct_posicao,
    cor_segmento: str = "#016837",
    height: int = 160,
):
    atual = _parse_percentual(rentabilidade_atual)
    alvo = _parse_percentual(rentabilidade_alvo)
    mtd_valor = _parse_percentual(mtd)
    m12_valor = _parse_percentual(m12)

    # Valor real: pode ser negativo ou passar de 100%
    pct_meta_real = 0 if alvo == 0 else atual / alvo

    # Valor visual do arco: limitado entre 0% e 100%
    pct_meta_gauge = max(0, min(pct_meta_real, 1))

    atual_fmt = _format_percentual(atual, 2)
    alvo_fmt = _format_percentual(alvo, 2)
    mtd_fmt = _format_percentual(mtd_valor, 2)
    m12_fmt = _format_percentual(m12_valor, 2)

    # Label real: permite -20%, 135%, etc.
    avanco_fmt = _format_percentual(pct_meta_real * 100, 0)

    segmento_safe = html_lib.escape(str(segmento))
    pos_curto = html_lib.escape(_format_brl_curto(posicao))
    pos_completo = html_lib.escape(_format_brl_completo(posicao))
    uid = _safe_id(segmento)

    if pct_meta_real >= 1.01:
        fill_color = "#D3AF37"
    elif pct_meta_real >= 1.0:
        fill_color = "#016837"
    elif pct_meta_real >= 0.7:
        fill_color = "#558B2F"
    elif pct_meta_real >= 0.4:
        fill_color = "#558B2F"
    else:
        fill_color = "#558B2F"

    # Gauge
    cx, cy, r = 100, 104, 82
    start_deg = 150
    total_span = 240
    end_deg = start_deg + total_span
    fill_deg = start_deg + total_span * pct_meta_gauge

    track_path = _svg_arc_path(cx, cy, r, start_deg, end_deg)
    fill_path = _svg_arc_path(cx, cy, r, start_deg, fill_deg) if pct_meta_gauge > 0.005 else ""

    # Label sobrepondo o medidor
    # Se valor for negativo, fica no início do gauge.
    # Se passar de 100%, fica no fim do gauge.
    # Entre 0 e 100%, acompanha o avanço.
    if pct_meta_real < 0:
        label_deg = start_deg
    elif pct_meta_real > 1:
        label_deg = end_deg
    else:
        label_deg = fill_deg

    # r = exatamente em cima do arco.
    # r - 4 = mais para dentro.
    # r + 4 = mais para fora.
    label_r = r
    lx, ly = _svg_point(cx, cy, label_r, label_deg)

    # Fundo arredondado da label
    label_chars = len(avanco_fmt)
    label_w = max(46, label_chars * 11)
    label_h = 26
    label_x = lx - label_w / 2
    label_y = ly - label_h / 2

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700;800;900&display=swap');

            html,
            body {{
                width: 100%;
                height: 100%;
                margin: 0;
                padding: 0;
                overflow: hidden;
                background: transparent;
                box-sizing: border-box;
                font-family: 'Figtree', sans-serif;
            }}

            *,
            *::before,
            *::after {{
                box-sizing: border-box;
            }}

            .seg-card-{uid} {{
                width: 100%;
                height: 100%;
                max-width: none;
                min-width: 0;
                background-color: rgba(219, 208, 178, 0.14);
                padding: 8px 12px 8px 16px;
                border-radius: 10px;
                margin: 0;
                box-shadow: none;
                transition: none;
                font-family: 'Figtree', sans-serif;
                position: relative;
                overflow: hidden;
                display: flex;
                flex-direction: column;
            }}

            .seg-card-{uid}:hover {{
                transform: none;
                box-shadow: none;
            }}

            .seg-color-bar {{
                position: absolute;
                left: 0;
                top: 0;
                width: 5px;
                height: 100%;
                border-radius: 10px 0 0 10px;
                background: {cor_segmento};
            }}

            .seg-title {{
                font-size: clamp(14px, 1.6vw, 15px);
                font-weight: 400;
                font-family: 'Figtree', sans-serif;
                white-space: normal;
                overflow: hidden;
                text-overflow: ellipsis;
                line-height: 1.1;
                padding-right: 22px;
                margin-top: 8px;
                margin-left: 16px;
            }}

            .seg-body {{
                flex: 1 1 auto;
                min-height: 0;
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 12px;
                width: 100%;
            }}

            .seg-gauge-col {{
                flex: 0 0 48%;
                min-width: 0;
                height: 100%;
                display: flex;
                align-items: center;
                justify-content: center;
            }}

            .seg-svg-wrap {{
                position: relative;
                width: min(100%, 230px);
                max-height: 118px;
                aspect-ratio: 200 / 172;
                margin: 0;
            }}

            .seg-svg-wrap svg {{
                width: 100%;
                height: 100%;
                display: block;
                overflow: visible;
            }}

            .seg-gauge-ano-label {{
                position: absolute;
                top: 22px;
                left: 28px;
                color: #5a5a5a;
                font-size: clamp(11px, 1.5vw, 12px);
                font-weight: 600;
                font-family: 'Figtree', sans-serif;
                line-height: 1;
                z-index: 2;
                pointer-events: none;
            }}

            .seg-center-text {{
                position: absolute;
                top: 52%;
                left: 50%;
                transform: translate(-50%, -35%);
                text-align: center;
                pointer-events: none;
                width: 100%;
            }}

            .seg-ytd-val {{
                font-size: clamp(21px, 4vw, 22px);
                font-weight: 600;
                color: #0B2F13;
                display: block;
                line-height: 1;
            }}

            .seg-ytd-sub-label {{
                font-size: clamp(10px, 1.5vw, 11px);
                color: #5a5a5a;
                display: block;
                margin-top: 5px;
                font-weight: 500;
                line-height: 1;
            }}

            .seg-ytd-sub-value {{
                font-size: clamp(13px, 2vw, 14px);
                color: #0B2F13;
                display: block;
                margin-top: 3px;
                font-weight: 700;
                line-height: 1;
            }}

            .seg-gauge-label-bg {{
                fill: rgba(250, 251, 235, 0.92);
                stroke: rgba(90,90,90,0.18);
                stroke-width: 0.8;
            }}

            .seg-gauge-pct {{
                font-size: 18px;
                font-family: 'Figtree', sans-serif;
                font-weight: 500;
                fill: rgba(90,90,90,0.88);
            }}

            .seg-side-values {{
                flex: 1 1 52%;
                min-width: 0;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: stretch;
                gap: 7px;
                height: 100%;
                padding-right: 30px;
            }}

            .seg-metric {{
                position: relative;
                display: flex;
                align-items: baseline;
                justify-content: space-between;
                gap: 8px;
                min-width: 0;
            }}

            .seg-footer-label {{
                font-size: clamp(11px, 1.6vw, 15px);
                color: #5a5a5a;
                font-weight: 500;
                line-height: 1;
                white-space: nowrap;
            }}

            .seg-footer-val {{
                font-size: clamp(13px, 1.6vw, 16px);
                font-weight: 600;
                color: #0B2F13;
                
                word-break: keep-all;
                line-height: 1.1;
                white-space: nowrap;
            }}

            .seg-pos-wrap {{
                cursor: default;
            }}

            .seg-pos-tooltip {{
                visibility: hidden;
                opacity: 0;
                position: absolute;
                bottom: calc(100% + 7px);
                right: 0;
                background: #0B2F13;
                color: #FAFBEB;
                padding: 6px 10px;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 500;
                white-space: nowrap;
                box-shadow: 0 4px 10px rgba(0,0,0,0.18);
                transition: opacity 0.16s ease-in-out;
                z-index: 999;
                pointer-events: none;
            }}

            .seg-pos-wrap:hover .seg-pos-tooltip {{
                visibility: visible;
                opacity: 1;
            }}

            @media (max-width: 420px) {{
                .seg-card-{uid} {{
                    padding: 8px 8px 8px 14px;
                }}

                .seg-body {{
                    gap: 8px;
                }}

                .seg-gauge-col {{
                    flex-basis: 50%;
                }}

                .seg-side-values {{
                    flex-basis: 50%;
                    gap: 6px;
                }}

                .seg-svg-wrap {{
                    width: min(100%, 205px);
                    max-height: 108px;
                }}

                .seg-gauge-ano-label {{
                    top: 7px;
                    left: 8px;
                    font-size: 9px;
                }}

                .seg-center-text {{
                    top: 52%;
                    transform: translate(-50%, -35%);
                }}

                .seg-gauge-pct {{
                    font-size: 16px;
                }}

                .seg-ytd-val {{
                    font-size: 21px;
                }}

                .seg-ytd-sub-label {{
                    font-size: 9px;
                }}

                .seg-ytd-sub-value {{
                    font-size: 12px;
                }}

                .seg-footer-val {{
                    font-size: 11px;
                }}
            }}
        </style>
    </head>

    <body>
        <div class="seg-card-{uid}">
            <div class="seg-color-bar"></div>

            <div class="seg-title">{segmento_safe}</div>

            <div class="seg-body">
                <div class="seg-gauge-col">
                    <div class="seg-svg-wrap">

                        <span class="seg-gauge-ano-label">Ano</span>

                        <svg viewBox="0 0 200 172" role="img" aria-label="Gauge de rentabilidade de {segmento_safe}">
                            <path d="{track_path}"
                                  fill="none"
                                  stroke="rgba(90,90,90,0.12)"
                                  stroke-width="24"
                                  stroke-linecap="round"/>

                            <path d="{fill_path}"
                                  fill="none"
                                  stroke="{fill_color}"
                                  stroke-width="24"
                                  stroke-linecap="round"/>

                            <rect x="{label_x:.1f}" y="{label_y:.1f}"
                                  width="{label_w:.1f}"
                                  height="{label_h:.1f}"
                                  rx="5"
                                  ry="5"
                                  class="seg-gauge-label-bg" />

                            <text x="{lx:.1f}" y="{ly:.1f}"
                                  class="seg-gauge-pct"
                                  text-anchor="middle"
                                  dominant-baseline="middle">
                                {avanco_fmt}
                            </text>
                        </svg>

                        <div class="seg-center-text">
                            <span class="seg-ytd-val">{atual_fmt}</span>
                            <span class="seg-ytd-sub-label">Projetada</span>
                            <span class="seg-ytd-sub-value">{alvo_fmt}</span>
                        </div>

                    </div>
                </div>

                <div class="seg-side-values">
                    <div class="seg-metric seg-pos-wrap">
                        <span class="seg-footer-label">Posição</span>
                        <span class="seg-footer-val">{pos_curto}</span>
                        <span class="seg-pos-tooltip">{pos_completo} ({pct_posicao} do plano).</span>
                    </div>

                    <div class="seg-metric">
                        <span class="seg-footer-label">MTD</span>
                        <span class="seg-footer-val">{mtd_fmt}</span>
                    </div>

                    <div class="seg-metric">
                        <span class="seg-footer-label">12 meses</span>
                        <span class="seg-footer-val">{m12_fmt}</span>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    st.iframe(
        html,
        height=height,
        width="stretch",
    )


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
    - Ano/rentabilidade atual à esquerda
    - Posição e % na mesma linha à direita
    - MTD e 12 meses empilhados à direita

    A cor do segmento é aplicada inline para evitar conflito de CSS
    quando vários cards são renderizados na mesma tela.
    """

    atual = _parse_percentual(rentabilidade_atual)
    mtd_valor = _parse_percentual(mtd)
    m12_valor = _parse_percentual(m12)
    posicao_pct_valor = _parse_percentual(posicao_pct)

    atual_fmt = f"{atual:.2f}%".replace(".", ",")
    mtd_fmt = f"{mtd_valor:.2f}%".replace(".", ",")
    m12_fmt = f"{m12_valor:.2f}%".replace(".", ",")
    posicao_pct_fmt = f"{posicao_pct_valor:.2f}%".replace(".", ",")

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
            i
            <span class="seg-card-tooltip">{help}</span>
        </div>
        """

    html_final = f"""
    <style>
        .seg-card-custom {{
            background-color: rgba(219, 208, 178, 0.14);
            padding: 15px 16px 24px 18px;
            border-radius: 10px;
            margin-top: 6px;
            box-shadow: none;
            transition: none;
            text-align: left;
            position: relative;
            font-family: 'Figtree', sans-serif;
            overflow: hidden;
            min-height: 150px;
            box-sizing: border-box;
            height: 150px;
        }}

        .seg-card-custom:hover {{
            transform: none;
            box-shadow: none;
        }}

        .seg-color-bar {{
            position: absolute;
            left: 0;
            top: 0;
            width: 5px;
            height: 100%;
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
            font-style: normal;
            font-family: 'Figtree', sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 2;
        }}

        .seg-card-tooltip {{
            visibility: hidden;
            opacity: 0;
            position: absolute;
            bottom: 130%;
            right: 0;
            width: 220px;
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
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
            transition: opacity 0.2s ease-in-out;
            z-index: 999;
        }}

        .seg-card-help:hover .seg-card-tooltip {{
            visibility: visible;
            opacity: 1;
        }}

        .seg-card-layout {{
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 14px;
            align-items: start;
            height: 100%;
        }}

        .seg-card-left {{
            min-width: 0;
            padding-right: 8px;
        }}

        .seg-card-title {{
            font-size: clamp(14px, 1.6vw, 15px);
            font-weight: 400;
            font-family: 'Figtree', sans-serif;
            white-space: normal;
            overflow: hidden;
            text-overflow: ellipsis;
            line-height: 1.1;
            padding-right: 22px;
        }}

        .seg-ano-box {{
            margin-top: 18px;
            margin-left: 35px;
        }}

        .seg-main-label {{
            color: #5a5a5a;
            font-size: clamp(14px, 1.6vw, 15px);
            font-weight: 600;
            font-family: 'Figtree', sans-serif;
            margin-bottom: 2px;
        }}

        .seg-main-value {{
            color: #0B2F13;
            font-size: 30px;
            font-weight: 900;
            font-family: 'Figtree', sans-serif;
            white-space: nowrap;
            line-height: 1;
        }}

        .seg-card-right {{
            display: flex;
            flex-direction: column;
            align-items: stretch;
            text-align: right;
            padding-right: 28px;
            margin-top: 20px;
            min-width: 210px;
        }}

        .seg-posicao-row {{
            display: grid;
            grid-template-columns: 1fr 60px;
            align-items: flex-start;
            gap: 16px;
            margin-bottom: 12px;
            width: 100%;
        }}

        .seg-metric-box {{
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            line-height: 1.1;
            min-width: 0;
        }}

        .seg-metric-box .seg-metric-value {{
            text-align: left;
        }}

        .seg-metrics-stack {{
            display: flex;
            flex-direction: column;
            align-items: stretch;
            gap: 6px;
            width: 100%;
        }}

        .seg-metric-line {{
            display: grid;
            grid-template-columns: 85px 1fr;
            align-items: baseline;
            column-gap: 10px;
            line-height: 1.1;
            white-space: nowrap;
            width: 100%;
        }}

        .seg-metric-label {{
            color: #5a5a5a;
            font-size: clamp(11px, 1.6vw, 15px);
            font-weight: 600;
            font-family: 'Figtree', sans-serif;
            text-align: left;
            white-space: nowrap;
        }}

        .seg-metric-value {{
            color: #0B2F13;
            font-size: clamp(13px, 1.6vw, 16px);
            font-weight: 500;
            font-family: 'Figtree', sans-serif;
            white-space: nowrap;
            text-align: right;
        }}
    </style>

    <div class="seg-card-container">
        <div class="seg-card-custom">

            <div class="seg-color-bar" style="background:{cor_segmento};"></div>

            {help_html}

            <div class="seg-card-layout">

                <div class="seg-card-left">
                    <div class="seg-card-title">{segmento}</div>

                    <div class="seg-ano-box">
                        <div class="seg-main-label">Ano</div>
                        <div class="seg-main-value">{atual_fmt}</div>
                    </div>
                </div>

                <div class="seg-card-right">

                    <div class="seg-posicao-row">
                        <div class="seg-metric-box">
                            <span class="seg-metric-label">Posição</span>
                            <span class="seg-metric-value">{posicao_fmt}</span>
                        </div>

                        <div class="seg-metric-box">
                            <span class="seg-metric-label">%</span>
                            <span class="seg-metric-value">{posicao_pct_fmt}</span>
                        </div>
                    </div>

                    <div class="seg-metrics-stack">

                        <div class="seg-metric-line">
                            <span class="seg-metric-label">MTD</span>
                            <span class="seg-metric-value">{mtd_fmt}</span>
                        </div>

                        <div class="seg-metric-line">
                            <span class="seg-metric-label">12 Meses</span>
                            <span class="seg-metric-value">{m12_fmt}</span>
                        </div>

                    </div>

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
        "ABDI FlexCeres_CD_Emprestimos": "Empréstimos ABDI FlexCeres",
        "CENESP (BLOCO C)": "CENESP (BLOCO C)",
        "CENESP (BLOCO J)": "CENESP (BLOCO J)",
        "Ceres Básico_BD_Emprestimos": "Empréstimos Ceres Básico",
        "Ceres Básico_BD_Financiamentos": "Financiamento Imobiliário Ceres Básico",
        "Ceres FlexCeres_CV_Emprestimos": "Empréstimos Ceres FlexCeres",
        "Cidasc FlexCeres_CV_Emprestimos": "Empréstimos Cidasc FlexCeres",
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



CORES_SEGMENTOS = {
    "Renda Fixa": "#0B2F13",
    "Renda Variável": "#D64550",
    "Estruturado": "#A8EC7D",
    "Operações com Participantes": "#2DC25F",
    "Imobiliário": "#CCF1DF",
    "Exterior": "#6D597A",
}





def card_limites_excedidos(
    titulo: str,
    qtd_ok,
    qtd_excedido,
    help: str = None
):
    """
    Renderiza um card no mesmo estilo do card_geral,
    mas exibindo duas badges no lugar do valor principal.
    """

    # Help opcional
    help_html = ""
    if help:
        help_html = f"""
        <div class="meu-card-help">
            i
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
            height: 130px;
            box-sizing: border-box;
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
            font-style: normal;
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

        .meu-card-titulo {{
            color:#5a5a5a;
            font-size:16px;
            padding:2px 8px;
            border-radius:6px;
            font-weight:900;
            display:inline-block;
            font-family: 'Figtree', sans-serif;
        }}

        .meu-card-badges {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            margin-top: 24px;
            font-family: 'Figtree', sans-serif;
        }}

        .meu-card-badge {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 5px;
            height: 28px;
            padding: 0 14px;
            border-radius: 999px;
            font-size: 14px;
            font-weight: 900;
            line-height: 1;
            white-space: nowrap;
        }}

        .meu-card-badge-ok {{
            background-color: rgba(1, 104, 55, 0.12);
            color: #016837;
            border: 1.5px solid rgba(1, 104, 55, 0.35);
        }}

        .meu-card-badge-excedido {{
            background-color: rgba(192, 57, 43, 0.12);
            color: #c0392b;
            border: 1.5px solid rgba(192, 57, 43, 0.35);
        }}
    </style>

    <div class="meu-card-container">
        <div class="meu-card-custom">
            {help_html}

            <span class="meu-card-titulo">
                {titulo}
            </span>

            <div class="meu-card-badges">
                <div class="meu-card-badge meu-card-badge-ok">
                    ✓ {qtd_ok} OK
                </div>

                <div class="meu-card-badge meu-card-badge-excedido">
                    ⚠ {qtd_excedido} Excedido
                </div>
            </div>
        </div>
    </div>
    """

    st.html(html_final)


from collections.abc import Iterable
import streamlit as st


_CHAVE_SESSION_STATE = "paginas_manutencao_liberadas"


def obter_paginas_manutencao_liberadas() -> set[str]:
    """
    Retorna as chaves das páginas em manutenção já liberadas na sessão atual.

    A função lê o valor armazenado no ``st.session_state`` e sempre devolve
    um ``set``. Isso evita duplicidades e facilita a consulta com o operador
    ``in``.

    A autorização permanece válida enquanto a sessão do Streamlit estiver
    ativa. Ao encerrar a sessão, reiniciar o app ou perder a conexão, o estado
    poderá ser descartado.
    """
    paginas = st.session_state.get(_CHAVE_SESSION_STATE, [])
    return {str(chave) for chave in paginas}


def pagina_manutencao_liberada(chave: str) -> bool:
    """
    Verifica se uma página em manutenção já foi liberada na sessão atual.

    Parâmetros
    ----------
    chave:
        Identificador único da página. Normalmente pode ser a própria URL
        ou o valor configurado em ``access_key``.

    Retorna
    -------
    bool
        ``True`` quando a página já foi autorizada; caso contrário, ``False``.
    """
    return str(chave) in obter_paginas_manutencao_liberadas()


def liberar_pagina_manutencao(chave: str) -> None:
    """
    Registra uma página como liberada na sessão atual.

    A chave é adicionada ao conjunto de páginas autorizadas e depois salva
    novamente no ``st.session_state`` como lista, mantendo compatibilidade
    com a serialização interna do Streamlit.

    Parâmetros
    ----------
    chave:
        Identificador único da página que acabou de ser autorizada.
    """
    paginas = obter_paginas_manutencao_liberadas()
    paginas.add(str(chave))
    st.session_state[_CHAVE_SESSION_STATE] = sorted(paginas)


def revogar_pagina_manutencao(chave: str) -> None:
    """
    Remove a autorização de uma página específica da sessão atual.

    Essa função é útil caso você queira implementar um botão de bloqueio ou
    logout apenas para uma página.

    Parâmetros
    ----------
    chave:
        Identificador único da página cuja autorização será removida.
    """
    paginas = obter_paginas_manutencao_liberadas()
    paginas.discard(str(chave))
    st.session_state[_CHAVE_SESSION_STATE] = sorted(paginas)


def limpar_paginas_manutencao_liberadas() -> None:
    """
    Remove todas as autorizações de páginas em manutenção da sessão atual.

    Pode ser usada em um fluxo de logout, troca de usuário ou redefinição de
    permissões.
    """
    st.session_state.pop(_CHAVE_SESSION_STATE, None)


def liberar_varias_paginas_manutencao(chaves: Iterable[str]) -> None:
    """
    Libera várias páginas de uma só vez na sessão atual.

    Parâmetros
    ----------
    chaves:
        Coleção de identificadores de páginas que devem ser autorizadas.
    """
    paginas = obter_paginas_manutencao_liberadas()
    paginas.update(str(chave) for chave in chaves)
    st.session_state[_CHAVE_SESSION_STATE] = sorted(paginas)