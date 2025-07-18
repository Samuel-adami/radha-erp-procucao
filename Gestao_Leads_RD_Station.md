# Fluxo do Módulo Gestão de Leads com Integração RD Station

Este documento descreve passo a passo como o Radha ERP importa e gerencia leads vindos do RD Station. São listados os arquivos Python e de frontend envolvidos e as informações que trafegam entre os sistemas.

## Visão Geral

O módulo "Gestão de Leads" faz parte do backend `marketing-digital-ia` e é acessado pelo frontend em `frontend-erp`. Os leads são buscados diretamente na API do RD Station Marketing e armazenados em cache por 15 minutos. Informações adicionais podem ser salvas localmente na tabela `leads_info`.

## 1. Autenticação e Tokens RD Station

1. **Variáveis de ambiente** (definidas em `marketing-digital-ia/backend/.env.example`):
   - `RDSTATION_CLIENT_ID`
   - `RDSTATION_CLIENT_SECRET`
   - `RDSTATION_REDIRECT_URI`

2. **Rotas de autenticação** (`marketing-digital-ia/backend/routes/rd_auth.py`):
   - `GET /rd/login` – redireciona o usuário para a tela de autorização do RD Station.
   - `GET /rd/callback` – recebe o `code` de autorização e chama `exchange_code` para obter `access_token` e `refresh_token`.
   - `POST /rd/tokens` – permite inserir tokens manualmente via JSON.

3. **Persistência de tokens** (`marketing-digital-ia/backend/services/rdstation_auth_service.py`):
   - Função `save_tokens(account_id, access, refresh, expires_in)` grava ou atualiza os tokens na tabela `rdstation_tokens` (modelo `RDStationTokenDB` em `db_models.py`).
   - `get_access_token` obtém o token atual e renova usando `refresh` quando necessário.

## 2. Coleta de Leads do RD Station

Arquivo principal: `marketing-digital-ia/backend/services/rdstation_service.py`.

### 2.1 Funções

- `async _fetch_leads(page_size=100, max_pages=None)`
  - Faz chamadas paginadas à API `https://api.rd.services/platform/contacts`.
  - Envia header `Authorization: Bearer {access_token}`.
  - Lê o campo `contacts` (ou `items`) de cada resposta, acumulando os resultados.
- `async obter_leads(force_refresh=False, page_size=100, max_pages=None)`
  - Controla um cache em memória (_CACHE) válido por 15 minutos (`CACHE_TTL`).
  - Em caso de erro, devolve o último cache disponível.

### 2.2 Dados Esperados

De cada item retornado pela API são usados (ver `routes/leads.py`):
- `uuid` (id do lead)
- `name` (nome)
- `email`
- `traffic_source.source` (origem do tráfego)
- `created_at` ou `conversion_date` (data de conversão)
- `funnel_step` (estágio no funil)

Esses campos formam a lista exibida na interface.

## 3. Rotas de Gestão de Leads

Definidas em `marketing-digital-ia/backend/routes/leads.py`:

- `GET /leads/`
  - Requer permissão `marketing-ia/gestao-leads`.
  - Chama `obter_leads()` para buscar na RD Station e filtra por datas, campanha e estágio.
- `GET /leads/info/{rd_id}`
  - Retorna informações complementares salvas em `leads_info` por `obter_info` (`services/leads_info_service.py`).
- `POST /leads/info/{rd_id}`
  - Atualiza estágio, descrição, vendedor e opcionalmente converte o lead em cliente (chama o gateway para `/clientes` e `/comercial/atendimentos`).

## 4. Tabelas do Banco de Dados

`marketing-digital-ia/backend/db_models.py` define:
- `RDStationTokenDB` – armazena `access_token`, `refresh_token` e `expires_at`.
- `LeadInfoDB` – guarda estágio, descrição, arquivos enviados e vínculos com cliente/atendimento.

## 5. Frontend Relacionado

Os componentes React ficam em `frontend-erp/src/modules/MarketingDigitalIA`.

- `pages/GestaoLeads.jsx`
  - Chama `fetchComAuth('/leads/')` para listar leads (função `fetchComAuth` em `src/utils/fetchComAuth.js`).
  - Aplica filtros de data, campanha e estágio e exibe links para abrir o lead no RD Station ou convertê-lo.
- `pages/LeadConversao.jsx`
  - Utiliza `fetchComAuth('/leads/info/{id}')` para salvar a conversão do lead em cliente.
  - Envia formulário (FormData) com descrição, arquivos e dados do cliente.
- `index.jsx`
  - Registra as rotas `gestao-leads` e `gestao-leads/converter/:id` dentro do módulo de Marketing Digital IA.

## 6. Fluxo Resumido

1. Usuário acessa **Gestão de Leads** no frontend (`GestaoLeads.jsx`).
2. O frontend chama o endpoint `/leads/` via gateway (`fetchComAuth` acrescenta o prefixo `/marketing-ia`).
3. O gateway encaminha a requisição para `marketing-digital-ia/backend`.
4. A rota `/leads/` obtém um `access_token` válido (renovando se necessário) e chama `https://api.rd.services/platform/contacts` para trazer os leads.
5. Os leads retornados são convertidos no formato esperado e enviados de volta ao frontend.
6. Caso o usuário escolha **Converter** um lead, `LeadConversao.jsx` envia os dados para `/leads/info/{id}`; o backend pode criar um cliente e registrar um atendimento através do gateway, salvando tudo em `leads_info`.

## 7. Possíveis Problemas ao Carregar Leads

- **Tokens inválidos ou expirados** – verifique a tabela `rdstation_tokens` ou reexecute o fluxo `/rd/login`.
- **Variáveis de ambiente ausentes** – `RDSTATION_CLIENT_ID`, `RDSTATION_CLIENT_SECRET` e `RDSTATION_REDIRECT_URI` devem estar configuradas.
- **Falha de comunicação com a API da RD Station** – erros de rede são registrados e o serviço pode retornar dados em cache.

Com estes arquivos e passos é possível depurar por que os leads não estão aparecendo no Radha ERP.
