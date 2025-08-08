from fastapi import FastAPI, Request, Depends, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from starlette.responses import JSONResponse, Response, FileResponse

import httpx
import os
import uuid
from pathlib import Path
from database import get_session, init_db
from models import Empresa, Cliente, Fornecedor, DocumentoTreinamento
from services import auth_service
from security import verificar_autenticacao

# CORRIGIDO: Adicionado redirect_slashes=False
app = FastAPI(title="Radha ERP Gateway API", version="1.0", redirect_slashes=False)

# Initialize gateway database tables on startup
init_db()
auth_service.ensure_default_admin()

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
# Algumas operações do backend de Produção, como gerar o lote final,
# podem levar minutos. Para evitar erro 503 no Gateway, o tempo limite
# de resposta pode ser configurado via PRODUCAO_TIMEOUT.
PRODUCAO_TIMEOUT = float(os.getenv("PRODUCAO_TIMEOUT", "120"))
COMERCIAL_BACKEND_URL = os.getenv("COMERCIAL_BACKEND_URL", "http://127.0.0.1:8070")
COMERCIAL_TIMEOUT = float(os.getenv("COMERCIAL_TIMEOUT", "300"))
FINANCE_BACKEND_URL = os.getenv("FINANCE_BACKEND_URL", "http://127.0.0.1:8080")


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

# Rota específica para integrações RD Station dentro do módulo de Marketing.
# Esta rota precisa ter prioridade sobre a rota genérica de marketing para
# garantir que callbacks como /marketing-ia/rd/callback sejam encaminhados
# corretamente ao backend de Marketing Digital IA.
@app.api_route("/marketing-ia/rd/{path:path}", methods=["GET", "POST"])
async def encaminhar_rdstation_callback(path: str, request: Request):
    url = f"{MARKETING_IA_BACKEND_URL}/rd/{path}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}
            response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                params=request.query_params,
                content=await request.body()
            )
            return create_response(response)
        except httpx.RequestError as e:
            return JSONResponse(
                {"detail": f"Erro ao encaminhar para backend de Marketing: {e}"},
                status_code=502,
            )

