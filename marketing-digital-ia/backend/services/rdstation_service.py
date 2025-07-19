import os
import time
import asyncio
import httpx
from fastapi import HTTPException
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
        raise HTTPException(status_code=401, detail="RD Station token missing")

    headers = {"Authorization": f"Bearer {token}"}
    resultados = []
    pagina = 1

    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            params = {"page": pagina, "page_size": page_size}
            resp = await client.get(API_URL, headers=headers, params=params)
            print("[DEBUG] Código da resposta:", resp.status_code)
            print("[DEBUG] Texto bruto da resposta:", resp.text)
            if resp.status_code == 401:
                print("[ERRO] Token expirado ou inválido. Tentando refresh...")
                await refresh()
                token = await get_access_token()
                print("[DEBUG] Novo token:", token)
                if not token:
                    print("[ERRO] Falha ao obter novo token.")
                    resp.raise_for_status()
                headers["Authorization"] = f"Bearer {token}"
                resp = await client.get(API_URL, headers=headers, params=params)

            resp.raise_for_status()
            data = resp.json()
            contatos = data.get("contacts", data.get("items", []))
            print(f"[DEBUG] Página {pagina} - {len(contatos)} contatos retornados")
            resultados.extend(contatos)

            if len(contatos) < page_size:
                break

            pagina += 1
            if max_pages and pagina > max_pages:
                break

    print(f"[DEBUG] Total de leads acumulados: {len(resultados)}")
    return resultados


async def obter_leads(
    force_refresh: bool = False,
    page_size: int = 100,
    max_pages: int | None = None,
):
    print("[DEBUG] Entrou em obter_leads()")
    global _CACHE, _CACHE_TIMESTAMP
    async with _CACHE_LOCK:
        if not force_refresh and _CACHE and time.time() - _CACHE_TIMESTAMP < CACHE_TTL:
            print("[DEBUG] Retornando dados do cache.")
            return _CACHE
        try:
            print("[DEBUG] Chamando _fetch_leads()")
            leads = await _fetch_leads(page_size=page_size, max_pages=max_pages)
            _CACHE = leads
            _CACHE_TIMESTAMP = time.time()
            print(f"[DEBUG] Leads recebidos: {len(leads)}")
            return leads
        except HTTPException:
            # Propaga erros de autenticação para que a rota trate adequadamente
            raise
        except Exception as e:
            print(f"[ERRO] Falha ao obter leads: {e}")
            return _CACHE or []

