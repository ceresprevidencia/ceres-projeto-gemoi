from html import escape
from io import BytesIO

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from utils.helpers import _NOMES_PLANOS
from utils.queries.risco_mercado_planos import buscar_dados


# =========================================================
# CONFIGURAÇÕES DO MÓDULO RRAS
# =========================================================

NOME_MODULO = "RRAS"

LIMITE_VAR = 5.0

COR_VERDE_ESCURO = "#0B2F13"
COR_VERDE_CLARO = "#A8EC7D"
COR_FUNDO_TABELA = "#FAFBEB"
COR_TEXTO = "#0B2F13"
COR_BORDA = "#D9E2D6"
COR_VAR = "#B45309"
COR_STATUS_ABAIXO = "#15803D"
COR_STATUS_ACIMA = "#DC2626"
COR_STATUS_SEM_INFO = "#6B7280"


# =========================================================
# CSS DA TABELA
# =========================================================

CSS_TABELA_RRAS = """
<style>
    .tabela-rras-wrapper {
        width: 100%;
        overflow-x: auto;
        border: 1px solid rgba(11, 47, 19, 0.14);
        border-radius: 14px;
        background-color: #FAFBEB;
        font-family: "Figtree", Arial, sans-serif;
    }

    .tabela-rras {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        table-layout: fixed;
        background-color: #FAFBEB;
    }

    .tabela-rras thead th {
        min-height: 42px;
        padding: 10px 12px;
        background-color: #0B2F13;
        color: #A8EC7D;
        font-size: 12px;
        font-weight: 700;
        line-height: 1.25;
        letter-spacing: 0.02em;
        text-align: left;
        vertical-align: middle;
        white-space: nowrap;
        border: none;
    }

    .tabela-rras thead th:first-child {
        border-top-left-radius: 13px;
    }

    .tabela-rras thead th:last-child {
        border-top-right-radius: 13px;
    }

    .tabela-rras tbody tr {
        background-color: #FAFBEB;
    }

    .tabela-rras tbody tr:hover {
        background-color: rgba(168, 236, 125, 0.10);
    }

    .tabela-rras tbody td {
        min-height: 40px;
        padding: 10px 12px;
        color: #0B2F13;
        font-size: 13px;
        font-weight: 500;
        line-height: 1.25;
        text-align: left;
        vertical-align: middle;
        border: none;
        border-bottom: 1px solid rgba(11, 47, 19, 0.14);
        background-color: transparent;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .tabela-rras tbody tr:last-child td {
        border-bottom: none;
    }

    .tabela-rras tbody tr:last-child td:first-child {
        border-bottom-left-radius: 13px;
    }

    .tabela-rras tbody tr:last-child td:last-child {
        border-bottom-right-radius: 13px;
    }

    .rras-col-plano {
        width: 27%;
        font-weight: 600 !important;
    }

    .rras-col-posicao {
        width: 18%;
    }

    .rras-col-var-rs {
        width: 18%;
    }

    .rras-col-var-pct {
        width: 11%;
    }

    .rras-col-limite {
        width: 11%;
    }

    .rras-col-status {
        width: 15%;
    }

    .rras-valor-var {
        color: #B45309;
        font-weight: 700;
    }

    .rras-status {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 68px;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 700;
        line-height: 1.2;
    }

    .rras-status-abaixo {
        color: #15803D;
        background-color: rgba(34, 197, 94, 0.12);
    }

    .rras-status-acima {
        color: #DC2626;
        background-color: rgba(239, 68, 68, 0.12);
    }

    .rras-status-sem-informacao {
        color: #6B7280;
        background-color: rgba(107, 114, 128, 0.12);
    }
</style>
"""


# =========================================================
# DADOS
# =========================================================

@st.cache_data(ttl="1h")
def carregar_dados_rras() -> pd.DataFrame:
    df = buscar_dados().copy()

    df.columns = (
        df.columns
        .astype(str)
        .str.upper()
        .str.strip()
    )

    colunas_obrigatorias = [
        "TESOURARIA",
        "POSICAO",
        "RISCO",
        "RISCO/POSICAO_%",
        "DATA_COTACAO",
    ]

    colunas_ausentes = [
        coluna
        for coluna in colunas_obrigatorias
        if coluna not in df.columns
    ]

    if colunas_ausentes:
        raise ValueError(
            "Colunas ausentes na consulta RRAS: "
            + ", ".join(colunas_ausentes)
        )

    df["DATA_COTACAO"] = pd.to_datetime(
        df["DATA_COTACAO"],
        errors="coerce",
    )

    for coluna in [
        "POSICAO",
        "RISCO",
        "RISCO/POSICAO_%",
    ]:
        df[coluna] = pd.to_numeric(
            df[coluna],
            errors="coerce",
        )

    return df.dropna(
        subset=["DATA_COTACAO"]
    )


# =========================================================
# FORMATAÇÃO
# =========================================================

