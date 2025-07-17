import os
import time
import httpx
from sqlalchemy import text
from database import get_db_connection

CLIENT_ID = os.getenv("RDSTATION_CLIENT_ID")
CLIENT_SECRET = os.getenv("RDSTATION_CLIENT_SECRET")
REDIRECT_URI = os.getenv("RDSTATION_REDIRECT_URI")
TOKEN_URL = "https://api.rd.services/auth/token"


def save_tokens(account_id: str, access: str, refresh: str, expires_in: int) -> None:
    expires_at = int(time.time()) + int(expires_in)
    conn = get_db_connection()
    row = conn.execute(text("SELECT id FROM rdstation_tokens WHERE account_id=:a"), {"a": account_id}).fetchone()
    if row:
        conn.execute(
            text("UPDATE rdstation_tokens SET access_token=:at, refresh_token=:rt, expires_at=:ea WHERE account_id=:a"),
            {"at": access, "rt": refresh, "ea": expires_at, "a": account_id},
        )
    else:
        conn.execute(
            text("INSERT INTO rdstation_tokens (account_id, access_token, refresh_token, expires_at) VALUES (:a, :at, :rt, :ea)"),
            {"a": account_id, "at": access, "rt": refresh, "ea": expires_at},
        )
    conn.commit()
    conn.close()


def delete_tokens(account_id: str) -> None:
    """Remove os tokens armazenados para forçar nova autenticação."""
    conn = get_db_connection()
    conn.execute(text("DELETE FROM rdstation_tokens WHERE account_id=:a"), {"a": account_id})
    conn.commit()
    conn.close()


def _get(account_id: str) -> dict | None:
    conn = get_db_connection()
    row = conn.execute(text("SELECT * FROM rdstation_tokens WHERE account_id=:a"), {"a": account_id}).fetchone()
    conn.close()
    return dict(row._mapping) if row else None


async def exchange_code(code: str, account_id: str = "default") -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            TOKEN_URL,
            json={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "code": code},
        )
        resp.raise_for_status()
        data = resp.json()
        save_tokens(account_id, data.get("access_token"), data.get("refresh_token"), data.get("expires_in", 0))
        return data


async def refresh(account_id: str = "default") -> dict | None:
    token = _get(account_id)
    if not token:
        return None
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                TOKEN_URL,
                json={
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "refresh_token": token.get("refresh_token"),
                },
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                # Tokens expiraram ou são inválidos. Remove do banco para que
                # uma nova autorização seja necessária.
                delete_tokens(account_id)
            raise
        data = resp.json()
        # Nem sempre a API retorna um novo refresh_token. Caso esteja ausente,
        # mantemos o token atual para evitar sobrescrever com ``None`` e causar
        # falhas na próxima atualização.
        refresh_token = data.get("refresh_token") or token.get("refresh_token")
        save_tokens(account_id, data.get("access_token"), refresh_token, data.get("expires_in", 0))
        return data


async def get_access_token(account_id: str = "default") -> str | None:
    token = _get(account_id)
    if not token:
        return None
    if token.get("expires_at") and token["expires_at"] <= int(time.time()):
        refreshed = await refresh(account_id)
        if not refreshed:
            return None
        token = _get(account_id)
    return token.get("access_token")
