#!/bin/bash

# Diretório base do seu monorepo
RADHA_ERP_ROOT="/opt/radha/radha-erp"

# Diretório para armazenar os logs de inicialização de cada serviço e PIDs
LOG_DIR="$RADHA_ERP_ROOT/logs"
mkdir -p "$LOG_DIR" # Cria o diretório de logs se não existir

echo "=== Iniciando serviços do Radha ERP ===" | tee -a "$LOG_DIR/startup_main.log"
echo "Data de início: $(date)" | tee -a "$LOG_DIR/startup_main.log"
echo "Logs detalhados de cada serviço serão encontrados em $LOG_DIR" | tee -a "$LOG_DIR/startup_main.log"

# Função para iniciar um serviço Python
start_python_service() {
    local service_name=$1
    local service_path=$2
    local app_module=$3
    local port=$4
    local pid_file="$LOG_DIR/${service_name}.pid"
    local log_file="$LOG_DIR/${service_name}.log"

    echo "Iniciando $service_name (porta $port)..." | tee -a "$LOG_DIR/startup_main.log"

    cd "$service_path" || { echo "Erro ao entrar no diretório de $service_name. Abortando." | tee -a "$LOG_DIR/startup_main.log"; exit 1; }

    # Ativa o ambiente virtual
    source venv/bin/activate || { echo "Erro ao ativar venv para $service_name. Abortando." | tee -a "$LOG_DIR/startup_main.log"; exit 1; }

    # Inicia o Uvicorn em segundo plano, redirecionando stdout/stderr para o log
    nohup uvicorn "$app_module" --host 0.0.0.0 --port "$port" --reload > "$log_file" 2>&1 &
    echo $! > "$pid_file" # Salva o PID do processo
    deactivate # Desativa o ambiente virtual

    echo "$service_name iniciado com PID $(cat "$pid_file")." | tee -a "$LOG_DIR/startup_main.log"
    sleep 5 # Espera 5 segundos para o serviço Python iniciar
}

# Função para iniciar o serviço Node.js (Frontend)
start_node_service() {
    local service_name=$1
    local service_path=$2
    local command=$3
    local port=$4
    local pid_file="$LOG_DIR/${service_name}.pid"
    local log_file="$LOG_DIR/${service_name}.log"

    echo "Iniciando $service_name (porta $port)..." | tee -a "$LOG_DIR/startup_main.log"

    cd "$service_path" || { echo "Erro ao entrar no diretório de $service_name. Abortando." | tee -a "$LOG_DIR/startup_main.log"; exit 1; }

    # Inicia o comando npm em segundo plano
    nohup $command > "$log_file" 2>&1 &
    echo $! > "$pid_file" # Salva o PID do processo

    echo "$service_name iniciado com PID $(cat "$pid_file")." | tee -a "$LOG_DIR/startup_main.log"
    sleep 10 # Espera um pouco mais para o Frontend estar pronto
}

# --- Iniciar Backends ---
start_python_service "Marketing_IA_Backend" "$RADHA_ERP_ROOT/marketing-digital-ia/backend/" "main:app" "8015"
start_python_service "Producao_Backend" "$RADHA_ERP_ROOT/producao/backend/src/" "api:app" "8020"
start_python_service "Backend_Gateway" "$RADHA_ERP_ROOT/backend-gateway/" "main:app" "8010"

# --- Iniciar Frontend ---
start_node_service "Frontend_ERP" "$RADHA_ERP_ROOT/frontend-erp/" "npm run dev" "3005"

echo "=== Todos os serviços do Radha ERP foram iniciados em segundo plano ===" | tee -a "$LOG_DIR/startup_main.log"
echo "Verifique os arquivos de log em $LOG_DIR para detalhes e erros." | tee -a "$LOG_DIR/startup_main.log"

# Opcional: mantém o script rodando por mais um tempo para dar tempo de escrever nos logs
sleep 5