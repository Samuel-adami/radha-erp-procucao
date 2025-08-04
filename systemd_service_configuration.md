## Systemd Service Configuration
On the production server each module runs as a systemd unit. The examples below assume the repository lives in `/home/samuel/radha-erp-procucao` and that the virtual environment is located at `venv`.

Each backend service reads a `.env` file located in the same directory as the service. This file must provide all `OBJECT_STORAGE_*` variables required by the applications.

### Produção Backend
```
/etc/systemd/system/radha-producao-backend.service

[Unit]
Description=Radha ERP - Backend Produção
After=network.target

[Service]
Type=simple
User=samuel
WorkingDirectory=/home/samuel/radha-erp-producao/producao/backend/src
EnvironmentFile=/home/samuel/radha-erp-producao/producao/backend/src/.env
ExecStart=/home/samuel/radha-erp-producao/venv/bin/uvicorn api:app --host 0.0.0.0 --port 8060
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Comercial Backend
```
/etc/systemd/system/radha-comercial-backend.service

[Unit]
Description=Radha ERP - Backend Comercial
After=network.target

[Service]
User=samuel
WorkingDirectory=/home/samuel/radha-erp-procucao/comercial-backend
ExecStart=/home/samuel/radha-erp-procucao/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8070
Restart=always

[Install]
WantedBy=multi-user.target
```

### Finance Backend
```
/etc/systemd/system/radha-finance-backend.service

[Unit]
Description=Radha ERP - Backend Financeiro
After=network.target

[Service]
User=samuel
WorkingDirectory=/home/samuel/radha-erp-procucao/finance_backend
ExecStart=/home/samuel/radha-erp-procucao/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
```

### Marketing Digital IA Backend
```
/etc/systemd/system/radha-marketing-backend.service

[Unit]
Description=Radha ERP - Backend Marketing Digital IA
After=network.target

[Service]
User=samuel
WorkingDirectory=/home/samuel/radha-erp-procucao/marketing-digital-ia/backend
EnvironmentFile=/home/samuel/radha-erp-procucao/marketing-digital-ia/backend/.env
ExecStart=/home/samuel/radha-erp-procucao/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8050
Restart=always

[Install]
WantedBy=multi-user.target
```

### Gateway Backend
```
/etc/systemd/system/radha-gateway-backend.service

[Unit]
Description=Radha ERP - Backend Gateway
After=network.target

[Service]
User=samuel
WorkingDirectory=/home/samuel/radha-erp-procucao/backend-gateway
EnvironmentFile=/home/samuel/radha-erp-procucao/backend-gateway/.env
ExecStart=/home/samuel/radha-erp-procucao/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8040
Restart=always

[Install]
WantedBy=multi-user.target
```

### Frontend
```
/etc/systemd/system/radha-frontend.service

[Unit]
Description=Radha ERP Frontend
After=network.target

[Service]
User=samuel
WorkingDirectory=/home/samuel/radha-erp-producao/frontend-erp
ExecStart=/usr/bin/npx serve -s dist -l 3015
Restart=always

[Install]
WantedBy=multi-user.target
```
