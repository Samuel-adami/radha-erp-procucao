import os
import re
import json

NGINX_PATH = "/etc/nginx/nginx.conf"
INCLUDE_DIR = "/etc/nginx/conf.d"
resultado = {"arquivos": []}

arquivos_para_ler = [NGINX_PATH]
if os.path.isdir(INCLUDE_DIR):
    for file in os.listdir(INCLUDE_DIR):
        if file.endswith(".conf"):
            arquivos_para_ler.append(os.path.join(INCLUDE_DIR, file))

for caminho in arquivos_para_ler:
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            conteudo = f.read()
            servidores = re.findall(r'server \{.*?\}', conteudo, re.DOTALL)
            localizações = re.findall(r'location\s+[^\{]+\{[^\}]+\}', conteudo, re.DOTALL)
            resultado["arquivos"].append({
                "arquivo": caminho,
                "servidores": servidores,
                "localizacoes": localizações
            })
    except Exception as e:
        resultado["arquivos"].append({
            "arquivo": caminho,
            "erro": str(e)
        })

with open("estrutura_nginx.json", "w", encoding="utf-8") as f:
    json.dump(resultado, f, indent=2, ensure_ascii=False)

print("Scanner de NGINX concluído. Resultado salvo em estrutura_nginx.json")