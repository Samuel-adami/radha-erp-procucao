"""Rotas e utilidades para persistência de lotes de produção."""

from fastapi import APIRouter, HTTPException
import json
from typing import Union

from database import get_db_connection, PLACEHOLDER, schema


router = APIRouter()

SCHEMA_PREFIX = f"{schema}." if schema else ""


def salvar_lote_db(ident: Union[str, int], pacotes: list) -> int:
    """Cria ou atualiza um lote de produção e retorna seu ``id``.

    ``ident`` pode ser o ``id`` do lote ou o ``nome``. Quando um ``id`` é
    informado, o lote correspondente é atualizado; caso contrário, o lote é
    criado/atualizado pelo nome.
    """

    pacotes_json = json.dumps(pacotes)
    with get_db_connection() as conn:
        if isinstance(ident, int) or str(ident).isdigit():
            result = conn.exec_driver_sql(
                f"""
                UPDATE {SCHEMA_PREFIX}lotes_producao
                SET pacotes_json={PLACEHOLDER}, atualizado_em=NOW()
                WHERE id={PLACEHOLDER}
                RETURNING id
                """,
                (pacotes_json, int(ident)),
            )
            lote_id = result.scalar_one_or_none()
            if lote_id is None:
                raise ValueError("Lote não encontrado")
        else:
            result = conn.exec_driver_sql(
                f"""
                INSERT INTO {SCHEMA_PREFIX}lotes_producao (nome, pacotes_json)
                VALUES ({PLACEHOLDER}, {PLACEHOLDER})
                ON CONFLICT (nome)
                DO UPDATE SET pacotes_json = EXCLUDED.pacotes_json,
                              atualizado_em = NOW()
                RETURNING id
                """,
                (ident, pacotes_json),
            )
            lote_id = result.scalar_one()
        conn.commit()
    return lote_id

@router.post("/lotes-producao")
async def salvar_lote_producao(lote: dict):
    """Cria ou atualiza um lote com seus pacotes."""

    ident = lote.get("id") or lote.get("nome")
    pacotes = lote.get("pacotes", [])
    if ident is None:
        raise HTTPException(status_code=400, detail="ID ou nome do lote é obrigatório")


    try:
        lote_id = salvar_lote_db(ident, pacotes)
    except ValueError:
        raise HTTPException(status_code=404, detail="Lote não encontrado")


    return {"id": lote_id}


@router.get("/lotes-producao")
async def listar_lotes_producao():
    """Lista todos os lotes cadastrados."""

    with get_db_connection() as conn:
        rows = conn.exec_driver_sql(
            f"SELECT id, nome, atualizado_em FROM {SCHEMA_PREFIX}lotes_producao ORDER BY atualizado_em DESC"
        ).mappings().all()
    return [dict(row) for row in rows]


@router.get("/lotes-producao/{ident}")
async def obter_lote_producao(ident: str):
    """Obtém os dados de um lote pelo ``id`` ou pelo ``nome``."""

    campo = "id" if ident.isdigit() else "nome"
    valor = int(ident) if ident.isdigit() else ident

    with get_db_connection() as conn:
        row = conn.exec_driver_sql(
            f"SELECT id, nome, pacotes_json FROM {SCHEMA_PREFIX}lotes_producao WHERE {campo}={PLACEHOLDER}",
            (valor,),
        ).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Lote não encontrado")

    pacotes = json.loads(row["pacotes_json"] or "[]")
    return {"id": row["id"], "nome": row["nome"], "pacotes": pacotes}


@router.delete("/lotes-producao/{ident}")
async def excluir_lote_producao(ident: str):
    """Remove um lote pelo ``id`` ou ``nome``."""

    campo = "id" if ident.isdigit() else "nome"
    valor = int(ident) if ident.isdigit() else ident

    with get_db_connection() as conn:
        conn.exec_driver_sql(
            f"DELETE FROM {SCHEMA_PREFIX}lotes_producao WHERE {campo}={PLACEHOLDER}",
            (valor,),
        )
        conn.commit()
    return {"status": "deleted"}

