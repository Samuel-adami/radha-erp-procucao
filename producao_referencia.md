# Documento de Referência – Módulo Produção do Radha ERP

---

## 1. Visão Geral do Módulo
O módulo **Produção** é responsável por gerenciar o fluxo de fabricação, desde a importação de arquivos de pedidos (XML ou DXT) até a geração de lotes e a otimização de corte (nesting). Ele converte arquivos em peças DXF e controla lotes, chapas, configurações de máquina e ocorrências de produção. Destina‑se a operadores de produção e usuários que precisam monitorar o processo fabril.

Os objetivos e as principais rotas do backend estão descritos em `manual-arquitetura.md`:

```
55  ## 3. producao
56  ### Objetivo
57  Gerenciar processos de produção, convertendo arquivos de pedidos em DXF e realizando nesting para otimização de corte.
59  ### Backend (`producao/backend/src`)
60  - **Principais rotas**
61    - `POST /importar-xml` – identifica e processa arquivos XML ou DXT
62    - `POST /gerar-lote-final` – cria o lote final em DXF
63    - `POST /executar-nesting` – executa algoritmo de nesting e registra o resultado
64    - `GET /listar-lotes` – retorna as chaves dos lotes registrados
65    - `GET /nestings` – lista otimizações realizadas
66    - `GET /download-lote/{lote}` e `GET /download-nesting/{id}` – baixa arquivos
67    - Cadastros auxiliares (`/chapas`, `/config-maquina`, `/config-ferramentas`, `/config-cortes`, `/config-layers`)
68    - Gerenciamento de ocorrências (`/lotes-ocorrencias`, `/motivos-ocorrencias`, `/relatorio-ocorrencias`)
69  - **Integrações**
70    - Biblioteca `ezdxf` para manipular arquivos DXF
71    - Algoritmo de nesting implementado em `nesting.py`
72  - **Banco de dados**
73    - Banco PostgreSQL (`DATABASE_URL` no `.env`) com tabelas de lotes, nestings, chapas e ocorrências
74  - **Lógica principal**
75    - Converte XML ou DXT em peças, gera DXFs e registra eventos de produção
```

As telas disponíveis no frontend estão listadas em `user-guide.md`:

```
12  ## Produção
13  - **Lotes** – criação de lotes de produção, importação de arquivos XML ou DXT, edição de peças e visualização. Permite baixar o lote final compactado.
14  - **Apontamento** – registra o andamento das peças na produção.
15  - **Apontamento Volume** – resumo de volumes produzidos por lote.
16  - **Nesting** – envia um lote para otimização de corte, gerando arquivos e relatórios. Cada otimização pode ser baixada em ZIP.
17  - **Chapas** – cadastro de chapas e materiais utilizados na produção.
18  - **Ocorrências** – geração de lotes de ocorrência e relatórios de motivos.
```

---

## 2. Principais Entidades e Modelos de Dados
O módulo utiliza PostgreSQL. As tabelas principais estão documentadas em `manual-banco-dados.md`:

```
38  ## 3. producao
39  ### Estrutura Atual (PostgreSQL)
40  - **Tabelas**
41    - `chapas` (id SERIAL PRIMARY KEY, possui_veio INTEGER, propriedade TEXT, espessura REAL, comprimento REAL, largura REAL)
42    - `lotes` (id SERIAL PRIMARY KEY, pasta TEXT, criado_em TEXT)
43    - `nestings` (id SERIAL PRIMARY KEY, lote TEXT, pasta_resultado TEXT, criado_em TEXT)
```

O arquivo `models.py` define essas tabelas via SQLAlchemy:

```
class Chapa(Base):
    __tablename__ = "chapas"

    id = Column(Integer, primary_key=True)
    possui_veio = Column(Integer)
    propriedade = Column(String)
    espessura = Column(Float)
    comprimento = Column(Float)
    largura = Column(Float)

class Lote(Base):
    __tablename__ = "lotes"

    id = Column(Integer, primary_key=True)
    pasta = Column(String)
    criado_em = Column(String)

class Nesting(Base):
    __tablename__ = "nestings"

    id = Column(Integer, primary_key=True)
    lote = Column(String)
    pasta_resultado = Column(String)
    criado_em = Column(String)
```

