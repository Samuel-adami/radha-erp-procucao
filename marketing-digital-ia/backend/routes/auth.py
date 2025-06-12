from fastapi import APIRouter, HTTPException, Request, Depends
from services import auth_service
from security import verificar_autenticacao

router = APIRouter()

@router.post("/login")
async def login(request: Request):
    body = await request.json()
    username = body.get("username")
    password = body.get("password")

    if not username or not password:
        raise HTTPException(status_code=400, detail="Usuário e senha são obrigatórios")

    user = auth_service.autenticar(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    return auth_service.criar_token(user)

def get_verificador():
    return verificar_autenticacao(None)

@router.get("/validate")
async def validar_token(usuario=Depends(get_verificador)):
    return {"status": "validado", "usuario": usuario}
 
