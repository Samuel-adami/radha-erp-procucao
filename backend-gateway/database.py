import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "gateway.db"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS empresa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT,
            razao_social TEXT,
            nome_fantasia TEXT,
            cnpj TEXT,
            inscricao_estadual TEXT,
            cep TEXT,
            rua TEXT,
            numero TEXT,
            bairro TEXT,
            cidade TEXT,
            estado TEXT,
            telefone1 TEXT,
            telefone2 TEXT,
            logo BLOB
        )"""
    )
    conn.commit()
    conn.close()


init_db()
