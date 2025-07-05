import os
from sqlalchemy import create_engine, text
from passlib.hash import bcrypt
import json
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    data_dir = os.environ.get("RADHA_DATA_DIR", os.path.dirname(__file__))
    os.makedirs(data_dir, exist_ok=True)
    DATABASE_URL = f"sqlite:///{os.path.join(data_dir, 'marketing_ia.db')}"

engine = create_engine(DATABASE_URL)

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
    "producao",
    "producao/apontamento",
    "producao/apontamento-volume",
    "producao/chapas",
    "producao/lote",
    "producao/nesting",
    "producao/ocorrencias",
    "producao/relatorios/ocorrencias",
]


def get_db_connection():
    return engine.connect()


def init_db():
    with engine.begin() as conn:
        conn.execute(text(
            """CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT,
                email TEXT,
                nome TEXT,
                cargo TEXT,
                permissoes TEXT
            )"""
        ))

        # Create initial admin user if the table is empty. This mirrors the
        # documentation which states that the first login is defined via the
        # RADHA_ADMIN_* environment variables.
        result = conn.execute(text("SELECT COUNT(*) AS count FROM users"))
        total = result.scalar_one()
        if total == 0:
            admin_user = os.getenv("RADHA_ADMIN_USER", "admin")
            admin_pass = os.getenv("RADHA_ADMIN_PASS", "admin")
            conn.execute(
                text(
                    "INSERT INTO users (username, password, email, nome, cargo, permissoes) "
                    "VALUES (:u, :p, '', 'Administrador', 'admin', :perms)"
                ),
                {
                    "u": admin_user,
                    "p": bcrypt.hash(admin_pass),
                    "perms": json.dumps(DEFAULT_ADMIN_PERMISSIONS),
                },
            )


