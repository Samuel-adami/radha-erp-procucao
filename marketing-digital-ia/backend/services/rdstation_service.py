import os
import time
import asyncio
import httpx
from services.rdstation_auth_service import get_access_token, refresh

API_URL = "https://api.rd.services/platform/contacts"

_CACHE = None
_CACHE_TIMESTAMP = 0.0
_CACHE_LOCK = asyncio.Lock()
CACHE_TTL = 900  # 15 minutos

async def _fetch_leads(page_size: int = 100, max_pages: int | None = None):
    print("[DEBUG] Iniciando _fetch_leads()")
    token = await get_access_token()
    print("[DEBUG] Token recebido:", token)
    if not token:
        print("[ERRO] Token de acesso ausente ou inválido.")
        return []

    headers = {"Authorization": f"Bearer {token}"}
    resultados = []
    pagina = 1

    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            params = {"page": pagina, "page_size": page_size}
            resp = await client.get(API_URL, headers=headers, params=params)
            print("[DEBUG] Resposta da RD:", resp.status_code, resp.json())
            if resp.status_code == 401:
                # Token expirado ou inválido, tenta atualizar e refazer a requisição
                await refresh()
                token = await get_access_token()
                print("[DEBUG] Usando token:", token)
                if not token:
                    resp.raise_for_status()
                headers["Authorization"] = f"Bearer {token}"
                resp = await client.get(API_URL, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
            print("[DEBUG] Resposta da RD Station:", data)
            contatos = data.get("contacts", data.get("items", []))
            resultados.extend(contatos)

            # Verifica se há mais páginas. A API pode retornar total ou next page.
            if len(contatos) < page_size:
                break

            pagina += 1
            if max_pages and pagina > max_pages:
                break

    return resultados

async def obter_leads(
    force_refresh: bool = False,
    page_size: int = 100,
    max_pages: int | None = None,
):
    global _CACHE, _CACHE_TIMESTAMP
    async with _CACHE_LOCK:
        if not force_refresh and _CACHE and time.time() - _CACHE_TIMESTAMP < CACHE_TTL:
            return _CACHE
        try:
            leads = await _fetch_leads(page_size=page_size, max_pages=max_pages)
            _CACHE = leads
            _CACHE_TIMESTAMP = time.time()
            return leads
        except Exception:
            # Em caso de falha, retorna dados em cache mesmo que expirados
            return _CACHE or []
