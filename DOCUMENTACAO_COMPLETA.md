# Documentação Completa do Radha ERP

Este documento detalha a arquitetura e os fluxos de cada módulo do projeto. Serve como referência para desenvolvedores e operadores.

## 1. Rotas por Módulo

### 1.1 Gateway (`backend-gateway/main.py`)

| Método | Caminho | Arquivo | Autenticação |
|-------|---------|---------|--------------|
|GET|`/`|main.py|Não|
|POST/GET/PUT/DELETE|`/marketing-ia/{path}`|main.py|Repassa token|
|POST/GET/PUT/DELETE|`/producao/{path}`|main.py|Repassa token|
|POST/GET/PUT/DELETE|`/comercial/{path}`|main.py|Repassa token|
|POST|`/auth/login`|main.py|Sem token|
|GET|`/auth/validate`|main.py|Bearer JWT|
|CRUD|`/empresa`|main.py|Bearer JWT|
|CRUD|`/clientes`|main.py|Bearer JWT|
|CRUD|`/fornecedores`|main.py|Bearer JWT|
|CRUD|`/usuarios`|main.py|Bearer JWT|

As rotas que repassam para outros serviços enviam headers e corpo originais. Exemplo de retorno para `GET /clientes`:
```json
{ "clientes": [{"id":1,"nome":"Exemplo"}] }
```

### 1.2 Marketing Digital IA (`marketing-digital-ia/backend/routes/`)

Prefixos definidos nos arquivos:

- `chat.py` – `POST /chat/` recebe `{mensagem, id_assistant}` e retorna `{resposta}`. Usa `verificar_autenticacao` para cargos **Diretoria**, **Marketing**, **Diretor**, **Comercial**, **Logística** e **admin**.
- `campanha.py` – `POST /nova-campanha/` recebe dados de campanha e devolve `{campanha}`.
- `publicacao.py` – `POST /nova-publicacao/` e `POST /nova-publicacao/gerar-imagem`.
- `publicos.py` – `POST /publicos/` e `GET /publicos/` (apenas Marketing/Diretoria).
- `conhecimento.py` – `POST /conhecimento/perguntar-sara` utiliza `OpenAI().chat.completions.create`.
- `auth.py` – `POST /auth/login` e `GET /auth/validate`.
- `usuarios.py` – `GET/POST /usuarios/`, `PUT/DELETE /usuarios/{id}`.

Todas retornam JSON, por exemplo `{"status":"validado","usuario":{...}}` em `/auth/validate`.

### 1.3 Produção (`producao/backend/src/api.py`)

Principais rotas:

- `POST /importar-xml` – upload de XML/DXT (retorna `{pacotes:[...]}`).
  - **Exemplo de requisição**:
```bash
curl -X POST https://erp.radhadigital.com.br/producao/importar-xml \
     -H "Authorization: Bearer <TOKEN>" \
     -F "files=@pedido.xml" \
     -F "files=@pecas.dxt"
```
- `POST /gerar-lote-final` – gera lote e salva `lotes/{nome}.zip` (campo `lotes.obj_key`).
- `GET /carregar-lote-final?pasta=...`
- `POST /executar-nesting`, `POST /nesting-preview`, `POST /executar-nesting-final` – gera `nestings/{lote}.zip` (tabela `nestings.obj_key`).
- `GET /listar-lotes` – retorna `{ "lotes": ["producao/lotes/Lote_001.zip", ...] }`.
- `GET /nestings` – listagens de otimizações.
- `GET /download-lote/{lote}` e `GET /download-nesting/{id}` – downloads via streaming.
- `POST /remover-nesting` e `POST /excluir-lote` – remoções.
- Cadastros auxiliares: `GET/POST /config-maquina`, `/config-ferramentas`, `/config-cortes`, `/config-layers`.
- `GET/POST/DELETE /chapas`.
- Ocorrências: `GET /lotes-ocorrencias`, `POST /lotes-ocorrencias`, `DELETE /lotes-ocorrencias/{id}`, `GET/POST/DELETE /motivos-ocorrencias`, `GET /relatorio-ocorrencias`.

