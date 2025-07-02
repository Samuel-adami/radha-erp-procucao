# Radha ERP Monorepo

Este repositório agrupa todos os serviços que compõem o Radha ERP. A solução contempla módulos de marketing digital com IA, controle comercial e ferramentas de produção.

## Conteúdo
- [Visão Geral](docs/overview.md)
- [Guia de Uso](docs/user-guide.md)
- [Guia de Manutenção](docs/admin-guide.md)

## Requisitos Básicos
Instale Python 3, Node.js e npm. Em sistemas baseados em Debian:
```bash
sudo apt install python3 python3-venv nodejs npm
```

## Scripts Principais
- `update_github.sh` – adiciona commits locais e envia ao GitHub.
- `start_services.sh` – inicia todos os backends e o frontend em modo de desenvolvimento.
- `rodar_ambientes.txt` – exemplos de comandos para executar cada módulo separadamente.

## Iniciando o Sistema
1. Ajuste as variáveis de ambiente desejadas (`RADHA_ADMIN_USER`, `RADHA_ADMIN_PASS`, `SECRET_KEY`, `RADHA_DATA_DIR`). Para importar orçamentos Gabster via API defina também `GABSTER_API_USER` e `GABSTER_API_KEY`.
2. Execute `./start_services.sh` para rodar todos os serviços.
3. Edite `frontend-erp/.env` definindo `VITE_GATEWAY_URL=http://212.85.13.74:8010`.
4. Acesse `http://212.85.13.74:3005` no navegador e faça login com o usuário configurado (padrão `admin`/`admin`).

O serviço `radha-erp.service` é um exemplo de unidade systemd para produção.

## Suporte
Caso o navegador exiba apenas uma tela de carregamento, verifique se as APIs estão em execução e se as portas 8010, 8015, 8020 e 8030 não estão ocupadas. Consulte os arquivos de log de cada serviço para mais detalhes.

