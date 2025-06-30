from fastapi import FastAPI, Request
from fastapi import UploadFile
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
import httpx
from typing import List
from database import get_db_connection

# CORRIGIDO: Adicionado redirect_slashes=False
app = FastAPI(title="Radha ERP Gateway API", version="1.0", redirect_slashes=False)

# Configuração de CORS - ATENÇÃO: SUBSTITUA SEU_IP_DO_VPS PELO IP REAL DO SEU VPS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3005",
        "http://127.0.0.1:3005",
        "http://212.85.13.74:3005", # <--- SEU_IP_DO_VPS REAL
        "https://seu-dominio-erp.com.br"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cliente HTTP para fazer requisições para os módulos de backend
# Ajuste as URLs conforme onde seus módulos de backend rodarão
MARKETING_IA_BACKEND_URL = "http://localhost:8015"
PRODUCAO_BACKEND_URL = "http://localhost:8020"
COMERCIAL_BACKEND_URL = "http://localhost:8030"

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
            headers = {k: v for k, v in request.headers.items() if k.lower() not in ["host", "authorization"]}
            if "authorization" in request.headers:
                headers["Authorization"] = request.headers["Authorization"]

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

# Rota para o módulo Comercial
@app.api_route("/comercial/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def call_comercial_backend(path: str, request: Request):
    async with httpx.AsyncClient() as client:
        url = f"{COMERCIAL_BACKEND_URL}/{path}"
        try:
            headers = {k: v for k, v in request.headers.items() if k.lower() not in ["host"]}
            response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                params=request.query_params,
                content=await request.body(),
            )
            response.raise_for_status()
            return JSONResponse(response.json(), status_code=response.status_code)
        except httpx.HTTPStatusError as e:
            return JSONResponse({"detail": e.response.text}, status_code=e.response.status_code)
        except httpx.RequestError as e:
            return JSONResponse({"detail": f"Erro de conexão com o backend Comercial: {e}"}, status_code=503)

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


# -------------------------
# Cadastros - Empresas
# -------------------------

@app.post("/empresa")
async def criar_empresa(request: Request):
    """Registra uma nova empresa."""
    form = await request.form()
    logo_file = form.get("logo")
    logo_bytes = await logo_file.read() if logo_file else None
    fields = (
        form.get("codigo"),
        form.get("razaoSocial"),
        form.get("nomeFantasia"),
        form.get("cnpj"),
        form.get("inscricaoEstadual"),
        form.get("cep"),
        form.get("rua"),
        form.get("numero"),
        form.get("bairro"),
        form.get("cidade"),
        form.get("estado"),
        form.get("telefone1"),
        form.get("telefone2"),
        form.get("slogan"),
        logo_bytes,
    )
    with get_db_connection() as conn:
        cur = conn.execute(
            """INSERT INTO empresa (
                codigo, razao_social, nome_fantasia, cnpj,
                inscricao_estadual, cep, rua, numero,
                bairro, cidade, estado, telefone1,
                telefone2, slogan, logo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            fields,
        )
        conn.commit()
        new_id = cur.lastrowid
    return {"id": new_id}


@app.get("/empresa")
async def listar_empresas():
    """Lista todas as empresas cadastradas."""
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT id, codigo, razao_social, nome_fantasia, cnpj, slogan FROM empresa ORDER BY id"
        ).fetchall()
        empresas = [dict(row) for row in rows]
    return {"empresas": empresas}


@app.get("/empresa/{empresa_id}")
async def obter_empresa(empresa_id: int):
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM empresa WHERE id=?", (empresa_id,)).fetchone()
        if not row:
            return JSONResponse({"detail": "Empresa não encontrada"}, status_code=404)
        return {"empresa": dict(row)}


@app.put("/empresa/{empresa_id}")
async def atualizar_empresa(empresa_id: int, request: Request):
    form = await request.form()
    logo_file = form.get("logo")
    logo_bytes = await logo_file.read() if logo_file else None
    fields = (
        form.get("codigo"),
        form.get("razaoSocial"),
        form.get("nomeFantasia"),
        form.get("cnpj"),
        form.get("inscricaoEstadual"),
        form.get("cep"),
        form.get("rua"),
        form.get("numero"),
        form.get("bairro"),
        form.get("cidade"),
        form.get("estado"),
        form.get("telefone1"),
        form.get("telefone2"),
        form.get("slogan"),
        logo_bytes,
        empresa_id,
    )
    with get_db_connection() as conn:
        conn.execute(
            """UPDATE empresa SET
                codigo=?, razao_social=?, nome_fantasia=?, cnpj=?,
                inscricao_estadual=?, cep=?, rua=?, numero=?,
                bairro=?, cidade=?, estado=?, telefone1=?,
                telefone2=?, slogan=?, logo=?
            WHERE id=?""",
            fields,
        )
        conn.commit()
    return {"ok": True}

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

# -------------------------
# Cadastros - Usuarios
# -------------------------

@app.api_route("/usuarios", methods=["GET", "POST", "PUT", "DELETE"])
async def usuarios_proxy_root(request: Request):
    """Repasse para o backend de usuarios na raiz do endpoint."""
    return await usuarios_proxy("", request)


@app.api_route("/usuarios/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def usuarios_proxy(path: str = "", request: Request = None):
    async with httpx.AsyncClient() as client:
        url = f"{MARKETING_IA_BACKEND_URL}/usuarios/{path}"
        try:
            headers = {k: v for k, v in request.headers.items() if k.lower() not in ["host"]}
            response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                params=request.query_params,
                content=await request.body(),
            )
            response.raise_for_status()
            return JSONResponse(response.json(), status_code=response.status_code)
        except httpx.HTTPStatusError as e:
            return JSONResponse({"detail": e.response.text}, status_code=e.response.status_code)
        except httpx.RequestError as e:
            return JSONResponse({"detail": f"Erro de conexão com backend de usuários: {e}"}, status_code=503)
