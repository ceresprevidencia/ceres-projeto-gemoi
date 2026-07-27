from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from utils.ddq_utils.criar_db import criar_banco
from utils.ddq_utils.crud import (
    atualizar_gestora,
    excluir_gestoras,
    listar_gestoras,
)
from utils.ddq_utils.etl import executar_etl


# ===========================================================================
# CONFIGURAÇÃO DA PÁGINA
# ===========================================================================

st.set_page_config(
    page_title="Configurações da Diligência",
    layout="wide",
)


# ===========================================================================
# FUNÇÕES AUXILIARES
# ===========================================================================

def inicializar_estado() -> None:
    """Inicializa os estados utilizados pela página."""

    st.session_state.setdefault(
        "gestoras_selecionadas_exclusao",
        [],
    )

    st.session_state.setdefault(
        "exclusao_concluida",
        False,
    )

    st.session_state.setdefault(
        "mensagem_exclusao",
        None,
    )


def limpar_estado_exclusao() -> None:
    """Limpa os dados temporários da exclusão."""

    st.session_state[
        "exclusao_concluida"
    ] = False

    st.session_state[
        "mensagem_exclusao"
    ] = None

    st.session_state.pop(
        "confirmacao_texto_exclusao",
        None,
    )


def carregar_gestoras() -> pd.DataFrame:
    """Busca as gestoras cadastradas."""

    try:
        return listar_gestoras()

    except Exception as erro:
        st.error(
            "Não foi possível carregar as gestoras."
        )
        st.exception(erro)

        return pd.DataFrame()


def valor_seguro(
    valor,
    padrao: str = "—",
) -> str:
    """Evita exibir valores vazios."""

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


def tratar_status_gestora(
    status,
) -> str:
    """
    Remove a data eventualmente anexada ao status.

    Exemplo:
    Inativa - 27/07/2026 10:27:24 -> Inativa
    """

    status_texto = valor_seguro(
        status,
        "Ativa",
    )

    return (
        status_texto
        .split(" - ", maxsplit=1)[0]
        .strip()
        .capitalize()
    )


