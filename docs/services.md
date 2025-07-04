## 1. Instale serve para o frontend (global ou local)
sudo npm install -g serve

## 2. Build de produção do frontend
cd frontend-erp
npm install
npm run build

## 3. Variáveis de Ambiente Importantes

No arquivo .env na raiz do projeto, adicione/exemplo:

RADHA_ADMIN_USER=admin
RADHA_ADMIN_PASS=admin
SECRET_KEY=radha-super-secreto
DATABASE_URL=postgresql://radha_admin:senha@localhost:5432/producao
OBJECT_STORAGE_ENDPOINT=https://nyc3.digitaloceanspaces.com
OBJECT_STORAGE_ACCESS_KEY=DO801.....
OBJECT_STORAGE_SECRET_KEY=0D4o8n......
OBJECT_STORAGE_BUCKET=radha-prod-backend
ALLOWED_HOSTS=radhadigital.com.br,www.radhadigital.com.br,erp.radhadigital.com.br,www.erp.radhadigital.com.br
DOMAIN=erp.radhadigital.com.br
GATEWAY_PORT=8040
MARKETING_PORT=8050
PRODUCAO_PORT=8060
COMERCIAL_PORT=8070
FRONTEND_PORT=3015

## 4. Build do Frontend

cd ~/radha-erp-producao/frontend-erp
npm install
npm run build
serve -s dist -l 3015

# Para rodar como serviço 24/7, use o systemd (ver seção abaixo).

## 5. Systemd: Serviços para Backends e Frontend
Exemplo para cada serviço (ajuste o caminho se necessário):

# Produção
/etc/systemd/system/radha-producao-backend.service

[Unit]
Description=Radha ERP - Backend Produção
After=network.target

[Service]
User=samuel
WorkingDirectory=/home/samuel/radha-erp-producao/producao/backend/src
ExecStart=/home/samuel/radha-erp-producao/venv/bin/uvicorn api:app --host 0.0.0.0 --port 8060
Restart=always
Environment=PATH=/home/samuel/radha-erp-producao/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

[Install]
WantedBy=multi-user.target

---

# Comercial
/etc/systemd/system/radha-comercial-backend.service

[Unit]
Description=Radha ERP - Backend Comercial
After=network.target

[Service]
User=samuel
WorkingDirectory=/home/samuel/radha-erp-producao/comercial-backend
ExecStart=/home/samuel/radha-erp-producao/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8070
Restart=always
Environment=PATH=/home/samuel/radha-erp-producao/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

[Install]
WantedBy=multi-user.target

---

# Marketing IA
/etc/systemd/system/radha-marketing-backend.service

[Unit]
Description=Radha ERP - Backend Marketing Digital IA
After=network.target

[Service]
User=samuel
WorkingDirectory=/home/samuel/radha-erp-producao/marketing-digital-ia/backend
ExecStart=/home/samuel/radha-erp-producao/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8050
Restart=always
Environment=PATH=/home/samuel/radha-erp-producao/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

[Install]
WantedBy=multi-user.target

---

# Gateway
/etc/systemd/system/radha-gateway-backend.service

[Unit]
Description=Radha ERP - Backend Gateway
After=network.target

[Service]
User=samuel
WorkingDirectory=/home/samuel/radha-erp-producao/backend-gateway
ExecStart=/home/samuel/radha-erp-producao/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8040
Restart=always
Environment=PATH=/home/samuel/radha-erp-producao/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

[Install]
WantedBy=multi-user.target

---

# Frontend
/etc/systemd/system/radha-frontend.service

[Unit]
Description=Radha ERP Frontend
After=network.target

[Service]
User=samuel
WorkingDirectory=/home/samuel/radha-erp-producao/frontend-erp
ExecStart=/usr/bin/npx serve -s dist -l 3015
Restart=always
Environment=PATH=/usr/local/bin:/usr/bin:/bin

[Install]
WantedBy=multi-user.target

---

# Ative e inicie todos os serviços:

sudo systemctl daemon-reload
sudo systemctl enable radha-producao-backend
sudo systemctl enable radha-comercial-backend
sudo systemctl enable radha-marketing-backend
sudo systemctl enable radha-gateway-backend
sudo systemctl enable radha-frontend

sudo systemctl start radha-producao-backend
sudo systemctl start radha-comercial-backend
sudo systemctl start radha-marketing-backend
sudo systemctl start radha-gateway-backend
sudo systemctl start radha-frontend

## 6. Comandos Úteis para Gerenciamento dos Serviços

# Verificar status individual
sudo systemctl status radha-producao-backend
sudo systemctl status radha-comercial-backend
sudo systemctl status radha-marketing-backend
sudo systemctl status radha-gateway-backend
sudo systemctl status radha-frontend

# Parar, iniciar, reiniciar
sudo systemctl restart radha-producao-backend
sudo systemctl stop radha-producao-backend
sudo systemctl start radha-producao-backend
# Repita para os outros serviços

# Ver logs em tempo real
sudo journalctl -u radha-producao-backend -f
sudo journalctl -u radha-frontend -f

## 7. Scripts Prontos para Status de Todos os Serviços

#!/bin/bash
for svc in producao-backend comercial-backend marketing-backend gateway-backend frontend; do
    echo "==== radha-$svc ===="
    systemctl status radha-$svc --no-pager -n 5 | head -20
    echo
done

Uso:

Salve como radha-status.sh

Dê permissão: chmod +x radha-status.sh

Rode: ./radha-status.sh

## 8. Logs de Produção
Todos os logs dos serviços podem ser visualizados via journalctl, ex:

sudo journalctl -u radha-producao-backend -n 40 --no-pager
sudo journalctl -u radha-frontend -f
Ou consulte a pasta /home/samuel/radha-erp-producao/logs/ se estiver redirecionando manualmente algum log.

## 9. Observações Finais
Sempre verifique o status dos serviços após atualizações ou reboot.

Em caso de erro, verifique os logs do serviço com journalctl.

# Para atualizar o sistema, use sempre git pull e, se necessário, reinicie os serviços:

git pull
sudo systemctl restart radha-producao-backend
sudo systemctl restart radha-frontend
# ... e os demais
