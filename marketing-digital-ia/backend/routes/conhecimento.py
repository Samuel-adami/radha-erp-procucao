# routes/conhecimento.py
from fastapi import APIRouter, Request, Depends, UploadFile, File, Form
from services.embedding_service import buscar_contexto
from services.search_service import indexar_documento, buscar_documentos
from openai import OpenAI
from security import verificar_autenticacao

router = APIRouter(tags=["Conhecimento"])


@router.post("/conhecimento/importar")
async def importar_conhecimento(
    titulo: str = Form(...),
    arquivo: UploadFile = File(...),
    usuario=Depends(
        verificar_autenticacao(permissoes=["marketing-ia/gerir-conhecimento"])
    ),
):
    conteudo = (await arquivo.read()).decode("utf-8", errors="ignore")
    indexar_documento(titulo, conteudo)
    return {"status": "ok"}


@router.get("/conhecimento/buscar")
async def buscar_conhecimento(
    q: str,
    usuario=Depends(verificar_autenticacao(permissoes=["marketing-ia/chat"])),
):
    resultados = buscar_documentos(q)
    return {"resultados": resultados}

@router.post("/perguntar-sara")
async def perguntar_sara(
    request: Request,
    usuario=Depends(
        verificar_autenticacao(permissoes=["marketing-ia/chat"])
    ),
):
    dados = await request.json()
    pergunta = dados.get("pergunta")
    contexto = buscar_contexto(pergunta)

    resposta = OpenAI().chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Você é a Sara, assistente especialista da Radha."},
            {"role": "user", "content": f"Com base neste contexto:\n{contexto}\n\nResponda: {pergunta}"}
        ]
    )

    return {"resposta": resposta.choices[0].message.content.strip()}
