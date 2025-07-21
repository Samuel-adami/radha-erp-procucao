import os
from sqlalchemy import create_engine
from dotenv import load_dotenv, find_dotenv
from db_models import Base, User

load_dotenv(find_dotenv())

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not configured")

schema = os.environ.get("DATABASE_SCHEMA")
connect_args = {"options": f"-c search_path={schema}"} if schema else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

# All available permission strings, granting access to every module of the ERP
# front-end. These are applied to the initial administrator created on first
# run so the admin can configure the system and cadastrar novos usuários.
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
    "marketing-ia/gestao-leads",
    "finance",
    "finance/bancos",
    "finance/contas",
    "finance/contas-pagar",
    "finance/contas-receber",
    "finance/config-fiscal",
    "producao",
    "producao/apontamento",
    "producao/apontamento-volume",
    "producao/chapas",
    "producao/chapas/estoque",
    "producao/lote",
    "producao/nesting",
    "producao/ocorrencias",
    "producao/relatorios/ocorrencias",
]


def get_db_connection():
    return engine.connect()


def init_db():
    """Create all tables defined in db_models.py."""
    Base.metadata.create_all(engine)


