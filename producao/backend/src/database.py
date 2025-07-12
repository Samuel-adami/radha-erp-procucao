from sqlalchemy import create_engine
from models import Base

# Configurações de conexão definidas diretamente no código para evitar
# dependência de variáveis de ambiente externas.
DATABASE_URL = "postgresql://radha_admin:84840105@localhost:5432/producao"
schema = "producao"
connect_args = {"options": f"-c search_path={schema}"} if schema else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

if engine.dialect.name != "postgresql":
    raise RuntimeError("Production backend requires a PostgreSQL database")

PLACEHOLDER = "%s"


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

