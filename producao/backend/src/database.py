import sqlite3
import os
from pathlib import Path

# Allow custom data directory via RADHA_DATA_DIR
DATA_DIR = Path(os.environ.get("RADHA_DATA_DIR", Path(__file__).resolve().parent))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "producao.db"


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
        "CREATE TABLE IF NOT EXISTS config_ferramentas (id INTEGER PRIMARY KEY CHECK (id = 1), dados TEXT)"
    )
    cur.execute(
        "CREATE TABLE IF NOT EXISTS config_cortes (id INTEGER PRIMARY KEY CHECK (id = 1), dados TEXT)"
    )
    cur.execute(
        "CREATE TABLE IF NOT EXISTS config_layers (id INTEGER PRIMARY KEY CHECK (id = 1), dados TEXT)"
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS chapas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            possui_veio INTEGER,
            propriedade TEXT,
            espessura REAL,
            comprimento REAL,
            largura REAL
        )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS lotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pasta TEXT UNIQUE,
            criado_em TEXT
        )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS nestings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lote TEXT,
            pasta_resultado TEXT,
            criado_em TEXT
        )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS lotes_ocorrencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lote TEXT,
            pacote TEXT,
            oc_numero INTEGER UNIQUE,
            pasta TEXT,
            criado_em TEXT
        )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS motivos_ocorrencia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE,
            descricao TEXT,
            tipo TEXT,
            setor TEXT
        )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS ocorrencias_pecas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            oc_id INTEGER,
            peca_id INTEGER,
            descricao_peca TEXT,
            motivo_id TEXT,
            FOREIGN KEY(oc_id) REFERENCES lotes_ocorrencias(id),
            FOREIGN KEY(motivo_id) REFERENCES motivos_ocorrencia(codigo)
        )"""
    )
    conn.commit()
    conn.close()


init_db()