Além dessas tabelas, há registros de ocorrências (lotes_ocorrencias, ocorrencias_pecas e motivos_ocorrencia) gerados via API. As validações incluem verificação de motivos ao gerar lotes de ocorrência, conforme o manual de arquitetura.

---

## 3. APIs e Rotas Expostas
O backend FastAPI implementa diversos endpoints (ver trechos principais em `api.py`). Alguns exemplos:

```
85  @app.post("/importar-xml")
86  async def importar_xml(files: list[UploadFile] = File(...)):
...
115  @app.post("/gerar-lote-final")
116  async def gerar_lote_final(request: Request):
...
225  @app.post("/executar-nesting")
...
258  @app.post("/nesting-preview")
...
300  @app.post("/executar-nesting-final")
...
644  @app.get("/listar-lotes")
...
687  @app.get("/nestings")
...
742  @app.get("/download-lote/{lote}")
...
759  @app.get("/download-nesting/{nid}")
...
788  @app.post("/remover-nesting")
...
806  @app.post("/excluir-lote")
```

Endpoints de configuração e cadastros de apoio:

```
572  @app.get("/config-cortes")
...
591  @app.post("/config-cortes")
...
604  @app.get("/config-layers")
...
617  @app.post("/config-layers")
...
646  @app.get("/chapas")
...
659  @app.post("/chapas")
...
694  @app.delete("/chapas/{chapa_id}")
...
708  @app.get("/lotes-ocorrencias")
...
721  @app.post("/lotes-ocorrencias")
...
850  @app.delete("/lotes-ocorrencias/{oc_id}")
...
877  @app.get("/motivos-ocorrencias")
...
889  @app.post("/motivos-ocorrencias")
...
905  @app.delete("/motivos-ocorrencias/{codigo}")
...
917  @app.get("/relatorio-ocorrencias")
```

As respostas geralmente retornam JSON; downloads são enviados como ZIP. A autenticação é feita no gateway, exigindo token JWT compartilhado por todos os serviços.

---

## 4. Fluxos Principais e Integrações
O manual `NESTING.md` explica o fluxo do nesting:

```
18  2. **Execução do nesting** (`Nesting.jsx`)
19     - Primeiro são consultados os layers existentes via `/coletar-layers`.
20     - Em seguida é enviado um `POST` para `/executar-nesting` contendo:
21       - Pasta do lote (arquivos `.dxt`/`dxf`).
22       - Dimensões da chapa.
23       - Ferramentas e definições de layers.
24       - Configuração da máquina salva no `localStorage`.
25     - A resposta traz a disposição preliminar das chapas e eventuais layers faltantes.
26     - A tela `VisualizacaoNesting.tsx` carrega essa prévia novamente usando o endpoint `/nesting-preview`.
27     - Após a confirmação do operador é feito `POST` em `/executar-nesting-final`, que gera os arquivos definitivos.
```

O módulo também se integra ao Gateway via prefixo `/producao/`, que encaminha as chamadas para o backend de Produção. Todos os serviços usam a mesma instância de PostgreSQL, com schemas separados, conforme `AGENTS.md`:

```
50  All backends connect to the same PostgreSQL instance defined by
51  `DATABASE_URL`.  Each service uses its own `DATABASE_SCHEMA` so tables are
52  isolated by module.  The production database is named `producao` and includes
53  these schemas:
56  - **gateway** – table `empresa` com dados cadastrais.
57  - **marketing** – table `users` contendo usuários e permissões.
58  - **producao** – tables `chapas`, `lotes` e `nestings` para o fluxo de
59    fabricação.
60  - **comercial** – table `atendimentos` armazenando registros de vendas.
```

