# Manual de Arquitetura dos Módulos do Radha ERP

## 1. backend-gateway
### Objetivo
API centralizadora escrita em FastAPI que recebe todas as chamadas do `frontend-erp` e as repassa aos demais serviços.

### Backend
- **Principais rotas**
  - Proxy para Marketing Digital IA: `GET/POST/PUT/DELETE /marketing-ia/{path}`
  - Proxy para Produção: `GET/POST/PUT/DELETE /producao/{path}`
  - Proxy para Comercial: `GET/POST/PUT/DELETE /comercial/{path}`
  - Cadastro de empresas (`POST /empresa`, `GET /empresa`, `PUT /empresa/{id}`)
  - Gerenciamento de usuários em `/usuarios` (repassado ao Marketing IA)
  - Autenticação (`/auth/login`, `/auth/validate`) encaminhada ao backend de marketing
- **Integrações**
  - Encaminha requisições via `httpx` para os backends configurados nas variáveis `MARKETING_IA_BACKEND_URL`, `PRODUCAO_BACKEND_URL` e `COMERCIAL_BACKEND_URL`
- **Banco de dados**
  - SQLite `gateway.db` inicializado em `database.py`
- **Lógica principal**
  - Atua como proxy unificando CORS e validações, concentrando a autenticação e o cadastro de empresas

### Frontend
Não possui interface própria; é utilizado pelo `frontend-erp`.

### Entrega ao usuário final
Oferece um único endpoint para as várias APIs do ERP, simplificando as chamadas do frontend.

## 2. marketing-digital-ia
### Objetivo
Ferramentas de marketing utilizando IA generativa para criar campanhas, publicações e responder dúvidas.

### Backend (`marketing-digital-ia/backend`)
- **Principais rotas**
  - `/chat/` – interface com o assistente OpenAI
  - `/nova-campanha/` – gera campanhas de marketing
  - `/nova-publicacao/` e `/nova-publicacao/gerar-imagem` – cria publicações e imagens
  - `/publicos/` – cadastro em memória de públicos-alvo
  - `/conhecimento/perguntar-sara` – consulta à base de conhecimento
  - `/auth/login`, `/auth/validate` e `/usuarios` – autenticação e CRUD de usuários
- **Integrações**
  - Utiliza a API da OpenAI em `openai_service.py`
  - Busca contexto em embeddings FAISS para melhorar respostas
- **Banco de dados**
  - SQLite `marketing_ia.db` contendo usuários, criado em `database.py`
- **Lógica principal**
  - Autenticação via JWT
  - Geração de textos e imagens de marketing com prompts customizados

### Frontend (`marketing-digital-ia/frontend`)
- Contém apenas tela de login de exemplo; no uso real as rotas são consumidas pelo `frontend-erp`.

### Entrega ao usuário final
Permite planejar campanhas e publicações, conversar com a assistente Sara e gerenciar usuários do sistema.

## 3. producao
### Objetivo
Gerenciar processos de produção, convertendo arquivos de pedidos em DXF e realizando nesting para otimização de corte.

### Backend (`producao/backend/src`)
- **Principais rotas**
  - `POST /importar-xml` – identifica e processa arquivos XML ou DXT
  - `POST /gerar-lote-final` – cria o lote final em DXF
  - `POST /executar-nesting` – executa algoritmo de nesting e registra o resultado
  - `GET /listar-lotes` – lista lotes registrados
  - `GET /nestings` – lista otimizações realizadas
  - `GET /download-lote/{lote}` e `GET /download-nesting/{id}` – baixa arquivos
  - Cadastros auxiliares (`/chapas`, `/config-maquina`, `/config-ferramentas`, `/config-cortes`, `/config-layers`)
  - Gerenciamento de ocorrências (`/lotes-ocorrencias`, `/motivos-ocorrencias`, `/relatorio-ocorrencias`)
- **Integrações**
  - Biblioteca `ezdxf` para manipular arquivos DXF
  - Algoritmo de nesting implementado em `nesting.py`
- **Banco de dados**
  - SQLite `producao.db` com tabelas de lotes, nestings, chapas e ocorrências
- **Lógica principal**
  - Converte XML ou DXT em peças, gera DXFs e registra eventos de produção

### Frontend (`frontend-erp/src/modules/Producao`)
- **Telas disponíveis** (conforme `user-guide.md`)
  - Lotes, Apontamento, Apontamento Volume, Nesting, Chapas e Ocorrências
- **Fluxo principal**
  - Usuário importa arquivos, gera lote, executa nesting e baixa os resultados
  - Telas consomem as rotas do backend via Gateway
- **Regras**
  - Verificação de motivos ao gerar lotes de ocorrência e preenchimento de dados obrigatórios

### Entrega ao usuário final
Automatiza a geração de arquivos de corte e o controle de todo o processo de produção.

## 4. comercial-backend
### Objetivo
Registrar atendimentos comerciais, controlar tarefas do processo de venda e condições de pagamento.

### Backend (`comercial-backend`)
- **Principais rotas**
  - `GET /atendimentos/proximo-codigo` – gera código sequencial para novo atendimento
  - `POST /atendimentos` e CRUD completo para atendimentos
  - `GET /atendimentos/{id}/tarefas` e `PUT` correspondente – gerencia tarefas
  - `POST /condicoes-pagamento` e rotas `GET/PUT/DELETE` para condições de pagamento
  - `POST /contratos/assinar` – gera PDF simples com a assinatura
- **Integrações**
  - Leitura de orçamento PDF externo via `orcamento_pdf.parse_gabster_pdf`
- **Banco de dados**
  - SQLite `comercial.db` definido em `database.py`
- **Lógica principal**
  - Controle sequencial das etapas de atendimento e armazenamento de arquivos

### Frontend
Consumido pelo `frontend-erp` no módulo Comercial.

### Entrega ao usuário final
Oferece acompanhamento de vendas, tarefas e assinatura de contratos.

## 5. frontend-erp
### Objetivo
Aplicação web (React + Vite) que integra todos os módulos do ERP em uma única interface.

### Frontend (`frontend-erp/src`)
- **Estrutura**
  - Contexto de usuário em `UserContext.jsx`
  - Rotas protegidas definidas em `App.jsx`
  - Módulos: MarketingDigitalIA, Producao, Cadastros, Comercial e Formularios
- **Fluxo principal**
  - Usuário efetua login e, conforme as permissões, acessa as páginas listadas no Guia de Uso
  - As requisições são feitas com `fetchComAuth`, que insere o token e direciona para o Gateway (`VITE_GATEWAY_URL`)
- **Regras de validação**
  - Permissões do usuário controlam a exibição de menus e rotas

### Entrega ao usuário final
Interface unificada para operar Marketing Digital, Produção, Cadastros e Comercial em um único site.

---

Este manual resume a arquitetura de microsserviços do Radha ERP descrita em `docs/overview.md` e detalha as telas listadas no `docs/user-guide.md`. Cada módulo roda de forma independente (vide `start_services.sh`) e se comunica através do `backend-gateway`.
