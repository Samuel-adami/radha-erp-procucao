# Manual do Banco de Dados do Radha ERP

Este documento resume as tabelas atuais de cada módulo (utilizando SQLite) e orienta sobre a migração para PostgreSQL em um servidor VPS.

## 1. backend-gateway
### Estrutura Atual (SQLite)
- **Arquivo**: `gateway.db`
- **Tabela `empresa`**
  - `id` INTEGER PRIMARY KEY AUTOINCREMENT
  - `codigo` TEXT
  - `razao_social` TEXT
  - `nome_fantasia` TEXT
  - `cnpj` TEXT
  - `inscricao_estadual` TEXT
  - `cep` TEXT
  - `rua` TEXT
  - `numero` TEXT
  - `bairro` TEXT
  - `cidade` TEXT
  - `estado` TEXT
  - `telefone1` TEXT
  - `telefone2` TEXT
  - `slogan` TEXT
  - `logo` BLOB

## 2. marketing-digital-ia
### Estrutura Atual (SQLite)
- **Arquivo**: `marketing_ia.db`
- **Tabela `users`**
  - `id` INTEGER PRIMARY KEY AUTOINCREMENT
  - `username` TEXT UNIQUE
  - `password` TEXT
  - `email` TEXT
  - `nome` TEXT
  - `cargo` TEXT
  - `permissoes` TEXT (JSON)
- **Outros dados**: índices FAISS em `embeddings/faiss_index` mantêm embeddings de documentos para a assistente Sara.

## 3. producao
### Estrutura Atual (SQLite)
- **Arquivo**: `producao.db`
- **Tabelas**
  - `config_maquina` (id, dados)
  - `config_ferramentas` (id, dados)
  - `config_cortes` (id, dados)
  - `config_layers` (id, dados)
  - `chapas` (id, possui_veio, propriedade, espessura, comprimento, largura)
  - `lotes` (id, pasta, criado_em)
  - `nestings` (id, lote, pasta_resultado, criado_em)
  - `lotes_ocorrencias` (id, lote, pacote, oc_numero, pasta, criado_em)
  - `motivos_ocorrencia` (id, codigo, descricao, tipo, setor)
  - `ocorrencias_pecas` (id, oc_id, peca_id, descricao_peca, motivo_id)

## 4. comercial-backend
### Estrutura Atual (SQLite)
- **Arquivo**: `comercial.db`
- **Tabelas**
  - `atendimentos` (id, cliente, codigo, projetos, previsao_fechamento, temperatura, tem_especificador, especificador_nome, rt_percent, entrega_diferente, historico, arquivos_json, procedencia, vendedor, telefone, email, rua, numero, complemento, bairro, cidade, estado, cep, data_cadastro)
  - `atendimento_tarefas` (id, atendimento_id, nome, concluida, dados, data_execucao)
  - `condicoes_pagamento` (id, nome, numero_parcelas, juros_parcela, dias_vencimento, ativa, parcelas_json)
  - `templates` (id, tipo, titulo, campos_json)

## 5. frontend-erp
Este módulo é somente frontend e não possui banco próprio. Todas as chamadas são feitas ao Gateway e, por consequência, aos backends acima.

---

## Migração para PostgreSQL na VPS
1. **Instalação do servidor**: instale PostgreSQL na VPS e crie bancos separados (ou schemas) para `gateway`, `marketing`, `producao` e `comercial`.
2. **Criação das tabelas**: use o `sqlite3` para exportar o schema atual (ex.: `sqlite3 gateway.db .schema > gateway.sql`) e adapte os tipos conforme necessário. Em seguida, execute os scripts no PostgreSQL usando `psql`.
3. **Dependências dos serviços**: instale `psycopg2` (ou `asyncpg`) em cada backend e substitua o módulo `sqlite3` pelas funções de conexão ao PostgreSQL.
4. **Variáveis de ambiente**: defina URLs de conexão como `DATABASE_URL=postgresql://user:senha@localhost:5432/gateway` (ajustando para cada serviço). Remova ou ignore `RADHA_DATA_DIR`.
5. **Ajustes de código**: modifique `get_db_connection()` em cada `database.py` para abrir uma conexão PostgreSQL. Mantenha a lógica de criação de tabelas (`CREATE TABLE IF NOT EXISTS`) ou utilize migrações específicas.
6. **Importação dos dados**: utilize `sqlite3 <db> .dump` para gerar scripts SQL e importe-os via `psql`. Revise tipos (`TEXT` → `TEXT`, `REAL` → `DOUBLE PRECISION`, `INTEGER` → `INTEGER`).
7. **Teste nos módulos**: após a migração, execute `start_services.sh` (ou serviços individuais) e verifique se as APIs continuam respondendo corretamente usando o novo banco.

Com essas etapas, o Radha ERP passará a persistir os dados em PostgreSQL, mantendo a mesma estrutura de tabelas descrita acima.
