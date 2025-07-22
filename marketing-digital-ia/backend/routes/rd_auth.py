from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from pydantic import BaseModel
import os
from services.rdstation_auth_service import exchange_code, save_tokens


router = APIRouter(prefix="/rd", tags=["RD Station"])

CLIENT_ID = os.getenv("RDSTATION_CLIENT_ID")
REDIRECT_URI = os.getenv("RDSTATION_REDIRECT_URI")
AUTH_URL = "https://api.rd.services/auth/dialog"



class TokenData(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    account_id: str = "default"


@router.get("/login")
async def rd_login():
    if not CLIENT_ID or not REDIRECT_URI:
        raise HTTPException(status_code=500, detail="Integração RD Station não configurada")
    scope = "contacts"
    url = (
        f"{AUTH_URL}?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
        f"&response_type=code&scope={scope}"
    )
    return RedirectResponse(url)


@router.get("/callback")
async def rd_callback(code: str):
    try:
        await exchange_code(code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


@router.post("/tokens")
async def store_tokens(data: TokenData):
    try:
        save_tokens(data.account_id, data.access_token, data.refresh_token, data.expires_in)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}

