import os
import time
import asyncio
import httpx

RD_TOKEN = os.getenv("RDSTATION_TOKEN")
API_URL = "https://api.rd.services/platform/contacts"

_CACHE = None
_CACHE_TIMESTAMP = 0.0
_CACHE_LOCK = asyncio.Lock()
CACHE_TTL = 900  # 15 minutos

async def _fetch_leads():
    if not RD_TOKEN:
        return []
    headers = {"Authorization": f"Bearer {RD_TOKEN}"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(API_URL, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data.get("contacts", data)

async def obter_leads(force_refresh: bool = False):
    global _CACHE, _CACHE_TIMESTAMP
    async with _CACHE_LOCK:
        if not force_refresh and _CACHE and time.time() - _CACHE_TIMESTAMP < CACHE_TTL:
            return _CACHE
        try:
            leads = await _fetch_leads()
            _CACHE = leads
            _CACHE_TIMESTAMP = time.time()
            return leads
        except Exception:
            # Em caso de falha, retorna dados em cache mesmo que expirados
            return _CACHE or []