def formatar_moeda(valor) -> str:
    if pd.isna(valor):
        return "—"

    texto = f"{float(valor):,.2f}"

    texto = (
        texto
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

    return f"R$ {texto}"


def formatar_percentual(valor) -> str:
    if pd.isna(valor):
        return "—"

    texto = f"{float(valor):,.2f}"

    texto = (
        texto
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

    return f"{texto}%"


def calcular_status(valor) -> str:
    if pd.isna(valor):
        return "Sem informação"

    if float(valor) <= LIMITE_VAR:
        return "Abaixo"

    return "Acima"


def aplicar_nome_plano(valor) -> str:
    if pd.isna(valor):
        return "—"

    valor_texto = str(valor).strip()

    return _NOMES_PLANOS.get(
        valor_texto,
        valor_texto,
    )


# =========================================================
# PREPARAÇÃO DA TABELA
# =========================================================

def preparar_tabela_rras(
    df: pd.DataFrame,
    data_selecionada,
) -> pd.DataFrame:
    df_filtrado = df[
        df["DATA_COTACAO"].dt.date == data_selecionada
    ].copy()

    tabela = df_filtrado[
        [
            "TESOURARIA",
            "POSICAO",
            "RISCO",
            "RISCO/POSICAO_%",
        ]
    ].rename(
        columns={
            "TESOURARIA": "Plano",
            "POSICAO": "Posição",
            "RISCO": "VaR R$",
            "RISCO/POSICAO_%": "VaR %",
        }
    )

    tabela = tabela[
        tabela["Plano"] != "[CERES TOTAL]"
    ].copy()

    tabela["Plano"] = (
        tabela["Plano"]
        .apply(aplicar_nome_plano)
    )

    tabela["Limite"] = LIMITE_VAR

    tabela["Status"] = (
        tabela["VaR %"]
        .apply(calcular_status)
    )

    tabela = tabela[
        [
            "Plano",
            "Posição",
            "VaR R$",
            "VaR %",
            "Limite",
            "Status",
        ]
    ]

    return (
        tabela
        .sort_values(
            by="VaR %",
            ascending=False,
            na_position="last",
        )
        .reset_index(drop=True)
    )


# =========================================================
# HTML DA TABELA
# =========================================================

def gerar_html_rras(
    tabela: pd.DataFrame,
) -> str:
    html = CSS_TABELA_RRAS

    html += """
    <div class="tabela-rras-wrapper">
        <table class="tabela-rras">
            <thead>
                <tr>
                    <th class="rras-col-plano">Plano</th>
                    <th class="rras-col-posicao">Posição</th>
                    <th class="rras-col-var-rs">VaR R$</th>
                    <th class="rras-col-var-pct">VaR %</th>
                    <th class="rras-col-limite">Limite</th>
                    <th class="rras-col-status">Status</th>
                </tr>
            </thead>
            <tbody>
    """

    for _, linha in tabela.iterrows():
        plano = escape(str(linha["Plano"]))
        posicao = escape(formatar_moeda(linha["Posição"]))
        var_rs = escape(formatar_moeda(linha["VaR R$"]))
        var_pct = escape(formatar_percentual(linha["VaR %"]))
        limite = escape(formatar_percentual(linha["Limite"]))
        status = str(linha["Status"])

        if status == "Abaixo":
            classe_status = "rras-status-abaixo"

        elif status == "Acima":
            classe_status = "rras-status-acima"

        else:
            classe_status = "rras-status-sem-informacao"

        html += f"""
            <tr>
                <td class="rras-col-plano" title="{plano}">
                    {plano}
                </td>

                <td class="rras-col-posicao">
                    {posicao}
                </td>

                <td class="rras-col-var-rs">
                    <span class="rras-valor-var">
                        {var_rs}
                    </span>
                </td>

                <td class="rras-col-var-pct">
                    <span class="rras-valor-var">
                        {var_pct}
                    </span>
                </td>

                <td class="rras-col-limite">
                    {limite}
                </td>

                <td class="rras-col-status">
                    <span class="rras-status {classe_status}">
                        {escape(status)}
                    </span>
                </td>
            </tr>
        """

    html += """
            </tbody>
        </table>
    </div>
    """

    return html


# =========================================================
# PNG
# =========================================================

@st.cache_data(show_spinner=False)
def gerar_png_rras(
    tabela: pd.DataFrame,
) -> bytes:
    df_png = tabela.copy()

    df_png["Posição"] = (
        df_png["Posição"]
        .apply(formatar_moeda)
    )

    df_png["VaR R$"] = (
        df_png["VaR R$"]
        .apply(formatar_moeda)
    )

    df_png["VaR %"] = (
        df_png["VaR %"]
        .apply(formatar_percentual)
    )

    df_png["Limite"] = (
        df_png["Limite"]
        .apply(formatar_percentual)
    )

    quantidade_linhas = max(
        len(df_png),
        1,
    )

    altura_total = (
        0.48
        + quantidade_linhas * 0.46
    )

    figura, eixo = plt.subplots(
        figsize=(15, altura_total)
    )

    figura.patch.set_facecolor(
        COR_FUNDO_TABELA
    )

    eixo.set_facecolor(
        COR_FUNDO_TABELA
    )

    eixo.axis("off")

    tabela_plot = eixo.table(
        cellText=df_png.values,
        colLabels=df_png.columns,
        cellLoc="left",
        colLoc="left",
        bbox=[0, 0, 1, 1],
        colWidths=[
            0.27,
            0.18,
            0.18,
            0.11,
            0.11,
            0.15,
        ],
    )

    tabela_plot.auto_set_font_size(False)
    tabela_plot.set_fontsize(10)

    for (
        linha,
        coluna,
    ), celula in tabela_plot.get_celld().items():
        celula.PAD = 0.08
        celula.set_linewidth(0)

        texto = celula.get_text()

        texto.set_fontfamily(
            "DejaVu Sans"
        )

        texto.set_horizontalalignment(
            "left"
        )

        texto.set_verticalalignment(
            "center"
        )

        if linha == 0:
            celula.set_facecolor(
                COR_VERDE_ESCURO
            )

            texto.set_color(
                COR_VERDE_CLARO
            )

            texto.set_fontweight(
                "bold"
            )

        else:
            celula.set_facecolor(
                COR_FUNDO_TABELA
            )

            texto.set_color(
                COR_TEXTO
            )

            nome_coluna = (
                df_png.columns[coluna]
            )

            if nome_coluna == "Plano":
                texto.set_fontweight(
                    "bold"
                )

            elif nome_coluna in [
                "VaR R$",
                "VaR %",
            ]:
                texto.set_color(
                    COR_VAR
                )

                texto.set_fontweight(
                    "bold"
                )

            elif nome_coluna == "Status":
                status = str(
                    df_png.iloc[
                        linha - 1
                    ]["Status"]
                )

                texto.set_fontweight(
                    "bold"
                )

                if status == "Abaixo":
                    texto.set_color(
                        COR_STATUS_ABAIXO
                    )

                elif status == "Acima":
                    texto.set_color(
                        COR_STATUS_ACIMA
                    )

                else:
                    texto.set_color(
                        COR_STATUS_SEM_INFO
                    )

    total_linhas = quantidade_linhas + 1

    for indice in range(
        1,
        total_linhas,
    ):
        y = 1 - indice / total_linhas

        eixo.plot(
            [0, 1],
            [y, y],
            transform=eixo.transAxes,
            color=COR_BORDA,
            linewidth=0.7,
            clip_on=False,
        )

    figura.subplots_adjust(
        left=0,
        right=1,
        top=1,
        bottom=0,
    )

    buffer = BytesIO()

    figura.savefig(
        buffer,
        format="png",
        dpi=200,
        bbox_inches="tight",
        pad_inches=0,
        facecolor=COR_FUNDO_TABELA,
    )

    plt.close(figura)

    buffer.seek(0)

    return buffer.getvalue()


# =========================================================
# FUNÇÃO PRINCIPAL DO MÓDULO
# =========================================================

def renderizar_rras():
    try:
        df = carregar_dados_rras()

    except Exception as erro:
        st.error(
            f"Erro ao carregar RRAS: {erro}"
        )
        return

    if df.empty:
        st.warning(
            "Não foram encontrados dados para o RRAS."
        )
        return

    datas_disponiveis = sorted(
        df["DATA_COTACAO"]
        .dt.date
        .dropna()
        .unique()
    )

    if not datas_disponiveis:
        st.warning(
            "Não existem datas disponíveis para o RRAS."
        )
        return

    coluna_data, coluna_botao = st.columns(
        [0.72, 0.28],
        vertical_alignment="bottom",
    )

    with coluna_data:
        data_selecionada = st.date_input(
            "Selecione a data posição",
            value=datas_disponiveis[-1],
            min_value=datas_disponiveis[0],
            max_value=datas_disponiveis[-1],
            format="DD/MM/YYYY",
            key="data_exportavel_rras",
        )

    if data_selecionada not in datas_disponiveis:
        st.warning(
            "Não existem dados para "
            f"{data_selecionada.strftime('%d/%m/%Y')}."
        )
        return

    tabela = preparar_tabela_rras(
        df=df,
        data_selecionada=data_selecionada,
    )

    if tabela.empty:
        st.info(
            "Não existem registros RRAS para a data selecionada."
        )
        return

    html_tabela = gerar_html_rras(
        tabela
    )

    png_tabela = gerar_png_rras(
        tabela
    )

    with coluna_botao:
        st.download_button(
            label="Exportar RRAS em PNG",
            data=png_tabela,
            file_name=(
                "rras_"
                f"{data_selecionada.strftime('%Y%m%d')}"
                ".png"
            ),
            mime="image/png",
            type="primary",
            width="stretch",
            key="download_rras_png",
        )

    st.space(
        size="small"
    )

    st.html(
        html_tabela
    )