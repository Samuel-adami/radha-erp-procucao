import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base, Empresa
from sqlalchemy import text
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not configured")

schema = os.environ.get("DATABASE_SCHEMA")
connect_args = {"options": f"-c search_path={schema}"} if schema else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine)

# Permissions granted to the initial administrator account.
DEFAULT_ADMIN_PERMISSIONS = [
    "cadastros",
    "cadastros/dados-empresa",
    "cadastros/clientes",
    "cadastros/fornecedores",
    "cadastros/usuarios",
    "cadastros/condicoes-pagamento",
    "comercial",
    "comercial/atendimentos",
    "formularios",
    "formularios/briefing-vendas",
    "marketing-ia",
    "marketing-ia/chat",
    "marketing-ia/nova-campanha",
    "marketing-ia/nova-publicacao",
    "marketing-ia/publicos-alvo",
    "producao",
    "producao/apontamento",
    "producao/apontamento-volume",
    "producao/chapas",
    "producao/lote",
    "producao/nesting",
    "producao/ocorrencias",
    "producao/relatorios/ocorrencias",
]


def get_session() -> Session:
    """Return a new SQLAlchemy session."""
    return SessionLocal()


def get_db_connection():
    """Return a raw database connection."""
    return engine.connect()


def init_db():
    """Create all tables defined in models.py."""
    Base.metadata.create_all(engine)

