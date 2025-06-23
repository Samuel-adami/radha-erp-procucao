import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "producao.db"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS config_maquina (id INTEGER PRIMARY KEY CHECK (id = 1), dados TEXT)"
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS lotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pasta TEXT UNIQUE,
            criado_em TEXT
        )"""
    )
    conn.commit()
    conn.close()


init_db()
