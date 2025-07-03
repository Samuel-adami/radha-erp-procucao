#!/bin/bash
DIR=$(dirname "$0")
[ -f "$DIR/.env" ] && export $(grep -v '^#' "$DIR/.env" | xargs)

export GATEWAY_PORT=${GATEWAY_PORT:-8040}
export MARKETING_PORT=${MARKETING_PORT:-8050}
export PRODUCAO_PORT=${PRODUCAO_PORT:-8060}
export COMERCIAL_PORT=${COMERCIAL_PORT:-8070}
export FRONTEND_PORT=${FRONTEND_PORT:-3015}
export SECRET_KEY=${SECRET_KEY:-radha-super-secreto}

cd "$DIR/marketing-digital-ia/backend" && nohup uvicorn main:app --host 0.0.0.0 --port $MARKETING_PORT > ../../logs/marketing.log 2>&1 &
cd "$DIR/producao/backend/src" && nohup uvicorn api:app --host 0.0.0.0 --port $PRODUCAO_PORT > ../../../logs/producao.log 2>&1 &
cd "$DIR/backend-gateway" && nohup uvicorn main:app --host 0.0.0.0 --port $GATEWAY_PORT > ../logs/gateway.log 2>&1 &
cd "$DIR/comercial-backend" && nohup uvicorn main:app --host 0.0.0.0 --port $COMERCIAL_PORT > ../logs/comercial.log 2>&1 &
cd "$DIR/frontend-erp" && nohup PORT=$FRONTEND_PORT npm run build && nohup npx serve -s dist -l $FRONTEND_PORT > ../logs/frontend.log 2>&1 &
