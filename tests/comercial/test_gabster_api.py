import sys
import importlib
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
MOD_DIR = ROOT_DIR / "comercial-backend"


def load_module():
    sys.path.insert(0, str(MOD_DIR))
    try:
        return importlib.import_module("gabster_api")
    finally:
        sys.path.pop(0)


def test_list_projetos(monkeypatch):
    gabster_api = load_module()

    class MockResponse:
        def __init__(self, data, status=200):
            self._data = data
            self.status_code = status
            self.text = str(data)

        def json(self):
            return self._data

        def raise_for_status(self):
            if self.status_code >= 400:
                raise gabster_api.requests.HTTPError("error")

    calls = []

    def fake_get(url, headers=None, timeout=15):
        calls.append(url)
        return MockResponse([{"id": 1, "nome": "Proj", "cd_cliente": 2}])

    monkeypatch.setattr(gabster_api.requests, "get", fake_get)
    projetos = gabster_api.list_projetos(offset=5, limit=10, user="u", api_key="k")
    assert calls
    assert "offset=5" in calls[0]
    assert len(projetos) == 1
    assert projetos[0].id == 1
    assert projetos[0].nome == "Proj"
