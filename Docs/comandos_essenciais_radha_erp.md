# Comandos Essenciais e Funções — Radha ERP (Ubuntu VPS)

> **Este documento traz todos os comandos e funções usados na implantação, troubleshooting e rotina do Radha ERP em ambiente de produção (Ubuntu).**

---

## 🟩 Atualização e Instalação de Pacotes

```bash
# Atualizar o sistema
debian/ubuntu:
sudo apt update
sudo apt upgrade -y

# Instalar pacotes básicos
sudo apt install git curl build-essential -y
sudo apt install python3.11 python3.11-venv python3.11-dev -y
sudo apt install nginx -y
sudo apt install nodejs npm -y
```

**Função:** Mantém sistema atualizado e instala dependências essenciais para o ambiente do Radha ERP.

---

## 🟩 Clonar e Atualizar o Repositório

```bash
# Clonar o projeto
cd ~
git clone git@github.com:SEU_USUARIO/radha-erp-producao.git

# Atualizar repo
cd ~/radha-erp-producao
git pull origin main
```
git add <nome_do_arquivo>
git commit -m "Atualizações feitas na VPS"
git push origin main


**Função:** Baixar ou atualizar o código-fonte do Radha ERP localmente.

---

## 🟩 Python Virtualenv

```bash
# Criar o ambiente virtual
python3.11 -m venv venv

# Ativar ambiente virtual
source venv/bin/activate
source ../venv/bin/activate
source ../../venv/bin/activate
source ../../../venv/bin/activate

# Sair do ambiente virtual
deactivate
```

**Função:** Isolar dependências do projeto e garantir ambiente controlado.

---

## Configuração do bash

``` bash
nano ~/.bashrc
source ~/.bashrc

```
---

## 🟩 Instalar Dependências Python (Backend)

```bash
pip install -r requirements.txt
# Ou instalar individualmente:
pip install fastapi uvicorn pydantic httpx python-dotenv openai Pillow requests python-jose passlib[bcrypt] sqlalchemy psycopg2-binary boto3 sentence-transformers==2.2.2 huggingface_hub<0.15 transformers==4.31.0 faiss-cpu torch==2.0.1 torchvision==0.15.2
```

**Função:** Instala pacotes obrigatórios para funcionamento dos serviços backend do Radha ERP.

---

## 🟩 Gerenciar Serviços com systemctl (Systemd)

```bash
# Ver status do serviço
sudo systemctl status NOME_DO_SERVICO
sudo systemctl status radha-producao-backend
sudo systemctl status radha-comercial-backend
sudo systemctl status radha-marketing-backend
sudo systemctl status radha-gateway-backend
sudo systemctl status radha-finance-backend
sudo systemctl status radha-frontend

# Iniciar serviço
sudo systemctl start NOME_DO_SERVICO

# Parar serviço
sudo systemctl stop NOME_DO_SERVICO

# Reiniciar serviço
sudo systemctl restart NOME_DO_SERVICO

# Ativar para iniciar com o sistema
sudo systemctl enable NOME_DO_SERVICO

# Desativar auto inicialização
sudo systemctl disable NOME_DO_SERVICO

# Ver logs do serviço em tempo real
sudo journalctl -u radha-producao-backend -f
sudo journalctl -u radha-comercial-backend -f
sudo journalctl -u radha-marketing-backend -f
sudo journalctl -u radha-gateway-backend -f
sudo journalctl -u radha-finance-backend -f
sudo journalctl -u radha-frontend -f

# Ver logs do serviço
sudo journalctl -u NOME_DO_SERVICO -n 40 --no-pager
sudo journalctl -u radha-producao-backend -n 40 --no-pager
sudo journalctl -u radha-comercial-backend -n 40 --no-pager
sudo journalctl -u radha-marketing-backend -n 40 --no-pager
sudo journalctl -u radha-gateway-backend -n 40 --no-pager
sudo journalctl -u radha-finance-backend -n 40 --no-pager
sudo journalctl -u radha-frontend -n 40 --no-pager

# Recarregar serviços após editar arquivo systemd
sudo systemctl daemon-reload

# Comandos atualização completa
sudo systemctl daemon-reload
sudo systemctl restart radha-producao-backend
sudo systemctl restart radha-marketing-backend
sudo systemctl restart radha-comercial-backend
sudo systemctl restart radha-gateway-backend
sudo systemctl restart radha-finance-backend
sudo systemctl restart radha-frontend
sudo systemctl restart nginx
```
**Função:** Gerencia execução dos serviços backend/frontend no modo produção. Facilitam controle, restart automático e logs centralizados.

---

## 🟩 NGINX: Comandos e Testes

```bash
# Testar sintaxe do nginx
sudo nginx -t

# Reiniciar nginx
sudo systemctl restart nginx

# Recarregar nginx
sudo systemctl reload nginx

# Ver status nginx
sudo systemctl status nginx

# Ver arquivos de configuração nginx
ls /etc/nginx/sites-available/
ls /etc/nginx/sites-enabled/

# Editar arquivos nginx
sudo nano /etc/nginx/sites-available/NOME_DO_ARQUIVO
```

**Função:** Gerencia o reverse proxy, HTTPS, balanceamento e rotas públicas dos serviços.

---

## 🟩 Manipular Portas e Processos

