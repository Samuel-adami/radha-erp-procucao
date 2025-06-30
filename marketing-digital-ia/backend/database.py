import sqlite3
import os
from pathlib import Path
import bcrypt as _bcrypt
from types import SimpleNamespace
if not hasattr(_bcrypt, "__about__"):
    _bcrypt.__about__ = SimpleNamespace(__version__=_bcrypt.__version__)
from passlib.hash import bcrypt

DATA_DIR = Path(os.environ.get("RADHA_DATA_DIR", Path(__file__).resolve().parent))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "marketing_ia.db"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _migrate_passwords(conn):
    """Hash any plaintext passwords using bcrypt."""
    cur = conn.cursor()
    rows = cur.execute("SELECT id, password FROM users").fetchall()
    updated = 0
    for row in rows:
        pwd = row["password"]
        if pwd and not str(pwd).startswith("$2"):
            cur.execute(
                "UPDATE users SET password=? WHERE id=?",
                (bcrypt.hash(pwd), row["id"]),
            )
            updated += 1
    if updated:
        conn.commit()


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            email TEXT,
            nome TEXT,
            cargo TEXT,
            permissoes TEXT
        )"""
    )
    conn.commit()

    _migrate_passwords(conn)

    # Create a default admin user on first run
    exists = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if exists == 0:
        cur.execute(
            "INSERT INTO users (username, password, email, nome, cargo, permissoes)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (
                os.getenv("RADHA_ADMIN_USER", "admin"),
                bcrypt.hash(os.getenv("RADHA_ADMIN_PASS", "admin")),
                "admin@example.com",
                "Administrador",
                "admin",
                "[\"chat\", \"campanhas\", \"publicacoes\", \"publico\", \"marketing-ia\", \"producao\", \"cadastros\", \"comercial\", \"comercial/atendimentos\"]",
            ),
        )
        conn.commit()

    _migrate_passwords(conn)
    conn.close()


init_db()
