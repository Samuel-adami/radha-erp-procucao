from fastapi import FastAPI, Request
from fastapi import UploadFile
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, Response
import httpx
from typing import List
import os
from database import get_session, init_db
from models import Empresa, Cliente, Fornecedor

# CORRIGIDO: Adicionado redirect_slashes=False
app = FastAPI(title="Radha ERP Gateway API", version="1.0", redirect_slashes=False)

# Initialize gateway database tables on startup
init_db()

# Configuração de CORS - ATENÇÃO: SUBSTITUA SEU_IP_DO_VPS PELO IP REAL DO SEU VPS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3015",
        "http://127.0.0.1:3015",
        "http://212.85.13.74:3015", 
        "https://erp.radhadigital.com.br"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cliente HTTP para fazer requisições para os módulos de backend
# URLs podem ser configuradas via variáveis de ambiente
# Use IPv4 loopback by default to avoid potential issues resolving "localhost"
MARKETING_IA_BACKEND_URL = os.getenv(
    "MARKETING_IA_BACKEND_URL", "http://127.0.0.1:8050"
)
PRODUCAO_BACKEND_URL = os.getenv("PRODUCAO_BACKEND_URL", "http://127.0.0.1:8060")
COMERCIAL_BACKEND_URL = os.getenv("COMERCIAL_BACKEND_URL", "http://127.0.0.1:8070")


def create_response(response: httpx.Response):
    """Transforma a resposta do backend em uma resposta FastAPI apropriada."""
    content_type = response.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        return JSONResponse(response.json(), status_code=response.status_code)
    headers = dict(response.headers)
    return Response(content=response.content, status_code=response.status_code, headers=headers)

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
            return create_response(response)
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
            return create_response(response)
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
            return create_response(response)
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
            headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}
            response = await client.post(
                url,
                content=await request.body(),
                headers=headers,
            )
            response.raise_for_status()
            return create_response(response)
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
        form.get("complemento"),
        form.get("bairro"),
        form.get("cidade"),
        form.get("estado"),
        form.get("telefone1"),
        form.get("telefone2"),
        form.get("slogan"),
        logo_bytes,
    )
    session = get_session()
    try:
        empresa = Empresa(
            codigo=form.get("codigo"),
            razao_social=form.get("razaoSocial"),
            nome_fantasia=form.get("nomeFantasia"),
            cnpj=form.get("cnpj"),
            inscricao_estadual=form.get("inscricaoEstadual"),
            cep=form.get("cep"),
            rua=form.get("rua"),
            numero=form.get("numero"),
            complemento=form.get("complemento"),
            bairro=form.get("bairro"),
            cidade=form.get("cidade"),
            estado=form.get("estado"),
            telefone1=form.get("telefone1"),
            telefone2=form.get("telefone2"),
            slogan=form.get("slogan"),
            logo=logo_bytes,
        )
        session.add(empresa)
        session.commit()
        session.refresh(empresa)
        return {"id": empresa.id}
    finally:
        session.close()


@app.get("/empresa")
async def listar_empresas():
    """Lista todas as empresas cadastradas."""
    session = get_session()
    try:
        rows = session.query(Empresa).order_by(Empresa.id).all()
        empresas = [
            {
                "id": e.id,
                "codigo": e.codigo,
                "razao_social": e.razao_social,
                "nome_fantasia": e.nome_fantasia,
                "cnpj": e.cnpj,
                "slogan": e.slogan,
            }
            for e in rows
        ]
        return {"empresas": empresas}
    finally:
        session.close()


@app.get("/empresa/{empresa_id}")
async def obter_empresa(empresa_id: int):
    session = get_session()
    try:
        empresa = session.query(Empresa).filter(Empresa.id == empresa_id).first()
        if not empresa:
            return JSONResponse({"detail": "Empresa não encontrada"}, status_code=404)
        return {"empresa": {
            "id": empresa.id,
            "codigo": empresa.codigo,
            "razao_social": empresa.razao_social,
            "nome_fantasia": empresa.nome_fantasia,
            "cnpj": empresa.cnpj,
            "inscricao_estadual": empresa.inscricao_estadual,
            "cep": empresa.cep,
            "rua": empresa.rua,
            "numero": empresa.numero,
            "complemento": empresa.complemento,
            "bairro": empresa.bairro,
            "cidade": empresa.cidade,
            "estado": empresa.estado,
            "telefone1": empresa.telefone1,
            "telefone2": empresa.telefone2,
            "slogan": empresa.slogan,
            "logo": empresa.logo,
        }}
    finally:
        session.close()


