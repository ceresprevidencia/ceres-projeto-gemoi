import os
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly"
]


def obter_variavel(nome: str) -> str:
    valor = os.getenv(nome)

    if not valor:
        raise RuntimeError(
            f"A variável de ambiente {nome} não foi configurada."
        )

    return valor


def obter_credenciais() -> Credentials:
    credentials_path = Path(
        obter_variavel("GOOGLE_CREDENTIALS_PATH")
    ).expanduser()

    token_path = Path(
        obter_variavel("GOOGLE_TOKEN_PATH")
    ).expanduser()

    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(
            str(token_path),
            SCOPES,
        )

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path),
                SCOPES,
            )

            creds = flow.run_local_server(port=0)

        token_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        token_path.write_text(
            creds.to_json(),
            encoding="utf-8",
        )

    return creds


def puxar_dados() -> list[list[str]]:
    spreadsheet_id = obter_variavel(
        "DDQ_GOOGLE_SHEET_ID"
    )

    intervalo = obter_variavel(
        "DDQ_GOOGLE_SHEET_RANGE"
    )

    creds = obter_credenciais()

    service = build(
        "sheets",
        "v4",
        credentials=creds,
        cache_discovery=False,
    )

    resposta = (
        service.spreadsheets()
        .values()
        .get(
            spreadsheetId=spreadsheet_id,
            range=intervalo,
        )
        .execute()
    )

    return resposta.get("values", [])


if __name__ == "__main__":
    dados = puxar_dados()

  