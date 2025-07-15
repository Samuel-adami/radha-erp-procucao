from fastapi import APIRouter, Depends
from pydantic import BaseModel
from services.openai_service import gerar_resposta
from security import verificar_autenticacao

router = APIRouter(prefix="/nova-campanha", tags=["Campanhas"])

# ✅ Apenas marketing, diretores e administradores podem criar campanhas
autorizacao = verificar_autenticacao(["Marketing", "Diretoria", "admin"])

class CampanhaInput(BaseModel):
    tema: str
    objetivo: str
    publico_alvo: str
    orcamento: float
    duracao: str
    id_assistant: str = None

@router.post("/")
async def criar_campanha(input: CampanhaInput, user=Depends(autorizacao)):
    prompt = (
        f"Você está ajudando {user['nome']} ({user['cargo']}) a planejar uma nova campanha.\n\n"
        f"Tema: {input.tema}\n"
        f"Objetivo: {input.objetivo}\n"
        f"Público-alvo: {input.publico_alvo}\n"
        f"Orçamento: R${input.orcamento}\n"
        f"Duração: {input.duracao}\n\n"
        "Crie conteúdos criativos com CTA, roteiros para landing pages, posts e reels. "
        "Use linguagem compatível com o posicionamento institucional da Radha."
    )

    resposta = await gerar_resposta(
        prompt,
        input.id_assistant
    )

    return {"campanha": resposta}