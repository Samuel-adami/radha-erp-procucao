#!/bin/bash

set -e  # Pare ao primeiro erro

echo ">>> [1/6] Criando/Recriando o ambiente virtual Python..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

echo ">>> [2/6] Instalando dependências dos backends..."

pip install --no-cache-dir -r backend-gateway/requirements.txt
pip install --no-cache-dir -r producao/backend/requirements.txt
pip install --no-cache-dir -r comercial-backend/requirements.txt
pip install --no-cache-dir -r marketing-digital-ia/backend/requirements.txt

echo ">>> [3/6] Instalando dependências do frontend-erp..."
cd frontend-erp
npm install
cd ..

echo ">>> [4/6] Criando pasta de logs (se não existir)..."
mkdir -p logs

echo ">>> [5/6] Rodando o sistema em modo produção (primeira vez)..."
bash start_services_prod.sh

echo ">>> [6/6] Pronto! O Radha ERP está rodando em produção."
echo ""
echo "Use 'ps aux | grep uvicorn' para ver os processos, ou cheque os arquivos de log na pasta logs/"
