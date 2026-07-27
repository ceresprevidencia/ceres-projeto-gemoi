import html
import re
from datetime import date, datetime

import pandas as pd
import streamlit as st

from utils.ddq_utils.crud import (
    atualizar_resposta,
    listar_gestoras_preenchimento,
    listar_respostas,
)


# ===========================================================================
# CONFIGURAÇÃO DA PÁGINA
# ===========================================================================

st.set_page_config(
    page_title="Análise Qualitativa do Gestor",
    layout="wide",
)


# ===========================================================================
# FUNÇÕES AUXILIARES
# ===========================================================================

def valor_seguro(
    valor,
    padrao: str = "Não informado",
) -> str:
    """Evita exibir valores vazios na interface."""

    if valor is None:
        return padrao

    try:
        if pd.isna(valor):
            return padrao
    except (TypeError, ValueError):
        pass

    texto = str(valor).strip()

    if not texto or texto.lower() in {
        "none",
        "nan",
        "nat",
        "<na>",
    }:
        return padrao

    return texto


def formatar_cnpj(
    valor,
    padrao: str = "Não informado",
) -> str:
    """
    Formata o CNPJ como 00.000.000/0000-00.

    Aceita valores com ou sem pontuação.
    Caso o valor não tenha 14 dígitos, mantém
    o conteúdo original.
    """

    texto = valor_seguro(
        valor,
        padrao,
    )

    if texto == padrao:
        return padrao

    digitos = re.sub(
        r"\D",
        "",
        texto,
    )

    if len(digitos) != 14:
        return texto

    return (
        f"{digitos[0:2]}."
        f"{digitos[2:5]}."
        f"{digitos[5:8]}/"
        f"{digitos[8:12]}-"
        f"{digitos[12:14]}"
    )


def formatar_data(
    valor,
    padrao: str = "Não informado",
) -> str:
    """
    Formata datas para dd/mm/aaaa, removendo o horário.

    Exemplos:
    2026-07-27 10:27:24 -> 27/07/2026
    27/07/2026 10:27:24 -> 27/07/2026
    """

    if valor is None:
        return padrao

    try:
        if pd.isna(valor):
            return padrao
    except (TypeError, ValueError):
        pass

    if isinstance(
        valor,
        (
            datetime,
            date,
            pd.Timestamp,
        ),
    ):
        return valor.strftime(
            "%d/%m/%Y"
        )

    texto = str(valor).strip()

    if not texto or texto.lower() in {
        "none",
        "nan",
        "nat",
        "<na>",
    }:
        return padrao

    formatos = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y",
    ]

    for formato in formatos:
        try:
            data = datetime.strptime(
                texto,
                formato,
            )

            return data.strftime(
                "%d/%m/%Y"
            )

        except ValueError:
            continue

    data_convertida = pd.to_datetime(
        texto,
        errors="coerce",
        dayfirst=True,
    )

    if pd.isna(
        data_convertida
    ):
        return texto

    return data_convertida.strftime(
        "%d/%m/%Y"
    )


def tratar_status_gestora(
    status,
    padrao: str = "Não informado",
) -> str:
    """
    Remove a data e o horário anexados ao status.

    Exemplos:
    Inativa - 27/07/2026 10:27:24 -> Inativa
    Ativa - 27/07/2026 10:27:24   -> Ativa
    """

    status_texto = valor_seguro(
        status,
        padrao,
    )

    if status_texto == padrao:
        return padrao

    status_limpo = status_texto.split(
        " - ",
        maxsplit=1,
    )[0].strip()

    mapa_status = {
        "ATIVO": "Ativa",
        "ATIVA": "Ativa",
        "INATIVO": "Inativa",
        "INATIVA": "Inativa",
    }

    return mapa_status.get(
        status_limpo.upper(),
        status_limpo,
    )


