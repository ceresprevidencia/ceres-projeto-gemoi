import streamlit as st
import os
import oracledb
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(env_path)

@st.cache_resource(ttl=3600)
def get_connection():
    user = os.getenv("MITRA_USER")
    password = os.getenv("MITRA_PASSWORD")

    if not all([user, password]):
        raise ValueError("Credenciais do banco não configuradas no .env")

    dsn = oracledb.makedsn(
    host="10.200.16.8",
    port=1521,
    service_name="MITRA.CERES.LEF.INTRA"  # ← testa com service_name
)

    return create_engine(
        "oracle+oracledb://",
        connect_args={
            "user": user,
            "password": password,
            "dsn": dsn
        }
    )