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
            """CREATE TABLE IF NOT EXISTS atendimentos (
                id SERIAL PRIMARY KEY,
                cliente TEXT,
                codigo TEXT,
                projetos TEXT,
                previsao_fechamento TEXT,
                temperatura TEXT,
                tem_especificador INTEGER,
                especificador_nome TEXT,
                rt_percent REAL,
                entrega_diferente INTEGER,
                historico TEXT,
                arquivos_json TEXT,
                procedencia TEXT,
                vendedor TEXT,
                telefone TEXT,
                email TEXT,
                rua TEXT,
                numero TEXT,
                complemento TEXT,
                bairro TEXT,
                cidade TEXT,
                estado TEXT,
                cep TEXT,
                data_cadastro TEXT
            )"""
        ))

