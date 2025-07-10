import json

arquivos = [
    "relatorio_integridade.json",
    "estrutura_banco_producao.json",
    "estrutura_backend.json",
    "estrutura_frontend.json",
    "estrutura_nginx.json",
    "estrutura_servicos.json"
]

contexto = {}

for nome in arquivos:
    try:
        with open(nome, "r", encoding="utf-8") as f:
            contexto[nome] = json.load(f)
    except Exception as e:
        contexto[nome] = {"erro": str(e)}

with open("contexto_projeto.json", "w", encoding="utf-8") as f:
    json.dump(contexto, f, indent=2, ensure_ascii=False)

print("Contexto consolidado salvo em contexto_projeto.json")
