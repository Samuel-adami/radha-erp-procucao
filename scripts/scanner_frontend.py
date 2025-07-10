import os
import re
import json

FRONTEND_DIR = "../frontend-erp"
resultado = []

for root, _, files in os.walk(FRONTEND_DIR):
    for file in files:
        if file.endswith(('.vue', '.js', '.ts')):
            caminho_completo = os.path.join(root, file)
            try:
                with open(caminho_completo, "r", encoding="utf-8") as f:
                    conteudo = f.read()
                    rotas = re.findall(r'\b(fetch|axios|api)\s*\(\s*["\'](.*?)\b', conteudo)
                    resultado.append({
                        "arquivo": caminho_completo,
                        "chamadas_api": [rota[1] for rota in rotas]
                    })
            except Exception as e:
                resultado.append({
                    "arquivo": caminho_completo,
                    "erro": str(e)
                })

# Salvar resultado
with open("estrutura_frontend.json", "w", encoding="utf-8") as f:
    json.dump(resultado, f, indent=2, ensure_ascii=False)

print("Scanner de frontend concluído. Resultado salvo em estrutura_frontend.json")
