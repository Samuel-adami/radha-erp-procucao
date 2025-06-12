from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import chat, campanha, publicacao, publicos, auth

app = FastAPI(
    title="Radha Executor",
    version="1.0"
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sara.radhadigital.com.br"],  # Domínio em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusão das rotas com prefixos apropriados
app.include_router(chat.router)
app.include_router(campanha.router)
app.include_router(publicacao.router)
app.include_router(publicos.router)
app.include_router(auth.router, prefix="/auth")  # ✅ Aqui está a correção

@app.get("/")
async def root():
    return {"message": "Radha Executor API funcionando!"}
