import base64
import html
import re
from pathlib import Path

import pandas as pd
import streamlit as st

from utils.ddq_utils.crud import (
    CnpjDuplicadoError,
    inserir_gestora,
    listar_gestoras_preenchimento,
)


# ===========================================================================
# CONFIGURAÇÃO DA PÁGINA
# ===========================================================================

st.set_page_config(
    page_title="Diligência - Ceres",
    layout="wide",
)


# ===========================================================================
# CAMINHOS DO PROJETO
# ===========================================================================

# Estrutura esperada:
#
# projeto/
# ├── images/
# │   └── logo_padrao.png
# └── src/
#     └── pages/
#         └── seu_arquivo.py
#
# __file__                     -> src/pages/seu_arquivo.py
# parents[0]                   -> src/pages
# parents[1]                   -> src
# parents[2]                   -> raiz do projeto

RAIZ_PROJETO = Path(__file__).resolve().parents[2]

PASTA_IMAGES = (
    RAIZ_PROJETO
    / "images"
)

PASTA_LOGOS_GESTORAS = (
    PASTA_IMAGES
    / "gestoras"
)

CAMINHO_LOGO_PADRAO = (
    PASTA_LOGOS_GESTORAS
    / "logo_padrao.png"
)


# ===========================================================================
# FUNÇÕES AUXILIARES
# ===========================================================================

def valor_seguro(
    valor,
    padrao: str = "—",
) -> str:
    """Evita exibir None, NaN ou NaT."""

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


def normalizar_cnpj(
    valor,
) -> str:
    """
    Remove pontuação, espaços e converte letras para maiúsculas.

    Aceita o CNPJ numérico tradicional e o formato alfanumérico.
    """

    if valor is None:
        return ""

    return re.sub(
        r"[^A-Z0-9]",
        "",
        str(valor).strip().upper(),
    )


def calcular_digito_cnpj(
    caracteres: str,
    pesos: list[int],
) -> int:
    """
    Calcula um dígito verificador do CNPJ pelo módulo 11.

    Para o CNPJ alfanumérico, cada caractere é convertido
    pelo valor ASCII menos 48.
    """

    soma = sum(
        (ord(caractere) - 48) * peso
        for caractere, peso in zip(
            caracteres,
            pesos,
        )
    )

    resto = soma % 11

    if resto in {
        0,
        1,
    }:
        return 0

    return 11 - resto


def validar_cnpj(
    valor,
) -> bool:
    """
    Valida CNPJ numérico ou alfanumérico.

    Regras aplicadas:
    - 14 caracteres após a normalização;
    - 12 primeiras posições alfanuméricas;
    - 2 últimas posições numéricas;
    - verificação dos dois dígitos verificadores;
    - bloqueio de CNPJ numérico com todos os dígitos iguais.
    """

    cnpj = normalizar_cnpj(
        valor
    )

    if len(cnpj) != 14:
        return False

    if not re.fullmatch(
        r"[A-Z0-9]{12}[0-9]{2}",
        cnpj,
    ):
        return False

    if (
        cnpj.isdigit()
        and len(set(cnpj)) == 1
    ):
        return False

    base = cnpj[:12]

    primeiro_digito = calcular_digito_cnpj(
        base,
        [
            5,
            4,
            3,
            2,
            9,
            8,
            7,
            6,
            5,
            4,
            3,
            2,
        ],
    )

    segundo_digito = calcular_digito_cnpj(
        base + str(primeiro_digito),
        [
            6,
            5,
            4,
            3,
            2,
            9,
            8,
            7,
            6,
            5,
            4,
            3,
            2,
        ],
    )

    return cnpj[-2:] == (
        f"{primeiro_digito}"
        f"{segundo_digito}"
    )


def formatar_cnpj(
    valor,
    padrao: str = "CNPJ não informado",
) -> str:
    """
    Exibe o CNPJ no formato 00.000.000/0000-00.

    Também preserva letras nas posições alfanuméricas.
    """

    cnpj = normalizar_cnpj(
        valor
    )

    if not cnpj:
        return padrao

    if len(cnpj) != 14:
        return valor_seguro(
            valor,
            padrao,
        )

    return (
        f"{cnpj[0:2]}."
        f"{cnpj[2:5]}."
        f"{cnpj[5:8]}/"
        f"{cnpj[8:12]}-"
        f"{cnpj[12:14]}"
    )


