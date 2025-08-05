"""Rotas e utilidades para persistência de lotes de produção."""

from fastapi import APIRouter, HTTPException
import json

from database import get_db_connection, PLACEHOLDER, schema


router = APIRouter()

SCHEMA_PREFIX = f"{schema}." if schema else ""


def salvar_lote_db(nome: str, pacotes: list) -> None:
    """Cria ou atualiza um lote de produção no banco."""

    pacotes_json = json.dumps(pacotes)
    with get_db_connection() as conn:
        conn.exec_driver_sql(
            f"""
            INSERT INTO {SCHEMA_PREFIX}lotes_producao (nome, pacotes_json)
            VALUES ({PLACEHOLDER}, {PLACEHOLDER})
            ON CONFLICT (nome)
            DO UPDATE SET pacotes_json = {PLACEHOLDER}, atualizado_em = NOW()
            """,
            (nome, pacotes_json, pacotes_json),
        )


@router.post("/lotes-producao")
async def salvar_lote_producao(lote: dict):
    """Cria ou atualiza um lote com seus pacotes."""

    nome = lote.get("nome")
    pacotes = lote.get("pacotes", [])
    if not nome:
        raise HTTPException(status_code=400, detail="Nome do lote é obrigatório")

    salvar_lote_db(nome, pacotes)
    return {"status": "ok"}


@router.get("/lotes-producao")
async def listar_lotes_producao():
    """Lista todos os lotes cadastrados."""

    with get_db_connection() as conn:
        rows = conn.exec_driver_sql(
            f"SELECT nome, atualizado_em FROM {SCHEMA_PREFIX}lotes_producao ORDER BY atualizado_em DESC"
        ).mappings().all()
    return [dict(row) for row in rows]


@router.get("/lotes-producao/{nome}")
async def obter_lote_producao(nome: str):
    """Obtém os dados de um lote pelo nome."""

    with get_db_connection() as conn:
        row = conn.exec_driver_sql(
            f"SELECT pacotes_json FROM {SCHEMA_PREFIX}lotes_producao WHERE nome={PLACEHOLDER}",
            (nome,),
        ).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Lote não encontrado")

    pacotes = json.loads(row["pacotes_json"] or "[]")
    return {"nome": nome, "pacotes": pacotes}


@router.delete("/lotes-producao/{nome}")
async def excluir_lote_producao(nome: str):
    """Remove um lote pelo nome."""

    with get_db_connection() as conn:
        conn.exec_driver_sql(
            f"DELETE FROM {SCHEMA_PREFIX}lotes_producao WHERE nome={PLACEHOLDER}",
            (nome,),
        )
    return {"status": "deleted"}

