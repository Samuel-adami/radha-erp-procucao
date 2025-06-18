#!/bin/bash

# Diretório base do monorepo
# Use a variável RADHA_ERP_ROOT se definida; caso contrário, detecta o diretório
# do repositório Git (ou o diretório atual como fallback)
RADHA_ERP_ROOT="${RADHA_ERP_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

# Diretório para armazenar os logs de inicialização de cada serviço e PIDs
LOG_DIR="$RADHA_ERP_ROOT/logs"
mkdir -p "$LOG_DIR" # Cria o diretório de logs se não existir

export SECRET_KEY="${SECRET_KEY:-radha-super-secreto}"
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

    if [ ! -f venv/bin/activate ]; then
        echo "Criando ambiente virtual para $service_name..." | tee -a "$LOG_DIR/startup_main.log"
        python3 -m venv venv >> "$log_file" 2>&1 || { echo "Erro ao criar venv para $service_name." | tee -a "$LOG_DIR/startup_main.log"; exit 1; }
        source venv/bin/activate
        if [ -f requirements.txt ]; then
            pip install --upgrade pip >> "$log_file" 2>&1
            pip install -r requirements.txt >> "$log_file" 2>&1 || { echo "Erro ao instalar dependências para $service_name." | tee -a "$LOG_DIR/startup_main.log"; exit 1; }
        fi
        deactivate
    fi

    source venv/bin/activate || { echo "Erro ao ativar venv para $service_name. Abortando." | tee -a "$LOG_DIR/startup_main.log"; exit 1; }

    nohup uvicorn "$app_module" --host 0.0.0.0 --port "$port" --reload > "$log_file" 2>&1 &
    echo $! > "$pid_file"
    deactivate

    echo "$service_name iniciado com PID $(cat "$pid_file")." | tee -a "$LOG_DIR/startup_main.log"
    sleep 5
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

    if [ ! -d node_modules ]; then
        echo "Instalando dependências Node para $service_name..." | tee -a "$LOG_DIR/startup_main.log"
        npm install >> "$log_file" 2>&1 || { echo "Erro ao instalar dependências do $service_name." | tee -a "$LOG_DIR/startup_main.log"; exit 1; }
    fi

    nohup $command > "$log_file" 2>&1 &
    echo $! > "$pid_file"

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
