import sys
from pathlib import Path
from sqlalchemy import create_engine, text
import pytest

# Add backend path to import modules
BACKEND_DIR = Path(__file__).resolve().parents[2] / "marketing-digital-ia" / "backend"
sys.path.extend([str(BACKEND_DIR), str(BACKEND_DIR / "services")])

import rdstation_auth_service  # type: ignore


@pytest.mark.asyncio
async def test_tokens_are_loaded_from_db(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(
            text(
                "CREATE TABLE rdstation_tokens (id INTEGER PRIMARY KEY, account_id TEXT UNIQUE, access_token TEXT, refresh_token TEXT, expires_at INTEGER)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO rdstation_tokens (account_id, access_token, refresh_token, expires_at) VALUES ('default', 'token123', 'refresh', 9999999999)"
            )
        )
        conn.commit()

    monkeypatch.setattr(rdstation_auth_service, "get_db_connection", engine.connect)

    token = await rdstation_auth_service.get_access_token()
    assert token == "token123"
