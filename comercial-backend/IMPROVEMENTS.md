# Arquitetura e Organização Refatorada - Backend Comercial

Este documento lista as principais melhorias aplicadas no refactoring do módulo **comercial-backend** e orienta como trabalhar a partir da nova estrutura.

## 1. Backup
- A pasta original foi copiada para **comercial-backend.bak/** para manter referência e permitir rollback seguro.

## 2. Nova Estrutura de Pastas
```
comercial-backend/
├─ app/
│  ├─ main.py            # Entrypoint do FastAPI
│  ├─ api/               # Routers e endpoints (ainda a ser distribuído)
│  ├─ core/              # Configurações gerais (ex: Pydantic Settings)
│  ├─ db/                # Sessão e conexão com o banco (SQLAlchemy)
│  ├─ services/          # Lógica de negócio e integrações externas
│  ├─ utils/             # Funções auxiliares (p.ex. safe_float, safe_int)
│  ├─ models/            # Models SQLAlchemy (declarative Base)
│  ├─ templates/         # Templates Jinja2
  └─ static/            # Recursos estáticos (ex: imagens)
├─ migrations/           # Scripts de migração de esquema SQL
├─ requirements.txt      # Dependências do projeto
└─ IMPROVEMENTS.md       # Este guia de mudanças
```

## 3. Principais Melhorias

- **Modularização**: o código foi distribuído em pacotes `app/db`, `app/services`, `app/utils`, `app/models`, separando responsabilidades.
- **Helpers**: extração das funções utilitárias (`safe_float`, `safe_int`, `TASKS`, `get_next_codigo`) para `app/utils/helpers.py`.
- **Módulos de serviço**: parsing, integração com Gabster e storage agora vivem em `app/services/*_service.py`.
- **Session DB**: `database.py` foi renomeado e movido para `app/db/session.py`.
- **Templating e estáticos**: `templates/` e `static/` passaram para dentro de `app/` para serem localizados a partir de `main.py`.

## 4. Como trabalhar a partir de agora

1. **Iniciar a aplicação**
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Adicionar novos endpoints**
   - Crie arquivos de roteamento em `app/api/` e importe-os em `app/main.py`.

3. **Novos serviços e integrações**
   - Coloque lógica de negócio ou chamadas externas em `app/services/`.

4. **Funções utilitárias**
   - Extraia helpers genéricos para `app/utils/`.

5. **Models e migrações**
   - Defina suas models SQLAlchemy em `app/models/`.
   - Mantenha scripts de migração em `migrations/` (ou migre para Alembic).

---
Refatoração focada em clarear responsabilidades, facilitar testes e preparar o código para crescer de forma organizada.