```bash
# Ver processos usando uma porta específica
sudo lsof -i :PORTA

# Matar processo por comando (exemplo uvicorn ou npm)
sudo pkill -f "uvicorn main:app"
sudo pkill -f "npm run dev"
```

**Função:** Libera portas presas e resolve conflitos de serviços antigos ou processos travados.

---

## 🟩 Banco de Dados PostgreSQL

```bash
# Acessar o PostgreSQL
sudo -u postgres psql producao

# Listar usuários (roles)
\du

# Alterar senha de usuário
ALTER USER NOME_USUARIO WITH PASSWORD 'NOVA_SENHA';

# Criar um Schema
CREATE SCHEMA nome_do_schema;

# Excluir (Drop) um Schema (e tudo que estiver dentro)
DROP SCHEMA nome_do_schema CASCADE;

# Ver Schemas Existentes
\dn

# Criar uma Tabela
CREATE TABLE nome_do_schema.nome_da_tabela (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100)
);

# Excluir (Drop) uma Tabela
DROP TABLE nome_da_tabela;
DROP TABLE nome_do_schema.nome_da_tabela;

# Adicionar Coluna em uma Tabela
ALTER TABLE nome_da_tabela ADD COLUMN nova_coluna VARCHAR(50);

# Excluir Coluna de uma Tabela
 ALTER TABLE nome_da_tabela DROP COLUMN nome_coluna;

# Listar Todas as Tabelas do Schema Atual
 \dt

# Para listar todas as tabelas de um schema específico:
 \dt nome_do_schema.*

# Visualizar a Estrutura de uma Tabela
 \d nome_da_tabela

# Visualizar os Dados de uma Tabela
 SELECT * FROM nome_da_tabela;

# Mudar de schema (setar search_path):
SET search_path TO nome_do_schema;

# Sair do psql
\q
```

**Função:** Administração básica do banco PostgreSQL (usuário, senha, permissões).

---

## 🟩 Atualização do esquema

Caso o banco tenha sido criado com versões antigas do backend, execute a migração
abaixo para renomear as colunas `pasta` e `pasta_resultado` para `obj_key`.

```bash
sudo -u postgres psql -d producao -f producao/backend/migrations/002_obj_key.sql
```

Após rodar o script, os endpoints que manipulam lotes e nestings conseguem
encontrar os arquivos `.zip` normalmente.

Caso o banco tenha sido criado antes da versão que inclui a coluna `tarefa_id`
em `gabster_projeto_itens`, execute a migração abaixo para adicioná-la:

```bash
sudo -u postgres psql -d producao -f comercial-backend/migrations/001_alter_gabster_projeto_itens.sql
```

---

## 🟩 Docker (Para MinIO/S3 Local)

```bash
# Rodar MinIO com Docker
# (lembre da senha mínima de 8 caracteres)
docker run -d -p 9000:9000 -p 9001:9001 --name minio \
  -e "MINIO_ROOT_USER=admin" \
  -e "MINIO_ROOT_PASSWORD=umaSenhaForte" \
  minio/minio server /data --console-address ":9001"

# Ver containers rodando
docker ps

# Parar container
docker stop minio

# Remover container
docker rm minio

# Ver logs do container
docker logs minio
```

**Função:** Subir storage local ou externo para testes de arquivos.

---

## 🟩 Certbot/Let's Encrypt (HTTPS)

```bash
# Gerar/renovar certificado
sudo certbot --nginx -d erp.radhadigital.com.br

# Testar renovação
sudo certbot renew --dry-run

# Ver certificados
sudo certbot certificates

# Ver logs do certbot
sudo tail -n 40 /var/log/letsencrypt/letsencrypt.log
```

**Função:** Gerar e renovar certificados SSL para HTTPS seguro.

---

## 🟩 Cron (Agendar Backup)

```bash
# Editar cron para backups automáticos
sudo nano /etc/crontab

# Exemplo de linha para backup diário às 2h
0 2 * * * samuel /usr/local/bin/backup_postgres.sh
```

---

## 🟩 Scripts Customizados (Backup, MinIO, Logs)

```bash
# Dar permissão de execução
sudo chmod +x /CAMINHO/DO/SCRIPT.sh

# Executar script manualmente
bash /CAMINHO/DO/SCRIPT.sh
```

**Função:** Automatizar backups, rotinas e testes.

---

## 🟩 Comandos Úteis Diversos

```bash
# Verificar variáveis de ambiente .env
cat .env

# Ver endereço IP da máquina
hostname -I

# Sair de terminal (ou venv)
exit
```

---

## 📌 Dicas Finais

- Sempre teste configurações do nginx com `nginx -t` **antes** de reiniciar o serviço.
- Para cada serviço systemd, monitore logs com `journalctl` se der erro inesperado.
- Use sempre **systemctl** para subir/parar/reiniciar qualquer serviço do Radha ERP — nunca rode backends manualmente em produção.
- Se precisar liberar porta, sempre mate o processo antigo antes de tentar reiniciar o serviço.
- Documente sempre o que muda nos scripts, configs e .env para não perder rastreabilidade.

---

## 🟩 OAuth RD Station — Gerar novo authorization code

```bash
# Use o script que automatiza todo o fluxo (OAuth, login e fetch de leads):
./scripts/fetch_rdstation_leads.sh
```

---

> **Qualquer dúvida sobre uso dos comandos, só chamar!**
