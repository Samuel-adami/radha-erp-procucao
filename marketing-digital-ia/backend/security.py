# backend/security.py

from fastapi import Header, HTTPException
from jose import JWTError, jwt
from typing import List, Optional
from services.auth_service import SECRET_KEY, ALGORITHM, decodificar_token

def verificar_autenticacao(cargos_permitidos: Optional[List[str]] = None):
    def verificar(authorization: str = Header(None)):
        if not authorization:
            raise HTTPException(status_code=401, detail="Token não fornecido")
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Formato inválido de token")

        token = authorization.split(" ")[1]

        try:
            payload = decodificar_token(token)
            if not payload:
                raise HTTPException(status_code=401, detail="Token inválido ou expirado")

            if cargos_permitidos and payload.get("cargo") not in cargos_permitidos:
                raise HTTPException(status_code=403, detail="Permissão insuficiente")

            return payload  # Esse será o 'usuario' retornado às rotas protegidas

        except JWTError:
            raise HTTPException(status_code=403, detail="Erro ao processar o token")
    return verificar
