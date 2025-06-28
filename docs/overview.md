# Visão Geral do Radha ERP

Radha ERP é um conjunto de serviços voltados para a gestão de processos de marketing, comercial e produção.
A solução segue uma arquitetura de microsserviços em Python e JavaScript.

## Estrutura do Repositório
- **backend-gateway** – API FastAPI que centraliza as chamadas para os demais módulos.
- **marketing-digital-ia** – módulo de marketing digital com backend FastAPI e frontend React.
- **producao** – módulo de produção, contendo backend FastAPI e ferramentas para geração de DXF e nesting.
- **comercial-backend** – módulo backend que registra atendimentos de clientes.
- **frontend-erp** – aplicativo web principal em React que integra todos os módulos.

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

