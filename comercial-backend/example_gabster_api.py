import requests

url = 'https://api.gabster.com.br/integracao/api/v2/orcamento_cliente/?format=json'
headers = {
    'Content-Type': 'application/json',
    'charset': 'UTF-8',
    'Authorization': 'ApiKey SEU_USUARIO:SUA_CHAVE'
}

if __name__ == '__main__':
    resp = requests.get(url, headers=headers)
    print(resp.json())
