# Visão Geral do Radha ERP

Radha ERP é um conjunto de serviços voltados para a gestão de marketing digital com IA, controle comercial e processos de produção. A solução está organizada em uma arquitetura de microsserviços escrita principalmente em **Python** e **JavaScript**.

## Estrutura do Repositório
- **backend-gateway** – API FastAPI que centraliza as chamadas para os demais módulos.
- **marketing-digital-ia** – módulo de marketing digital com IA (backend FastAPI e frontend React).
- **producao** – módulo de produção com backend FastAPI, rotinas de DXF e ferramentas de nesting.
- **comercial-backend** – backend responsável por registros comerciais e atendimentos a clientes.
- **frontend-erp** – aplicativo web principal (React + Vite) que integra todos os módulos via gateway.

Cada módulo possui seu próprio `requirements.txt` ou `package.json` para dependências.

## Ferramentas Utilizadas
- **Python 3.11+** com [FastAPI](https://fastapi.tiangolo.com) para as APIs.
- **Node.js** com [React](https://reactjs.org) e [Vite](https://vitejs.dev) para os frontends.
- **SQLite** como banco de dados padrão (arquivos `*.db` em `RADHA_DATA_DIR`).
- **OpenAI API** no módulo de Marketing Digital para geração de conteúdos.

## Programas Integrados
- Exportação e leitura de arquivos **DXF** e **XML** no módulo de Produção.
- Geração de relatórios de ocorrências e arquivos de Nesting para corte.
- Gerenciamento de públicos, campanhas e publicações com IA.
- Cadastro de empresas, clientes, fornecedores e usuários.

A pasta `rodar_ambientes.txt` contém comandos úteis para iniciar cada serviço separadamente. A automação em produção pode ser feita através do serviço `radha-erp.service` para o `systemd`.

## Organização de Pastas
```
radha-erp-monorepo/
├─ backend-gateway/        # API Gateway (FastAPI)
├─ comercial-backend/      # Gestão comercial e atendimentos
├─ marketing-digital-ia/
│  ├─ backend/             # FastAPI com rotas de IA e autenticação
│  └─ frontend/            # Interface React voltada para marketing
├─ producao/
│  ├─ backend/             # APIs de produção, DXF e nesting
│  └─ frontend/            # (opcional) interface específica de produção
├─ frontend-erp/           # Aplicativo principal em React
├─ start_services.sh       # Inicia todos os backends e o frontend
├─ radha-erp.service       # Exemplo de unidade systemd
└─ docs/                   # Documentação do projeto
```

## Execução dos Serviços
Para desenvolvimento local existem duas abordagens:

1. **Rodar individualmente** seguindo o arquivo `rodar_ambientes.txt` (cada serviço em um terminal diferente).
2. **Executar tudo de uma vez** com `./start_services.sh`, que inicia os quatro backends (gateway, marketing, produção e comercial) e o frontend principal.

Em produção o script `start_services.sh` é referenciado por `radha-erp.service`, permitindo que o `systemd` mantenha os processos ativos.

### Variáveis de Ambiente Principais
- `SECRET_KEY` – chave usada para assinar tokens de autenticação em todos os serviços.
- `RADHA_DATA_DIR` – caminho onde os bancos de dados SQLite serão criados (`*.db`).
- `RADHA_ADMIN_USER` e `RADHA_ADMIN_PASS` – usuário e senha criados no primeiro acesso ao sistema.

## Fluxo Geral
O **frontend-erp** se comunica apenas com o **backend-gateway** (porta 8010). Esse gateway repassa as requisições para os backends de marketing, produção e comercial de acordo com o prefixo da rota. Cada backend utiliza SQLite para persistir dados localmente. A infraestrutura está preparada para uso com contêineres ou serviços em nuvem, bastando definir as variáveis de ambiente e portas desejadas.

## Próximos Passos
- Leia o [Guia de Uso](user-guide.md) para entender as telas disponíveis.
- Consulte o [Guia de Manutenção](admin-guide.md) para detalhes de instalação e logs.
- Utilize o script `update_github.sh` para versionar e publicar alterações no repositório.

