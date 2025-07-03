#!/bin/bash
DIR=$(dirname "$0")
source ~/miniconda3/etc/profile.d/conda.sh
conda activate radha-prod

export SECRET_KEY=${SECRET_KEY:-radha-super-secreto}
export GATEWAY_PORT=${GATEWAY_PORT:-8040}
export MARKETING_PORT=${MARKETING_PORT:-8050}
export PRODUCAO_PORT=${PRODUCAO_PORT:-8060}
export COMERCIAL_PORT=${COMERCIAL_PORT:-8070}
export FRONTEND_PORT=${FRONTEND_PORT:-3015}

cd "$DIR/marketing-digital-ia/backend" && uvicorn main:app --host 0.0.0.0 --port $MARKETING_PORT --reload &
PID1=$!
cd "$DIR/producao/backend/src" && uvicorn api:app --host 0.0.0.0 --port $PRODUCAO_PORT --reload &
PID2=$!
cd "$DIR/backend-gateway" && uvicorn main:app --host 0.0.0.0 --port $GATEWAY_PORT --reload &
PID3=$!
cd "$DIR/comercial-backend" && uvicorn main:app --host 0.0.0.0 --port $COMERCIAL_PORT --reload &
PID4=$!
cd "$DIR/frontend-erp" && PORT=$FRONTEND_PORT npm run dev &
PID5=$!
wait $PID1 $PID2 $PID3 $PID4 $PID5
