import os
import ast
import json

BACKEND_DIRS = [
    "../backend-gateway",
    "../comercial-backend",
    "../producao/backend",
    "../marketing-digital-ia/backend"
]

resultado = {}

for backend in BACKEND_DIRS:
    backend_nome = os.path.basename(backend.strip("/"))
    resultado[backend_nome] = []
    for root, _, files in os.walk(backend):
        for file in files:
            if file.endswith(".py"):
                caminho_completo = os.path.join(root, file)
                try:
                    with open(caminho_completo, "r", encoding="utf-8") as f:
                        conteudo = f.read()
                        tree = ast.parse(conteudo)
                        funcoes = [
                            {
                                "nome": node.name,
                                "lineno": node.lineno,
                                "args": [arg.arg for arg in node.args.args]
                            }
                            for node in ast.walk(tree)
                            if isinstance(node, ast.FunctionDef)
                        ]
                        if funcoes:
                            resultado[backend_nome].append({
                                "arquivo": caminho_completo,
                                "funcoes": funcoes
                            })
                except Exception as e:
                    resultado[backend_nome].append({
                        "arquivo": caminho_completo,
                        "erro": str(e)
                    })

# Salvar resultado
with open("estrutura_backend.json", "w", encoding="utf-8") as f:
    json.dump(resultado, f, indent=2, ensure_ascii=False)

print("Scanner de backend concluído. Resultado salvo em estrutura_backend.json")
