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
    conn.close()


init_db()