def classe_status(
    status: str,
) -> str:
    """Retorna a classe CSS correspondente ao vencimento."""

    mapa = {
        "Em dia": "status-em-dia",
        "A vencer": "status-a-vencer",
        "Vencido": "status-vencido",
        "Não preenchida": "status-nao-preenchida",
    }

    return mapa.get(
        status,
        "status-neutro",
    )


def classe_status_gestora(
    status: str,
) -> str:
    """Retorna a classe CSS do status cadastral da gestora."""

    status_normalizado = (
        tratar_status_gestora(
            status
        )
        .strip()
        .upper()
    )

    if status_normalizado in {
        "ATIVO",
        "ATIVA",
    }:
        return "gestora-ativa"

    if status_normalizado in {
        "INATIVO",
        "INATIVA",
    }:
        return "gestora-inativa"

    return "gestora-status-neutro"


def separar_indice_pergunta(
    pergunta: str,
) -> tuple[str, str]:
    """
    Considera os três primeiros caracteres como índice.

    Exemplo:
    '1.1 Qual é a política de risco?'

    Retorna:
    ('1.1', 'Qual é a política de risco?')
    """

    pergunta = valor_seguro(
        pergunta,
        "Pergunta não informada",
    )

    indice = pergunta[:3].strip()
    texto_pergunta = pergunta[3:].strip()

    texto_pergunta = texto_pergunta.lstrip(
        " -–—.:"
    ).strip()

    if not texto_pergunta:
        texto_pergunta = pergunta

    return indice, texto_pergunta


# ===========================================================================
# CSS
# ===========================================================================

