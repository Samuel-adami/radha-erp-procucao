import subprocess
import json

resultado = {"systemctl": [], "pm2": []}

# Systemctl - serviços ativos contendo radha
try:
    output = subprocess.check_output("systemctl list-units --type=service --no-pager", shell=True, text=True)
    linhas = output.splitlines()
    for linha in linhas:
        if "radha" in linha.lower():
            resultado["systemctl"].append(linha.strip())
except Exception as e:
    resultado["systemctl"] = [f"Erro: {e}"]

# PM2 - serviços gerenciados
try:
    output = subprocess.check_output("pm2 list", shell=True, text=True)
    resultado["pm2"] = output.splitlines()
except Exception as e:
    resultado["pm2"] = [f"Erro: {e}"]

# Salvar resultado
with open("estrutura_servicos.json", "w", encoding="utf-8") as f:
    json.dump(resultado, f, indent=2, ensure_ascii=False)

print("Scanner de serviços concluído. Resultado salvo em estrutura_servicos.json")