Todas as rotas exigem token via Gateway. Retornos são JSON ou `StreamingResponse` para downloads.

### 1.4 Comercial (`comercial-backend/main.py`)

- `GET /` – teste do serviço.
- `GET /atendimentos/proximo-codigo`.
- `POST /leitor-orcamento-gabster` – usa `gabster_api.list_orcamento_cliente_item`.
- `POST /gabster-projeto` – usa `gabster_api.get_projeto` e `parse_gabster_projeto`.
- `POST /leitor-orcamento-promob`.
- CRUD completo de `/atendimentos` e `/atendimentos/{id}/tarefas`.
- CRUD de `/condicoes-pagamento` e `/templates`.
- `POST /contratos/assinar` – gera PDF com assinatura.

Todas são protegidas por token via Gateway.

## 2. Modelos de Dados

### 2.1 Gateway (`backend-gateway/models.py`)

- **Empresa** – tabela `empresa` com colunas `id`, `codigo`, `razao_social`, `nome_fantasia`, `cnpj`, etc.
- **Cliente** – tabela `clientes` (`id`, `codigo`, `nome`, `documento`, ...).
- **Fornecedor** – tabela `fornecedores` (`id`, `nome`, `contato`, ...).

Usadas pelas rotas `/empresa`, `/clientes` e `/fornecedores`.

### 2.2 Marketing Digital IA (`marketing-digital-ia/backend/db_models.py`)

- **User** – tabela `users` com `id`, `username`, `password`, `email`, `nome`, `cargo`, `permissoes`.

Manipulado em `/usuarios` e autenticação (`/auth/login`, `/auth/validate`).

### 2.3 Produção (`producao/backend/src/models.py`)

- **Chapa** – tabela `chapas` (`possui_veio`, `propriedade`, `espessura`, `comprimento`, `largura`).
- **Lote** – tabela `lotes` (`obj_key`, `criado_em`).
- **Nesting** – tabela `nestings` (`lote`, `obj_key`, `criado_em`).
- **LoteOcorrencia** – tabela `lotes_ocorrencias` (`lote`, `pacote`, `oc_numero`, `obj_key`).
- **OcorrenciaPeca** – tabela `ocorrencias_pecas` (`oc_id`, `peca_id`, `descricao_peca`, `motivo_id`).
- **MotivoOcorrencia** – tabela `motivos_ocorrencia` (`codigo`, `descricao`, `tipo`, `setor`).

Relacionadas às rotas de produção descritas na seção anterior.

#### Diagrama ERD (Produção)

![ERD Produção](erd_producao.png)


### 2.4 Comercial (`comercial-backend/models.py`)

- **Atendimento** – tabela `atendimentos` com diversos campos do fluxo de vendas.
- **AtendimentoTarefa** – tabela `atendimento_tarefas` (tarefas por atendimento).
- **CondicaoPagamento** – tabela `condicoes_pagamento` (parcelas e juros).
- **Template** – tabela `templates` (tipo, título, campos).
- **ProjetoItem** – tabela `projeto_itens` (itens de projeto dentro de tarefas).
- **GabsterProjetoItem** – tabela `gabster_projeto_itens` para itens importados da API.
  Os registros são gravados ao atualizar uma tarefa de projeto com `programa` igual a `Gabster`.

Esses modelos aparecem nas rotas de `/atendimentos`, `/condicoes-pagamento` e `/templates`.

## 3. Integrações Externas

