from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, Text, TIMESTAMP, func
from models import Base
from dotenv import load_dotenv, find_dotenv
import os

# Permite que a URL de conexão e o schema sejam definidos via variáveis de
# ambiente. Caso não estejam configurados, valores padrão são utilizados para
# facilitar o desenvolvimento local.
load_dotenv(find_dotenv())

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://radha_admin:84840105@localhost:5432/producao"
)
schema = os.getenv("DATABASE_SCHEMA", "producao")
connect_args = {"options": f"-c search_path={schema}"} if schema else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

if engine.dialect.name != "postgresql":
    raise RuntimeError("Production backend requires a PostgreSQL database")

PLACEHOLDER = "%s"

# Metadata object for table definitions
metadata = Base.metadata

# Table for draft production lots
lotes_producao = Table(
    "lotes_producao",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nome", Text, unique=True, nullable=False),
    Column("pacotes_json", Text),
    Column("usuario_id", Integer, nullable=True),
    Column("criado_em", TIMESTAMP, server_default=func.now()),
    Column("atualizado_em", TIMESTAMP, server_default=func.now(), onupdate=func.now()),
)



def insert_with_id(conn, sql: str, params: tuple) -> int:
    """Execute INSERT and return generated primary key."""
    result = conn.exec_driver_sql(sql + " RETURNING id", params)
    return result.scalar()


def exec_ignore(conn, sql: str, params: tuple) -> None:
    """Execute INSERT ignoring duplicates."""
    conn.exec_driver_sql(sql + " ON CONFLICT DO NOTHING", params)


def get_db_connection():
    return engine.connect()


def init_db():
    """Create all tables defined in models.py."""
    Base.metadata.create_all(engine)

