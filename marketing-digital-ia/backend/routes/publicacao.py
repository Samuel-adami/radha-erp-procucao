from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from services.openai_service import gerar_resposta, gerar_imagem
from security import verificar_autenticacao
import os

router = APIRouter(prefix="/nova-publicacao", tags=["Publicacoes"])

# ✅ Permissão controlada pelo cadastro de usuários
autorizacao = verificar_autenticacao(permissoes=["marketing-ia/nova-publicacao"])

class PublicacaoInput(BaseModel):
    tema: str
    objetivo: str
    formato: str
    quantidade: int
    id_assistant: str = None

class ImagemInput(BaseModel):
    prompt: str

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
        f"Quantidade de publicações: {input.quantidade}{observacao}\n\n"
    )

    if formato == "post único":
        corpo = (
            f"Crie {input.quantidade} publicações no formato post único sobre {input.tema}. Para cada uma:\n"
            f"1. Gere uma legenda criativa com CTA e hashtags;\n"
            f"2. Sugira uma imagem (ex: cozinha planejada realista);\n"
            f"3. Sugira uma música sem direitos autorais e forneça o link direto da música no site do Pixabay."
        )
    elif formato == "post carrossel":
        corpo = (
            f"Crie {input.quantidade} posts carrossel sobre {input.tema}. Cada post deve conter exatamente 5 slides.\n"
            f"Para cada slide, gere:\n"
            f"- Um texto envolvente que estimule retenção e conversão, com métodos modernos de copywriting (ex: perguntas, quebra de padrão, micro-narrações);\n"
            f"- Um prompt detalhado para geração de imagem realista no estilo da Radha (ambientes planejados);\n"
            f"Ao final de cada carrossel:\n"
            f"- Gere uma legenda principal com CTA forte e hashtags bem selecionadas;\n"
            f"- Sugira uma trilha sonora sem direitos autorais e forneça o link direto da música no Pixabay."
        )
    elif formato == "reels":
        corpo = (
            f"Crie {input.quantidade} roteiros de Reels sobre {input.tema}.\n"
            f"Inclua:\n"
            f"1. Roteiro audiovisual detalhado;\n"
            f"2. Texto para sobreposição no vídeo;\n"
            f"3. Legenda completa com CTA e hashtags;\n"
            f"4. Sugestão de trilha sonora do Pixabay com link direto."
        )
    elif formato == "story":
        corpo = (
            f"Crie {input.quantidade} sequências de Story sobre {input.tema}.\n"
            f"Inclua:\n"
            f"1. Roteiro visual (imagem ou vídeo curto);\n"
            f"2. Texto para criativo;\n"
            f"3. Sugestão de sticker ou interação;\n"
            f"4. Legenda com CTA e hashtags;\n"
            f"5. Sugestão de trilha sonora do Pixabay com link direto."
        )
    else:
        corpo = (
            f"Crie {input.quantidade} conteúdos no formato {input.formato} sobre {input.tema}.\n"
            f"Inclua legenda com CTA, imagem realista, texto de sobreposição e música do Pixabay com link."
        )

    prompt = introducao + corpo

    resposta = await gerar_resposta(
        prompt,
        input.id_assistant
    )

    return {"publicacao": resposta}

@router.post("/gerar-imagem")
async def gerar_imagem_ia(input: ImagemInput, user=Depends(autorizacao)):
    try:
        url = await gerar_imagem(input.prompt)
        return {"imagem": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
