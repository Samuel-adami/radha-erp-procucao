import os
import sys
import json
import time
import asyncio
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text

# Adiciona o backend ao path para importar modulos existentes
BACKEND_DIR = Path(__file__).resolve().parents[1] / "marketing-digital-ia" / "backend"
sys.path.extend([str(BACKEND_DIR), str(BACKEND_DIR / "services")])

# Carrega .env local se existir
env_path = BACKEND_DIR / ".env"
if env_path.exists():
    load_dotenv(env_path)

from database import get_db_connection  # type: ignore
from services import rdstation_auth_service, rdstation_service  # type: ignore


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

        # Tenta atualizar o token
        try:
            refreshed = await rdstation_auth_service.refresh(token.get("account_id", "default"))
            info["refresh_success"] = True
            info["refresh_response"] = refreshed
        except Exception as exc:
            info["refresh_success"] = False
            info["refresh_error"] = str(exc)

        # Tenta buscar um lead para validar a comunicacao
        try:
            leads = await rdstation_service._fetch_leads(page_size=1, max_pages=1)
            info["fetch_success"] = True
            info["lead_sample"] = leads[0] if leads else None
        except Exception as exc:
            info["fetch_success"] = False
            info["fetch_error"] = str(exc)

    with open("rdstation_debug_info.json", "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)

    print("Informacoes salvas em rdstation_debug_info.json")


if __name__ == "__main__":
    asyncio.run(main())
