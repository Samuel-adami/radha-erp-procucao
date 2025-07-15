from fastapi import FastAPI
from fastapi.responses import JSONResponse
from routes import usuarios
from routes import chat, campanha, publicacao, publicos, conhecimento
import os
import uvicorn
from database import init_db
from services.auth_service import ensure_default_admin

import sys
import numpy

print(f"Numpy version: {numpy.__version__}")
print(f"Python path: {sys.executable}")


# CORRIGIDO: Adicionado redirect_slashes=False
app = FastAPI(redirect_slashes=False)

# Initialize database tables on startup
init_db()
ensure_default_admin()

# Removido: Configuração de CORS, pois será gerenciada pelo Gateway API

# Incluir routers
app.include_router(chat.router, prefix="/chat")
app.include_router(campanha.router, prefix="/nova-campanha")
app.include_router(publicacao.router, prefix="/nova-publicacao")
app.include_router(publicos.router, prefix="/publicos")
app.include_router(conhecimento.router, prefix="/conhecimento")
# A rota de usuarios ja define um prefixo, portanto nao precisamos
# adicionar outro aqui. Mantendo apenas o include simples evita que a
# rota final fique "/usuarios/usuarios" e resolvemos erros 404 ao
# acessar via gateway.
app.include_router(usuarios.router)


@app.get("/")
async def read_root():
    return {"message": "Bem-vindo ao Backend de Marketing Digital IA (Radha)!"}

# Você pode manter este bloco ou removê-lo se for usar um script de execução externo (como uvicorn)
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8015) # Porta do Marketing Digital IA atualizada para 8015