# Rota para o módulo de Marketing Digital IA (mantém as rotas existentes)
@app.api_route("/marketing-ia/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def call_marketing_ia_backend(path: str, request: Request):
    # Marketing IA endpoints podem demorar para responder devido à
    # geração de conteúdos pela OpenAI. O timeout padrão de 30s era
    # insuficiente e fazia o gateway retornar erro 503 quando a resposta
    # atrasava. Permitimos configurar esse valor via variável de ambiente
    # e elevamos o padrão para 90s para evitar falhas desnecessárias.
    marketing_timeout = float(os.getenv("MARKETING_TIMEOUT", "90"))
    timeout = httpx.Timeout(marketing_timeout)
    async with httpx.AsyncClient(timeout=timeout) as client:

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
            import traceback
            print("🟥 ERRO DE CONEXÃO COM BACKEND MARKETING:")
            traceback.print_exc()
            return JSONResponse({"detail": f"Erro de conexão com o backend de Marketing Digital IA: {e}"}, status_code=503)


# Rota para o módulo de Produção (mantém as rotas existentes)
@app.api_route("/producao/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def call_producao_backend(path: str, request: Request):
    timeout = httpx.Timeout(PRODUCAO_TIMEOUT)
    async with httpx.AsyncClient(timeout=timeout) as client:
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
    timeout = httpx.Timeout(COMERCIAL_TIMEOUT)
    async with httpx.AsyncClient(timeout=timeout) as client:
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

# Rota para o módulo Financeiro
@app.api_route("/finance/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def call_finance_backend(path: str, request: Request):
    async with httpx.AsyncClient() as client:
        # The finance backend exposes its routes under the /finance prefix
        # so we need to preserve it when forwarding the request.
        url = f"{FINANCE_BACKEND_URL}/finance/{path}"
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
            return JSONResponse({"detail": f"Erro de conexão com o backend Financeiro: {e}"}, status_code=503)

# Rotas de Autenticação agora processadas localmente
@app.post("/auth/login")
async def login(request: Request):
    body = await request.json()
    username = body.get("username")
    password = body.get("password")

    if not username or not password:
        return JSONResponse({"detail": "Usuário e senha são obrigatórios"}, status_code=400)

    user = auth_service.autenticar(username, password)
    if not user:
        return JSONResponse({"detail": "Credenciais inválidas"}, status_code=401)

    return auth_service.criar_token(user)


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
                "razaoSocial": e.razao_social,
                "nomeFantasia": e.nome_fantasia,
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
            "razaoSocial": empresa.razao_social,
            "nomeFantasia": empresa.nome_fantasia,
            "cnpj": empresa.cnpj,
            "inscricaoEstadual": empresa.inscricao_estadual,
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
async def validate_token(usuario=Depends(verificar_autenticacao())):
    return {"status": "validado", "usuario": usuario}

# -------------------------
# Cadastros - Usuarios
# -------------------------

@app.get("/usuarios")
async def listar_usuarios():
    """Retorna a lista de usuários cadastrados."""
    return {"usuarios": auth_service.listar_usuarios()}


@app.post("/usuarios")
async def criar_usuario(request: Request):
    """Cria um novo usuário no banco local."""
    data = await request.json()
    new_id = auth_service.criar_usuario(data)
    return {"id": new_id}


@app.put("/usuarios/{user_id}")
async def atualizar_usuario(user_id: int, request: Request):
    """Atualiza um usuário existente."""
    data = await request.json()
    if not auth_service.atualizar_usuario(user_id, data):
        return JSONResponse({"detail": "Usuário não encontrado"}, status_code=404)
    return {"ok": True}


@app.delete("/usuarios/{user_id}")
async def excluir_usuario(user_id: int):
    """Remove um usuário."""
    if not auth_service.excluir_usuario(user_id):
        return JSONResponse({"detail": "Usuário não encontrado"}, status_code=404)
    return {"ok": True}


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


# -------------------------------
# Universidade Radha - Documentos
# -------------------------------

UPLOAD_DIR = (Path(__file__).resolve().parent / "uploads" / "documentos_treinamento")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.post("/universidade-radha/documentos")
async def enviar_documento(
    titulo: str = Form(...),
    autor: str = Form(...),
    data: str = Form(...),
    arquivo: UploadFile = File(...),
    usuario=Depends(verificar_autenticacao()),
):
    ext = os.path.splitext(arquivo.filename)[1].lower()
    if ext not in [".pdf", ".html"]:
        raise HTTPException(status_code=400, detail="Formato não suportado")

    nome_arquivo = f"{uuid.uuid4()}{ext}"
    caminho = UPLOAD_DIR / nome_arquivo
    with open(caminho, "wb") as f:
        f.write(await arquivo.read())

    session = get_session()
    try:
        doc = DocumentoTreinamento(
            titulo=titulo, autor=autor, data=data, caminho=nome_arquivo
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)
        return {"id": doc.id}
    finally:
        session.close()


@app.get("/universidade-radha/documentos")
async def listar_documentos(usuario=Depends(verificar_autenticacao())):
    session = get_session()
    try:
        docs = session.query(DocumentoTreinamento).order_by(DocumentoTreinamento.id).all()
        return {
            "documentos": [
                {
                    "id": d.id,
                    "titulo": d.titulo,
                    "autor": d.autor,
                    "data": d.data,
                }
                for d in docs
            ]
        }
    finally:
        session.close()


@app.get("/universidade-radha/documentos/{doc_id}/arquivo")
async def obter_documento_arquivo(doc_id: int, usuario=Depends(verificar_autenticacao())):
    session = get_session()
    try:
        doc = session.query(DocumentoTreinamento).filter(DocumentoTreinamento.id == doc_id).first()
        caminho = UPLOAD_DIR / doc.caminho if doc else None
        if not doc or not caminho.exists():
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        media_type = "application/pdf" if doc.caminho.endswith(".pdf") else "text/html"
        return FileResponse(str(caminho), media_type=media_type)
    finally:
        session.close()


@app.delete("/universidade-radha/documentos/{doc_id}")
async def excluir_documento(doc_id: int, usuario=Depends(verificar_autenticacao())):
    session = get_session()
    try:
        doc = session.query(DocumentoTreinamento).filter(DocumentoTreinamento.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Documento não encontrado")
        caminho = UPLOAD_DIR / doc.caminho
        if caminho.exists():
            os.remove(caminho)
        session.delete(doc)
        session.commit()
        return {"ok": True}
    finally:
        session.close()
# -----------------------------------------------------
# Fallback for React SPA routes
# -----------------------------------------------------

front_root = os.getenv(
    "FRONTEND_DIST_DIR",
    os.path.join(os.path.dirname(__file__), "..", "frontend-erp", "dist"),
)
index_file = os.path.join(front_root, "index.html")

if not os.path.exists(index_file):
    # Allow serving directly from the source directory when not built
    front_root = os.path.join(os.path.dirname(__file__), "..", "frontend-erp")
    index_file = os.path.join(front_root, "index.html")

if os.path.exists(index_file):
    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        """Serve static files or the React entry point for unknown routes."""
        candidate = os.path.join(front_root, full_path)
        if os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(index_file)
