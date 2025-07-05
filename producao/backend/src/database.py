import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not configured")

schema = os.environ.get("DATABASE_SCHEMA")
connect_args = {"options": f"-c search_path={schema}"} if schema else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)


def get_db_connection():
    return engine.connect()


def init_db():
    with engine.begin() as conn:
        conn.execute(text(
            """CREATE TABLE IF NOT EXISTS chapas (
                id SERIAL PRIMARY KEY,
                possui_veio INTEGER,
                propriedade TEXT,
                espessura REAL,
                comprimento REAL,
                largura REAL
            )"""
        ))
        conn.execute(text(
            """CREATE TABLE IF NOT EXISTS lotes (
                id SERIAL PRIMARY KEY,
                pasta TEXT,
                criado_em TEXT
            )"""
        ))
        conn.execute(text(
            """CREATE TABLE IF NOT EXISTS nestings (
                id SERIAL PRIMARY KEY,
                lote TEXT,
                pasta_resultado TEXT,
                criado_em TEXT
            )"""
        ))