def classe_status_gestora(
    status: str,
) -> str:
    """Retorna a classe visual do status."""

    status_normalizado = (
        tratar_status_gestora(status)
        .upper()
    )

    if status_normalizado in {
        "ATIVA",
        "ATIVO",
    }:
        return "status-ativa"

    if status_normalizado in {
        "INATIVA",
        "INATIVO",
    }:
        return "status-inativa"

    return "status-neutro"


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
        max-width: 1420px;
        padding-top: 3.8rem;
        padding-left: 2.5rem;
        padding-right: 2.5rem;
        padding-bottom: 4rem;
    }


    /* ======================================================
       CABEÇALHO
       ====================================================== */

    .settings-header {
        position: relative;

        margin-bottom: 28px;
        padding: 27px 29px;

        border-left: 6px solid #2DC25F;
        border-radius: 0 17px 17px 0;

        background:
            linear-gradient(
                105deg,
                #0B2F13 0%,
                #123f20 58%,
                #016837 100%
            );

        box-shadow:
            0 8px 23px
            rgba(11, 47, 19, 0.16);
    }

    .settings-header-content {
        display: flex;
        align-items: center;
        justify-content: space-between;

        gap: 22px;
    }

    .settings-header-text {
        min-width: 0;
    }

    .settings-header-kicker {
        margin-bottom: 7px;

        color: #A8EC7D;

        font-size: 0.68rem;
        font-weight: 750;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .settings-header-title {
        margin: 0;

        color: #FAFBEB;

        font-size:
            clamp(1.5rem, 2.1vw, 2.15rem);

        font-weight: 680;
        line-height: 1.2;
    }

    .settings-header-description {
        max-width: 760px;

        margin-top: 8px;
        margin-bottom: 0;

        color:
            rgba(250, 251, 235, 0.72);

        font-size: 0.82rem;
        line-height: 1.5;
    }

    .settings-header-line {
        width: 94px;
        height: 4px;
        min-width: 94px;

        border-radius: 999px;

        background:
            linear-gradient(
                90deg,
                #A8EC7D,
                #2DC25F
            );
    }


    /* ======================================================
       ABAS
       ====================================================== */

    [data-testid="stTabs"] {
        margin-top: 5px;
    }

    [data-testid="stTabs"]
    [data-baseweb="tab-list"] {
        gap: 8px;

        padding: 6px;

        border:
            1px solid
            rgba(1, 104, 55, 0.13);

        border-radius: 13px;

        background: #FAFBEB;
    }

    [data-testid="stTabs"]
    [data-baseweb="tab"] {
        min-height: 42px;

        padding-left: 18px;
        padding-right: 18px;

        border-radius: 12px;

        color: #53645a;

        font-size: 0.8rem;
        font-weight: 700;
    }

    [data-testid="stTabs"]
    [aria-selected="true"] {
        color: #FAFBEB;
        background: #016837;
    }

    [data-testid="stTabs"]
    [data-baseweb="tab-highlight"] {
        display: none;
    }

    [data-testid="stTabs"]
    [data-baseweb="tab-border"] {
        display: none;
    }


    /* ======================================================
       CABEÇALHOS DAS SEÇÕES
       ====================================================== */

    .panel-heading {
        margin-top: 22px;
        margin-bottom: 17px;
    }

    .panel-eyebrow {
        margin-bottom: 5px;

        color: #016837;

        font-size: 0.67rem;
        font-weight: 750;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }

    .panel-title {
        margin: 0;

        color: #0B2F13;

        font-size: 1.25rem;
        font-weight: 770;
        line-height: 1.3;
    }

    .panel-description {
        max-width: 810px;

        margin-top: 6px;

        color: #6c7970;

        font-size: 0.81rem;
        line-height: 1.55;
    }


    /* ======================================================
       BLOCOS DE ORIENTAÇÃO
       ====================================================== */

    .info-strip {
        display: flex;
        align-items: flex-start;

        gap: 12px;

        margin-bottom: 17px;
        padding: 14px 16px;

        border:
            1px solid
            rgba(1, 104, 55, 0.14);

        border-radius: 12px;

        color: #526258;

        background:
            rgba(168, 236, 125, 0.14);

        font-size: 0.79rem;
        line-height: 1.5;
    }

    .info-strip-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;

        width: 30px;
        height: 30px;
        min-width: 30px;

        border-radius: 9px;

        color: #FAFBEB;
        background: #016837;

        font-size: 0.85rem;
        font-weight: 800;
    }

    .danger-strip {
        display: flex;
        align-items: flex-start;

        gap: 12px;

        margin-bottom: 17px;
        padding: 14px 16px;

        border:
            1px solid
            rgba(180, 35, 24, 0.17);

        border-radius: 12px;

        color: #7d332d;
        background: #fff0ef;

        font-size: 0.79rem;
        line-height: 1.5;
    }

    .danger-strip-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;

        width: 30px;
        height: 30px;
        min-width: 30px;

        border-radius: 9px;

        color: #ffffff;
        background: #b42318;

        font-size: 0.85rem;
        font-weight: 800;
    }


    /* ======================================================
       FORMULÁRIOS
       ====================================================== */

    [data-testid="stForm"] {
        padding: 20px;

        border:
            1px solid
            rgba(1, 104, 55, 0.11);

        border-radius: 14px;

        background: #FAFBEB;

        box-shadow:
            0 4px 14px
            rgba(11, 47, 19, 0.045);
    }

    [data-baseweb="input"] > div,
    [data-baseweb="select"] > div {
        border-radius: 10px;
    }

    [data-baseweb="input"] > div:focus-within,
    [data-baseweb="select"] > div:focus-within {
        border-color: #016837;

        box-shadow:
            0 0 0 1px
            rgba(1, 104, 55, 0.15);
    }


    /* ======================================================
       BOTÕES PRINCIPAIS
       ====================================================== */

    .stButton > button[kind="primary"],
    .stFormSubmitButton > button[kind="primary"] {
        min-height: 42px;

        border: 1px solid #016837;
        border-radius: 10px;

        color: #FAFBEB;
        background: #016837;

        font-size: 0.79rem;
        font-weight: 700;

        transition:
            transform 0.16s ease,
            background 0.16s ease,
            box-shadow 0.16s ease;
    }

    .stButton > button[kind="primary"]:hover,
    .stFormSubmitButton > button[kind="primary"]:hover {
        color: #FAFBEB;
        background: #0B2F13;

        transform: translateY(-1px);

        box-shadow:
            0 6px 13px
            rgba(11, 47, 19, 0.15);
    }


    /* ======================================================
       BOTÕES DE EXCLUSÃO
       ====================================================== */

    [class*="st-key-botao_abrir_confirmacao_exclusao"]
    .stButton > button,
    [class*="st-key-botao_confirmar_exclusao"]
    .stButton > button {
        border-color: #b42318;

        color: #ffffff;
        background: #b42318;
    }

    [class*="st-key-botao_abrir_confirmacao_exclusao"]
    .stButton > button:hover,
    [class*="st-key-botao_confirmar_exclusao"]
    .stButton > button:hover {
        border-color: #8f1d14;

        color: #ffffff;
        background: #8f1d14;
    }


    /* ======================================================
       MÉTRICAS DA ETL
       ====================================================== */

    .etl-summary {
        margin-top: 18px;
        margin-bottom: 16px;
    }

    [class*="st-key-etl_metric_"] {
        min-height: 115px;
        padding: 18px 19px;

        border:
            1px solid
            rgba(1, 104, 55, 0.13);

        border-radius: 14px;

        background: #FAFBEB;

        box-shadow:
            0 4px 14px
            rgba(11, 47, 19, 0.045);
    }

    [class*="st-key-etl_metric_"]
    [data-testid="stMetricLabel"] {
        color: #607067;

        font-size: 0.72rem;
        font-weight: 700;
    }

    [class*="st-key-etl_metric_"]
    [data-testid="stMetricValue"] {
        color: #0B2F13;

        font-size: 1.75rem;
        font-weight: 780;
    }


    /* ======================================================
       TABELAS
       ====================================================== */

    [data-testid="stDataFrame"] {
        overflow: hidden;

        border:
            1px solid
            rgba(1, 104, 55, 0.11);

        border-radius: 12px;
    }


    /* ======================================================
       GESTORA SELECIONADA
       ====================================================== */

    .selected-gestora-card {
        display: flex;
        align-items: center;
        justify-content: space-between;

        gap: 16px;

        margin-bottom: 17px;
        padding: 15px 17px;

        border:
            1px solid
            rgba(1, 104, 55, 0.13);

        border-radius: 12px;

        background:
            rgba(168, 236, 125, 0.12);
    }

    .selected-gestora-name {
        color: #0B2F13;

        font-size: 0.91rem;
        font-weight: 720;
    }

    .selected-gestora-cnpj {
        margin-top: 4px;

        color: #708077;

        font-size: 0.71rem;
    }

    .status-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;

        min-width: 84px;

        padding: 7px 13px;

        border-radius: 999px;

        font-size: 0.7rem;
        font-weight: 750;
        text-transform: uppercase;
        white-space: nowrap;
    }

    .status-ativa {
        color: #016837;

        background:
            rgba(168, 236, 125, 0.42);

        border:
            1px solid
            rgba(1, 104, 55, 0.15);
    }

    .status-inativa {
        color: #a4261d;
        background: #fde8e6;

        border:
            1px solid
            #f2c5c1;
    }

    .status-neutro {
        color: #5d6961;
        background: #edf0ed;

        border:
            1px solid
            #d9dfda;
    }


    /* ======================================================
       BOTÃO VOLTAR
       ====================================================== */

    [class*="st-key-voltar_pagina"] {
        margin-top: 28px;
    }

    [class*="st-key-voltar_pagina"]
    .stButton > button {
        min-height: 41px;

        padding-left: 20px;
        padding-right: 20px;

        border:
            1px solid
            rgba(1, 104, 55, 0.20);

        border-radius: 10px;

        color: #016837;
        background: #FAFBEB;

        font-size: 0.79rem;
        font-weight: 700;
    }

    [class*="st-key-voltar_pagina"]
    .stButton > button:hover {
        color: #0B2F13;

        border-color: #016837;

        background:
            rgba(168, 236, 125, 0.28);
    }


    /* ======================================================
       RESPONSIVIDADE
       ====================================================== */

    @media (max-width: 900px) {

        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .settings-header {
            padding: 22px 20px;
        }

        .settings-header-content {
            align-items: flex-start;
            flex-direction: column;
        }

        .settings-header-line {
            width: 70px;
            min-width: 70px;
        }

        .settings-header-title {
            font-size: 1.4rem;
        }

        .selected-gestora-card {
            align-items: flex-start;
            flex-direction: column;
        }
    }

    </style>
    """
)


# ===========================================================================
# DIALOG DE EXCLUSÃO
# ===========================================================================

@st.dialog(
    "Confirmar exclusão de gestoras",
    width="large",
)
def confirmar_exclusao(
    gestoras_selecionadas: list[dict],
) -> None:
    """Solicita confirmação antes de excluir as gestoras."""

    if st.session_state.get(
        "exclusao_concluida"
    ):
        mensagem = st.session_state.get(
            "mensagem_exclusao",
            "Gestoras excluídas com sucesso.",
        )

        st.success(
            mensagem,
            icon=":material/check_circle:",
        )

        st.info(
            "Os preenchimentos e as respostas foram "
            "preservados. Os preenchimentos vinculados "
            "às gestoras excluídas ficaram com o campo "
            "id_gestora igual a NULL."
        )

        if st.button(
            "Fechar e atualizar a página",
            type="primary",
            use_container_width=True,
            key="botao_fechar_exclusao",
        ):
            limpar_estado_exclusao()
            st.rerun()

        return

    quantidade = len(
        gestoras_selecionadas
    )

    st.html(
        f"""
        <div class="danger-strip">

            <div class="danger-strip-icon">
                !
            </div>

            <div>
                Você está prestes a excluir
                <strong>
                    {quantidade}
                    {
                        " gestora"
                        if quantidade == 1
                        else " gestoras"
                    }
                </strong>.

                Esta operação remove permanentemente
                o cadastro selecionado.
            </div>

        </div>
        """
    )

    dados_confirmacao = pd.DataFrame(
        gestoras_selecionadas
    )

    colunas_disponiveis = [
        coluna
        for coluna in [
            "id_gestora",
            "nome",
            "cnpj",
            "email",
        ]
        if coluna in dados_confirmacao.columns
    ]

    st.dataframe(
        dados_confirmacao[
            colunas_disponiveis
        ],
        hide_index=True,
        use_container_width=True,
        column_config={
            "id_gestora": (
                st.column_config.NumberColumn(
                    "ID",
                    format="%d",
                )
            ),
            "nome": (
                st.column_config.TextColumn(
                    "Nome"
                )
            ),
            "cnpj": (
                st.column_config.TextColumn(
                    "CNPJ"
                )
            ),
            "email": (
                st.column_config.TextColumn(
                    "E-mail"
                )
            ),
        },
    )

    st.info(
        "Os preenchimentos e respostas não serão apagados. "
        "Os preenchimentos relacionados ficarão sem uma "
        "gestora vinculada."
    )

    st.write(
        "Para confirmar, digite "
        "**EXCLUIR** no campo abaixo."
    )

    texto_confirmacao = st.text_input(
        "Confirmação",
        key="confirmacao_texto_exclusao",
        placeholder="Digite EXCLUIR",
    )

    confirmacao_valida = (
        texto_confirmacao.strip()
        == "EXCLUIR"
    )

    if (
        texto_confirmacao
        and not confirmacao_valida
    ):
        st.error(
            "A confirmação está incorreta. "
            "Digite exatamente EXCLUIR, "
            "em letras maiúsculas."
        )

    coluna_cancelar, coluna_excluir = (
        st.columns(
            2,
            gap="small",
        )
    )

    with coluna_cancelar:

        if st.button(
            "Cancelar",
            use_container_width=True,
            key="botao_cancelar_exclusao",
        ):
            limpar_estado_exclusao()
            st.rerun()

    with coluna_excluir:

        excluir = st.button(
            "Excluir gestoras",
            type="primary",
            use_container_width=True,
            disabled=not confirmacao_valida,
            key="botao_confirmar_exclusao",
        )

    if not excluir:
        return

    ids_gestoras = [
        int(gestora["id_gestora"])
        for gestora
        in gestoras_selecionadas
    ]

    try:
        quantidade_excluida = excluir_gestoras(
            ids_gestoras
        )

    except ValueError as erro:
        st.error(str(erro))
        return

    except Exception as erro:
        st.error(
            "Não foi possível excluir as gestoras."
        )
        st.exception(erro)
        return

    st.session_state[
        "exclusao_concluida"
    ] = True

    st.session_state[
        "mensagem_exclusao"
    ] = (
        f"{quantidade_excluida} "
        "gestora(s) excluída(s) "
        "com sucesso."
    )

    st.rerun()


# ===========================================================================
# LISTA PARA EXCLUSÃO
# ===========================================================================

def renderizar_lista_exclusao(
    gestoras: pd.DataFrame,
) -> None:
    """Exibe a listagem e permite selecionar gestoras."""

    if gestoras.empty:
        st.info(
            "Nenhuma gestora cadastrada."
        )
        return

    colunas_tabela = [
        coluna
        for coluna in [
            "id_gestora",
            "nome",
            "telefone",
            "email",
            "cnpj",
            "status",
            "atualizado",
        ]
        if coluna in gestoras.columns
    ]

    st.dataframe(
        gestoras[colunas_tabela],
        hide_index=True,
        use_container_width=True,
        column_config={
            "id_gestora": (
                st.column_config.NumberColumn(
                    "ID",
                    format="%d",
                )
            ),
            "nome": (
                st.column_config.TextColumn(
                    "Nome"
                )
            ),
            "telefone": (
                st.column_config.TextColumn(
                    "Telefone"
                )
            ),
            "email": (
                st.column_config.TextColumn(
                    "E-mail"
                )
            ),
            "cnpj": (
                st.column_config.TextColumn(
                    "CNPJ"
                )
            ),
            "status": (
                st.column_config.TextColumn(
                    "Status"
                )
            ),
            "atualizado": (
                st.column_config.TextColumn(
                    "Atualizado em"
                )
            ),
        },
    )

    opcoes: dict[str, dict] = {}

    for _, linha in gestoras.iterrows():

        id_gestora = int(
            linha["id_gestora"]
        )

        nome = str(
            linha["nome"]
        )

        cnpj = (
            ""
            if pd.isna(
                linha.get("cnpj")
            )
            else str(
                linha.get("cnpj")
            )
        )

        rotulo = (
            f"{nome} — ID {id_gestora}"
        )

        if cnpj:
            rotulo += f" — CNPJ {cnpj}"

        opcoes[rotulo] = {
            "id_gestora": id_gestora,
            "nome": nome,
            "telefone": (
                None
                if pd.isna(
                    linha.get("telefone")
                )
                else linha.get("telefone")
            ),
            "email": (
                None
                if pd.isna(
                    linha.get("email")
                )
                else linha.get("email")
            ),
            "cnpj": (
                None
                if pd.isna(
                    linha.get("cnpj")
                )
                else linha.get("cnpj")
            ),
        }

    rotulos_selecionados = st.multiselect(
        "Selecione as gestoras que deseja excluir",
        options=list(opcoes.keys()),
        placeholder=(
            "Selecione uma ou mais gestoras"
        ),
    )

    gestoras_selecionadas = [
        opcoes[rotulo]
        for rotulo
        in rotulos_selecionados
    ]

    quantidade_selecionada = len(
        gestoras_selecionadas
    )

    if quantidade_selecionada:

        st.caption(
            f"{quantidade_selecionada} "
            "gestora(s) selecionada(s)."
        )

    if st.button(
        "Excluir gestoras selecionadas",
        type="primary",
        use_container_width=True,
        disabled=(
            quantidade_selecionada == 0
        ),
        key=(
            "botao_abrir_"
            "confirmacao_exclusao"
        ),
        icon=":material/delete:",
    ):
        limpar_estado_exclusao()

        confirmar_exclusao(
            gestoras_selecionadas
        )


# ===========================================================================
# INICIALIZAÇÃO
# ===========================================================================

inicializar_estado()


# ===========================================================================
# CABEÇALHO
# ===========================================================================

st.html(
    """
    <section class="settings-header">

        <div class="settings-header-content">

            <div class="settings-header-text">

                <div class="settings-header-kicker">
                    Diligência
                </div>

                <h1 class="settings-header-title">
                    Configurações e manutenção
                </h1>

                <p class="settings-header-description">
                    Gerencie os cadastros das gestoras,
                    execute a integração dos questionários,
                    valide o banco de dados e controle
                    as exclusões do sistema.
                </p>

            </div>

            <div class="settings-header-line"></div>

        </div>

    </section>
    """
)


# ===========================================================================
# ABAS
# ===========================================================================

(
    aba_atualizacao,
    aba_etl,
    aba_banco,
    aba_exclusao,
) = st.tabs(
    [
        "Atualização",
        "Importação ETL",
        "Banco de dados",
        "Exclusão",
    ]
)


# ===========================================================================
# ABA — ATUALIZAÇÃO
# ===========================================================================

with aba_atualizacao:

    st.html(
        """
        <div class="panel-heading">

            <div class="panel-eyebrow">
                Dados cadastrais
            </div>

            <h2 class="panel-title">
                Atualizar gestora
            </h2>

            <div class="panel-description">
                Selecione uma gestora e atualize
                seus dados cadastrais e sua situação.
            </div>

        </div>
        """
    )

    gestoras_edicao = carregar_gestoras()

    if gestoras_edicao.empty:

        st.info(
            "Nenhuma gestora cadastrada."
        )

    else:

        gestoras_edicao = (
            gestoras_edicao
            .set_index("id_gestora")
        )

        id_gestora = st.selectbox(
            "Gestora",
            gestoras_edicao.index,
            format_func=lambda identificador: (
                gestoras_edicao.loc[
                    identificador,
                    "nome",
                ]
            ),
        )

        gestora = gestoras_edicao.loc[
            id_gestora
        ]

        status_atual = tratar_status_gestora(
            gestora.get("status")
        )

        st.html(
            f"""
            <div class="selected-gestora-card">

                <div>

                    <div class="selected-gestora-name">
                        {
                            html.escape(
                                valor_seguro(
                                    gestora.get("nome")
                                )
                            )
                        }
                    </div>

                    <div class="selected-gestora-cnpj">
                        CNPJ:
                        {
                            html.escape(
                                valor_seguro(
                                    gestora.get("cnpj")
                                )
                            )
                        }
                    </div>

                </div>

                <span class="
                    status-badge
                    {
                        classe_status_gestora(
                            status_atual
                        )
                    }
                ">
                    {html.escape(status_atual)}
                </span>

            </div>
            """
        )

        with st.form(
            "editar_gestora",
            clear_on_submit=False,
        ):

            coluna_nome, coluna_cnpj = (
                st.columns(
                    2,
                    gap="medium",
                )
            )

            with coluna_nome:

                nome = st.text_input(
                    "Nome",
                    value=valor_seguro(
                        gestora.get("nome"),
                        "",
                    ),
                )

            with coluna_cnpj:

                cnpj = st.text_input(
                    "CNPJ",
                    value=valor_seguro(
                        gestora.get("cnpj"),
                        "",
                    ),
                )

            coluna_email, coluna_status = (
                st.columns(
                    2,
                    gap="medium",
                )
            )

            with coluna_email:

                email = st.text_input(
                    "E-mail",
                    value=valor_seguro(
                        gestora.get("email"),
                        "",
                    ),
                )

            with coluna_status:

                opcoes_status = [
                    "Ativa",
                    "Inativa",
                ]

                status = st.selectbox(
                    "Status",
                    options=opcoes_status,
                    index=(
                        opcoes_status.index(
                            status_atual
                        )
                        if status_atual
                        in opcoes_status
                        else 0
                    ),
                )

            salvar = st.form_submit_button(
                "Salvar alterações",
                type="primary",
                use_container_width=True,
                icon=":material/save:",
            )

        if salvar:

            try:
                atualizar_gestora(
                    id_gestora=int(
                        id_gestora
                    ),
                    nome=nome,
                    cnpj=cnpj,
                    email=email,
                    status=status,
                )

                st.success(
                    "Gestora atualizada "
                    "com sucesso.",
                    icon=":material/check_circle:",
                )

            except ValueError as erro:
                st.error(str(erro))

            except Exception as erro:
                st.error(
                    "Não foi possível "
                    "atualizar a gestora."
                )
                st.exception(erro)


# ===========================================================================
# ABA — ETL
# ===========================================================================

with aba_etl:

    st.html(
        """
        <div class="panel-heading">

            <div class="panel-eyebrow">
                Integração de dados
            </div>

            <h2 class="panel-title">
                Importar preenchimentos e respostas
            </h2>

            <div class="panel-description">
                Execute a leitura dos dados disponíveis
                no Google Sheets e atualize o banco local.
            </div>

        </div>
        """
    )

    st.html(
        """
        <div class="info-strip">

            <div class="info-strip-icon">
                i
            </div>

            <div>
                A execução adiciona novos preenchimentos,
                inclui novas respostas e atualiza respostas
                que foram modificadas na origem.
            </div>

        </div>
        """
    )

    if st.button(
        "Executar ETL",
        type="primary",
        use_container_width=True,
        icon=":material/sync:",
        key="executar_etl",
    ):

        try:
            with st.spinner(
                "Executando ETL..."
            ):
                resultado = executar_etl()

        except Exception as erro:
            st.error(
                "Não foi possível executar a ETL."
            )
            st.exception(erro)

        else:
            if not resultado.sucesso:

                st.error(
                    resultado.mensagem_erro
                    or (
                        "Ocorreu um erro "
                        "durante a execução."
                    )
                )

            else:

                st.success(
                    "ETL executada com sucesso.",
                    icon=":material/check_circle:",
                )

                st.html(
                    """
                    <div class="etl-summary">
                    </div>
                    """
                )

                coluna_1, coluna_2, coluna_3 = (
                    st.columns(
                        3,
                        gap="small",
                    )
                )

                with coluna_1:

                    with st.container(
                        key="etl_metric_preenchimentos",
                    ):

                        st.metric(
                            "Preenchimentos adicionados",
                            (
                                resultado
                                .preenchimentos_adicionados
                            ),
                        )

                with coluna_2:

                    with st.container(
                        key="etl_metric_respostas",
                    ):

                        st.metric(
                            "Respostas adicionadas",
                            (
                                resultado
                                .respostas_adicionadas
                            ),
                        )

                with coluna_3:

                    with st.container(
                        key="etl_metric_atualizadas",
                    ):

                        st.metric(
                            "Respostas atualizadas",
                            (
                                resultado
                                .respostas_atualizadas
                            ),
                        )

                if resultado.cnpjs_nao_encontrados:

                    st.warning(
                        "Alguns CNPJs não foram "
                        "encontrados no cadastro."
                    )

                    st.dataframe(
                        pd.DataFrame(
                            {
                                "CNPJ não encontrado": (
                                    sorted(
                                        resultado
                                        .cnpjs_nao_encontrados
                                    )
                                )
                            }
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )

                if resultado.novos_preenchimentos:

                    with st.expander(
                        "Novos preenchimentos"
                    ):

                        st.dataframe(
                            pd.DataFrame(
                                resultado
                                .novos_preenchimentos
                            ),
                            use_container_width=True,
                            hide_index=True,
                        )

                if resultado.novas_respostas:

                    with st.expander(
                        "Novas respostas"
                    ):

                        st.dataframe(
                            pd.DataFrame(
                                resultado
                                .novas_respostas
                            ),
                            use_container_width=True,
                            hide_index=True,
                        )

                if resultado.respostas_modificadas:

                    with st.expander(
                        "Respostas atualizadas"
                    ):

                        st.dataframe(
                            pd.DataFrame(
                                resultado
                                .respostas_modificadas
                            ),
                            use_container_width=True,
                            hide_index=True,
                        )


# ===========================================================================
# ABA — BANCO DE DADOS
# ===========================================================================

with aba_banco:

    st.html(
        """
        <div class="panel-heading">

            <div class="panel-eyebrow">
                Estrutura do sistema
            </div>

            <h2 class="panel-title">
                Criar ou validar banco de dados
            </h2>

            <div class="panel-description">
                Crie o arquivo SQLite e valide se as tabelas,
                os relacionamentos e o índice utilizados pelo
                módulo de diligência estão disponíveis.
            </div>

        </div>
        """
    )

    st.html(
        """
        <div class="info-strip">

            <div class="info-strip-icon">
                i
            </div>

            <div>
                Esta operação pode ser executada mais de uma vez.
                As tabelas existentes e os dados já cadastrados
                não serão apagados.
            </div>

        </div>
        """
    )

    st.warning(
        "O arquivo SQLite será criado no caminho definido "
        "pela função get_connection().",
        icon=":material/database:",
    )

    if st.button(
        "Criar ou validar banco de dados",
        type="primary",
        use_container_width=True,
        key="botao_criar_banco",
        icon=":material/database:",
    ):

        try:
            with st.spinner(
                "Criando e validando o banco de dados..."
            ):
                criar_banco()

            st.success(
                "Banco de dados criado ou validado "
                "com sucesso.",
                icon=":material/check_circle:",
            )

            st.info(
                "As tabelas gestora, preenchimento e resposta "
                "foram validadas. O índice único de CNPJ "
                "também está disponível."
            )

        except Exception as erro:
            st.error(
                "Não foi possível criar ou validar "
                "o banco de dados."
            )

            st.exception(erro)


# ===========================================================================
# ABA — EXCLUSÃO
# ===========================================================================

with aba_exclusao:

    st.html(
        """
        <div class="panel-heading">

            <div class="panel-eyebrow">
                Área crítica
            </div>

            <h2 class="panel-title">
                Excluir gestoras
            </h2>

            <div class="panel-description">
                Selecione um ou mais cadastros para
                remoção. Os preenchimentos e respostas
                existentes serão preservados.
            </div>

        </div>
        """
    )

    st.html(
        """
        <div class="danger-strip">

            <div class="danger-strip-icon">
                !
            </div>

            <div>
                A exclusão remove permanentemente
                o cadastro da gestora. Revise
                cuidadosamente a seleção antes
                de continuar.
            </div>

        </div>
        """
    )

    gestoras_exclusao = carregar_gestoras()

    renderizar_lista_exclusao(
        gestoras_exclusao
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