st.html(
    """
    <style>

    /* ======================================================
       PALETA

       Confiança: #016837
       Movimento: #A8EC7D
       Estrutura: #0B2F13
       Horizonte: #2DC25F
       Liberdade: #FAFBEB
       ====================================================== */

    .block-container {
        max-width: 1400px;
        padding-top: 3.8rem;
        padding-bottom: 3rem;
    }


    /* ======================================================
       CABEÇALHO
       ====================================================== */

    .page-header {
        position: relative;
        overflow: hidden;

        padding: 28px 30px;
        margin-bottom: 20px;

        border:
            1px solid
            rgba(1, 104, 55, 0.16);

        border-radius: 18px;

        background: #FAFBEB;

        box-shadow:
            0 6px 22px
            rgba(11, 47, 19, 0.07);
    }

    .page-header::after {
        content: "";

        position: absolute;
        top: -85px;
        right: -65px;

        width: 220px;
        height: 220px;

        border-radius: 50%;

        background:
            rgba(168, 236, 125, 0.35);
    }

    .page-header-content {
        position: relative;
        z-index: 1;
    }

    .page-eyebrow {
        margin-bottom: 8px;

        color: #016837;

        font-size: 0.73rem;
        font-weight: 750;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .page-title {
        margin: 0;

        color: #0B2F13;

        font-size:
            clamp(
                1.5rem,
                2.1vw,
                2.2rem
            );

        font-weight: 780;
        line-height: 1.25;
    }

    .page-description {
        max-width: 820px;

        margin-top: 10px;
        margin-bottom: 0;

        color: #496151;

        font-size: 0.9rem;
        line-height: 1.55;
    }


    /* ======================================================
       STATUS DE VENCIMENTO
       ====================================================== */

    .status-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;

        min-height: 31px;

        padding: 6px 14px;
        margin-top: 16px;

        border-radius: 999px;

        font-size: 0.74rem;
        font-weight: 750;
        white-space: nowrap;
    }

    .status-em-dia {
        color: #016837;

        background:
            rgba(168, 236, 125, 0.42);

        border:
            1px solid
            rgba(1, 104, 55, 0.16);
    }

    .status-a-vencer {
        color: #725200;
        background: #fff0b3;
        border: 1px solid #ead98d;
    }

    .status-vencido {
        color: #a4261d;
        background: #fde8e6;
        border: 1px solid #f2c5c1;
    }

    .status-nao-preenchida,
    .status-neutro {
        color: #536058;
        background: #edf0ed;
        border: 1px solid #d9dfda;
    }


    /* ======================================================
       CARDS DE INFORMAÇÃO
       ====================================================== */

    .info-card {
        height: 100%;
        min-height: 108px;

        padding: 17px 18px;

        border:
            1px solid
            rgba(1, 104, 55, 0.13);

        border-radius: 14px;

        background: #FAFBEB;

        box-shadow:
            0 3px 12px
            rgba(11, 47, 19, 0.045);

        overflow: hidden;
        box-sizing: border-box;
    }

    .info-card-label {
        margin-bottom: 8px;

        color: #016837;

        font-size: 0.68rem;
        font-weight: 750;
        letter-spacing: 0.045em;
        text-transform: uppercase;
    }

    .info-card-value {
        min-width: 0;

        color: #0B2F13;

        font-size: 0.87rem;
        font-weight: 650;
        line-height: 1.45;

        overflow-wrap: anywhere;
        word-break: break-word;
    }


    /* ======================================================
       CARD DE CONTATO
       ====================================================== */

    .contact-wrapper {
        width: 100%;
        min-width: 0;
        overflow: hidden;
    }

    .contact-email {
        display: -webkit-box;

        width: 100%;
        max-width: 100%;

        overflow: hidden;

        -webkit-box-orient: vertical;
        -webkit-line-clamp: 2;

        color: #0B2F13;

        line-height: 1.4;

        overflow-wrap: anywhere;
        word-break: break-word;

        cursor: help;
    }

    .contact-phone {
        width: 100%;
        max-width: 100%;

        margin-top: 7px;

        color: #627168;

        font-size: 0.78rem;
        font-weight: 600;
        line-height: 1.35;

        overflow-wrap: anywhere;
        word-break: break-word;
    }


    /* ======================================================
       STATUS CADASTRAL DA GESTORA
       ====================================================== */

    .status-gestora {
        display: inline-flex;
        align-items: center;
        justify-content: center;

        min-width: 88px;
        min-height: 30px;

        padding: 6px 13px;

        border-radius: 999px;

        font-size: 0.74rem;
        font-weight: 750;
        line-height: 1;

        text-transform: uppercase;
        white-space: nowrap;
    }

    .gestora-ativa {
        color: #016837;

        background:
            rgba(168, 236, 125, 0.42);

        border:
            1px solid
            rgba(1, 104, 55, 0.18);
    }

    .gestora-inativa {
        color: #a4261d;
        background: #fde8e6;
        border: 1px solid #f2c5c1;
    }

    .gestora-status-neutro {
        color: #536058;
        background: #edf0ed;
        border: 1px solid #d9dfda;
    }


    /* ======================================================
       BOTÃO VOLTAR
       ====================================================== */

    [class*="st-key-voltar_pagina"] {
        margin-top: 15px;
        margin-bottom: 28px;
    }

    [class*="st-key-voltar_pagina"]
    .stButton > button {
        min-height: 40px;

        padding-left: 18px;
        padding-right: 18px;

        border:
            1px solid
            rgba(1, 104, 55, 0.22);

        border-radius: 10px;

        color: #016837;
        background: #FAFBEB;

        font-size: 0.8rem;
        font-weight: 700;

        transition:
            background 0.16s ease,
            border-color 0.16s ease,
            transform 0.16s ease;
    }

    [class*="st-key-voltar_pagina"]
    .stButton > button:hover {
        color: #0B2F13;

        background:
            rgba(168, 236, 125, 0.32);

        border-color: #016837;

        transform: translateY(-1px);
    }


    /* ======================================================
       TÍTULO DA SEÇÃO
       ====================================================== */

    .section-heading {
        display: flex;
        align-items: center;
        justify-content: space-between;

        gap: 16px;

        margin-top: 8px;
        margin-bottom: 17px;
    }

    .section-title {
        margin: 0;

        color: #0B2F13;

        font-size: 1.18rem;
        font-weight: 760;
    }

    .section-description {
        margin-top: 4px;

        color: #67756b;

        font-size: 0.82rem;
    }

    .response-counter {
        display: inline-flex;
        align-items: center;
        justify-content: center;

        min-width: 100px;

        padding: 8px 14px;

        border:
            1px solid
            rgba(1, 104, 55, 0.13);

        border-radius: 999px;

        color: #016837;

        background:
            rgba(168, 236, 125, 0.28);

        font-size: 0.75rem;
        font-weight: 750;
        white-space: nowrap;
    }


    /* ======================================================
       CARD DE RESPOSTA
       ====================================================== */

    [class*="st-key-resposta_card_"] {
        margin-bottom: 15px;
        padding: 20px 22px;

        border:
            1px solid
            rgba(1, 104, 55, 0.13);

        border-radius: 16px;

        background: #FAFBEB;

        box-shadow:
            0 4px 14px
            rgba(11, 47, 19, 0.05);

        transition:
            transform 0.18s ease,
            box-shadow 0.18s ease,
            border-color 0.18s ease;
    }

    [class*="st-key-resposta_card_"]:hover {
        transform: translateY(-2px);

        border-color:
            rgba(1, 104, 55, 0.28);

        box-shadow:
            0 9px 23px
            rgba(11, 47, 19, 0.09);
    }

    [class*="st-key-resposta_card_"]
    [data-testid="stVerticalBlock"] {
        gap: 0.5rem;
    }


    /* ======================================================
       PERGUNTA
       ====================================================== */

    .question-header {
        display: flex;
        align-items: flex-start;

        gap: 13px;

        margin-bottom: 4px;
    }

    .question-index {
        display: inline-flex;
        align-items: center;
        justify-content: center;

        min-width: 49px;
        height: 38px;

        padding: 0 9px;

        border-radius: 10px;

        color: #FAFBEB;
        background: #016837;

        font-size: 0.78rem;
        font-weight: 750;
        line-height: 1;
    }

    .question-content {
        flex: 1;
        min-width: 0;
    }

    .question-label {
        margin-bottom: 4px;

        color: #43805d;

        font-size: 0.66rem;
        font-weight: 750;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .question-text {
        color: #0B2F13;

        font-size: 0.94rem;
        font-weight: 700;
        line-height: 1.5;

        overflow-wrap: anywhere;
    }


    /* ======================================================
       CAIXA DA RESPOSTA
       ====================================================== */

    .answer-box {
        margin-top: 12px;
        margin-left: 62px;

        padding: 15px 17px;

        border-left:
            4px solid #2DC25F;

        border-radius:
            0 11px 11px 0;

        color: #33493a;

        background:
            rgba(168, 236, 125, 0.16);

        font-size: 0.87rem;
        line-height: 1.65;

        white-space: pre-wrap;
        overflow-wrap: anywhere;
    }

    .answer-id {
        margin-top: 8px;
        margin-left: 62px;

        color: #819087;

        font-size: 0.65rem;
    }


    /* ======================================================
       BOTÃO EDITAR
       ====================================================== */

    [class*="st-key-resposta_card_"]
    .stButton > button {
        min-height: 39px;

        border:
            1px solid
            rgba(1, 104, 55, 0.22);

        border-radius: 9px;

        color: #016837;
        background: transparent;

        font-size: 0.76rem;
        font-weight: 700;

        transition:
            background 0.16s ease,
            border-color 0.16s ease,
            transform 0.16s ease;
    }

    [class*="st-key-resposta_card_"]
    .stButton > button:hover {
        transform: translateY(-1px);

        color: #0B2F13;

        background:
            rgba(168, 236, 125, 0.3);

        border-color: #016837;
    }


    /* ======================================================
       ESTADO VAZIO
       ====================================================== */

    .empty-state {
        padding: 48px 25px;

        border:
            1px dashed
            rgba(1, 104, 55, 0.25);

        border-radius: 16px;

        color: #657268;
        background: #FAFBEB;

        text-align: center;
    }

    .empty-state-title {
        margin-bottom: 6px;

        color: #0B2F13;

        font-size: 1rem;
        font-weight: 750;
    }


    /* ======================================================
       RESPONSIVIDADE
       ====================================================== */

    @media (max-width: 768px) {

        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .page-header {
            padding: 22px 20px;
        }

        .page-title {
            font-size: 1.4rem;
        }

        .section-heading {
            align-items: flex-start;
            flex-direction: column;
        }

        [class*="st-key-resposta_card_"] {
            padding: 17px 16px;
        }

        .question-index {
            min-width: 44px;
        }

        .answer-box,
        .answer-id {
            margin-left: 0;
        }

        .info-card {
            min-height: auto;
        }
    }

    </style>
    """
)


