from fastapi import FastAPI
from fastapi.responses import JSONResponse
# GARANTA que esta linha NÃO esteja comentada e esteja no início do arquivo:
from routes import auth # Importar o módulo de autenticação
from routes import chat, campanha, publicacao, publicos, conhecimento
import os
import uvicorn

app = FastAPI()

# Removido: Configuração de CORS, pois será gerenciada pelo Gateway API

# Incluir routers
app.include_router(chat.router, prefix="/chat")
app.include_router(campanha.router, prefix="/nova-campanha")
app.include_router(publicacao.router, prefix="/nova-publicacao")
app.include_router(publicos.router, prefix="/publicos")
app.include_router(conhecimento.router, prefix="/conhecimento")
# Esta linha deve estar presente e não comentada
app.include_router(auth.router, prefix="/auth")


@app.get("/")
async def read_root():
    return {"message": "Bem-vindo ao Backend de Marketing Digital IA (Radha)!"}

# Você pode manter este bloco ou removê-lo se for usar um script de execução externo (como uvicorn)
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8015) # Porta do Marketing Digital IA atualizada para 8015