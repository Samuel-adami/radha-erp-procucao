#!/bin/bash

# Diretório raiz do monorepo
# Use RADHA_ERP_ROOT se definido; caso contrário, tenta detectar o repositório
# Git atual (ou usa o diretório corrente)
RADHA_ERP_ROOT="${RADHA_ERP_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

echo "--- Sincronizando o monorepo Radha ERP com o GitHub ---"
echo "Navegando para $RADHA_ERP_ROOT"
cd "$RADHA_ERP_ROOT" || { echo "Erro: Diretório $RADHA_ERP_ROOT não encontrado. Abortando." ; exit 1; }

# Adiciona todas as alterações (novos, modificados, deletados)
echo "Adicionando todas as alterações ao stage..."
git add .

# Faz um commit, se houver alterações
# O '|| true' impede que o script pare se não houver nada para commitar
echo "Fazendo commit das alterações..."
git commit -m "feat: Latest local changes and bug fixes" || true

# Envia as alterações para o repositório remoto 'origin' na branch 'main'
echo "Enviando alterações para o GitHub..."
git push origin main

if [ $? -eq 0 ]; then
    echo "✅ Repositório GitHub atualizado com sucesso!"
else
    echo "❌ Erro ao enviar alterações para o GitHub. Verifique suas credenciais e conexão."
fi
echo "--- Sincronização Concluída ---"