# ===========================================================================
# DIALOG DE EDIÇÃO
# ===========================================================================

@st.dialog(
    "Editar resposta",
    width="large",
)
def editar_resposta(
    id_resposta: str,
    pergunta: str,
    resposta_atual: str | None,
) -> None:
    """Exibe o diálogo para alterar uma resposta."""

    indice_pergunta, texto_pergunta = (
        separar_indice_pergunta(
            pergunta
        )
    )

    indice_html = html.escape(
        indice_pergunta
    )

    pergunta_html = html.escape(
        texto_pergunta
    )

    st.html(
        f"""
        <div style="
            padding: 15px 17px;
            margin-bottom: 16px;
            border: 1px solid rgba(1, 104, 55, 0.15);
            border-radius: 12px;
            background: #FAFBEB;
        ">

            <div style="
                display: flex;
                align-items: flex-start;
                gap: 12px;
            ">

                <div style="
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    min-width: 48px;
                    height: 36px;
                    padding: 0 8px;
                    border-radius: 9px;
                    color: #FAFBEB;
                    background: #016837;
                    font-size: 0.76rem;
                    font-weight: 750;
                ">
                    {indice_html}
                </div>

                <div style="
                    color: #0B2F13;
                    font-size: 0.9rem;
                    font-weight: 680;
                    line-height: 1.5;
                ">
                    {pergunta_html}
                </div>

            </div>

        </div>
        """
    )

    nova_resposta = st.text_area(
        "Nova resposta",
        value=resposta_atual or "",
        height=190,
        key=f"editar_resposta_{id_resposta}",
        placeholder="Digite a nova resposta...",
    )

    st.info(
        "Para confirmar a alteração, digite "
        "**ALTERAR** no campo abaixo.",
        icon=":material/info:",
    )

    texto_confirmacao = st.text_input(
        "Confirmação",
        key=(
            f"confirmacao_alteracao_"
            f"{id_resposta}"
        ),
        placeholder="Digite ALTERAR",
    )

    confirmacao_valida = (
        texto_confirmacao.strip()
        == "ALTERAR"
    )

    if (
        texto_confirmacao
        and not confirmacao_valida
    ):
        st.error(
            "Digite exatamente ALTERAR, "
            "em letras maiúsculas."
        )

    salvar = st.button(
        "Salvar alteração",
        type="primary",
        icon=":material/save:",
        width="content",
        disabled=not confirmacao_valida,
        key=f"salvar_resposta_{id_resposta}",
    )

    if not salvar:
        return

    nova_resposta = nova_resposta.strip()

    if not nova_resposta:
        st.error(
            "A resposta não pode ficar vazia."
        )
        return

    if nova_resposta == (
        resposta_atual or ""
    ).strip():
        st.info(
            "Nenhuma alteração foi identificada."
        )
        return

    try:
        atualizar_resposta(
            id_resposta=id_resposta,
            nova_resposta=nova_resposta,
        )

        st.session_state[
            "resposta_atualizada"
        ] = True

        st.rerun()

    except ValueError as erro:
        st.error(str(erro))

    except Exception as erro:
        st.error(
            "Não foi possível atualizar a resposta."
        )
        st.exception(erro)


