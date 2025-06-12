import json
import os
from typing import Optional
from jose import jwt
from datetime import datetime, timedelta

# ⚙️ Configuração do JWT
SECRET_KEY = "radha-super-secreto"  # Substitua por algo seguro em produção
ALGORITHM = "HS256"
EXPIRATION_MINUTES = 60

# 🔍 Carregar usuários do JSON
def carregar_usuarios():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    users_path = os.path.join(base_dir, "..", "users.json")
    users_path = os.path.normpath(users_path)
    with open(users_path, "r", encoding="utf-8") as f:
        return json.load(f)

# ✅ Validar login
def autenticar(username: str, password: str) -> Optional[dict]:
    usuarios = carregar_usuarios()
    for user in usuarios:
        if user["username"] == username and user["password"] == password:
            return user
    return None

# 🧾 Gerar token e retorno completo
def criar_token(usuario: dict) -> dict:
    token = jwt.encode({
        "sub": usuario["username"],
        "nome": usuario["nome"],
        "cargo": usuario["cargo"],
        "permissoes": usuario.get("permissoes", []),
        "exp": datetime.utcnow() + timedelta(minutes=EXPIRATION_MINUTES)
    }, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "access_token": token,
        "usuario": {
            "username": usuario["username"],
            "permissoes": usuario.get("permissoes", [])
        }
    }

# 🔍 Decodificar token
def decodificar_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None
