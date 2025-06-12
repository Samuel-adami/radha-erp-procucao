from fastapi import APIRouter, Depends
from typing import List
from models.publicos import PublicoAlvo
from security import verificar_autenticacao

router = APIRouter(prefix="/publicos", tags=["Publicos"])

# ✅ Apenas cargos autorizados podem interagir com essa rota
autorizacao = Depends(verificar_autenticacao(["Marketing", "Diretoria"]))

publicos_db: List[PublicoAlvo] = []

@router.post("/", dependencies=[autorizacao])
async def adicionar_publico(publico: PublicoAlvo):
    publicos_db.append(publico)
    return {"mensagem": "Público adicionado com sucesso"}

@router.get("/", dependencies=[autorizacao])
async def listar_publicos():
    return publicos_db