def formatar_data(valor) -> str:
    """Formata datas como dd/mm/aaaa."""

    if valor is None:
        return "—"

    try:
        data = pd.to_datetime(
            valor,
            errors="coerce",
        )

        if pd.isna(data):
            return "—"

        return data.strftime(
            "%d/%m/%Y"
        )

    except (TypeError, ValueError):
        return valor_seguro(valor)


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
        "status-nao-preenchida",
    )


def classe_cadastro(
    status: str,
) -> str:
    """Retorna a classe CSS correspondente ao cadastro."""

    status_normalizado = (
        valor_seguro(
            status,
            "",
        )
        .strip()
        .upper()
    )

    if status_normalizado in {
        "ATIVO",
        "ATIVA",
    }:
        return "cadastro-ativo"

    if status_normalizado in {
        "INATIVO",
        "INATIVA",
    }:
        return "cadastro-inativo"

    return "cadastro-neutro"


def carregar_imagem_base64(
    caminho: Path,
) -> str:
    """
    Converte uma imagem local para Base64.

    Retorna uma string pronta para ser usada
    no atributo src de uma tag HTML img.
    """

    if not caminho.exists():
        return ""

    if not caminho.is_file():
        return ""

    tipos_imagem = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
    }

    extensao = caminho.suffix.lower()

    tipo_imagem = tipos_imagem.get(
        extensao,
        "image/png",
    )

    try:
        conteudo_base64 = base64.b64encode(
            caminho.read_bytes()
        ).decode("utf-8")

    except OSError:
        return ""

    return (
        f"data:{tipo_imagem};"
        f"base64,{conteudo_base64}"
    )