# ===========================================================================
# LEITURA DOS QUERY PARAMS
# ===========================================================================

id_gestora = st.query_params.get(
    "id_gestora"
)

id_preenchimento = st.query_params.get(
    "id_preenchimento"
)

status_vencimento = st.query_params.get(
    "status_vencimento"
)

data_vencimento = st.query_params.get(
    "data_vencimento"
)


if (
    not id_gestora
    or not id_preenchimento
):
    st.error(
        "Parâmetros inválidos. "
        "Volte à página anterior."
    )
    st.stop()


# ===========================================================================
# CARREGAMENTO DOS DADOS
# ===========================================================================

preenchimentos_df = (
    listar_gestoras_preenchimento()
)

gestoras_selecionada_preenchimento = (
    preenchimentos_df[
        preenchimentos_df[
            "id_gestora"
        ]
        == int(id_gestora)
    ]
)


gestoras_respostas_df = (
    listar_respostas()
)

gestoras_selecionada_respostas = (
    gestoras_respostas_df[
        gestoras_respostas_df[
            "id_preenchimento"
        ]
        == int(
            float(
                id_preenchimento
            )
        )
    ]
)


if (
    gestoras_selecionada_preenchimento
    .empty
):
    st.error(
        "Não foi possível localizar os dados "
        "da gestora selecionada."
    )
    st.stop()


