import json
import os
from typing import Optional, List
from jose import jwt
from datetime import datetime, timedelta
from database import get_db_connection

SECRET_KEY = os.getenv("SECRET_KEY", "radha-super-secreto")
ALGORITHM = "HS256"
EXPIRATION_MINUTES = 60


def _row_to_user(row) -> dict:
    user = dict(row)
    user["permissoes"] = json.loads(user.get("permissoes", "[]"))
    return user


def autenticar(username: str, password: str) -> Optional[dict]:
    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password),
    ).fetchone()
    conn.close()
    return _row_to_user(row) if row else None


def criar_token(usuario: dict) -> dict:
    token = jwt.encode(
        {
            "sub": usuario["username"],
            "nome": usuario.get("nome"),
            "cargo": usuario.get("cargo"),
            "permissoes": usuario.get("permissoes", []),
            "exp": datetime.utcnow() + timedelta(minutes=EXPIRATION_MINUTES),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    return {"access_token": token, "usuario": {"username": usuario["username"], "permissoes": usuario.get("permissoes", [])}}


def decodificar_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None


def listar_usuarios() -> List[dict]:
    conn = get_db_connection()
    rows = conn.execute("SELECT id, username, email, nome, cargo, permissoes FROM users ORDER BY id").fetchall()
    conn.close()
    return [_row_to_user(r) for r in rows]


def criar_usuario(data: dict) -> int:
    conn = get_db_connection()
    cur = conn.execute(
        "INSERT INTO users (username, password, email, nome, cargo, permissoes) VALUES (?, ?, ?, ?, ?, ?)",
        (
            data.get("username"),
            data.get("password"),
            data.get("email"),
            data.get("nome"),
            data.get("cargo"),
            json.dumps(data.get("permissoes", [])),
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def atualizar_usuario(user_id: int, data: dict) -> bool:
    conn = get_db_connection()
    cur = conn.execute(
        "UPDATE users SET username=?, password=?, email=?, nome=?, cargo=?, permissoes=? WHERE id=?",
        (
            data.get("username"),
            data.get("password"),
            data.get("email"),
            data.get("nome"),
            data.get("cargo"),
            json.dumps(data.get("permissoes", [])),
            user_id,
        ),
    )
    conn.commit()
    updated = cur.rowcount
    conn.close()
    return updated > 0


def excluir_usuario(user_id: int) -> bool:
    conn = get_db_connection()
    cur = conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    deleted = cur.rowcount
    conn.close()
    return deleted > 0
