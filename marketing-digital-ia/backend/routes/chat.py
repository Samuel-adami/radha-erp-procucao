from fastapi import APIRouter, Depends, HTTPException
import logging
import os
from pydantic import BaseModel
from services.openai_service import gerar_resposta
from security import verificar_autenticacao

router = APIRouter(tags=["Chat"])
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

class ChatInput(BaseModel):
    mensagem: str
    id_assistant: str = None

@router.post("/")
async def conversar(
    input: ChatInput,
    # Inclui "admin" para que usuários administradores também possam utilizar o chat

    usuario=Depends(verificar_autenticacao(["Diretoria", "Marketing", "Diretor", "Comercial", "Logística", "admin"]))


):
    if not input.id_assistant:
        raise HTTPException(status_code=400, detail="ID do assistente é obrigatório.")


    # 🧭 Prompt com tom mais sóbrio, direto e institucional
    prompt_com_contexto = f"""
Você é a Sara, assistente institucional da Radha Ambientes Planejados.

Sua função é fornecer respostas claras, objetivas e confiáveis com base nas informações disponíveis. Evite qualquer linguagem promocional, chamadas para ação, hashtags ou links.

Este atendimento está sendo feito para: {usuario['nome']} ({usuario['cargo']})

Comunique-se de forma sóbria e acolhedora. Ajude tanto clientes quanto colaboradores a compreender os processos, diferenciais e diretrizes da Radha.

"""

    try:
        resposta = await gerar_resposta(input.mensagem, input.id_assistant)
    except Exception as e:
        logging.exception("Erro ao gerar resposta: %s", e)
        resposta = "Desculpe, ocorreu um erro ao processar a mensagem."

        if DEBUG:
            resposta += f" Detalhes: {e}"


    return {"resposta": resposta}
