import sqlite3
import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("RADHA_DATA_DIR", Path(__file__).resolve().parent))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "comercial.db"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS atendimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            codigo TEXT,
            projetos TEXT,
            previsao_fechamento TEXT,
            temperatura TEXT,
            tem_especificador INTEGER,
            especificador_nome TEXT,
            rt_percent REAL,
            historico TEXT
        )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS atendimento_tarefas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            atendimento_id INTEGER,
            nome TEXT,
            concluida INTEGER DEFAULT 0,
            dados TEXT,
            FOREIGN KEY (atendimento_id) REFERENCES atendimentos(id)
        )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS condicoes_pagamento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            numero_parcelas INTEGER NOT NULL,
            juros_parcela REAL DEFAULT 0,
            dias_vencimento TEXT,
            ativa INTEGER DEFAULT 1
        )"""
    )
    conn.commit()
    conn.close()


init_db()