@app.put("/empresa/{empresa_id}")
async def atualizar_empresa(empresa_id: int, request: Request):
    form = await request.form()
    logo_file = form.get("logo")
    logo_bytes = await logo_file.read() if logo_file else None

    session = get_session()
    try:
        empresa = session.query(Empresa).filter(Empresa.id == empresa_id).first()
        if not empresa:
            return JSONResponse({"detail": "Empresa não encontrada"}, status_code=404)

        empresa.codigo = form.get("codigo")
        empresa.razao_social = form.get("razaoSocial")
        empresa.nome_fantasia = form.get("nomeFantasia")
        empresa.cnpj = form.get("cnpj")
        empresa.inscricao_estadual = form.get("inscricaoEstadual")
        empresa.cep = form.get("cep")
        empresa.rua = form.get("rua")
        empresa.numero = form.get("numero")
        empresa.complemento = form.get("complemento")
        empresa.bairro = form.get("bairro")
        empresa.cidade = form.get("cidade")
        empresa.estado = form.get("estado")
        empresa.telefone1 = form.get("telefone1")
        empresa.telefone2 = form.get("telefone2")
        empresa.slogan = form.get("slogan")
        empresa.logo = logo_bytes

        session.commit()
        return {"ok": True}
    finally:
        session.close()

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


# -------------------------
# Cadastros - Clientes
# -------------------------

@app.post("/clientes")
async def criar_cliente(request: Request):
    data = await request.json()
    session = get_session()
    try:
        cliente = Cliente(**data)
        session.add(cliente)
        session.commit()
        session.refresh(cliente)
        return {"id": cliente.id}
    finally:
        session.close()


@app.get("/clientes")
async def listar_clientes():
    session = get_session()
    try:
        itens = [c.__dict__ for c in session.query(Cliente).order_by(Cliente.id).all()]
        for it in itens:
            it.pop("_sa_instance_state", None)
        return {"clientes": itens}
    finally:
        session.close()


@app.get("/clientes/{cliente_id}")
async def obter_cliente(cliente_id: int):
    session = get_session()
    try:
        c = session.query(Cliente).filter(Cliente.id == cliente_id).first()
        if not c:
            return JSONResponse({"detail": "Cliente não encontrado"}, status_code=404)
        data = c.__dict__.copy()
        data.pop("_sa_instance_state", None)
        return {"cliente": data}
    finally:
        session.close()


@app.put("/clientes/{cliente_id}")
async def atualizar_cliente(cliente_id: int, request: Request):
    data = await request.json()
    session = get_session()
    try:
        cliente = session.query(Cliente).filter(Cliente.id == cliente_id).first()
        if not cliente:
            return JSONResponse({"detail": "Cliente não encontrado"}, status_code=404)
        for k, v in data.items():
            setattr(cliente, k, v)
        session.commit()
        return {"ok": True}
    finally:
        session.close()


@app.delete("/clientes/{cliente_id}")
async def excluir_cliente(cliente_id: int):
    session = get_session()
    try:
        session.query(Cliente).filter(Cliente.id == cliente_id).delete()
        session.commit()
        return {"ok": True}
    finally:
        session.close()


# -------------------------
# Cadastros - Fornecedores
# -------------------------

@app.post("/fornecedores")
async def criar_fornecedor(request: Request):
    data = await request.json()
    session = get_session()
    try:
        fornecedor = Fornecedor(**data)
        session.add(fornecedor)
        session.commit()
        session.refresh(fornecedor)
        return {"id": fornecedor.id}
    finally:
        session.close()


@app.get("/fornecedores")
async def listar_fornecedores():
    session = get_session()
    try:
        itens = [f.__dict__ for f in session.query(Fornecedor).order_by(Fornecedor.id).all()]
        for it in itens:
            it.pop("_sa_instance_state", None)
        return {"fornecedores": itens}
    finally:
        session.close()


@app.get("/fornecedores/{fornecedor_id}")
async def obter_fornecedor(fornecedor_id: int):
    session = get_session()
    try:
        f = session.query(Fornecedor).filter(Fornecedor.id == fornecedor_id).first()
        if not f:
            return JSONResponse({"detail": "Fornecedor não encontrado"}, status_code=404)
        data = f.__dict__.copy()
        data.pop("_sa_instance_state", None)
        return {"fornecedor": data}
    finally:
        session.close()


@app.put("/fornecedores/{fornecedor_id}")
async def atualizar_fornecedor(fornecedor_id: int, request: Request):
    data = await request.json()
    session = get_session()
    try:
        fornecedor = session.query(Fornecedor).filter(Fornecedor.id == fornecedor_id).first()
        if not fornecedor:
            return JSONResponse({"detail": "Fornecedor não encontrado"}, status_code=404)
        for k, v in data.items():
            setattr(fornecedor, k, v)
        session.commit()
        return {"ok": True}
    finally:
        session.close()


@app.delete("/fornecedores/{fornecedor_id}")
async def excluir_fornecedor(fornecedor_id: int):
    session = get_session()
    try:
        session.query(Fornecedor).filter(Fornecedor.id == fornecedor_id).delete()
        session.commit()
        return {"ok": True}
    finally:
        session.close()
