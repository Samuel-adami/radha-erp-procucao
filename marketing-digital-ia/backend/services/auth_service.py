import json
import os
from typing import Optional, List
from jose import jwt
from datetime import datetime, timedelta
import bcrypt as _bcrypt
from types import SimpleNamespace
if not hasattr(_bcrypt, "__about__"):
    _bcrypt.__about__ = SimpleNamespace(__version__=_bcrypt.__version__)
from passlib.hash import bcrypt
from database import get_db_connection

SECRET_KEY = os.getenv("SECRET_KEY", "radha-super-secreto")
ALGORITHM = "HS256"
EXPIRATION_MINUTES = 60


def _row_to_user(row) -> dict:
    user = dict(row)
    user["permissoes"] = json.loads(user.get("permissoes", "[]"))
    return user


def autenticar(username: str, password: str) -> Optional[dict]:
    """Autentica um usuário pelo nome e senha.

    Este método também migra senhas antigas não criptografadas para o formato
    bcrypt. Ao detectar que o campo ``password`` não está no formato esperado,
    ele compara a senha em texto simples e, em caso de sucesso, salva a versão
    criptografada no banco de dados.
    """

    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE username=?",
        (username,),
    ).fetchone()

    if not row:
        conn.close()
        return None

    stored_pwd = row["password"]

    # Se a senha armazenada não parece estar no formato bcrypt, tenta verificar
    # como texto simples e, em caso positivo, atualiza para o hash seguro.
    try:
        valid = bcrypt.verify(password, stored_pwd)
    except ValueError:
        valid = password == stored_pwd
        if valid:
            conn.execute(
                "UPDATE users SET password=? WHERE id=?",
                (bcrypt.hash(password), row["id"]),
            )
            conn.commit()

    conn.close()

    if valid:
        return _row_to_user(row)

    return None


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
    return {
        "access_token": token,
        "usuario": {
            "username": usuario["username"],
            "nome": usuario.get("nome"),
            "cargo": usuario.get("cargo"),
            "permissoes": usuario.get("permissoes", []),
        },
    }


def decodificar_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None


def listar_usuarios() -> List[dict]:
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT id, username, password, email, nome, cargo, permissoes FROM users ORDER BY id"
    ).fetchall()
    conn.close()
    return [_row_to_user(r) for r in rows]


def criar_usuario(data: dict) -> int:
    conn = get_db_connection()
    cur = conn.execute(
        "INSERT INTO users (username, password, email, nome, cargo, permissoes) VALUES (?, ?, ?, ?, ?, ?)",
        (
            data.get("username"),
            bcrypt.hash(data.get("password")),
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
            bcrypt.hash(data.get("password")) if data.get("password") else None,
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
