import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    data_dir = os.environ.get("RADHA_DATA_DIR", os.path.dirname(__file__))
    os.makedirs(data_dir, exist_ok=True)
    DATABASE_URL = f"sqlite:///{os.path.join(data_dir, 'producao.db')}"

engine = create_engine(DATABASE_URL)


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

