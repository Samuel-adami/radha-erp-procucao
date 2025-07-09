import os
from sqlalchemy import create_engine
from dotenv import load_dotenv, find_dotenv
from models import (
    Base,
    Atendimento,
    AtendimentoTarefa,
    CondicaoPagamento,
    Template,
    ProjetoItem,
    GabsterProjetoItem,
)

load_dotenv(find_dotenv())

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not configured")

schema = os.environ.get("DATABASE_SCHEMA")
connect_args = {"options": f"-c search_path={schema}"} if schema else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

if engine.dialect.name != "postgresql":
    raise RuntimeError("Comercial backend requires a PostgreSQL database")


def get_db_connection():
    return engine.connect()


def insert_with_id(conn, sql: str, params: tuple):

    """Execute INSERT and return generated primary key across DBs."""
    if engine.dialect.name == "postgresql":
        result = conn.exec_driver_sql(sql + " RETURNING id", params)
        return result.scalar()
    else:
        result = conn.exec_driver_sql(sql, params)
        return result.lastrowid



def init_db():
    """Create all tables defined in models.py."""
    Base.metadata.create_all(engine)