# ===========================================================================
# DADOS DA GESTORA
# ===========================================================================

dados_gestora = (
    gestoras_selecionada_preenchimento
    .iloc[0]
)

nome_gestora = valor_seguro(
    dados_gestora.get("nome"),
    "Gestora não identificada",
)

data_envio = formatar_data(
    dados_gestora.get(
        "data_envio"
    ),
)

cnpj = formatar_cnpj(
    dados_gestora.get(
        "cnpj"
    ),
)

email = valor_seguro(
    dados_gestora.get(
        "email"
    ),
)

telefone = valor_seguro(
    dados_gestora.get(
        "telefone"
    ),
)

status_gestora = tratar_status_gestora(
    dados_gestora.get(
        "status"
    ),
)

status_vencimento = valor_seguro(
    status_vencimento,
    "Não informado",
)

data_vencimento = formatar_data(
    data_vencimento,
)

quantidade_respostas = len(
    gestoras_selecionada_respostas
)


# ===========================================================================
# MENSAGEM DE SUCESSO
# ===========================================================================

if st.session_state.pop(
    "resposta_atualizada",
    False,
):
    st.toast(
        "Resposta atualizada com sucesso.",
    )


# ===========================================================================
# CABEÇALHO
# ===========================================================================

nome_html = html.escape(
    nome_gestora
)

status_html = html.escape(
    status_vencimento
)

st.html(
    f"""
    <section class="page-header">

        <div class="page-header-content">

            <div class="page-eyebrow">
                Questionário Due Diligence
            </div>

            <h1 class="page-title">
                Análise Qualitativa do Gestor –
                {nome_html}
            </h1>

            <p class="page-description">
                Consulte as informações do preenchimento
                e as respostas apresentadas pela gestora.
            </p>

            <span class="
                status-badge
                {classe_status(status_vencimento)}
            ">
                {status_html}
            </span>

        </div>

    </section>
    """
)


# ===========================================================================
# CARDS DE INFORMAÇÃO
# ===========================================================================

info_colunas = st.columns(
    5,
    gap="small",
)

informacoes = [
    (
        "Diligência",
        data_envio,
    ),
    (
        "Vigência",
        data_vencimento,
    ),
    (
        "CNPJ",
        cnpj,
    ),
    (
        "Contato",
        "",
    ),
    (
        "Status da gestora",
        status_gestora,
    ),
]


