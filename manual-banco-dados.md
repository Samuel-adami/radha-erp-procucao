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

# Reestruturação do Radha ERP para produção web: PostgreSQL, Object Storage e Deploy 24/7

## Objetivo

Migrar o Radha ERP do modelo atual (banco SQLite + arquivos locais) para um ambiente de produção robusto com:

- Banco de dados **PostgreSQL**
- Armazenamento de arquivos em bucket S3/MinIO (object storage)
- Deploy contínuo para rodar como serviço web 24/7 no domínio próprio `radhadigital.com.br`

---

## 1. Migração do Banco de Dados para PostgreSQL

- Migrar todas as tabelas de cada módulo (`gateway`, `producao`, `comercial`, `marketing-digital-ia`) do SQLite para PostgreSQL.
- Adaptar as funções de conexão (substituir `sqlite3` por `psycopg2` ou `asyncpg`) em cada backend.
- Ajustar o método `get_db_connection()` para usar a variável de ambiente `DATABASE_URL` (exemplo: `postgresql://user:senha@localhost:5432/producao`).
- Executar scripts de migração, convertendo os arquivos `.db` SQLite existentes para os bancos correspondentes no PostgreSQL.
- Remover dependência da variável `RADHA_DATA_DIR` para bancos.

---

## 2. Armazenamento de Arquivos em S3/MinIO

- Provisionar um bucket (S3, MinIO ou compatível) para armazenar arquivos gerados nos módulos de produção (`lotes`, `nestings`, `lotes_ocorrencias`).
- Adicionar ao `.env` ou como variáveis de ambiente:
  - `OBJECT_STORAGE_ENDPOINT`
  - `OBJECT_STORAGE_ACCESS_KEY`
  - `OBJECT_STORAGE_SECRET_KEY`
  - `OBJECT_STORAGE_BUCKET`
- Instalar e usar um SDK Python (`boto3` para S3, `minio` para MinIO) nos backends relevantes.
- Alterar as tabelas (`lotes`, `nestings`, `lotes_ocorrencias`) para que as colunas que guardam caminho local de arquivo (`pasta`, `pasta_resultado`) passem a armazenar apenas a **chave do objeto** ou **URL** no storage.
- Implementar upload dos arquivos gerados (DXF, DXT, ZIP) diretamente para o bucket no momento da geração, salvando a referência no banco.
- Atualizar endpoints de download para buscar os arquivos do storage e streamar via `StreamingResponse` para o usuário.
- Implementar deleção de arquivos no storage ao excluir registros.
- Remover o uso de pastas locais para arquivos de saída.

---

## 3. Preparação para Produção Web (Deploy 24/7)

- Garantir que todos os backends podem rodar desacoplados de terminais, usando um serviço systemd ou outro process manager (gunicorn/uvicorn com supervisão).
- Manter o script `start_services.sh` atualizado, mas documentar a configuração de produção via `radha-erp.service` (unit do systemd), apontando para o domínio `radhadigital.com.br`.
- Certificar-se de que variáveis de ambiente estejam seguras (idealmente via arquivos `.env` ou gerenciador de segredos).
- Documentar instruções de deploy e manutenção no `admin-guide.md`, incluindo:
  - Setup do PostgreSQL
  - Setup do bucket S3/MinIO
  - Configuração do serviço systemd
  - Endpoints do frontend apontando para o backend no domínio
  - (Opcional: habilitar HTTPS no domínio via proxy reverso ou configuração cloud)

---

## 4. Validação e Testes

- Validar toda a operação dos módulos: criação e download de lotes, nestings, ocorrências, cadastros, geração de documentos.
- Testar upload, download e deleção de arquivos via storage.
- Validar a conexão e integridade do PostgreSQL para todos os módulos.
- Testar o deploy em ambiente de staging e em produção.
- Atualizar a documentação técnica conforme as mudanças.

---

## Notas e Particularidades

- Usar sempre nomes de arquivos, rotas e padrões do monorepo Radha ERP.
- Não alterar endpoints do frontend, mantendo a compatibilidade com o React (os downloads só mudam internamente).
- Garantir uso de streaming para arquivos grandes.
- Recomenda-se rodar o storage (MinIO) em container local ou usar bucket cloud com autenticação.
- Atenção à segurança: não expor secrets no repositório.

---

**Esta reestruturação deixa o Radha ERP pronto para produção web robusta e escalável, eliminando dependências locais e facilitando a gestão de dados e arquivos via cloud.**

