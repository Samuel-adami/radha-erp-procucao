#!/bin/bash

LOGDIR="/home/samuel/radha-erp-producao/logs"
VENVDIR="/home/samuel/radha-erp-producao/venv"

echo "Matando processos antigos nas portas 8040, 8050, 8060, 8070 e 3015..."
for port in 8040 8050 8060 8070 3015; do
    for pid in $(lsof -t -i:$port); do
        if [ -n "$pid" ]; then
            echo "Matando processo $pid na porta $port"
            kill -9 $pid
        fi
    done
done
sleep 2

# Garante que a pasta de logs existe
mkdir -p "$LOGDIR"

# Backend Gateway
cd /home/samuel/radha-erp-producao/backend-gateway
source "$VENVDIR/bin/activate"
nohup uvicorn main:app --host 0.0.0.0 --port 8040 > "$LOGDIR/gateway.log" 2>&1 &

# Backend Producao
cd /home/samuel/radha-erp-producao/producao/backend/src
source "$VENVDIR/bin/activate"
nohup uvicorn api:app --host 0.0.0.0 --port 8060 > "$LOGDIR/producao.log" 2>&1 &

# Backend Comercial
cd /home/samuel/radha-erp-producao/comercial-backend
source "$VENVDIR/bin/activate"
nohup uvicorn main:app --host 0.0.0.0 --port 8070 > "$LOGDIR/comercial.log" 2>&1 &

# Backend Marketing-IA
cd /home/samuel/radha-erp-producao/marketing-digital-ia/backend
source "$VENVDIR/bin/activate"
nohup uvicorn main:app --host 0.0.0.0 --port 8050 > "$LOGDIR/marketing-ia.log" 2>&1 &

# Frontend ERP
cd /home/samuel/radha-erp-producao/frontend-erp
nohup npm run dev -- --port 3015 > "$LOGDIR/frontend.log" 2>&1 &

echo "Todos os serviços foram iniciados."
