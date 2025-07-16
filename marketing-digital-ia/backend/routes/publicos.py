from fastapi import APIRouter, Depends
from models.publicos import PublicoAlvo
from services import publico_service
from security import verificar_autenticacao

router = APIRouter(prefix="/publicos", tags=["Publicos"])

# ✅ Permissão controlada pelo cadastro de usuários
autorizacao = Depends(
    verificar_autenticacao(permissoes=["marketing-ia/publicos-alvo"])
)


@router.post("/", dependencies=[autorizacao])
async def adicionar_publico(publico: PublicoAlvo):
    novo_id = publico_service.criar_publico(publico.dict())
    return {"id": novo_id}


@router.get("/", dependencies=[autorizacao])
async def listar_publicos():
    return publico_service.listar_publicos()
