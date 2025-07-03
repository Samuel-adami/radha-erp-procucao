#!/bin/bash

# Backend Gateway
cd /home/samuel/radha-erp-producao/backend-gateway
source /home/samuel/radha-erp-producao/venv/bin/activate
nohup uvicorn main:app --host 0.0.0.0 --port 8040 > ../../logs/gateway.log 2>&1 &

# Backend Producao
cd /home/samuel/radha-erp-producao/producao/backend
source /home/samuel/radha-erp-producao/venv/bin/activate
nohup uvicorn main:app --host 0.0.0.0 --port 8060 > ../../../logs/producao.log 2>&1 &

# Backend Comercial
cd /home/samuel/radha-erp-producao/comercial-backend
source /home/samuel/radha-erp-producao/venv/bin/activate
nohup uvicorn main:app --host 0.0.0.0 --port 8070 > ../logs/comercial.log 2>&1 &

# Backend Marketing-IA
cd /home/samuel/radha-erp-producao/marketing-digital-ia/backend
source /home/samuel/radha-erp-producao/venv/bin/activate
nohup uvicorn main:app --host 0.0.0.0 --port 8050 > ../../../logs/marketing-ia.log 2>&1 &

# Frontend ERP
cd /home/samuel/radha-erp-producao/frontend-erp
nohup npm run dev -- --port 3015 > ../logs/frontend.log 2>&1 &

echo "Todos os serviços foram iniciados."
