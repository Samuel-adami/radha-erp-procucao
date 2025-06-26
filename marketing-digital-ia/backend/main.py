from fastapi import FastAPI
from fastapi.responses import JSONResponse
from routes import auth, usuarios
from routes import chat, campanha, publicacao, publicos, conhecimento
import os
import uvicorn

# CORRIGIDO: Adicionado redirect_slashes=False
app = FastAPI(redirect_slashes=False)

# Removido: Configuração de CORS, pois será gerenciada pelo Gateway API

# Incluir routers
app.include_router(chat.router, prefix="/chat")
app.include_router(campanha.router, prefix="/nova-campanha")
app.include_router(publicacao.router, prefix="/nova-publicacao")
app.include_router(publicos.router, prefix="/publicos")
app.include_router(conhecimento.router, prefix="/conhecimento")
app.include_router(auth.router, prefix="/auth")
app.include_router(usuarios.router, prefix="/usuarios")


@app.get("/")
async def read_root():
    return {"message": "Bem-vindo ao Backend de Marketing Digital IA (Radha)!"}

# Você pode manter este bloco ou removê-lo se for usar um script de execução externo (como uvicorn)
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8015) # Porta do Marketing Digital IA atualizada para 8015