from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
import os
from services.rdstation_auth_service import exchange_code

router = APIRouter(prefix="/rd", tags=["RD Station"])

CLIENT_ID = os.getenv("RDSTATION_CLIENT_ID")
REDIRECT_URI = os.getenv("RDSTATION_REDIRECT_URI")
AUTH_URL = "https://api.rd.services/auth/dialog"

@router.get("/login")
async def rd_login():
    if not CLIENT_ID or not REDIRECT_URI:
        raise HTTPException(status_code=500, detail="Integração RD Station não configurada")
    url = f"{AUTH_URL}?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
    return RedirectResponse(url)


@router.get("/callback")
async def rd_callback(code: str):
    try:
        await exchange_code(code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}
