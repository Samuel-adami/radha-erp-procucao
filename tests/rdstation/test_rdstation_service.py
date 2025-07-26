import sys
import json
from pathlib import Path
import pytest
import types

# Add backend path to import modules
BACKEND_DIR = Path(__file__).resolve().parents[2] / "marketing-digital-ia" / "backend"
sys.path.extend([str(BACKEND_DIR), str(BACKEND_DIR / "services")])

import rdstation_service  # type: ignore
import rdstation_auth_service  # type: ignore
import httpx
import _rdstation_http  # client compartilhado para RD Station

class MockResponse:
    def __init__(self, status_code, data=None):
        self.status_code = status_code
        self._data = data or {}
        self.text = json.dumps(self._data)

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=None, response=self)

class MockAsyncClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def get(self, url, headers=None, params=None):
        self.calls.append((url, headers, params))
        return self.responses.pop(0)


@pytest.mark.asyncio
async def test_fetch_leads_refreshes_token(monkeypatch):
    responses = [
        MockResponse(401, {}),
        MockResponse(200, {"contacts": [{"id": 1}]}),
        MockResponse(200, {"contacts": []}),
    ]
    monkeypatch.setattr(_rdstation_http, "client", MockAsyncClient(responses))

    tokens = ["old", "new"]
    async def fake_get_token(account_id="default"):
        return tokens.pop(0)

    async def fake_refresh(account_id="default"):
        return {"access_token": "new"}

    monkeypatch.setattr(rdstation_auth_service, "get_access_token", fake_get_token)
    monkeypatch.setattr(rdstation_auth_service, "refresh", fake_refresh)
    monkeypatch.setattr(rdstation_service, "get_access_token", fake_get_token)
    monkeypatch.setattr(rdstation_service, "refresh", fake_refresh)

    leads = await rdstation_service._fetch_leads(page_size=1)
    assert leads == [{"id": 1}]
    assert not tokens  # both tokens consumed


@pytest.mark.asyncio
async def test_fetch_leads_paginates(monkeypatch):
    responses = [
        MockResponse(200, {"contacts": [{"id": 1}, {"id": 2}]}),
        MockResponse(200, {"contacts": [{"id": 3}]}),
    ]
    monkeypatch.setattr(_rdstation_http, "client", MockAsyncClient(responses))

    async def fake_get_token(account_id="default"):
        return "token"

    monkeypatch.setattr(rdstation_auth_service, "get_access_token", fake_get_token)
    monkeypatch.setattr(rdstation_service, "get_access_token", fake_get_token)

    leads = await rdstation_service._fetch_leads(page_size=2)
    assert leads == [{"id": 1}, {"id": 2}, {"id": 3}]


@pytest.mark.asyncio
async def test_fetch_leads_raises_when_no_token(monkeypatch):
    async def fake_get_token(account_id="default"):
        raise RuntimeError("no tokens")

    monkeypatch.setattr(rdstation_auth_service, "get_access_token", fake_get_token)
    monkeypatch.setattr(rdstation_service, "get_access_token", fake_get_token)
    monkeypatch.setattr(_rdstation_http, "client", MockAsyncClient([]))

    with pytest.raises(RuntimeError):
        await rdstation_service._fetch_leads()
