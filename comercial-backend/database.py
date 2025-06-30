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
            historico TEXT,
            arquivos_json TEXT,
            vendedor TEXT,
            telefone TEXT,
            email TEXT,
            rua TEXT,
            numero TEXT,
            cidade TEXT,
            estado TEXT,
            cep TEXT,
            data_cadastro TEXT DEFAULT CURRENT_TIMESTAMP
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
            ativa INTEGER DEFAULT 1,
            parcelas_json TEXT
        )"""
    )
    cols = [row[1] for row in cur.execute("PRAGMA table_info(condicoes_pagamento)")]
    if "parcelas_json" not in cols:
        cur.execute("ALTER TABLE condicoes_pagamento ADD COLUMN parcelas_json TEXT")
    cols_a = [row[1] for row in cur.execute("PRAGMA table_info(atendimentos)")]
    if "arquivos_json" not in cols_a:
        cur.execute("ALTER TABLE atendimentos ADD COLUMN arquivos_json TEXT")
    if "data_cadastro" not in cols_a:
        # SQLite não permite adicionar uma coluna com DEFAULT CURRENT_TIMESTAMP
        # via ALTER TABLE. Criamos a coluna e definimos o valor atual para
        # registros existentes.
        cur.execute("ALTER TABLE atendimentos ADD COLUMN data_cadastro TEXT")
        cur.execute(
            "UPDATE atendimentos SET data_cadastro = CURRENT_TIMESTAMP WHERE data_cadastro IS NULL"
        )
    # Campos adicionais para dados do cliente/vendedor
    adicionais = [
        "vendedor",
        "telefone",
        "email",
        "rua",
        "numero",
        "cidade",
        "estado",
        "cep",
    ]
    for campo in adicionais:
        if campo not in cols_a:
            cur.execute(f"ALTER TABLE atendimentos ADD COLUMN {campo} TEXT")
    conn.commit()
    conn.close()


init_db()
