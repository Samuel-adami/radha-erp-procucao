import time
import asyncio
import logging
import httpx
from fastapi import HTTPException
from services.rdstation_auth_service import get_access_token, refresh

API_URL = "https://api.rd.services/platform/contacts"

_CACHE = None
_CACHE_TIMESTAMP = 0.0
_CACHE_LOCK = asyncio.Lock()
CACHE_TTL = 900  # 15 minutos

async def _fetch_leads(page_size: int = 100, max_pages: int | None = None):
    logging.debug("Iniciando _fetch_leads()")
    token = await get_access_token()
    logging.debug("Token recebido com sucesso")
    if not token:

        print("[ERRO] Token de acesso ausente ou inválido.")
        raise HTTPException(status_code=401, detail="RD Station token missing")


    headers = {"Authorization": f"Bearer {token}"}
    resultados = []
    pagina = 1

    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            params = {"page": pagina, "page_size": page_size}
            resp = await client.get(API_URL, headers=headers, params=params)
            logging.debug("Código da resposta: %s", resp.status_code)
            logging.debug("Texto bruto da resposta: %s", resp.text)
            if resp.status_code == 401:
                logging.error("Token expirado ou inválido. Tentando refresh...")
                await refresh()
                token = await get_access_token()
                logging.debug("Novo token obtido com sucesso")
                if not token:
                    logging.error("Falha ao obter novo token.")
                    resp.raise_for_status()
                headers["Authorization"] = f"Bearer {token}"
                resp = await client.get(API_URL, headers=headers, params=params)

            resp.raise_for_status()
            data = resp.json()
            contatos = data.get("contacts", data.get("items", []))
            logging.debug(
                "Página %s - %s contatos retornados", pagina, len(contatos)
            )
            resultados.extend(contatos)

            if len(contatos) < page_size:
                break

            pagina += 1
            if max_pages and pagina > max_pages:
                break

    logging.debug("Total de leads acumulados: %s", len(resultados))
    return resultados


async def obter_leads(
    force_refresh: bool = False,
    page_size: int = 100,
    max_pages: int | None = None,
):
    logging.debug("Entrou em obter_leads()")
    global _CACHE, _CACHE_TIMESTAMP
    async with _CACHE_LOCK:
        if not force_refresh and _CACHE and time.time() - _CACHE_TIMESTAMP < CACHE_TTL:
            logging.debug("Retornando dados do cache.")
            return _CACHE
        try:
            logging.debug("Chamando _fetch_leads()")
            leads = await _fetch_leads(page_size=page_size, max_pages=max_pages)
            _CACHE = leads
            _CACHE_TIMESTAMP = time.time()
            logging.debug("Leads recebidos: %s", len(leads))
            return leads
        except HTTPException:
            # Propaga erros de autenticação para que a rota trate adequadamente
            raise
        except Exception as e:
            logging.error("Falha ao obter leads: %s", e)
            return _CACHE or []

