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
   `VITE_GATEWAY_URL=http://localhost:8010`. Optionally set `VITE_DEFAULT_USERNAME` and
   `VITE_DEFAULT_PASSWORD` for automatic login. Before running the services export:
   ```bash
   export SECRET_KEY=radha-super-secreto
   export RADHA_DATA_DIR=$PWD/data
   export RADHA_ADMIN_USER=admin
   export RADHA_ADMIN_PASS=admin
   ```
   `OPENAI_API_KEY` may be defined to enable AI features in Marketing Digital.

## Running the Application
Execute `./start_services.sh` in the repository root. The script launches all backends and the
React frontend in development mode:
- Gateway: http://localhost:8010
- Marketing Digital IA: http://localhost:8015
- Produção: http://localhost:8020
- Comercial: http://localhost:8030
- Frontend React: http://localhost:3005

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
