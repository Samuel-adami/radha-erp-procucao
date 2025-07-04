# Manual do Banco de Dados do Radha ERP

Este documento resume as tabelas atuais de cada módulo (agora utilizando **PostgreSQL** via SQLAlchemy) e orienta sobre a configuração das variáveis de ambiente para execução em produção ou desenvolvimento. Todas as aplicações carregam o arquivo `.env` na raiz com `python-dotenv` (`load_dotenv`).

## 1. backend-gateway
### Estrutura Atual (PostgreSQL)
- **Tabela `empresa`**
  - `id` SERIAL PRIMARY KEY
  - `codigo` TEXT
  - `razao_social` TEXT
  - `nome_fantasia` TEXT
  - `cnpj` TEXT
  - `inscricao_estadual` TEXT
  - `cep` TEXT
  - `rua` TEXT
  - `numero` TEXT
  - `complemento` TEXT
  - `bairro` TEXT
  - `cidade` TEXT
  - `estado` TEXT
  - `telefone1` TEXT
  - `telefone2` TEXT
  - `slogan` TEXT
  - `logo` BYTEA

## 2. marketing-digital-ia
### Estrutura Atual (PostgreSQL)
- **Tabela `users`**
  - `id` SERIAL PRIMARY KEY
  - `username` TEXT UNIQUE
  - `password` TEXT
  - `email` TEXT
  - `nome` TEXT
  - `cargo` TEXT
  - `permissoes` TEXT (JSON)
- **Outros dados**: índices FAISS em `embeddings/faiss_index` mantêm embeddings de documentos para a assistente Sara.

## 3. producao
### Estrutura Atual (PostgreSQL)
- **Tabelas**
  - `chapas` (id SERIAL PRIMARY KEY, possui_veio INTEGER, propriedade TEXT, espessura REAL, comprimento REAL, largura REAL)
  - `lotes` (id SERIAL PRIMARY KEY, pasta TEXT, criado_em TEXT)
  - `nestings` (id SERIAL PRIMARY KEY, lote TEXT, pasta_resultado TEXT, criado_em TEXT)

## 4. comercial-backend
### Estrutura Atual (PostgreSQL)
- **Tabela `atendimentos`**
  - `id` SERIAL PRIMARY KEY
  - `cliente` TEXT
  - `codigo` TEXT
  - `projetos` TEXT
  - `previsao_fechamento` TEXT
  - `temperatura` TEXT
  - `tem_especificador` INTEGER
  - `especificador_nome` TEXT
  - `rt_percent` REAL
  - `entrega_diferente` INTEGER
  - `historico` TEXT
  - `arquivos_json` TEXT
  - `procedencia` TEXT
  - `vendedor` TEXT
  - `telefone` TEXT
  - `email` TEXT
  - `rua` TEXT
  - `numero` TEXT
  - `complemento` TEXT
  - `bairro` TEXT
  - `cidade` TEXT
  - `estado` TEXT
  - `cep` TEXT
  - `data_cadastro` TEXT

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
- Ajustar o método `get_db_connection()` para usar a variável de ambiente `DATABASE_URL` (exemplo: `postgresql://radha_admin:Sma@xsisx@localhost:5432/producao`). Cada módulo deve definir seu esquema em `DATABASE_SCHEMA` para isolar as tabelas.
- Executar scripts de migração, convertendo os arquivos `.db` SQLite existentes para os bancos correspondentes no PostgreSQL.
- Remover dependência da variável `RADHA_DATA_DIR` para bancos.

---

## 2. Armazenamento de Arquivos em S3/MinIO

- Provisionar um único bucket (S3, MinIO ou compatível) para armazenar os arquivos de todos os módulos. Cada backend utilizará um prefixo próprio dentro desse bucket.
- Adicionar ao `.env` ou como variáveis de ambiente:
  - `OBJECT_STORAGE_ENDPOINT` (ex.: `https://nyc3.digitaloceanspaces.com`)
  - `OBJECT_STORAGE_ACCESS_KEY`
  - `OBJECT_STORAGE_SECRET_KEY`
  - `OBJECT_STORAGE_BUCKET` (ex.: `radha-prod-backend`)

  - `OBJECT_STORAGE_PREFIX` (ex.: `producao/`, `gateway/`, `comercial/`)

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

Modelos de variáveis de ambiente estão disponíveis em `.env.wsl.example` (desenvolvimento WSL) e `.env.prod.example` (produção).

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

## Implementação Realizada

Os módulos agora utilizam `DATABASE_URL` para conectar ao PostgreSQL e fazem upload de arquivos gerados para o bucket definido em `OBJECT_STORAGE_BUCKET`. Os scripts `start_services_wsl.sh` e `start_services_prod.sh` centralizam a configuração das portas (8040–8070) e garantem execução contínua via `systemd`. Exemplos de variáveis de ambiente estão disponíveis em `.env.wsl.example` e `.env.prod.example`.

