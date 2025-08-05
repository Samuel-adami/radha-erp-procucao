import importlib
import json
import sys
import types
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text


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


def setup_conn():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
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
            id INTEGER PRIMARY KEY,
            nome TEXT,
            cd_cliente TEXT,
            nome_arquivo_skp TEXT,
            identificador_arquivo_skp TEXT,
            descricao TEXT,
            observacao TEXT,
            ambiente TEXT,
            projeto_ref TEXT
        )"""
        )
    )
    conn.execute(
        text(
            "INSERT INTO atendimento_tarefas (id, atendimento_id, nome, concluida) VALUES (1,1,'Projeto 3D',0)"
        )
    )
    conn.commit()
    return conn


def test_projeto3d_requires_import_before_finalize(monkeypatch):
    main = load_main()
    conn = setup_conn()

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

    resp = client.put("/atendimentos/1/tarefas/1", json={"concluida": True})
    assert resp.status_code == 400


def test_projeto3d_persist_and_finalize(monkeypatch):
    main = load_main()
    conn = setup_conn()

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
                "codigo": "XYZ",
                "cabecalho": {"cd_projeto": 123},
                "itens": [
                    {"descricao": "Armario", "unitario": 100, "quantidade": 2, "total": 200}
                ],
            }
        },
    }

    resp = client.put("/atendimentos/1/tarefas/1", json={"dados": json.dumps(dados)})
    assert resp.status_code == 200

    resp = client.get("/atendimentos/1/tarefas")
    tarefa = resp.json()["tarefas"][0]
    info = json.loads(tarefa["dados"])
    assert info["projetos"]["Cozinha"]["codigo"] == "XYZ"

    resp = client.put(
        "/atendimentos/1/tarefas/1",
        json={"concluida": True, "dados": json.dumps(dados)},
    )
    assert resp.status_code == 200

    resp = client.get("/atendimentos/1/tarefas")
    tarefa = resp.json()["tarefas"][0]
    assert tarefa["concluida"] == 1


def test_projeto3d_accepts_dict_payload(monkeypatch):
    main = load_main()
    conn = setup_conn()

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
                "codigo": "XYZ",
                "cabecalho": {"cd_projeto": 123},
                "itens": [
                    {"descricao": "Armario", "unitario": 100, "quantidade": 2, "total": 200}
                ],
            }
        },
    }

    resp = client.put("/atendimentos/1/tarefas/1", json={"dados": dados})
    assert resp.status_code == 200

    resp = client.get("/atendimentos/1/tarefas")
    tarefa = resp.json()["tarefas"][0]
    info = json.loads(tarefa["dados"])
    assert info["projetos"]["Cozinha"]["codigo"] == "XYZ"

    resp = client.put("/atendimentos/1/tarefas/1", json={"concluida": True})
    assert resp.status_code == 200

    resp = client.get("/atendimentos/1/tarefas")
    tarefa = resp.json()["tarefas"][0]
    assert tarefa["concluida"] == 1

