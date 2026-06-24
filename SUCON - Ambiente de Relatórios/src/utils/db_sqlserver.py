from sqlalchemy import create_engine
import os
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(env_path)

@st.cache_resource(ttl=3600)
def get_connection():
    connection_string = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=yes;"
        f"SERVER={os.getenv('CERES_SERVER')};"
        f"UID={os.getenv('CERES_USER')};"
        f"PWD={os.getenv('CERES_PASSWORD')};"
        f"DATABASE={os.getenv('DB')};"
    )
    connection_url = f"mssql+pyodbc:///?odbc_connect={connection_string}"
    return create_engine(connection_url)