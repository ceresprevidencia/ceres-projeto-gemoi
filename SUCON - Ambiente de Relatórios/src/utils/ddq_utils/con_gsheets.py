import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]


def localizar_raiz_projeto() -> Path:
    """
    Localiza a raiz do projeto considerando que o código está
    dentro de alguma subpasta da pasta 'src'.

    Exemplo esperado:

    projeto/
    ├── credentials/
    ├── src/
    │   └── utils/
    │       └── ddq_utils/
    │           └── con_gsheets.py
    └── .env
    """
    arquivo_atual = Path(__file__).resolve()

    for pasta in arquivo_atual.parents:
        if pasta.name.lower() == "src":
            return pasta.parent

    raise RuntimeError(
        "Não foi possível localizar a raiz do projeto. "
        "A pasta 'src' não foi encontrada nos diretórios superiores de "
        f"{arquivo_atual}."
    )


BASE_DIR = localizar_raiz_projeto()

# Procura o .env na raiz do projeto.
load_dotenv(BASE_DIR / ".env")


def obter_variavel(nome: str) -> str:
    """
    Obtém uma variável de ambiente obrigatória.
    """
    valor = os.getenv(nome)

    if not valor or not valor.strip():
        raise RuntimeError(
            f"A variável de ambiente '{nome}' não foi configurada."
        )

    return valor.strip()


def resolver_caminho(nome_variavel: str) -> Path:
    """
    Resolve o caminho informado em uma variável de ambiente.

    Se o caminho for relativo, ele será considerado relativo à raiz
    do projeto, e não ao diretório de execução do Python ou Jenkins.
    """
    valor = obter_variavel(nome_variavel)

    caminho = Path(valor).expanduser()

    if not caminho.is_absolute():
        caminho = BASE_DIR / caminho

    return caminho.resolve()


def salvar_token(
    token_path: Path,
    creds: Credentials,
) -> None:
    """
    Salva ou atualiza o token OAuth do Google.
    """
    token_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    token_path.write_text(
        creds.to_json(),
        encoding="utf-8",
    )


def esta_no_jenkins() -> bool:
    """
    Verifica se o código está sendo executado pelo Jenkins.
    """
    return any(
        os.getenv(nome)
        for nome in (
            "JENKINS_HOME",
            "JENKINS_URL",
            "BUILD_ID",
            "BUILD_NUMBER",
        )
    )


def obter_credenciais() -> Credentials:
    """
    Carrega as credenciais OAuth do Google.

    Ordem utilizada:
    1. Tenta carregar o token existente.
    2. Se estiver expirado e possuir refresh_token, renova.
    3. Se não houver token válido:
       - localmente, abre o fluxo de autenticação no navegador;
       - no Jenkins, gera erro porque não há navegador interativo.
    """
    credentials_path = resolver_caminho(
        "GOOGLE_CREDENTIALS_PATH"
    )

    token_path = resolver_caminho(
        "GOOGLE_TOKEN_PATH"
    )

    if not credentials_path.exists():
        raise FileNotFoundError(
            "Arquivo de credenciais do Google não encontrado. "
            f"Caminho procurado: {credentials_path}"
        )

    if not credentials_path.is_file():
        raise FileNotFoundError(
            "O caminho configurado para as credenciais do Google "
            "não aponta para um arquivo. "
            f"Caminho recebido: {credentials_path}"
        )

    creds: Credentials | None = None

    if token_path.exists():
        if not token_path.is_file():
            raise FileNotFoundError(
                "O caminho configurado para o token do Google "
                "não aponta para um arquivo. "
                f"Caminho recebido: {token_path}"
            )

        try:
            creds = Credentials.from_authorized_user_file(
                str(token_path),
                SCOPES,
            )
        except Exception as erro:
            raise RuntimeError(
                "Não foi possível carregar o token do Google. "
                f"Arquivo: {token_path}. "
                f"Detalhes: {erro}"
            ) from erro

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            salvar_token(token_path, creds)
            return creds
        except Exception as erro:
            raise RuntimeError(
                "Não foi possível renovar o token de acesso do Google. "
                f"Arquivo do token: {token_path}. "
                f"Detalhes: {erro}"
            ) from erro

    if esta_no_jenkins():
        raise RuntimeError(
            "Não existe um token válido do Google para execução no Jenkins. "
            "O Jenkins não consegue concluir o login OAuth interativo. "
            "Execute este arquivo uma vez localmente para gerar o token "
            "ou disponibilize um token válido no Jenkins. "
            f"Caminho esperado do token: {token_path}"
        )

    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(credentials_path),
            SCOPES,
        )

        creds = flow.run_local_server(
            port=0,
        )
    except Exception as erro:
        raise RuntimeError(
            "Não foi possível concluir a autenticação com o Google. "
            f"Credencial utilizada: {credentials_path}. "
            f"Detalhes: {erro}"
        ) from erro

    salvar_token(token_path, creds)

    return creds


def criar_servico_sheets() -> Any:
    """
    Cria o cliente da API do Google Sheets.
    """
    creds = obter_credenciais()

    try:
        return build(
            "sheets",
            "v4",
            credentials=creds,
            cache_discovery=False,
        )
    except Exception as erro:
        raise RuntimeError(
            "Não foi possível criar o serviço da API do Google Sheets. "
            f"Detalhes: {erro}"
        ) from erro


def puxar_dados() -> list[list[str]]:
    """
    Busca os dados da planilha configurada nas variáveis de ambiente.

    Retorna:
        Lista de linhas da planilha.
    """
    spreadsheet_id = obter_variavel(
        "DDQ_GOOGLE_SHEET_ID"
    )

    intervalo = obter_variavel(
        "DDQ_GOOGLE_SHEET_RANGE"
    )

    service = criar_servico_sheets()

    try:
        resposta = (
            service.spreadsheets()
            .values()
            .get(
                spreadsheetId=spreadsheet_id,
                range=intervalo,
            )
            .execute()
        )
    except Exception as erro:
        raise RuntimeError(
            "Erro ao carregar dados da planilha do Google Sheets. "
            f"Planilha: {spreadsheet_id}. "
            f"Intervalo: {intervalo}. "
            f"Detalhes: {erro}"
        ) from erro

    valores = resposta.get("values", [])

    if not isinstance(valores, list):
        raise RuntimeError(
            "A API do Google Sheets retornou um formato de dados inesperado."
        )

    return valores


def exibir_configuracao() -> None:
    """
    Exibe informações úteis para diagnóstico.
    Não mostra o conteúdo das credenciais.
    """
    credentials_path = resolver_caminho(
        "GOOGLE_CREDENTIALS_PATH"
    )

    token_path = resolver_caminho(
        "GOOGLE_TOKEN_PATH"
    )

    print(f"Arquivo atual: {Path(__file__).resolve()}")
    print(f"Raiz do projeto: {BASE_DIR}")
    print(f"Arquivo .env: {BASE_DIR / '.env'}")
    print(f"Credenciais: {credentials_path}")
    print(
        "Credenciais existem: "
        f"{credentials_path.exists()}"
    )
    print(f"Token: {token_path}")
    print(f"Token existe: {token_path.exists()}")
    print(f"Execução no Jenkins: {esta_no_jenkins()}")


if __name__ == "__main__":
    try:
        exibir_configuracao()

        dados = puxar_dados()

        print(
            f"Dados carregados com sucesso: {len(dados)} linhas."
        )

        if dados:
            print(
                f"Quantidade de colunas da primeira linha: "
                f"{len(dados[0])}"
            )

    except Exception as erro:
        print(f"Erro ao carregar dados da planilha: {erro}")
        raise