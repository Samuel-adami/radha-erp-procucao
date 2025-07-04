# Radha ERP Agent Instructions

This repository contains multiple Python backends and a React frontend. The instructions below
allow any agent to start the services locally and replicate the interface for testing.

## Environment Setup
1. **Install dependencies**: Python 3.11+ and Node.js 18+ with npm.
2. **Python virtual environments**: in each backend directory create a `venv` and install requirements.
   Example for the marketing module:
   ```bash
   cd marketing-digital-ia/backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
   Repeat for `producao/backend/src`, `backend-gateway` and `comercial-backend`.
3. **Frontend dependencies**: install npm packages once inside `frontend-erp`:
   ```bash
   cd frontend-erp
   npm install
   ```
4. **Environment variables**: copy `frontend-erp/.env.example` to `.env` and set
   `VITE_GATEWAY_URL=http://localhost:8040`. Optionally set `VITE_DEFAULT_USERNAME` and
   `VITE_DEFAULT_PASSWORD` for automatic login. Each backend also provides a
   `.env.example` file with `DATABASE_URL`, `SECRET_KEY` and other variables. Copy
   them to `.env` in their respective folders:

   - `backend-gateway/.env.example`
   - `marketing-digital-ia/backend/.env.example`
   - `producao/backend/src/.env.example`
   - `comercial-backend/.env.example`

   Before running the services export:
   ```bash
   export SECRET_KEY=radha-super-secreto
   export RADHA_DATA_DIR=$PWD/data
   export RADHA_ADMIN_USER=admin
   export RADHA_ADMIN_PASS=admin
   ```
   `OPENAI_API_KEY` may be defined to enable AI features in Marketing Digital.
   Configure gateway URLs if needed:
   ```bash
   export MARKETING_IA_BACKEND_URL=http://localhost:8050
   export PRODUCAO_BACKEND_URL=http://localhost:8060
   export COMERCIAL_BACKEND_URL=http://localhost:8070
   ```

## Running the Application
Execute `./start_services.sh` in the repository root. The script launches all backends and the
React frontend in development mode:
 - Gateway: http://localhost:8040
 - Marketing Digital IA: http://localhost:8050
 - Produção: http://localhost:8060
 - Comercial: http://localhost:8070
 - Frontend React: http://localhost:3015

Access `http://localhost:3005` in your browser and log in using the credentials from
`RADHA_ADMIN_USER`/`RADHA_ADMIN_PASS`.

## Development Checks
- Run `npm run lint` inside `frontend-erp` before committing changes to JS/TS files.
- Backends currently lack automated tests; ensure each service starts without errors when executing `uvicorn`.

## Stopping the Services
Stop `start_services.sh` with `Ctrl+C`. If any process remains running, kill it manually
using `pkill uvicorn` and `pkill node` or the process IDs shown when the services started.

## Systemd Service Configuration
On the production server each module runs as a systemd unit. The examples below assume the repository lives in `/home/samuel/radha-erp-procucao` and that the virtual environment is located at `venv`.

### Produção Backend
```
/etc/systemd/system/radha-producao-backend.service

[Unit]
Description=Radha ERP - Backend Produção
After=network.target

[Service]
User=samuel
WorkingDirectory=/home/samuel/radha-erp-procucao/producao/backend/src
ExecStart=/home/samuel/radha-erp-procucao/venv/bin/uvicorn api:app --host 0.0.0.0 --port 8060
Restart=always

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

### Marketing Digital IA Backend
```
/etc/systemd/system/radha-marketing-backend.service

[Unit]
Description=Radha ERP - Backend Marketing Digital IA
After=network.target

[Service]
User=samuel
WorkingDirectory=/home/samuel/radha-erp-procucao/marketing-digital-ia/backend
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
WorkingDirectory=/home/samuel/radha-erp-procucao/frontend-erp
ExecStart=/usr/bin/npx serve -s dist -l 3015
Restart=always

[Install]
WantedBy=multi-user.target
```

## Nginx Configuration
The production server uses Nginx as a reverse proxy in front of the
FastAPI backends and the React frontend. Below are the configuration
files currently enabled under `/etc/nginx/sites-available`.

### /etc/nginx/sites-available/erp.radhadigital.com.br
```
server {
    listen 80;
    server_name erp.radhadigital.com.br;

    # Redireciona tudo para HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name erp.radhadigital.com.br;

    # SSL
    ssl_certificate /etc/letsencrypt/live/erp.radhadigital.com.br/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/erp.radhadigital.com.br/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # FRONTEND (React build, na porta 3015 via serve ou similar)
    location / {
        proxy_pass http://127.0.0.1:3015;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # GATEWAY (backend FastAPI rodando na porta 8040)
    # Tudo que for /auth ou /api (ou o que for do seu gateway) vai para o backend
    location /auth/ {
        proxy_pass http://127.0.0.1:8040;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Se tiver outras rotas de API, adicione aqui:
}
```

### /etc/nginx/sites-available/radha-gateway-https
```
server {
    listen 443 ssl;
    server_name erp.radhadigital.com.br;

    ssl_certificate /etc/letsencrypt/live/erp.radhadigital.com.br/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/erp.radhadigital.com.br/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8040;   # Gateway backend
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
