import os
import sys
import json
import time
import asyncio
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
import httpx

# Adiciona o backend ao path para importar modulos existentes
BACKEND_DIR = Path(__file__).resolve().parents[1] / "marketing-digital-ia" / "backend"
sys.path.extend([str(BACKEND_DIR), str(BACKEND_DIR / "services")])

# Carrega .env local se existir
env_path = BACKEND_DIR / ".env"
if env_path.exists():
    load_dotenv(env_path)

from database import get_db_connection  # type: ignore
from services import rdstation_auth_service, rdstation_service  # type: ignore

API_URL = rdstation_service.API_URL
TOKEN_URL = rdstation_auth_service.TOKEN_URL


async def main() -> None:
    info: dict[str, object] = {}

    # Verifica variaveis de ambiente essenciais
    required_env = [
        "RDSTATION_CLIENT_ID",
        "RDSTATION_CLIENT_SECRET",
        "RDSTATION_REDIRECT_URI",
    ]
    info["env"] = {var: bool(os.getenv(var)) for var in required_env}

    # Consulta tokens salvos
    conn = get_db_connection()
    rows = conn.execute(text("SELECT * FROM rdstation_tokens"))
    tokens = [dict(r._mapping) for r in rows.fetchall()]
    conn.close()
    info["tokens"] = tokens

    if tokens:
        token = tokens[0]
        expires_in = token.get("expires_at", 0) - int(time.time())
        info["token_status"] = "expired" if expires_in <= 0 else "valid"

        async with httpx.AsyncClient(timeout=30.0) as client:
            # ------- Refresh Token -------
            refresh_payload = {
                "client_id": os.getenv("RDSTATION_CLIENT_ID"),
                "client_secret": os.getenv("RDSTATION_CLIENT_SECRET"),
                "refresh_token": token.get("refresh_token"),
            }
            refresh_headers = {"Content-Type": "application/json"}
            refresh_ts = time.strftime("%Y-%m-%d %H:%M:%S")
            refresh_info = {
                "endpoint": TOKEN_URL,
                "body": refresh_payload,
                "headers": refresh_headers,
                "timestamp": refresh_ts,
            }
            try:
                resp = await client.post(TOKEN_URL, json=refresh_payload)
                refresh_info.update(
                    {
                        "status": resp.status_code,
                        "response": resp.text,
                    }
                )
            except Exception as exc:
                refresh_info["error"] = str(exc)
            info["refresh_attempt"] = refresh_info

            # ------- Fetch Sample Lead -------
            fetch_headers = {"Authorization": f"Bearer {token.get('access_token')}"}
            params = {"page": 1, "page_size": 1}
            fetch_ts = time.strftime("%Y-%m-%d %H:%M:%S")
            fetch_info = {
                "endpoint": API_URL,
                "headers": fetch_headers,
                "params": params,
                "timestamp": fetch_ts,
            }
            try:
                resp = await client.get(API_URL, headers=fetch_headers, params=params)
                fetch_info.update(
                    {
                        "status": resp.status_code,
                        "response": resp.text,
                    }
                )
            except Exception as exc:
                fetch_info["error"] = str(exc)
            info["fetch_attempt"] = fetch_info

    with open("rdstation_debug_info.json", "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)

    print("Informacoes salvas em rdstation_debug_info.json")


if __name__ == "__main__":
    asyncio.run(main())
