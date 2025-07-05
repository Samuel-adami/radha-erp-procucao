import os
from sqlalchemy import create_engine, text
from passlib.hash import bcrypt
import json
from dotenv import load_dotenv, find_dotenv

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
        else:
            # Existing administrator accounts may have been created before the
            # DEFAULT_ADMIN_PERMISSIONS constant was defined. Ensure they have
            # at least all permissions for the Cadastros module so the menu is
            # visible.
            result = conn.execute(
                text("SELECT id, permissoes FROM users WHERE cargo='admin'")
            ).fetchall()
            for row in result:
                perms = json.loads(row._mapping["permissoes"] or "[]")
                updated = False
                for perm in DEFAULT_ADMIN_PERMISSIONS:
                    if perm.startswith("cadastros") and perm not in perms:
                        perms.append(perm)
                        updated = True
                if updated:
                    conn.execute(
                        text("UPDATE users SET permissoes=:p WHERE id=:id"),
                        {"p": json.dumps(perms), "id": row._mapping["id"]},
                    )


