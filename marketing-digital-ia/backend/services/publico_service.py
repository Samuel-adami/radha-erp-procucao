from typing import List
from sqlalchemy import text
from database import get_db_connection


def criar_publico(data: dict) -> int:
    conn = get_db_connection()
    cur = conn.execute(
        text(
            """INSERT INTO publicos_alvo
                (nome, descricao, idade_min, idade_max, genero, interesses, localizacao)
                VALUES (:nome, :descricao, :idade_min, :idade_max, :genero, :interesses, :localizacao)
            """
        ),
        {
            "nome": data.get("nome"),
            "descricao": data.get("descricao"),
            "idade_min": data.get("idade_min"),
            "idade_max": data.get("idade_max"),
            "genero": data.get("genero"),
            "interesses": ",".join(data.get("interesses", [])) if data.get("interesses") else None,
            "localizacao": data.get("localizacao"),
        },
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def listar_publicos() -> List[dict]:
    conn = get_db_connection()
    rows = conn.execute(
        text(
            "SELECT id, nome, descricao, idade_min, idade_max, genero, interesses, localizacao FROM publicos_alvo ORDER BY id"
        )
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        item = dict(r._mapping)
        if item.get("interesses"):
            item["interesses"] = item["interesses"].split(",")
        else:
            item["interesses"] = []
        result.append(item)
    return result
