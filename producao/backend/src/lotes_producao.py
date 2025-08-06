"""Rotas e utilidades para persistência de lotes de produção."""

from fastapi import APIRouter, HTTPException
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Union
import xml.etree.ElementTree as ET

from database import get_db_connection, PLACEHOLDER, schema
from storage import (
    upload_file,
    download_file,
    object_exists,
    PREFIX as OBJECT_PREFIX,
)
from operacoes import parse_dxt_producao
from nesting import _encontrar_dxt


router = APIRouter()

SCHEMA_PREFIX = f"{schema}." if schema else ""
BASE_DIR = Path(__file__).resolve().parent.parent
SAIDA_DIR = BASE_DIR / "saida"


def ensure_lote_local(key: str) -> Path:
    """Garante que o lote identificado por ``key`` esteja extraído localmente."""

    key_no_prefix = key[len(OBJECT_PREFIX) :] if key.startswith(OBJECT_PREFIX) else key
    if not key_no_prefix.startswith("lotes/"):
        raise ValueError("Chave de lote invalida")

    pasta = SAIDA_DIR / Path(key_no_prefix).stem
    if pasta.is_dir():
        return pasta

    status = object_exists(key)
    if status is False:
        raise FileNotFoundError(f"Objeto {key} nao encontrado")
    if status is None:
        raise FileNotFoundError(f"Objeto {key} nao encontrado")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    tmp.close()
    try:
        download_file(key, tmp.name)
        shutil.unpack_archive(tmp.name, SAIDA_DIR)
    finally:
        os.remove(tmp.name)

    return pasta


def salvar_lote_db(ident: Union[str, int], pacotes: list, pasta_arquivos: str | None = None) -> int:
    """Cria ou atualiza um lote de produção e retorna seu ``id``.

    Salva os pacotes em ``pacotes.json`` dentro da pasta do lote, compacta a
    pasta completa e armazena apenas o ``obj_key`` no banco ``lotes``.
    """

    nome = str(ident)
    pacotes_json = json.dumps(pacotes)
    obj_key = f"lotes/Lote_{nome}.zip"

    if pasta_arquivos:
        pasta_tmp = Path(pasta_arquivos)
        pasta_lote = pasta_tmp / f"Lote_{nome}"
        os.makedirs(pasta_lote, exist_ok=True)
        for child in list(pasta_tmp.iterdir()):
            if child == pasta_lote:
                continue
            shutil.move(str(child), pasta_lote / child.name)
    else:
        try:
            pasta_lote = ensure_lote_local(obj_key)
        except Exception:
            pasta_lote = SAIDA_DIR / f"Lote_{nome}"
            os.makedirs(pasta_lote, exist_ok=True)

    (pasta_lote / "pacotes.json").write_text(pacotes_json, encoding="utf-8")

    zip_path = shutil.make_archive(
        str(pasta_lote), "zip", root_dir=pasta_lote.parent, base_dir=pasta_lote.name
    )
    try:
        upload_file(zip_path, obj_key)
    finally:
        os.remove(zip_path)

    with get_db_connection() as conn:
        result = conn.exec_driver_sql(
            f"""
            INSERT INTO {SCHEMA_PREFIX}lotes (obj_key, criado_em)
            VALUES ({PLACEHOLDER}, NOW())
            ON CONFLICT (obj_key)
            DO UPDATE SET criado_em = EXCLUDED.criado_em
            RETURNING id
            """,
            (obj_key,),
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
            f"SELECT id, obj_key, criado_em FROM {SCHEMA_PREFIX}lotes ORDER BY criado_em DESC"
        ).mappings().all()

    resultado = []
    for row in rows:
        obj_key = row.get("obj_key") or ""
        nome = Path(obj_key).stem.replace("Lote_", "") if obj_key else ""
        resultado.append({"id": row["id"], "nome": nome, "obj_key": obj_key})
    return resultado


@router.get("/lotes-producao/{ident}")
async def obter_lote_producao(ident: str):
    """Obtém os dados de um lote pelo ``nome``."""

    nome = ident
    obj_key = f"lotes/Lote_{nome}.zip"

    with get_db_connection() as conn:
        row = conn.exec_driver_sql(
            f"SELECT id FROM {SCHEMA_PREFIX}lotes WHERE obj_key={PLACEHOLDER}",
            (obj_key,),
        ).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Lote não encontrado")

    pacotes: list = []
    try:
        pasta = ensure_lote_local(obj_key)
        pacotes_path = pasta / "pacotes.json"
        if pacotes_path.exists():
            pacotes = json.loads(pacotes_path.read_text(encoding="utf-8"))
        else:
            dxt = _encontrar_dxt(pasta)
            if dxt and dxt.exists():
                root = ET.fromstring(dxt.read_text(encoding="utf-8", errors="ignore"))
                pacotes = parse_dxt_producao(root, dxt)
    except Exception:
        pacotes = []

    return {"id": row["id"], "nome": nome, "pacotes": pacotes}


@router.delete("/lotes-producao/{ident}")
async def excluir_lote_producao(ident: str):
    """Remove um lote pelo ``nome``."""

    obj_key = f"lotes/Lote_{ident}.zip"
    with get_db_connection() as conn:
        conn.exec_driver_sql(
            f"DELETE FROM {SCHEMA_PREFIX}lotes WHERE obj_key={PLACEHOLDER}",
            (obj_key,),
        )
        conn.commit()
    return {"status": "deleted"}

