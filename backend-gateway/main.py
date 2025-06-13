from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
import httpx

app = FastAPI(title="Radha ERP Gateway API", version="1.0")

# Configuração de CORS - Ajuste allow_origins conforme seus domínios em produção
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3005", "https://seu-dominio-erp.com.br", "http://212.85.13.74:3005"], # Porta do frontend atualizada para 3005
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cliente HTTP para fazer requisições para os módulos de backend
# Ajuste as URLs conforme onde seus módulos de backend rodarão
MARKETING_IA_BACKEND_URL = "http://localhost:8015"  # Porta do Marketing Digital IA atualizada para 8015
PRODUCAO_BACKEND_URL = "http://localhost:8020"      # Porta da Produção atualizada para 8020

@app.get("/")
async def read_root():
    return {"message": "Radha ERP Gateway API is running!"}

# Rota para o módulo de Marketing Digital IA (mantém as rotas existentes)
@app.api_route("/marketing-ia/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def call_marketing_ia_backend(path: str, request: Request):
    async with httpx.AsyncClient() as client:
        url = f"{MARKETING_IA_BACKEND_URL}/{path}"
        try:
            # Reenvia headers, query params e body
            headers = {k: v for k, v in request.headers.items() if k.lower() not in ["host", "authorization"]} # Exclui headers que podem causar problemas
            if "authorization" in request.headers:
                headers["Authorization"] = request.headers["Authorization"] # Passa o token de autenticação

            response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                params=request.query_params,
                content=await request.body()
            )
            response.raise_for_status()
            return JSONResponse(response.json(), status_code=response.status_code)
        except httpx.HTTPStatusError as e:
            return JSONResponse({"detail": e.response.text}, status_code=e.response.status_code)
        except httpx.RequestError as e:
            return JSONResponse({"detail": f"Erro de conexão com o backend de Marketing Digital IA: {e}"}, status_code=503)

# Rota para o módulo de Produção (mantém as rotas existentes)
@app.api_route("/producao/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def call_producao_backend(path: str, request: Request):
    async with httpx.AsyncClient() as client:
        url = f"{PRODUCAO_BACKEND_URL}/{path}"
        try:
            headers = {k: v for k, v in request.headers.items() if k.lower() not in ["host"]}
            response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                params=request.query_params,
                content=await request.body()
            )
            response.raise_for_status()
            return JSONResponse(response.json(), status_code=response.status_code)
        except httpx.HTTPStatusError as e:
            return JSONResponse({"detail": e.response.text}, status_code=e.response.status_code)
        except httpx.RequestError as e:
            return JSONResponse({"detail": f"Erro de conexão com o backend de Produção: {e}"}, status_code=503)

# Rotas de Autenticação (do assistente-radha)
@app.post("/auth/login")
async def login(request: Request):
    async with httpx.AsyncClient() as client:
        url = f"{MARKETING_IA_BACKEND_URL}/auth/login"
        try:
            response = await client.post(url, content=await request.body())
            response.raise_for_status()
            return JSONResponse(response.json(), status_code=response.status_code)
        except httpx.HTTPStatusError as e:
            return JSONResponse({"detail": e.response.text}, status_code=e.response.status_code)
        except httpx.RequestError as e:
            return JSONResponse({"detail": f"Erro de conexão com o backend de autenticação: {e}"}, status_code=503)

@app.get("/auth/validate")
async def validate_token(request: Request):
    async with httpx.AsyncClient() as client:
        url = f"{MARKETING_IA_BACKEND_URL}/auth/validate"
        try:
            headers = {k: v for k, v in request.headers.items() if k.lower() not in ["host"]}
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return JSONResponse(response.json(), status_code=response.status_code)
        except httpx.HTTPStatusError as e:
            return JSONResponse({"detail": e.response.text}, status_code=e.response.status_code)
        except httpx.RequestError as e:
            return JSONResponse({"detail": f"Erro de conexão com o backend de autenticação: {e}"}, status_code=503)