def localizar_logo_gestora(
    cnpj,
) -> Path:
    """
    Localiza a logo da gestora pelo CNPJ normalizado.

    A busca é feita nas extensões suportadas. Caso nenhuma
    imagem específica seja encontrada, retorna a logo padrão.
    """

    cnpj_normalizado = normalizar_cnpj(
        cnpj
    )

    extensoes_permitidas = (
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".svg",
    )

    if cnpj_normalizado:

        for extensao in extensoes_permitidas:

            caminho_logo = (
                PASTA_LOGOS_GESTORAS
                / f"{cnpj_normalizado}{extensao}"
            )

            if (
                caminho_logo.exists()
                and caminho_logo.is_file()
            ):
                return caminho_logo

    return CAMINHO_LOGO_PADRAO


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
        max-width: 1440px;
        padding-top: 3.8rem;
        padding-left: 2.5rem;
        padding-right: 2.5rem;
        padding-bottom: 4rem;
    }


    /* ======================================================
       CABEÇALHO EM LARGURA TOTAL
       ====================================================== */

    .page-header-full {
        position: relative;
        left: 50%;

        width: 100vw;

        margin-left: -50vw;
        margin-bottom: 28px;

        overflow: hidden;

        background:
            linear-gradient(
                115deg,
                #0B2F13 0%,
                #016837 100%
            );

        box-shadow:
            0 10px 28px
            rgba(11, 47, 19, 0.18);
    }

    .page-header-inner {
        position: relative;

        width: min(
            100% - 5rem,
            1390px
        );

        margin: 0 auto;
        padding: 34px 0 36px 0;

        text-align: center;
    }

    .page-title {
        margin: 0;

        color: #FAFBEB;

        font-size:
            clamp(
                1.7rem,
                2.5vw,
                2.6rem
            );

        font-weight: 520;
        line-height: 1.16;
    }

    .page-title-highlight {
        color: #A8EC7D;

        font-family:
            "Source Serif 4",
            serif;

        font-style: italic;
        font-weight: 650;
    }


    /* ======================================================
       INDICADORES
       ====================================================== */

    .metric-card {
        position: relative;
        overflow: hidden;

        min-height: 118px;
        padding: 18px 19px;

        border:
            1px solid
            rgba(1, 104, 55, 0.13);

        border-radius: 15px;

        background: #FAFBEB;

        box-shadow:
            0 4px 14px
            rgba(11, 47, 19, 0.05);

        transition:
            transform 0.18s ease,
            box-shadow 0.18s ease,
            border-color 0.18s ease;
    }

    .metric-card:hover {
        transform: translateY(-2px);

        border-color:
            rgba(1, 104, 55, 0.24);

        box-shadow:
            0 9px 22px
            rgba(11, 47, 19, 0.08);
    }


    .metric-label {
        position: relative;
        z-index: 1;

        margin-bottom: 10px;

        color: #567060;

        font-size: 0.69rem;
        font-weight: 750;
        letter-spacing: 0.045em;
        text-transform: uppercase;
    }

    .metric-value {
        position: relative;
        z-index: 1;

        color: #0B2F13;

        font-size: 1.75rem;
        font-weight: 780;
        line-height: 1;
    }

    .metric-description {
        position: relative;
        z-index: 1;

        margin-top: 8px;

        color: #718078;

        font-size: 0.68rem;
        line-height: 1.35;
    }

    .metric-em-dia {
        border-top:
            4px solid #2DC25F;
    }

    .metric-a-vencer {
        border-top:
            4px solid #e6b73c;
    }

    .metric-vencido {
        border-top:
            4px solid #c74b43;
    }

    .metric-nao-preenchida {
        border-top:
            4px solid #89958d;
    }

    .metric-total {
        border-top:
            4px solid #016837;
    }


    /* ======================================================
       BARRA DE CONTROLES
       ====================================================== */

    [class*="st-key-barra_controles"] {
        margin-top: 22px;
        margin-bottom: 25px;

        padding: 17px 18px;

        border:
            1px solid
            rgba(1, 104, 55, 0.13);

        border-radius: 15px;

        background: #FAFBEB;

        box-shadow:
            0 4px 14px
            rgba(11, 47, 19, 0.045);
    }

    [class*="st-key-barra_controles"]
    [data-testid="stVerticalBlock"] {
        gap: 0.5rem;
    }

    .controls-heading {
        margin-bottom: 12px;
    }

    .controls-title {
        margin: 0;

        color: #0B2F13;

        font-size: 0.96rem;
        font-weight: 750;
    }

    .controls-description {
        margin-top: 3px;

        color: #748078;

        font-size: 0.74rem;
    }

    [class*="st-key-barra_controles"]
    [data-baseweb="select"] > div {
        min-height: 42px;

        border-color:
            rgba(1, 104, 55, 0.18);

        border-radius: 10px;

        background: #ffffff;
    }

    [class*="st-key-barra_controles"]
    [data-baseweb="select"] > div:hover {
        border-color: #016837;
    }


    /* ======================================================
       BOTÃO CADASTRAR
       ====================================================== */

    [class*="st-key-cadastrar_gestora"]
    .stButton > button {
        min-height: 42px;

        border: 1px solid #016837;
        border-radius: 10px;

        color: #FAFBEB;
        background: #016837;

        font-size: 0.79rem;
        font-weight: 700;

        transition:
            background 0.16s ease,
            transform 0.16s ease,
            box-shadow 0.16s ease;
    }

    [class*="st-key-cadastrar_gestora"]
    .stButton > button:hover {
        color: #FAFBEB;
        background: #0B2F13;

        transform: translateY(-1px);

        box-shadow:
            0 6px 13px
            rgba(11, 47, 19, 0.16);
    }


    /* ======================================================
       BOTÃO CONFIGURAÇÕES
       ====================================================== */

    [class*="st-key-configuracoes"]
    .stButton > button {
        min-height: 42px;

        border:
            1px solid
            rgba(1, 104, 55, 0.20);

        border-radius: 10px;

        color: #016837;
        background: #ffffff;
    }

    [class*="st-key-configuracoes"]
    .stButton > button:hover {
        color: #0B2F13;

        background:
            rgba(168, 236, 125, 0.28);

        border-color: #016837;
    }


    /* ======================================================
       CABEÇALHO DA LISTA
       ====================================================== */

    .list-heading {
        display: flex;
        align-items: flex-end;
        justify-content: space-between;

        gap: 16px;

        margin-bottom: 17px;
    }

    .list-title {
        margin: 0;

        color: #0B2F13;

        font-size: 1.2rem;
        font-weight: 760;
    }

    .list-description {
        margin-top: 4px;

        color: #6f7d74;

        font-size: 0.8rem;
    }

    .list-counter {
        display: inline-flex;
        align-items: center;
        justify-content: center;

        min-width: 105px;

        padding: 8px 14px;

        border:
            1px solid
            rgba(1, 104, 55, 0.14);

        border-radius: 999px;

        color: #016837;

        background:
            rgba(168, 236, 125, 0.28);

        font-size: 0.75rem;
        font-weight: 750;
        white-space: nowrap;
    }


    /* ======================================================
       CARD DA GESTORA
       ====================================================== */

    [class*="st-key-card_gestora_"] {
        min-height: 355px;
        margin-bottom: 5px;
        padding: 20px 20px 18px 20px;

        border:
            1px solid
            rgba(1, 104, 55, 0.13);

        border-radius: 17px;

        background: #FAFBEB;

        box-shadow:
            0 4px 14px
            rgba(11, 47, 19, 0.05);

        overflow: hidden;

        transition:
            transform 0.20s ease,
            box-shadow 0.20s ease,
            border-color 0.20s ease;
    }

    [class*="st-key-card_gestora_"]:hover {
        transform: translateY(-4px);

        border-color:
            rgba(1, 104, 55, 0.28);

        box-shadow:
            0 11px 26px
            rgba(11, 47, 19, 0.10);
    }

    [class*="st-key-card_gestora_"]
    [data-testid="stVerticalBlock"] {
        gap: 0.45rem;
    }

    .card-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;

        gap: 14px;

        margin-bottom: 4px;
    }

    .card-title-area {
        flex: 1;
        min-width: 0;
    }

    .card-eyebrow {
        margin-bottom: 5px;

        color: #43805d;

        font-size: 0.64rem;
        font-weight: 750;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .card-title {
        margin: 0;

        color: #0B2F13;

        font-size: 1.05rem;
        font-weight: 760;
        line-height: 1.35;

        overflow-wrap: anywhere;
    }


    /* ======================================================
       LOGO DOS CARDS
       ====================================================== */

    .card-logo {
        display: flex;
        align-items: center;
        justify-content: center;

        width: 66px;
        height: 66px;
        min-width: 66px;
        min-height: 66px;

        padding: 7px;

        border:
            1px solid
            rgba(1, 104, 55, 0.18);

        border-radius: 13px;

        background: transparent;

        box-shadow:
            0 3px 10px
            rgba(11, 47, 19, 0.05);

        overflow: hidden;
        box-sizing: border-box;
    }

    .card-logo img {
        display: block;

        width: 100%;
        height: 100%;

        object-fit: contain;
    }

    .card-logo-placeholder {
        color: #668070;

        font-size: 0.58rem;
        font-weight: 700;
        line-height: 1.2;

        text-align: center;
        text-transform: uppercase;
    }


    /* ======================================================
       CONTATO E CNPJ
       ====================================================== */

    .card-contact {
        min-height: 42px;
        margin-top: 7px;
        margin-bottom: 7px;

        color: #65746b;

        font-size: 0.77rem;
        line-height: 1.55;

        overflow-wrap: anywhere;
    }

    .card-cnpj {
        margin-bottom: 10px;

        color: #506258;

        font-size: 0.74rem;
        font-weight: 600;

        overflow-wrap: anywhere;
    }


    /* ======================================================
       MÉTRICAS DOS CARDS
       ====================================================== */

    .card-metrics {
        display: grid;

        grid-template-columns:
            repeat(
                3,
                minmax(0, 1fr)
            );

        gap: 7px;

        padding: 14px 0;

        border-top:
            1px solid
            rgba(1, 104, 55, 0.11);

        border-bottom:
            1px solid
            rgba(1, 104, 55, 0.11);
    }

    .card-metric {
        min-width: 0;
        padding: 0 5px;

        text-align: center;
    }

    .card-metric + .card-metric {
        border-left:
            1px solid
            rgba(1, 104, 55, 0.10);
    }

    .card-metric-label {
        min-height: 28px;
        margin-bottom: 5px;

        color: #708078;

        font-size: 0.65rem;
        line-height: 1.2;
    }

    .card-metric-value {
        color: #0B2F13;

        font-size: 0.77rem;
        font-weight: 720;
        line-height: 1.3;

        overflow-wrap: anywhere;
    }


    /* ======================================================
       STATUS CADASTRAL
       ====================================================== */

    .cadastro-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;

        min-width: 65px;

        padding: 4px 8px;

        border-radius: 999px;

        font-size: 0.63rem;
        font-weight: 750;
        text-transform: uppercase;
    }

    .cadastro-ativo {
        color: #016837;

        background:
            rgba(168, 236, 125, 0.42);
    }

    .cadastro-inativo {
        color: #a4261d;
        background: #fde8e6;
    }

    .cadastro-neutro {
        color: #5e6a63;
        background: #e9eeea;
    }

    .card-bottom-space {
        height: 21px;
    }

    .card-footer {
        display: flex;
        align-items: center;

        width: 100%;
        height: 40px;
        min-height: 40px;
    }


    /* ======================================================
       STATUS DE VENCIMENTO
       ====================================================== */

    .status-badge {
        display: flex;
        align-items: center;
        justify-content: center;

        width: 100%;
        height: 40px;
        min-height: 40px;

        padding: 0 10px;

        border-radius: 9px;

        font-size: 0.7rem;
        font-weight: 750;
        line-height: 1;

        white-space: nowrap;
        box-sizing: border-box;
    }

    .status-em-dia {
        color: #016837;

        background:
            rgba(168, 236, 125, 0.42);

        border:
            1px solid
            rgba(1, 104, 55, 0.14);
    }

    .status-a-vencer {
        color: #725200;
        background: #fff1bd;
        border: 1px solid #ead58d;
    }

    .status-vencido {
        color: #a4261d;
        background: #fde8e6;
        border: 1px solid #f2c5c1;
    }

    .status-nao-preenchida {
        color: #5e6a63;
        background: #edf0ed;
        border: 1px solid #d9dfda;
    }


    /* ======================================================
       BOTÕES DOS CARDS
       ====================================================== */

    [class*="st-key-card_gestora_"]
    .stButton {
        margin: 0;
    }

    [class*="st-key-card_gestora_"]
    .stButton > button {
        width: 100%;
        height: 40px;
        min-height: 40px;

        margin: 0;
        padding-top: 0;
        padding-bottom: 0;

        border: 1px solid #016837;
        border-radius: 9px;

        color: #FAFBEB;
        background: #016837;

        font-size: 0.74rem;
        font-weight: 720;
        white-space: nowrap;

        transition:
            background 0.18s ease,
            transform 0.18s ease,
            box-shadow 0.18s ease;
    }

    [class*="st-key-card_gestora_"]
    .stButton > button:hover {
        color: #FAFBEB;
        background: #0B2F13;

        transform: translateY(-1px);

        box-shadow:
            0 5px 12px
            rgba(11, 47, 19, 0.15);
    }

    [class*="st-key-card_gestora_"]
    .stButton > button:disabled {
        color: #858d88;
        background: #e4e8e5;

        border-color: #d8ddd9;

        cursor: not-allowed;
        transform: none;
        box-shadow: none;
    }

    [class*="st-key-card_gestora_"]
    [data-testid="stHorizontalBlock"]:has(.card-footer) {
        align-items: center;
    }


    /* ======================================================
       ESTADO VAZIO
       ====================================================== */

    .empty-state {
        padding: 50px 24px;

        border:
            1px dashed
            rgba(1, 104, 55, 0.24);

        border-radius: 17px;

        color: #68766d;
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

    @media (max-width: 900px) {

        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .page-header-inner {
            width: calc(100% - 2rem);
            padding-top: 27px;
            padding-bottom: 29px;
        }

        .page-title {
            font-size: 1.55rem;
        }

        .list-heading {
            align-items: flex-start;
            flex-direction: column;
        }

        [class*="st-key-card_gestora_"] {
            min-height: auto;
        }

        .card-logo {
            width: 56px;
            height: 56px;
            min-width: 56px;
            min-height: 56px;
        }
    }

    </style>
    """
)


# ===========================================================================
# DIALOG DE CADASTRO
# ===========================================================================

@st.dialog(
    "Cadastrar nova gestora",
    on_dismiss="rerun",
)
def cadastrar_gestora() -> None:

    st.html(
        """
        <div style="
            margin-bottom: 16px;
            padding: 14px 16px;
            border: 1px solid rgba(1, 104, 55, 0.14);
            border-radius: 12px;
            background: #FAFBEB;
            color: #4f6255;
            font-size: 0.82rem;
            line-height: 1.5;
        ">
            Cadastre os dados básicos da gestora.
            O nome é o único campo obrigatório.
        </div>
        """
    )

    with st.form(
        "form_cadastro_gestora",
        clear_on_submit=False,
    ):

        nome = st.text_input(
            "Nome da gestora *"
        )

        telefone = st.text_input(
            "Telefone"
        )

        email = st.text_input(
            "E-mail"
        )

        cnpj = st.text_input(
            "CNPJ",
            placeholder="00.000.000/0000-00",
            help=(
                "Informe um CNPJ válido. "
                "A pontuação é opcional."
            ),
            max_chars=18,
        )

        salvar = st.form_submit_button(
            "Cadastrar gestora",
            type="primary",
            use_container_width=True,
        )

    if not salvar:
        return

    if not nome.strip():
        st.error(
            'O campo "Nome da gestora" '
            "é obrigatório."
        )
        return

    cnpj_normalizado = normalizar_cnpj(
        cnpj
    )

    if not cnpj_normalizado:
        st.error(
            'O campo "CNPJ" é obrigatório.'
        )
        return

    if not validar_cnpj(
        cnpj_normalizado
    ):
        st.error(
            "O CNPJ informado é inválido. "
            "Verifique o número e os "
            "dígitos verificadores."
        )
        return

    try:
        novo_id = inserir_gestora(
            nome=nome.strip(),
            telefone=telefone.strip(),
            email=email.strip(),
            cnpj=cnpj_normalizado,
        )

        st.success(
            f'Gestora "{nome.strip()}" '
            "cadastrada com sucesso. "
            f"ID: {novo_id}"
        )

    except CnpjDuplicadoError as erro:
        st.error(str(erro))

    except ValueError as erro:
        st.error(str(erro))

    except Exception as erro:
        st.exception(erro)


# ===========================================================================
# CARREGAMENTO E TRATAMENTO DOS DADOS
# ===========================================================================

gestoras = listar_gestoras_preenchimento()

gestoras["data_envio"] = pd.to_datetime(
    gestoras["data_envio"],
    errors="coerce",
)

gestoras["vencimento"] = (
    gestoras["data_envio"]
    + pd.DateOffset(months=12)
)

agora = pd.Timestamp.now()

gestoras["status_vencimento"] = (
    gestoras["vencimento"].apply(
        lambda x: (
            "Não preenchida"
            if pd.isna(x)
            else "Vencido"
            if x < agora
            else "A vencer"
            if x - pd.DateOffset(
                months=2
            ) <= agora
            else "Em dia"
        )
    )
)

gestoras["status_geral"] = (
    gestoras["status"]
    .fillna("Não informado")
    .astype(str)
    .str.split(" - ")
    .str[0]
    .str.strip()
    .str.capitalize()
)


# ===========================================================================
# CONTADORES
# ===========================================================================

qtd_gestoras = len(gestoras)

qtd_em_dia = len(
    gestoras[
        gestoras[
            "status_vencimento"
        ] == "Em dia"
    ]
)

qtd_a_vencer = len(
    gestoras[
        gestoras[
            "status_vencimento"
        ] == "A vencer"
    ]
)

qtd_vencido = len(
    gestoras[
        gestoras[
            "status_vencimento"
        ] == "Vencido"
    ]
)

qtd_sem_data = len(
    gestoras[
        gestoras[
            "status_vencimento"
        ] == "Não preenchida"
    ]
)


# ===========================================================================
# CABEÇALHO
# ===========================================================================

st.html(
    """
    <section class="page-header-full">

        <div class="page-header-inner">

            <h1 class="page-title">
                Diligência —
                <span class="page-title-highlight">
                    Ceres
                </span>
            </h1>

        </div>

    </section>
    """
)


# ===========================================================================
# CARDS DOS INDICADORES
# ===========================================================================

metricas = [
    (
        "Gestoras",
        qtd_gestoras,
        "Cadastradas no sistema",
        "metric-total",
    ),
    (
        "Em dia",
        qtd_em_dia,
        "Questionários vigentes",
        "metric-em-dia",
    ),
    (
        "A vencer",
        qtd_a_vencer,
        "Vencem em até 2 meses",
        "metric-a-vencer",
    ),
    (
        "Vencidas",
        qtd_vencido,
        "Questionários fora do prazo",
        "metric-vencido",
    ),
    (
        "Não respondidas",
        qtd_sem_data,
        "Sem preenchimento registrado",
        "metric-nao-preenchida",
    ),
]

colunas_metricas = st.columns(
    5,
    gap="small",
)

for coluna, (
    titulo,
    quantidade,
    descricao,
    classe,
) in zip(
    colunas_metricas,
    metricas,
):

    with coluna:

        st.html(
            f"""
            <div class="metric-card {classe}">

                <div class="metric-label">
                    {html.escape(titulo)}
                </div>

                <div class="metric-value">
                    {quantidade}
                </div>

                <div class="metric-description">
                    {html.escape(descricao)}
                </div>

            </div>
            """
        )


# ===========================================================================
# FILTROS E AÇÕES
# ===========================================================================

with st.container(
    key="barra_controles",
):

    st.html(
        """
        <div class="controls-heading">

            <h2 class="controls-title">
                Filtros e ações
            </h2>

            <div class="controls-description">
                Refine a lista de gestoras ou realize
                um novo cadastro.
            </div>

        </div>
        """
    )

    (
        filtro_cadastro,
        filtro_vencimento,
        botao_cadastro,
        botao_config,
    ) = st.columns(
        [
            1.2,
            1.2,
            1,
            0.25,
        ],
        gap="small",
        vertical_alignment="bottom",
    )

    with filtro_cadastro:

        opcoes_status = [
            "Todos",
            *sorted(
                gestoras[
                    "status_geral"
                ]
                .dropna()
                .unique()
                .tolist()
            ),
        ]

        sit_cadastral = st.selectbox(
            "Situação cadastral",
            options=opcoes_status,
            index=0,
            key="gestora_selecionada",
        )

    with filtro_vencimento:

        opcoes_vencimento = [
            "Todos",
            "Em dia",
            "A vencer",
            "Vencido",
            "Não preenchida",
        ]

        status_selecionado = st.selectbox(
            "Status do vencimento",
            options=opcoes_vencimento,
            index=0,
            key="status_selecionado",
        )

    with botao_cadastro:

        with st.container(
            key="cadastrar_gestora",
        ):

            if st.button(
                "Cadastrar nova gestora",
                icon=":material/add_business:",
                use_container_width=True,
            ):
                cadastrar_gestora()

    with botao_config:

        with st.container(
            key="configuracoes",
        ):

            if st.button(
                "",
                icon=":material/settings:",
                help="Configurações",
                use_container_width=True,
            ):
                st.switch_page(
                    "pages/"
                    "s3_due_diligence_settings.py"
                )


# ===========================================================================
# APLICAÇÃO DOS FILTROS
# ===========================================================================

if sit_cadastral != "Todos":

    gestoras = gestoras[
        gestoras[
            "status_geral"
        ] == sit_cadastral
    ]

if status_selecionado != "Todos":

    gestoras = gestoras[
        gestoras[
            "status_vencimento"
        ] == status_selecionado
    ]


# ===========================================================================
# TÍTULO DA LISTA
# ===========================================================================

quantidade_filtrada = len(
    gestoras
)

st.html(
    f"""
    <div class="list-heading">

        <div>

            <h2 class="list-title">
                Gestoras
            </h2>

            <div class="list-description">
                Consulte os dados, os prazos e abra
                o questionário da gestora selecionada.
            </div>

        </div>

        <div class="list-counter">
            {quantidade_filtrada}
            {
                " gestora"
                if quantidade_filtrada == 1
                else " gestoras"
            }
        </div>

    </div>
    """
)


# ===========================================================================
# CARDS DAS GESTORAS
# ===========================================================================

if gestoras.empty:

    st.html(
        """
        <div class="empty-state">

            <div class="empty-state-title">
                Nenhuma gestora localizada
            </div>

            <div>
                Não existem gestoras que atendam
                aos filtros selecionados.
            </div>

        </div>
        """
    )

else:

    col_linha = 3

    qtd_gestoras_filtradas = len(
        gestoras
    )

    for i in range(
        0,
        qtd_gestoras_filtradas,
        col_linha,
    ):

        cols = st.columns(
            col_linha,
            gap="medium",
            vertical_alignment="top",
        )

        for j in range(
            col_linha
        ):

            indice = i + j

            if indice >= qtd_gestoras_filtradas:
                continue

            gestora = gestoras.iloc[
                indice
            ]

            id_gestora = str(
                gestora[
                    "id_gestora"
                ]
            )

            nome = valor_seguro(
                gestora.get("nome"),
                "Gestora sem nome",
            )

            email = valor_seguro(
                gestora.get("email"),
                "E-mail não informado",
            )

            cnpj_original = gestora.get(
                "cnpj"
            )

            cnpj = formatar_cnpj(
                cnpj_original,
                "CNPJ não informado",
            )

            caminho_logo_gestora = (
                localizar_logo_gestora(
                    cnpj_original
                )
            )

            logo_gestora_base64 = (
                carregar_imagem_base64(
                    caminho_logo_gestora
                )
            )

            telefone = valor_seguro(
                gestora.get("telefone"),
                "Não informado",
            )

            status_vencimento = valor_seguro(
                gestora.get(
                    "status_vencimento"
                ),
                "Não preenchida",
            )

            data_envio = formatar_data(
                gestora.get(
                    "data_envio"
                )
            )

            vencimento = formatar_data(
                gestora.get(
                    "vencimento"
                )
            )

            status_gestora = valor_seguro(
                gestora.get(
                    "status_geral"
                ),
                "Não informado",
            )

            preenchida = (
                status_vencimento
                != "Não preenchida"
            )

            nome_html = html.escape(
                nome
            )

            email_html = html.escape(
                email
            )

            cnpj_html = html.escape(
                cnpj
            )

            telefone_html = html.escape(
                telefone
            )

            status_html = html.escape(
                status_vencimento
            )

            status_gestora_html = html.escape(
                status_gestora
            )


            # ===============================================================
            # HTML DA LOGO
            # ===============================================================

            if logo_gestora_base64:

                nome_logo_html = html.escape(
                    nome,
                    quote=True,
                )

                logo_html = f"""
                    <img
                        src="{logo_gestora_base64}"
                        alt="Logo da gestora {nome_logo_html}"
                    >
                """

            else:

                logo_html = """
                    <span class="card-logo-placeholder">
                        Logo não<br>
                        encontrada
                    </span>
                """


            with cols[j]:

                with st.container(
                    key=(
                        f"card_gestora_"
                        f"{id_gestora}"
                    ),
                ):

                    st.html(
                        f"""
                        <div class="card-header">

                            <div class="card-title-area">

                                <div class="card-eyebrow">
                                    Gestora
                                </div>

                                <div class="card-title">
                                    {nome_html}
                                </div>

                            </div>

                            <div
                                class="card-logo"
                                title="Logo da gestora"
                            >
                                {logo_html}
                            </div>

                        </div>

                        <div class="card-contact">
                            ✉ {email_html}<br>
                            ☎ {telefone_html}
                        </div>

                        <div class="card-cnpj">
                            CNPJ: {cnpj_html}
                        </div>
                        """
                    )

                    st.html(
                        f"""
                        <div class="card-metrics">

                            <div class="card-metric">

                                <div class="card-metric-label">
                                    Último envio
                                </div>

                                <div class="card-metric-value">
                                    {
                                        data_envio
                                        if preenchida
                                        else "—"
                                    }
                                </div>

                            </div>

                            <div class="card-metric">

                                <div class="card-metric-label">
                                    Vencimento
                                </div>

                                <div class="card-metric-value">
                                    {
                                        vencimento
                                        if preenchida
                                        else "—"
                                    }
                                </div>

                            </div>

                            <div class="card-metric">

                                <div class="card-metric-label">
                                    Cadastro
                                </div>

                                <div class="card-metric-value">

                                    <span class="
                                        cadastro-badge
                                        {
                                            classe_cadastro(
                                                status_gestora
                                            )
                                        }
                                    ">
                                        {status_gestora_html}
                                    </span>

                                </div>

                            </div>

                        </div>
                        """
                    )

                    st.html(
                        """
                        <div class="card-bottom-space">
                        </div>
                        """
                    )

                    (
                        rodape_status,
                        rodape_botao,
                    ) = st.columns(
                        [
                            1,
                            1.55,
                        ],
                        gap="small",
                        vertical_alignment="center",
                    )

                    with rodape_status:

                        st.html(
                            f"""
                            <div class="card-footer">

                                <span class="
                                    status-badge
                                    {
                                        classe_status(
                                            status_vencimento
                                        )
                                    }
                                ">
                                    {status_html}
                                </span>

                            </div>
                            """
                        )

                    with rodape_botao:

                        abrir_questionario = (
                            st.button(
                                "Abrir questionário",
                                key=(
                                    f"abrir_"
                                    f"{id_gestora}"
                                ),
                                use_container_width=True,
                                disabled=not preenchida,
                            )
                        )

                        if abrir_questionario:

                            st.switch_page(
                                (
                                    "pages/"
                                    "s3_due_diligence_"
                                    "questionario.py"
                                ),
                                query_params={
                                    "id_gestora": str(
                                        id_gestora
                                    ),
                                    "id_preenchimento": str(
                                        gestora[
                                            "id_preenchimento"
                                        ]
                                    ),
                                    "status_vencimento": (
                                        status_vencimento
                                    ),
                                    "data_vencimento": (
                                        valor_seguro(
                                            gestora.get(
                                                "vencimento"
                                            ),
                                            "",
                                        )
                                    ),
                                },
                            )