A autenticação é centralizada no backend de Marketing (rota `/auth`) e validada pelo Gateway, que repassa o token às demais APIs.

---

## 5. Requisitos Técnicos
Principais variáveis de ambiente do módulo (`.env.example`):

```
1  # Produção backend environment variables
2  DATABASE_URL=postgresql://radha_admin:12345@localhost:5432/producao
3  DATABASE_SCHEMA=producao
4  SECRET_KEY=radha-super-secreto
5  RADHA_DATA_DIR=radha-arquivos
6  OBJECT_STORAGE_ENDPOINT=https://nyc3.digitaloceanspaces.com
7  OBJECT_STORAGE_ACCESS_KEY=DO801RV.......
8  OBJECT_STORAGE_SECRET_KEY=0D4o8nUESJUP0X......
9  OBJECT_STORAGE_BUCKET=radha-prod-backend
11 OBJECT_STORAGE_PREFIX=producao/
```

Outras variáveis globais estão em `docs/overview.md`:

```
54  ### Variáveis de Ambiente Principais
55   - `SECRET_KEY` – chave usada para assinar tokens de autenticação em todos os serviços.
56   - `DATABASE_URL` – string de conexão do PostgreSQL compartilhado.
57   - `DATABASE_SCHEMA` – schema específico de cada módulo (gateway, producao etc.).
58   - `OBJECT_STORAGE_BUCKET` – bucket único para uploads.
59   - `OBJECT_STORAGE_PREFIX` – pasta/prefixo de cada módulo dentro do bucket.
60  - `RADHA_ADMIN_USER` e `RADHA_ADMIN_PASS` – definem o login inicial criado no primeiro acesso. Esse usuário recebe permissões completas para configurar o ERP e cadastrar novos usuários.
61  Todas essas variáveis podem ser definidas no arquivo `.env` na raiz do projeto, carregado automaticamente pelos backends com `python-dotenv`.
```

Dependências básicas: Python 3.11+, Node.js 18+, bibliotecas do `requirements.txt` e `package.json` de cada módulo.

---

## 6. Detalhes sobre Scripts e Inicialização
Para desenvolvimento local, execute `./start_services.sh`, que inicia todos os backends e o frontend (portas 8040–8070 e 3015):

```
1  #!/bin/bash
2  DIR=$(dirname "$0")
3  export SECRET_KEY=${SECRET_KEY:-radha-super-secreto}
5  export MARKETING_IA_BACKEND_URL=${MARKETING_IA_BACKEND_URL:-http://127.0.0.1:8050}
6  export PRODUCAO_BACKEND_URL=${PRODUCAO_BACKEND_URL:-http://127.0.0.1:8060}
7  export COMERCIAL_BACKEND_URL=${COMERCIAL_BACKEND_URL:-http://127.0.0.1:8070}
...
9  cd "$DIR/marketing-digital-ia/backend" && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8050 --reload &
11 cd "$DIR/producao/backend/src" && source venv/bin/activate && uvicorn api:app --host 0.0.0.0 --port 8060 --reload &
13 cd "$DIR/backend-gateway" && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8040 --reload &
15 cd "$DIR/comercial-backend" && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8070 --reload &
17 cd "$DIR/frontend-erp" && npm run dev &
18 PID5=$!
19 wait $PID1 $PID2 $PID3 $PID4 $PID5
```

Em produção, cada backend roda como serviço systemd. Exemplo do backend de Produção (`AGENTS.md`):

```
85  ### Produção Backend
87  /etc/systemd/system/radha-producao-backend.service
...
95  WorkingDirectory=/home/samuel/radha-erp-procucao/producao/backend/src
96  ExecStart=/home/samuel/radha-erp-procucao/venv/bin/uvicorn api:app --host 0.0.0.0 --port 8060
97  Restart=always
100 WantedBy=multi-user.target
```

O Nginx faz o proxy para os serviços, conforme a configuração no mesmo arquivo.

---

