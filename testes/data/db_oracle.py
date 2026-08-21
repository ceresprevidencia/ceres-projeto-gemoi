import os
import oracledb
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine


ENV_PATH = (
    Path(__file__).resolve().parents[2]
    / "SUCON - Ambiente de Relatórios"
    / ".env"
)
load_dotenv(ENV_PATH)

def get_connection():
    user = os.getenv("MITRA_USER")
    password = os.getenv("MITRA_PASSWORD")

    if not all([user, password]):
        raise ValueError("Credenciais do banco não configuradas no .env")

    dsn = oracledb.makedsn(
    host="10.200.16.8",
    port=1521,
    service_name="MITRA.CERES.LEF.INTRA"  
)

    return create_engine(
        "oracle+oracledb://",
        connect_args={
            "user": user,
            "password": password,
            "dsn": dsn
        }
    )