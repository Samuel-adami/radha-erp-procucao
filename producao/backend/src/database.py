import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv, find_dotenv
from models import Base, Chapa, Lote, Nesting

load_dotenv(find_dotenv())

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not configured")

schema = os.environ.get("DATABASE_SCHEMA")
connect_args = {"options": f"-c search_path={schema}"} if schema else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)


def _ph() -> str:
    """Return parameter placeholder according to the DB dialect."""
    return "%s" if engine.dialect.name == "postgresql" else "?"


def insert_with_id(conn, sql: str, params: tuple) -> int:
    """Execute INSERT and return generated primary key across DBs."""
    if engine.dialect.name == "postgresql":
        result = conn.exec_driver_sql(sql + " RETURNING id", params)
        return result.scalar()
    else:
        result = conn.exec_driver_sql(sql, params)
        return result.lastrowid


def exec_ignore(conn, sql: str, params: tuple) -> None:
    """Execute INSERT ignoring duplicates depending on the database."""
    if engine.dialect.name == "postgresql":
        sql += " ON CONFLICT DO NOTHING"
    conn.exec_driver_sql(sql, params)


def get_db_connection():
    return engine.connect()


def init_db():
    """Create all tables defined in models.py."""
    Base.metadata.create_all(engine)