## 7. Principais Problemas Conhecidos e Soluções
Durante a migração para produção web foi necessário sair do SQLite e adotar PostgreSQL, além de utilizar object storage para arquivos. O manual de banco de dados detalha o processo:

```
82  Migrar o Radha ERP do modelo atual (banco SQLite + arquivos locais) para um ambiente de produção robusto com:
84  - Banco de dados **PostgreSQL**
85  - Armazenamento de arquivos em bucket S3/MinIO (object storage)
86  - Deploy contínuo para rodar como serviço web 24/7 no domínio próprio `radhadigital.com.br`
...
92  - Migrar todas as tabelas de cada módulo (`gateway`, `producao`, `comercial`, `marketing-digital-ia`) do SQLite para PostgreSQL.
93  - Adaptar as funções de conexão (substituir `sqlite3` por `psycopg2` ou `asyncpg`) em cada backend.
94  - Ajustar o método `get_db_connection()` para usar a variável de ambiente `DATABASE_URL`...
112  - Alterar as tabelas (`lotes`, `nestings`, `lotes_ocorrencias`) para que as colunas que guardam caminho local de arquivo (`pasta`, `pasta_resultado`) passem a armazenar apenas a **chave do objeto** ou **URL** no storage.
```

Esse processo garantiu a persistência correta e eliminou problemas de permissões do SQLite em produção.

---

## 8. Exemplo de Uso Passo a Passo
Um fluxo básico para registrar uma chapa e acompanhar o processamento de um lote:

1. **Cadastrar Chapa**  
   - Acesse a tela *Chapas* no frontend.  
   - Envie `POST /chapas` com dados da chapa: `possui_veio`, `propriedade`, `espessura`, `comprimento` e `largura`.  
   - A tabela `chapas` recebe um novo registro.

2. **Importar Arquivos do Pedido**  
   - Envie `POST /importar-xml` com o XML ou DXT do pedido.  
   - O backend interpreta as peças e retorna os pacotes para conferência.

3. **Gerar Lote Final**  
   - Chame `POST /gerar-lote-final` com a lista de peças.  
   - Os DXFs são gerados em `Lote_<numero>` dentro da pasta de saída e a tabela `lotes` registra o lote.

4. **Executar Nesting**  
   - Na tela *Nesting*, escolha o lote e clique em “Executar Nesting”.  
   - O frontend consulta `/coletar-layers`, envia o `POST /executar-nesting` e recebe a disposição das chapas.  
   - Após aprovar, chame `POST /executar-nesting-final`. A pasta `Lote_X/nesting/` é criada e registrada em `nestings`.

5. **Baixar Resultado**  
   - Use `GET /download-nesting/{id}` para baixar o ZIP com NCs, imagens, etiquetas e relatórios.  
   - Caso necessário, gere lotes de ocorrência em `/lotes-ocorrencias` e acompanhe pelo relatório `/relatorio-ocorrencias`.

---

## Resumo das Informações Críticas
- **Propósito**: Automatizar a criação de DXFs e a otimização de corte (nesting) a partir de pedidos, registrando lotes e ocorrências.
- **Principais tabelas**: `chapas`, `lotes`, `nestings` e tabelas de ocorrências.
- **Rotas de destaque**: `/importar-xml`, `/gerar-lote-final`, `/executar-nesting`, `/nesting-preview`, `/executar-nesting-final`, `/chapas`, `/lotes-ocorrencias`, `/relatorio-ocorrencias`.
- **Integrações**: Gateway central (porta 8040), PostgreSQL, object storage via S3/MinIO.
- **Variáveis de ambiente**: `DATABASE_URL`, `DATABASE_SCHEMA`, `SECRET_KEY`, `OBJECT_STORAGE_*`, `RADHA_ADMIN_USER`, `RADHA_ADMIN_PASS`.
- **Execução**: `./start_services.sh` para desenvolvimento; em produção, serviços systemd e Nginx conforme `AGENTS.md`.
- **Problemas resolvidos**: migração de SQLite para PostgreSQL e armazenamento em bucket, garantindo operação 24/7.

