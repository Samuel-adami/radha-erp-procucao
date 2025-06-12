#!/bin/bash

echo "Atualizando o repositório..."
git pull origin main || { echo "Erro ao atualizar o repositório."; exit 1; }

echo "Ativando ambiente virtual e iniciando Backend..."
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8005 --reload &
BACKEND_PID=$!
cd ..

echo "Iniciando Frontend em modo produção..."
cd frontend
npm run build
npx serve -s build -l 37017 &
FRONTEND_PID=$!
cd ..

echo "Assistente Radha rodando!"
echo "Backend rodando na porta 8005 - PID: $BACKEND_PID"
echo "Frontend rodando na porta 37017 - PID: $FRONTEND_PID"

echo "Para encerrar: kill $BACKEND_PID $FRONTEND_PID"