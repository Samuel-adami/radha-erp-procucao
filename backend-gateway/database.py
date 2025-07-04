import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    data_dir = os.environ.get("RADHA_DATA_DIR", os.path.dirname(__file__))
    os.makedirs(data_dir, exist_ok=True)
    DATABASE_URL = f"sqlite:///{os.path.join(data_dir, 'gateway.db')}"

engine = create_engine(DATABASE_URL)


def get_db_connection():
    return engine.connect()


def init_db():
    with engine.begin() as conn:
        conn.execute(text(
            """CREATE TABLE IF NOT EXISTS empresa (
                id SERIAL PRIMARY KEY,
                codigo TEXT,
                razao_social TEXT,
                nome_fantasia TEXT,
                cnpj TEXT,
                inscricao_estadual TEXT,
                cep TEXT,
                rua TEXT,
                numero TEXT,
                complemento TEXT,
                bairro TEXT,
                cidade TEXT,
                estado TEXT,
                telefone1 TEXT,
                telefone2 TEXT,
                slogan TEXT,
                logo BYTEA
            )"""
        ))

