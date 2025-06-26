from fastapi import APIRouter, HTTPException, Request
from services import auth_service

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.get("/")
async def listar():
    return {"usuarios": auth_service.listar_usuarios()}


@router.post("/")
async def criar(request: Request):
    data = await request.json()
    new_id = auth_service.criar_usuario(data)
    return {"id": new_id}


@router.put("/{user_id}")
async def atualizar(user_id: int, request: Request):
    data = await request.json()
    if not auth_service.atualizar_usuario(user_id, data):
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return {"ok": True}


@router.delete("/{user_id}")
async def excluir(user_id: int):
    if not auth_service.excluir_usuario(user_id):
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return {"ok": True}
