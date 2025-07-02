import sqlite3
import os
from pathlib import Path

# Allow custom data directory via RADHA_DATA_DIR
DATA_DIR = Path(os.environ.get("RADHA_DATA_DIR", Path(__file__).resolve().parent))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "gateway.db"


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
            complemento TEXT,
            bairro TEXT,
            cidade TEXT,
            estado TEXT,
            telefone1 TEXT,
            telefone2 TEXT,
            slogan TEXT,
            logo BLOB
        )"""
    )
    cols = [row[1] for row in cur.execute("PRAGMA table_info(empresa)")]
    if "slogan" not in cols:
        cur.execute("ALTER TABLE empresa ADD COLUMN slogan TEXT")
    if "complemento" not in cols:
        cur.execute("ALTER TABLE empresa ADD COLUMN complemento TEXT")
    conn.commit()
    conn.close()


init_db()
