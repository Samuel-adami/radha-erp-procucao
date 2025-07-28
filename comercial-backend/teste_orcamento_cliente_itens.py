import requests
import json

url = 'https://api.gabster.com.br/integracao/api/v2/orcamento_cliente_item/?format=json'

headers = {
    'Content-Type': 'application/json',
    'charset': 'UTF-8',
    'Authorization': 'ApiKey apiradha@gabster.com.br:e4b916e9a817264fdd4fd2a412c007792dbb4e02'
}

response = requests.get(url, headers=headers)

print("Status code:", response.status_code)

try:
    data = response.json()
    print("JSON recebido:")
    print(json.dumps(data, indent=2, ensure_ascii=False))

    # Exporta para arquivo
    with open("retorno_gabster.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("✅ JSON salvo como retorno_gabster.json")

except ValueError:
    print("❌ A resposta não é um JSON válido:")
    print(response.text)

