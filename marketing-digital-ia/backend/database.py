import sqlite3
import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("RADHA_DATA_DIR", Path(__file__).resolve().parent))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "marketing_ia.db"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


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

    # Create a default admin user on first run
    exists = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if exists == 0:
        cur.execute(
            "INSERT INTO users (username, password, email, nome, cargo, permissoes)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (
                os.getenv("RADHA_ADMIN_USER", "admin"),
                os.getenv("RADHA_ADMIN_PASS", "admin"),
                "admin@example.com",
                "Administrador",
                "admin",
                "[\"chat\", \"campanhas\", \"publicacoes\", \"publico\", \"marketing-ia\", \"producao\", \"cadastros\", \"comercial\"]",
            ),
        )
        conn.commit()
    conn.close()


init_db()
