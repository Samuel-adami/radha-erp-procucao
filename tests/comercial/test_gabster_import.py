import sys
import importlib
import json
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
import types

ROOT_DIR = Path(__file__).resolve().parents[2]
MOD_DIR = ROOT_DIR / "comercial-backend"


def load_main():
    """Import comercial backend `main` using a stub database module."""
    sys.path.insert(0, str(MOD_DIR))
    dummy_db = types.ModuleType("database")
    dummy_db.get_db_connection = lambda: None
    dummy_db.init_db = lambda: None
    dummy_db.insert_with_id = lambda *a, **k: 1
    sys.modules["database"] = dummy_db
    try:
        return importlib.import_module("main")
    finally:
        sys.path.pop(0)
        sys.modules.pop("database", None)


def test_gabster_import_saves_items(monkeypatch):
    main = load_main()

    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    conn = engine.connect()
    conn.execute(
        text(
            """CREATE TABLE atendimento_tarefas (
            id INTEGER PRIMARY KEY,
            atendimento_id INTEGER,
            nome TEXT,
            concluida INTEGER,
            dados TEXT,
            data_execucao TEXT
        )"""
        )
    )
    conn.execute(
        text(
            """CREATE TABLE projeto_itens (
            id INTEGER PRIMARY KEY,
            atendimento_id INTEGER,
            tarefa_id INTEGER,
            ambiente TEXT,
            descricao TEXT,
            unitario REAL,
            quantidade INTEGER,
            total REAL
        )"""
        )
    )
    conn.execute(
        text(
            """CREATE TABLE gabster_projeto_itens (
            pk INTEGER PRIMARY KEY,
            atendimento_id INTEGER,
            tarefa_id INTEGER,
            referencia TEXT,
            quantidade INTEGER,
            valor REAL
        )"""
        )
    )
    conn.execute(
        text(
            "INSERT INTO atendimento_tarefas (id, atendimento_id, nome, concluida)"
            " VALUES (1, 1, 'Projeto', 0)"
        )
    )
    conn.commit()

    def get_conn():
        class Wrapper:
            def __init__(self, c):
                self.c = c

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def exec_driver_sql(self, sql, params=None):
                sql = sql.replace("%s", "?")
                return self.c.exec_driver_sql(sql, params or ())

            def commit(self):
                self.c.commit()

            def close(self):
                self.c.close()

        return Wrapper(conn)

    monkeypatch.setattr(main, "get_db_connection", get_conn)

    client = TestClient(main.app)

    dados = {
        "programa": "Gabster",
        "projetos": {
            "Cozinha": {
                "itens": [
                    {"descricao": "Armario", "unitario": 100, "quantidade": 2, "total": 200}
                ]
            }
        }
    }
    resp = client.put("/atendimentos/1/tarefas/1", json={"dados": json.dumps(dados)})
    assert resp.status_code == 200

    rows = conn.execute(text("SELECT descricao, quantidade, total FROM projeto_itens")).fetchall()
    assert len(rows) == 1
    m = rows[0]._mapping
    assert m["descricao"] == "Armario"
    assert m["quantidade"] == 2
    assert m["total"] == 200.0

    grows = conn.execute(text("SELECT referencia, quantidade, valor FROM gabster_projeto_itens")).fetchall()
    assert len(grows) == 1
    gm = grows[0]._mapping
    assert gm["referencia"] == "Armario"
    assert gm["quantidade"] == 2
    assert gm["valor"] == 200.0
