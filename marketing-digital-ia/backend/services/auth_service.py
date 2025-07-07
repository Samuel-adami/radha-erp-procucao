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
from sqlalchemy import text
from database import get_db_connection, DEFAULT_ADMIN_PERMISSIONS

RADHA_ADMIN_USER = os.getenv("RADHA_ADMIN_USER")
RADHA_ADMIN_PASS = os.getenv("RADHA_ADMIN_PASS")

SECRET_KEY = os.getenv("SECRET_KEY", "radha-super-secreto")
ALGORITHM = "HS256"
EXPIRATION_MINUTES = 60


def _row_to_user(row) -> dict:
    user = dict(row._mapping)
    user["permissoes"] = json.loads(user.get("permissoes", "[]"))
    return user


def ensure_default_admin() -> None:
    """Create the default administrator account if it doesn't exist."""
    if not RADHA_ADMIN_USER or not RADHA_ADMIN_PASS:
        return

    conn = get_db_connection()
    exists = conn.execute(
        text("SELECT id FROM users WHERE username=:u"),
        {"u": RADHA_ADMIN_USER},
    ).fetchone()

    if not exists:
        conn.execute(
            text(
                "INSERT INTO users (username, password, nome, cargo, permissoes) "
                "VALUES (:username, :password, 'Administrador', 'admin', :permissoes)"
            ),
            {
                "username": RADHA_ADMIN_USER,
                "password": bcrypt.hash(RADHA_ADMIN_PASS),
                "permissoes": json.dumps(DEFAULT_ADMIN_PERMISSIONS),
            },
        )
        conn.commit()
    conn.close()


def autenticar(username: str, password: str) -> Optional[dict]:
    """Autentica um usuário pelo nome e senha.

    Este método também migra senhas antigas não criptografadas para o formato
    bcrypt. Ao detectar que o campo ``password`` não está no formato esperado,
    ele compara a senha em texto simples e, em caso de sucesso, salva a versão
    criptografada no banco de dados.
    """

    conn = get_db_connection()
    row = conn.execute(
        text("SELECT * FROM users WHERE username=:username"),
        {"username": username},
    ).fetchone()

    if not row:
        conn.close()
        return None

    stored_pwd = row._mapping["password"]

    # Se a senha armazenada não parece estar no formato bcrypt, tenta verificar
    # como texto simples e, em caso positivo, atualiza para o hash seguro.
    try:
        valid = bcrypt.verify(password, stored_pwd)
    except ValueError:
        valid = password == stored_pwd
        if valid:
            conn.execute(
                text("UPDATE users SET password=:pwd WHERE id=:id"),
                {"pwd": bcrypt.hash(password), "id": row._mapping["id"]},
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
        text(
            "SELECT id, username, password, email, nome, cargo, permissoes "
            "FROM users ORDER BY id"
        )
    ).fetchall()
    conn.close()
    return [_row_to_user(r) for r in rows]


def criar_usuario(data: dict) -> int:
    # If cargo is 'admin' and no permissions were provided, apply the default
    permissoes = data.get("permissoes")
    if data.get("cargo") == "admin" and not permissoes:
        permissoes = DEFAULT_ADMIN_PERMISSIONS

    conn = get_db_connection()
    cur = conn.execute(
        text(
            "INSERT INTO users (username, password, email, nome, cargo, permissoes) "
            "VALUES (:username, :password, :email, :nome, :cargo, :permissoes)"
        ),
        {
            "username": data.get("username"),
            "password": bcrypt.hash(data.get("password")),
            "email": data.get("email"),
            "nome": data.get("nome"),
            "cargo": data.get("cargo"),
            "permissoes": json.dumps(permissoes or []),
        },
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def atualizar_usuario(user_id: int, data: dict) -> bool:
    # Apply default permissions when elevating a user to admin with none set
    permissoes = data.get("permissoes")
    if data.get("cargo") == "admin" and not permissoes:
        permissoes = DEFAULT_ADMIN_PERMISSIONS

    conn = get_db_connection()
    cur = conn.execute(
        text(
            "UPDATE users SET username=:username, password=:password, email=:email, "
            "nome=:nome, cargo=:cargo, permissoes=:permissoes WHERE id=:id"
        ),
        {
            "username": data.get("username"),
            "password": bcrypt.hash(data.get("password")) if data.get("password") else None,
            "email": data.get("email"),
            "nome": data.get("nome"),
            "cargo": data.get("cargo"),
            "permissoes": json.dumps(permissoes or []),
            "id": user_id,
        },
    )
    conn.commit()
    updated = cur.rowcount
    conn.close()
    return updated > 0


def excluir_usuario(user_id: int) -> bool:
    conn = get_db_connection()
    cur = conn.execute(
        text("DELETE FROM users WHERE id=:id"),
        {"id": user_id},
    )
    conn.commit()
    deleted = cur.rowcount
    conn.close()
    return deleted > 0
