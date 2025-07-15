# ✅ publicacao.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from services.openai_service import gerar_resposta, gerar_imagem, gerar_imagem_com_texto
from security import verificar_autenticacao
import os

router = APIRouter(prefix="/nova-publicacao", tags=["Publicacoes"])

# Allow administrators to utilizar esta rota também
autorizacao = verificar_autenticacao(["Marketing", "Diretoria", "admin"])

class PublicacaoInput(BaseModel):
    tema: str
    objetivo: str
    formato: str
    quantidade: int
    id_assistant: str = None

class ImagemInput(BaseModel):
    prompt: str
    texto: str = None  # opcional

@router.post("/")
async def criar_publicacao(input: PublicacaoInput, user=Depends(autorizacao)):
    formato = input.formato.lower()

    observacao = ""
    if input.objetivo.lower() == "engajamento":
        observacao = (
            "\n\nObservação: evite tom comercial ou de vendas. "
            "O conteúdo deve ser informativo, com dicas úteis, e mencionar a Radha de forma leve e natural."
        )

    introducao = (
        f"Você está ajudando {user['nome']} ({user['cargo']}) a planejar conteúdos estratégicos para redes sociais.\n\n"
        f"Tema: {input.tema}\n"
        f"Objetivo: {input.objetivo}\n"
        f"Formato: {input.formato}\n"
        f"Quantidade: {input.quantidade}{observacao}\n\n"
    )

    if formato == "post único":
        corpo = (
            f"Crie {input.quantidade} publicações no formato post único sobre {input.tema}. "
            f"Para cada uma, elabore:\n"
            f"1. Legenda com CTA e hashtags;\n"
            f"2. Sugestão de imagem (incluindo uma cozinha planejada);\n"
            f"3. Sugestão de música sem direitos autorais do Pixabay."
        )
    elif formato == "post carrossel":
        corpo = (
            f"Crie {input.quantidade} carrosséis sobre {input.tema}.\n"
            f"Cada carrossel deve conter {input.quantidade} slides.\n"
            f"Para cada slide, gere:\n"
            f"- Um texto impactante para sobreposição na imagem;\n"
            f"- Um prompt para a geração da imagem no estilo da Radha.\n"
            f"Ao final de cada carrossel, inclua uma legenda única com CTA e hashtags."
        )
    elif formato == "reels":
        corpo = (
            f"Crie {input.quantidade} roteiros de Reels sobre {input.tema}.\n"
            f"Inclua:\n"
            f"1. Roteiro audiovisual detalhado;\n"
            f"2. Música do Pixabay;\n"
            f"3. Texto para vídeo (legenda sobreposta);\n"
            f"4. Legenda completa com CTA e hashtags."
        )
    elif formato == "story":
        corpo = (
            f"Crie {input.quantidade} roteiros de Story sobre {input.tema}.\n"
            f"Inclua:\n"
            f"1. Roteiro visual (imagem ou vídeo);\n"
            f"2. Texto para criativo;\n"
            f"3. Sugestão de sticker/interação;\n"
            f"4. Legenda com CTA e hashtags."
        )
    else:
        corpo = (
            f"Crie {input.quantidade} conteúdos no formato {input.formato} sobre {input.tema}.\n"
            f"Inclua legenda, CTA, roteiro visual, imagem e trilha sonora sem direitos autorais."
        )

    prompt = introducao + corpo

    resposta = await gerar_resposta(
        prompt,
        input.id_assistant,
        contexto='publicacao',
        tema=input.tema
    )

    return {"publicacao": resposta}

@router.post("/gerar-imagem")
async def gerar_imagem_ia(input: ImagemInput, user=Depends(autorizacao)):
    try:
        url = await gerar_imagem(input.prompt)
        if input.texto:
            imagem_base64 = gerar_imagem_com_texto(url, input.texto)
            return {"imagem": imagem_base64}
        return {"imagem": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))