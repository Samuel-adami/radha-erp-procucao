import os
import time
import asyncio
import logging
import httpx
from jose import jwt
from sqlalchemy import text
from database import get_db_connection

CLIENT_ID = os.getenv("RDSTATION_CLIENT_ID")
CLIENT_SECRET = os.getenv("RDSTATION_CLIENT_SECRET")
REDIRECT_URI = os.getenv("RDSTATION_REDIRECT_URI")
TOKEN_URL = "https://api.rd.services/auth/token"


def _calculate_expires_at(access_token: str | None, expires_in: int | None) -> int:
    """Return an absolute expiration timestamp for the given token."""
    if access_token:
        try:
            claims = jwt.get_unverified_claims(access_token)
            exp = claims.get("exp")
            if exp:
                return int(exp)
            if "iat" in claims and "exp" not in claims:
                # Some tokens provide the lifetime in "exp" relative to iat
                return int(claims["iat"]) + int(claims.get("expires_in", 0))
        except Exception:
            pass
    return int(time.time()) + int(expires_in or 0)


def save_tokens(account_id: str, access: str, refresh: str, expires_in: int) -> None:
    expires_at = _calculate_expires_at(access, expires_in)
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
            json={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": REDIRECT_URI,
            },
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
                    "grant_type": "refresh_token",
                    "refresh_token": token.get("refresh_token"),
                },
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                logging.warning(
                    "Refresh token expirado para %s, removendo do banco", account_id
                )
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


async def auto_refresh_tokens(interval: int = 3600, threshold: int = 300) -> None:
    """Periodicamente renova tokens prestes a expirar.

    Args:
        interval: Tempo em segundos entre cada verificação.
        threshold: Quantos segundos antes do vencimento o token será renovado.
    """
    while True:
        conn = get_db_connection()
        rows = conn.execute(
            text("SELECT account_id, expires_at FROM rdstation_tokens")
        ).fetchall()
        conn.close()
        now = int(time.time())
        for row in rows:
            data = row._mapping
            if data.get("expires_at") and data["expires_at"] <= now + threshold:
                try:
                    await refresh(data["account_id"])
                except Exception as exc:  # pragma: no cover - log only
                    logging.error(
                        "Erro ao renovar tokens para %s: %s", data["account_id"], exc
                    )
        await asyncio.sleep(interval)
