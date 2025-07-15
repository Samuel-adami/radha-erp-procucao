from fastapi import APIRouter, Depends
from models.publicos import PublicoAlvo
from services import publico_service
from security import verificar_autenticacao

router = APIRouter(prefix="/publicos", tags=["Publicos"])

# ✅ Apenas cargos autorizados podem interagir com essa rota
autorizacao = Depends(verificar_autenticacao(["Marketing", "Diretoria", "admin"]))


@router.post("/", dependencies=[autorizacao])
async def adicionar_publico(publico: PublicoAlvo):
    novo_id = publico_service.criar_publico(publico.dict())
    return {"id": novo_id}


@router.get("/", dependencies=[autorizacao])
async def listar_publicos():
    return publico_service.listar_publicos()
