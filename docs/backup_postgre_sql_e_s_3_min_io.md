# Script de Backup Automático do PostgreSQL e Bucket S3/MinIO (Ubuntu)

## 1. Backup do Banco de Dados PostgreSQL

### 1.1. Crie um script de backup

```bash
sudo nano /usr/local/bin/backup_postgres.sh
```

Conteúdo sugerido do script:

```bash
#!/bin/bash
# Ajuste as variáveis abaixo conforme seu ambiente
DB_NAME="producao"
DB_USER="radha_admin"
BACKUP_DIR="/home/samuel/backups/postgres"
DATE=$(date +"%Y-%m-%d_%H-%M-%S")

mkdir -p "$BACKUP_DIR"

pg_dump -U $DB_USER $DB_NAME | gzip > "$BACKUP_DIR/${DB_NAME}_$DATE.sql.gz"

# Opcional: Remover backups antigos (exemplo: mais de 7 dias)
find "$BACKUP_DIR" -type f -mtime +7 -delete
```

Permita execução:

```bash
sudo chmod +x /usr/local/bin/backup_postgres.sh
```

### 1.2. Agende o backup diário via cron

```bash
echo "0 2 * * * samuel /usr/local/bin/backup_postgres.sh" | sudo tee -a /etc/crontab
```

---

## 2. Backup dos Arquivos no Bucket S3/MinIO

### 2.1. Instale o cliente MinIO (mc)

```bash
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc
sudo mv mc /usr/local/bin/
```

### 2.2. Configure acesso ao bucket

```bash
mc alias set radha-backup https://nyc3.digitaloceanspaces.com SEU_ACCESS_KEY SEU_SECRET_KEY
# (ou endereço do seu MinIO/S3)
```

### 2.3. Script para backup do bucket (download local)

```bash
sudo nano /usr/local/bin/backup_bucket.sh
```

Exemplo de script:

```bash
#!/bin/bash
BUCKET="radha-arquivos"
DEST_DIR="/home/samuel/backups/s3"
DATE=$(date +"%Y-%m-%d_%H-%M-%S")

mkdir -p "$DEST_DIR/$DATE"
mc cp --recursive radha-backup/$BUCKET "$DEST_DIR/$DATE/"

# Remove backups antigos
find "$DEST_DIR" -type d -mtime +7 -exec rm -rf {} +
```

Permita execução:

```bash
sudo chmod +x /usr/local/bin/backup_bucket.sh
```

### 2.4. Agende backup diário do bucket

```bash
echo "30 2 * * * samuel /usr/local/bin/backup_bucket.sh" | sudo tee -a /etc/crontab
```

---

## 3. Restaurando um Backup PostgreSQL

```bash
gunzip < /home/samuel/backups/postgres/producao_YYYY-MM-DD_HH-MM-SS.sql.gz | psql -U radha_admin producao
```

---

## 4. Dicas de Segurança

- Guarde os backups em local seguro.
- Use outro disco, VPS, ou bucket para backups redundantes.
- Proteja scripts e pastas com permissão 700/600.

---

## Resumo dos Comandos

```bash
# PostgreSQL
sudo nano /usr/local/bin/backup_postgres.sh
sudo chmod +x /usr/local/bin/backup_postgres.sh
# MinIO/S3
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc
sudo mv mc /usr/local/bin/
sudo nano /usr/local/bin/backup_bucket.sh
sudo chmod +x /usr/local/bin/backup_bucket.sh
# Cron
sudo nano /etc/crontab
```

---

> **Em caso de dúvidas ou para customizações (criptografia, envio para outro bucket etc.), só avisar!**