for coluna, (
    rotulo,
    valor,
) in zip(
    info_colunas,
    informacoes,
):

    with coluna:

        rotulo_html = html.escape(
            rotulo
        )

        if rotulo == "Contato":

            email_html = html.escape(
                email
            )

            email_title = html.escape(
                email,
                quote=True,
            )

            telefone_html = html.escape(
                telefone
            )

            valor_html = f"""
                <div class="contact-wrapper">

                    <div
                        class="contact-email"
                        title="{email_title}"
                    >
                        {email_html}
                    </div>

                    <div class="contact-phone">
                        {telefone_html}
                    </div>

                </div>
            """

        elif rotulo == "Status da gestora":

            valor_html = f"""
                <span class="
                    status-gestora
                    {
                        classe_status_gestora(
                            status_gestora
                        )
                    }
                ">
                    {
                        html.escape(
                            status_gestora
                        )
                    }
                </span>
            """

        else:

            valor_html = html.escape(
                str(valor)
            )

        st.html(
            f"""
            <div class="info-card">

                <div class="info-card-label">
                    {rotulo_html}
                </div>

                <div class="info-card-value">
                    {valor_html}
                </div>

            </div>
            """
        )


# ===========================================================================
# BOTÃO VOLTAR
# ===========================================================================

with st.container(
    key="voltar_pagina",
):

    if st.button(
        "Voltar para gestoras",
        icon=":material/arrow_back:",
    ):
        st.switch_page(
            "pages/s3_due_diligence_hp.py"
        )


# ===========================================================================
# TÍTULO DA SEÇÃO
# ===========================================================================

st.html(
    f"""
    <div class="section-heading">

        <div>

            <h2 class="section-title">
                Respostas do questionário
            </h2>

            <div class="section-description">
                Consulte ou edite as respostas
                apresentadas pela gestora.
            </div>

        </div>

        <div class="response-counter">
            {quantidade_respostas}
            {
                " resposta"
                if quantidade_respostas == 1
                else " respostas"
            }
        </div>

    </div>
    """
)


# ===========================================================================
# LISTA DE RESPOSTAS
# ===========================================================================

gestoras_selecionada_respostas = (
    gestoras_selecionada_respostas
    .sort_values(
        by="pergunta"
    )
)


if (
    gestoras_selecionada_respostas
    .empty
):

    st.html(
        """
        <div class="empty-state">

            <div class="empty-state-title">
                Nenhuma resposta localizada
            </div>

            <div>
                Não existem respostas vinculadas
                a este preenchimento.
            </div>

        </div>
        """
    )

else:

    for _, registro in (
        gestoras_selecionada_respostas
        .iterrows()
    ):

        id_resposta = registro[
            "id_resposta"
        ]

        pergunta_original = valor_seguro(
            registro["pergunta"],
            "Pergunta não informada",
        )

        resposta = valor_seguro(
            registro["resposta"],
            "Resposta não informada",
        )

        indice_pergunta, pergunta = (
            separar_indice_pergunta(
                pergunta_original
            )
        )

        indice_html = html.escape(
            indice_pergunta
        )

        pergunta_html = html.escape(
            pergunta
        )

        resposta_html = html.escape(
            resposta
        )

        id_resposta_html = html.escape(
            str(
                id_resposta
            )
        )

        with st.container(
            key=(
                f"resposta_card_"
                f"{id_resposta}"
            ),
        ):

            coluna_conteudo, coluna_botao = (
                st.columns(
                    [
                        6,
                        1,
                    ],
                    gap="medium",
                    vertical_alignment="top",
                )
            )

            with coluna_conteudo:

                st.html(
                    f"""
                    <div class="question-header">

                        <div class="question-index">
                            {indice_html}
                        </div>

                        <div class="question-content">

                            <div class="question-label">
                                Pergunta
                            </div>

                            <div class="question-text">
                                {pergunta_html}
                            </div>

                        </div>

                    </div>

                    <div class="answer-box">
                        {resposta_html}
                    </div>

                    <div class="answer-id">
                        ID da resposta:
                        {id_resposta_html}
                    </div>
                    """
                )

            with coluna_botao:

                if st.button(
                    "Editar",
                    icon=":material/edit:",
                    key=(
                        f"editar_"
                        f"{id_resposta}"
                    ),
                    width="content",
                ):
                    editar_resposta(
                        id_resposta=id_resposta,
                        pergunta=pergunta_original,
                        resposta_atual=resposta,
                    )