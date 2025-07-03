#!/bin/bash
DIR=$(dirname "$0")
export SECRET_KEY=${SECRET_KEY:-radha-super-secreto}

cd "$DIR/marketing-digital-ia/backend" && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8050 --reload &
PID1=$!
cd "$DIR/producao/backend/src" && source venv/bin/activate && uvicorn api:app --host 0.0.0.0 --port 8060 --reload &
PID2=$!
cd "$DIR/backend-gateway" && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8040 --reload &
PID3=$!
cd "$DIR/comercial-backend" && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8070 --reload &
PID4=$!
cd "$DIR/frontend-erp" && npm run dev &
PID5=$!
wait $PID1 $PID2 $PID3 $PID4 $PID5
