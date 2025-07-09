from fastapi import APIRouter, Depends, HTTPException
import logging
from pydantic import BaseModel
from services.openai_service import gerar_resposta
from services.embedding_service import buscar_contexto
from security import verificar_autenticacao

# CORRIGIDO: Removido prefix="/chat" daqui. Ele já é adicionado em main.py
router = APIRouter(tags=["Chat"]) 

class ChatInput(BaseModel):
    mensagem: str
    id_assistant: str = None

@router.post("/")
async def conversar(
    input: ChatInput,
    # Inclui "admin" para que usuários administradores também possam utilizar o chat
    usuario=Depends(verificar_autenticacao(["Diretoria", "Marketing", "Comercial", "Logística", "admin"]))
):
    if not input.id_assistant:
        raise HTTPException(status_code=400, detail="ID do assistente é obrigatório.")

    # 🔎 Buscar contexto relevante da base de conhecimento
    contexto = buscar_contexto(input.mensagem)
    print("📚 Contexto carregado:\n", contexto)

    # 🧭 Prompt com tom mais sóbrio, direto e institucional
    prompt_com_contexto = f"""
Você é a Sara, assistente institucional da Radha Ambientes Planejados.

Sua função é fornecer respostas claras, objetivas e confiáveis com base nas informações disponíveis. Evite qualquer linguagem promocional, chamadas para ação, hashtags ou links.

Este atendimento está sendo feito para: {usuario['nome']} ({usuario['cargo']})

Comunique-se de forma sóbria e acolhedora. Ajude tanto clientes quanto colaboradores a compreender os processos, diferenciais e diretrizes da Radha.

Informações disponíveis:
{contexto}

Pergunta: {input.mensagem}
"""
    try:
        resposta = await gerar_resposta(prompt_com_contexto, input.id_assistant)
    except Exception:
        logging.exception("Erro ao gerar resposta")
        raise HTTPException(status_code=500, detail="Falha ao processar a mensagem")
    return {"resposta": resposta}