- **Gabster (Comercial)**: `gabster_api.py` implementa `get_projeto` e `list_orcamento_cliente_item` usados em `/gabster-projeto` e `/leitor-orcamento-gabster`【F:comercial-backend/gabster_api.py†L1-L31】.
- **OpenAI (Marketing)**: `services/openai_service.py` usa `AsyncOpenAI` e `openai.ChatCompletion` nas funções `gerar_resposta` e `gerar_imagem`【F:marketing-digital-ia/backend/services/openai_service.py†L18-L56】.
- **S3 (Produção)**: `storage.py` usa `boto3` para `upload_file`, `download_file` e `delete_file` com prefixo configurável【F:producao/backend/src/storage.py†L7-L32】. Exemplo de chave: `producao/lotes/Lote_123.zip`.

## 4. Armazenamento de Arquivos

- **Produção**: envia ZIPs de lotes e nestings para o bucket no prefixo `producao/`. As chaves são gravadas em `lotes.obj_key`, `nestings.obj_key` e `lotes_ocorrencias.obj_key`.
- **Marketing**: não armazena arquivos no bucket (apenas comunica com OpenAI).
- **Comercial**: atualmente não utiliza S3; PDFs e XMLs são processados em memória.
- **Gateway**: não faz uploads, apenas acessa banco.

## 5. Frontend

As telas React ficam em `frontend-erp/src/modules`.

- **Cadastros**: componentes `DadosEmpresa.jsx`, `Clientes.jsx`, `Fornecedores.jsx`, `Usuarios.jsx`, `CondicaoPagamento.jsx` e sub‑listas em `Lista*.jsx`.
- **Comercial**: páginas em `pages/Atendimentos.jsx`, `AtendimentoForm.jsx`, `Negociacao.jsx`, etc.
- **Marketing Digital IA**: `pages/Chat.jsx`, `NovaCampanha.jsx`, `NovaPublicacao.jsx`, `PublicosAlvo.jsx`.
- **Produção**: componentes diversos em `components/`, como `ImportarXML.jsx`, `Nesting.jsx`, `LotesOcorrencia.jsx` e `nesting-view/VisualizacaoNesting.tsx`. Na tela `Nesting.jsx` o campo *Pasta do Lote-final* é preenchido via `GET /listar-lotes`, permitindo escolher o lote que será otimizado.

Todas usam `fetchComAuth` para consumir a API. Essa função injeta o JWT armazenado e monta as URLs apontando para o Gateway conforme o prefixo【F:frontend-erp/src/utils/fetchComAuth.js†L1-L37】.

## 6. Fluxos Operacionais

### 6.1 Produção
1. Importar XML/DXT (`/producao/importar-xml`).
2. Gerar lote final (`/producao/gerar-lote-final`) – grava `lotes/{lote}.zip`.
3. Executar nesting (`/producao/executar-nesting` → `/producao/executar-nesting-final`).
4. Download do resultado via `/producao/download-nesting/{id}`.

### 6.2 Comercial
1. Criar atendimento (`/comercial/atendimentos`).
2. Buscar orçamentos na Gabster (`/comercial/leitor-orcamento-gabster`).
3. Obter dados de projeto (`/comercial/gabster-projeto`).
4. Registrar tarefas e itens de projeto.

### 6.3 Marketing
1. Login (`/auth/login`).
2. Usar `/chat/` ou `/nova-campanha/` para geração de conteúdo.
3. Criar publicações e públicos por `/nova-publicacao/` e `/publicos/`.

## 7. Ambiente de Produção

Arquivos de serviço systemd estão descritos em `systemd_service_configuration.md`. Exemplo do backend de Produção:
```ini
[Service]
User=samuel
WorkingDirectory=/home/samuel/radha-erp-procucao/producao/backend/src
ExecStart=/home/samuel/radha-erp-procucao/venv/bin/uvicorn api:app --host 0.0.0.0 --port 8060
```

O Nginx direciona requisições para o Gateway e para o frontend conforme `nginx_configuration.md`【F:nginx_configuration.md†L1-L63】.

