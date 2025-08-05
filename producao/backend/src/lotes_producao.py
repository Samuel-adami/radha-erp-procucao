from fastapi import APIRouter, HTTPException
from sqlalchemy import func
import json

from .database import database, lotes_producao

router = APIRouter()

@router.post("/lotes-producao")
async def salvar_lote_producao(lote: dict):
    nome = lote.get("nome")
    pacotes = lote.get("pacotes", [])
    if not nome:
        raise HTTPException(status_code=400, detail="Nome do lote é obrigatório")
    pacotes_json = json.dumps(pacotes)
    query = (
        lotes_producao.insert()
        .values(nome=nome, pacotes_json=pacotes_json)
        .on_conflict_do_update(
            index_elements=[lotes_producao.c.nome],
            set_={"pacotes_json": pacotes_json, "atualizado_em": func.now()},
        )
    )
    await database.execute(query)
    return {"status": "ok"}


@router.get("/lotes-producao")
async def listar_lotes_producao():
    query = lotes_producao.select()
    rows = await database.fetch_all(query)
    return [
        {"nome": row["nome"], "atualizado_em": row["atualizado_em"]}
        for row in rows
    ]


@router.get("/lotes-producao/{nome}")
async def obter_lote_producao(nome: str):
    query = lotes_producao.select().where(lotes_producao.c.nome == nome)
    row = await database.fetch_one(query)
    if not row:
        raise HTTPException(status_code=404, detail="Lote não encontrado")
    return json.loads(row["pacotes_json"] or "[]")


@router.delete("/lotes-producao/{nome}")
async def excluir_lote_producao(nome: str):
    query = lotes_producao.delete().where(lotes_producao.c.nome == nome)
    await database.execute(query)
    return {"status": "deleted"}
