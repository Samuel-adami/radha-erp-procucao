import os
import subprocess

# Função auxiliar para rodar comandos
def run(cmd, cwd=None):
    print(f"🔹 Executando: {cmd}")
    subprocess.run(cmd, shell=True, check=True, cwd=cwd)

# Estrutura de pastas
estrutura = {
    'backend': {
        'routes': ['chat.py', 'campanha.py', 'publicacao.py', 'publicos.py'],
        'services': ['openai_service.py', 'canva_service.py', 'meta_ads_service.py', 'capcut_service.py', 'google_ads_service.py'],
        'models': ['publicos.py'],
        'files': ['main.py', 'database.py', 'requirements.txt']
    },
    'frontend': {
        'src/pages': ['Chat.jsx', 'NovaCampanha.jsx', 'NovaPublicacao.jsx', 'PublicosAlvo.jsx'],
        'files': ['package.json', 'tailwind.config.js']
    }
}

conteudos = {
    'backend/main.py': '''
from fastapi import FastAPI
from routes import chat, campanha, publicacao, publicos

app = FastAPI(title="Radha Executor", version="1.0")

app.include_router(chat.router)
app.include_router(campanha.router)
app.include_router(publicacao.router)
app.include_router(publicos.router)

@app.get("/")
async def root():
    return {"message": "Radha Executor API funcionando!"}
''',
    'backend/database.py': '''
import os
from sqlalchemy import create_engine

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not configured")

engine = create_engine(DATABASE_URL)

def get_db_connection():
    return engine.connect()
''',
    'backend/requirements.txt': 'fastapi\nuvicorn\npydantic\nhttpx\npsycopg2-binary\n',
    'backend/routes/chat.py': '''
from fastapi import APIRouter
from pydantic import BaseModel
from services.openai_service import gerar_resposta

router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatInput(BaseModel):
    mensagem: str
    id_assistant: str = None

@router.post("/")
async def conversar(input: ChatInput):
    resposta = await gerar_resposta(input.mensagem, input.id_assistant)
    return {"resposta": resposta}
''',
    'backend/routes/campanha.py': '''
from fastapi import APIRouter
from pydantic import BaseModel
from services.openai_service import gerar_resposta

router = APIRouter(prefix="/nova-campanha", tags=["Campanhas"])

class CampanhaInput(BaseModel):
    tema: str
    objetivo: str
    publico_alvo: str
    orcamento: float
    duracao: str
    id_assistant: str = None

@router.post("/")
async def criar_campanha(input: CampanhaInput):
    prompt = (
        f"Crie uma campanha para {input.tema}. "
        f"Objetivo: {input.objetivo}. "
        f"Público: {input.publico_alvo}. "
        f"Orçamento: R${input.orcamento}. "
        f"Duração: {input.duracao}. "
        f"Crie conteúdos, CTA, roteiros de landing page, posts e reels."
    )
    resposta = await gerar_resposta(prompt, input.id_assistant)
    return {"campanha": resposta}
''',
    'backend/routes/publicacao.py': '''
from fastapi import APIRouter
from pydantic import BaseModel
from services.openai_service import gerar_resposta

router = APIRouter(prefix="/nova-publicacao", tags=["Publicações"])

class PublicacaoInput(BaseModel):
    tema: str
    objetivo: str
    formato: str
    quantidade: int
    id_assistant: str = None

@router.post("/")
async def criar_publicacao(input: PublicacaoInput):
    prompt = (
        f"Crie {input.quantidade} publicações no formato {input.formato} sobre {input.tema}. "
        f"Objetivo: {input.objetivo}. "
        f"Inclua legenda, CTA, roteiro visual, música sem direitos autorais do Pixabay, "
        f"sugestão de imagens (incluindo uma cozinha planejada)."
    )
    resposta = await gerar_resposta(prompt, input.id_assistant)
    return {"publicacao": resposta}
''',
    'backend/routes/publicos.py': '''
from fastapi import APIRouter
from typing import List
from models.publicos import PublicoAlvo

router = APIRouter(prefix="/publicos", tags=["Públicos"])

publicos_db: List[PublicoAlvo] = []

@router.post("/")
async def adicionar_publico(publico: PublicoAlvo):
    publicos_db.append(publico)
    return {"mensagem": "Público adicionado com sucesso"}

@router.get("/")
async def listar_publicos():
    return publicos_db
''',
    'backend/models/publicos.py': '''
from pydantic import BaseModel

class PublicoAlvo(BaseModel):
    nome: str
    descricao: str
''',
    'backend/services/openai_service.py': '''
import httpx

OPENAI_API_KEY = "sua_openai_api_key"
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-4"

async def gerar_resposta(mensagem: str, id_assistant: str = None):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": mensagem}]
    }
    
    if id_assistant:
        payload["tools"] = [{"type": "assistant", "id": id_assistant}]
    
    async with httpx.AsyncClient() as client:
        response = await client.post(OPENAI_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
    
    return data['choices'][0]['message']['content']
''',
    'frontend/package.json': '{"name": "radha-frontend", "version": "1.0.0"}',
    'frontend/tailwind.config.js': '''
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: { extend: {} },
  plugins: [],
}
''',
}

# Criar pastas e arquivos
for pasta, subpastas in estrutura.items():
    for subpasta, arquivos in subpastas.items():
        path = os.path.join(pasta, subpasta)
        os.makedirs(path, exist_ok=True)
        for arquivo in arquivos:
            file_path = os.path.join(path, arquivo)
            key = f"{pasta}/{subpasta}/{arquivo}".replace('\\','/')
            content = conteudos.get(key, 'def placeholder():\n    pass\n' if 'service' in key else 'Em construção')
            with open(file_path, 'w') as f:
                f.write(content)

# Criar arquivos principais
for key, content in conteudos.items():
    parts = key.split('/')
    if len(parts) == 2:
        path = os.path.join(parts[0], parts[1])
        os.makedirs(parts[0], exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)

print("✅ Estrutura criada!")

# Backend: criar e ativar venv, instalar dependências
os.chdir('backend')
run('python -m venv venv')
venv_activate = 'venv\\Scripts\\activate' if os.name == 'nt' else 'source venv/bin/activate'
print(f"✅ Ambiente virtual criado. ATIVE com: {venv_activate}")
run(f'{venv_activate} && pip install -r requirements.txt')

# Iniciar backend na porta 8010
print("✅ Iniciando backend em http://127.0.0.1:8010 ...")
run(f'{venv_activate} && uvicorn main:app --reload --port 8010')

# Frontend
os.chdir('../')
run('npx create-react-app frontend')
os.chdir('frontend')
run('npm install -D tailwindcss postcss autoprefixer')
run('npx tailwindcss init -p')
print("✅ Frontend configurado com Tailwind.")

# Iniciar frontend
print("✅ Iniciando frontend em http://localhost:3000 ...")
run('npm start')