**Exemplo de fluxo HTTP – Nesting**
1. O usuário faz `POST https://erp.radhadigital.com.br/producao/importar-xml` enviando os arquivos XML/DXT.
2. O Nginx direciona a requisição para `http://127.0.0.1:8040/producao/importar-xml`.
3. O Gateway repassa para `http://127.0.0.1:8060/importar-xml`, que responde com `{"pacotes": [...]}`.
4. Em seguida o frontend envia `POST /producao/gerar-lote-final` para o Gateway, que grava `producao/lotes/Lote_001.zip` em S3.
5. A tela `/producao` executa `GET /producao/listar-lotes` para preencher o campo **Pasta do Lote-final**. O operador escolhe a pasta desejada na lista.
6. Com a pasta selecionada (`pasta_lote`), `POST /producao/nesting-preview` gera o arranjo das chapas.
7. A etapa final `POST /producao/executar-nesting-final` produz `producao/nestings/Lote_001.zip` e registra na tabela `nestings`.
8. O download ocorre via `GET /producao/download-nesting/{id}` e o Gateway faz streaming do arquivo do bucket até o navegador.

---
## 8. Variáveis de Ambiente

Os arquivos `.env.example` em cada módulo definem as variáveis necessárias.

### 8.1 Gateway

```ini
DATABASE_URL=
DATABASE_SCHEMA=
SECRET_KEY=
RADHA_DATA_DIR=
OBJECT_STORAGE_ENDPOINT=
OBJECT_STORAGE_ACCESS_KEY=
OBJECT_STORAGE_SECRET_KEY=
OBJECT_STORAGE_BUCKET=
OBJECT_STORAGE_REGION=
OBJECT_STORAGE_PREFIX=
MARKETING_IA_BACKEND_URL=
PRODUCAO_BACKEND_URL=
COMERCIAL_BACKEND_URL=
RADHA_ADMIN_USER=  # opcional
RADHA_ADMIN_PASS=  # opcional
```

### 8.2 Marketing Digital IA

```ini
DATABASE_URL=
DATABASE_SCHEMA=
SECRET_KEY=
RADHA_DATA_DIR=
OBJECT_STORAGE_ENDPOINT=
OBJECT_STORAGE_ACCESS_KEY=
OBJECT_STORAGE_SECRET_KEY=
OBJECT_STORAGE_BUCKET=
OBJECT_STORAGE_REGION=
OBJECT_STORAGE_PREFIX=
OPENAI_API_KEY=
OPENAI_API_BASE=
```

### 8.3 Produção

```ini
DATABASE_URL=
DATABASE_SCHEMA=
SECRET_KEY=
RADHA_DATA_DIR=
OBJECT_STORAGE_ENDPOINT=
OBJECT_STORAGE_ACCESS_KEY=
OBJECT_STORAGE_SECRET_KEY=
OBJECT_STORAGE_BUCKET=
OBJECT_STORAGE_REGION=
OBJECT_STORAGE_PREFIX=
```

### 8.4 Comercial

```ini
DATABASE_URL=
DATABASE_SCHEMA=
SECRET_KEY=
RADHA_DATA_DIR=
OBJECT_STORAGE_ENDPOINT=
OBJECT_STORAGE_ACCESS_KEY=
OBJECT_STORAGE_SECRET_KEY=
OBJECT_STORAGE_BUCKET=
OBJECT_STORAGE_REGION=
OBJECT_STORAGE_PREFIX=
GABSTER_API_USER=
GABSTER_API_KEY=
```

### 8.5 Frontend

```ini
VITE_GATEWAY_URL=
```

As variáveis sem comentário são obrigatórias para execução de cada backend.

## 9. Permissões por Rota

| Módulo | Caminho | Cargos requeridos |
|--------|---------|-------------------|
| Marketing | `/chat/` | Diretoria, Marketing, Diretor, Comercial, Logística, admin |
| Marketing | `/nova-campanha/` e `/nova-publicacao/` | Marketing, Diretoria |
| Marketing | `/publicos/` | Marketing, Diretoria |
| Marketing | `/conhecimento/perguntar-sara` | Diretoria |
| Outros módulos | Demais rotas | Qualquer usuário autenticado |
