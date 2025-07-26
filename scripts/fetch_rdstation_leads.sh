#!/usr/bin/env bash
set -euo pipefail

# Script para executar o fluxo completo de OAuth RD Station e recuperar leads
# 1) Obtém authorization code via navegador
# 2) Callback para gravar tokens
# 3) Faz login no ERP e pega o JWT
# 4) Chama /leads/?force_refresh=true e exibe resultado

# Configuração de host/porta (ajuste se necessário)
HOST=${HOST:-localhost}
PORT=${PORT:-8050}
PREFIX=${PREFIX:-/marketing-ia}

echo
cat <<-EOF
==== Fluxo Gestão de Leads RD Station ====

1) Abra no navegador e autorize (OAuth RD Station):
   http://${HOST}:${PORT}${PREFIX}/rd/login

2) Após autorizar, você será redirecionado para:
   https://${HOST}${PREFIX}/rd/callback?code=SEU_CODE

   Copie o valor de 'code' e cole abaixo.
EOF

read -rp "Authorization code: " CODE

echo
echo "==> Trocando code por token RD Station..."
curl -sf -X GET "http://${HOST}:${PORT}${PREFIX}/rd/callback?code=${CODE}" \
     && echo "RD Station OK" || { echo "Erro no callback RD Station"; exit 1; }

echo
echo "==> Informe credenciais do ERP para login e pegar JWT"
read -rp "Usuário ERP: " USER
read -rsp "Senha ERP: " PASS
echo

echo "==> Autenticando no ERP e obtendo token..."
LOGIN_JSON=$(curl -sf -X POST "http://${HOST}:${PORT}/auth/login" \
                -H 'Content-Type: application/json' \
                -d "{\"username\":\"${USER}\",\"password\":\"${PASS}\"}")
TOKEN=$(printf '%s' "$LOGIN_JSON" \
        | python3 -c 'import sys,json; print(json.load(sys.stdin).get("access_token",""))')
if [[ -z "$TOKEN" ]]; then
  echo "Falha ao obter token JWT: $LOGIN_JSON"
  exit 1
fi
echo "Token JWT obtido com sucesso"

echo
echo "==> Buscando leads (force_refresh=true)..."
curl -sf -X GET "http://${HOST}:${PORT}${PREFIX}/leads/?force_refresh=true" \
     -H "Authorization: Bearer ${TOKEN}" \
     | (command -v jq >/dev/null 2>&1 && jq . || cat)

echo "=== Fluxo concluído ==="
