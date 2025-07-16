import json
import tempfile
import os
from sqlalchemy import text
from database import get_db_connection
# `services` is loaded as a namespace package when running the backend
# directly from the `backend` directory. Relative imports that traverse
# above the top-level package (e.g. ``..storage``) fail in this
# configuration, so we use an absolute import instead.
from storage import upload_file


def obter_info(rd_id: str) -> dict | None:
    conn = get_db_connection()
    row = conn.execute(
        text("SELECT * FROM leads_info WHERE rd_id=:r"),
        {"r": rd_id},
    ).fetchone()
    conn.close()
    if not row:
        return None
    item = dict(row._mapping)
    if item.get("arquivos_json"):
        try:
            item["arquivos"] = json.loads(item["arquivos_json"])
        except Exception:
            item["arquivos"] = []
    else:
        item["arquivos"] = []
    return item


def salvar_info(rd_id: str, dados: dict, arquivos: list[tuple[str, bytes]] | None = None) -> dict:
    arquivos_keys: list[str] = []
    if arquivos:
        for nome, conteudo in arquivos:
            tmp = tempfile.NamedTemporaryFile(delete=False)
            tmp.write(conteudo)
            tmp.close()
            key = f"leads/{rd_id}/{nome}"
            upload_file(tmp.name, key)
            arquivos_keys.append(key)
            os.remove(tmp.name)

    conn = get_db_connection()
    row = conn.execute(text("SELECT * FROM leads_info WHERE rd_id=:r"), {"r": rd_id}).fetchone()
    if row:
        existentes = json.loads(row._mapping.get("arquivos_json") or "[]")
        arquivos_keys = existentes + arquivos_keys
        conn.execute(
            text(
                "UPDATE leads_info SET estagio=:e, descricao=:d, arquivos_json=:a, vendedor_id=:v, cliente_id=:c, atendimento_id=:at WHERE rd_id=:r"
            ),
            {
                "e": dados.get("estagio"),
                "d": dados.get("descricao"),
                "a": json.dumps(arquivos_keys),
                "v": dados.get("vendedor_id"),
                "c": dados.get("cliente_id"),
                "at": dados.get("atendimento_id"),
                "r": rd_id,
            },
        )
    else:
        conn.execute(
            text(
                "INSERT INTO leads_info (rd_id, estagio, descricao, arquivos_json, vendedor_id, cliente_id, atendimento_id) "
                "VALUES (:r, :e, :d, :a, :v, :c, :at)"
            ),
            {
                "r": rd_id,
                "e": dados.get("estagio"),
                "d": dados.get("descricao"),
                "a": json.dumps(arquivos_keys),
                "v": dados.get("vendedor_id"),
                "c": dados.get("cliente_id"),
                "at": dados.get("atendimento_id"),
            },
        )
    conn.commit()
    conn.close()
    return obter_info(rd_id)
