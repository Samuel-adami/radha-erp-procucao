import psycopg2
import boto3
import json
import os
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

# Configurações de conexão
DATABASE_URL = "postgresql://radha_admin:minhasenha@localhost:5432/producao"
SCHEMAS = ["gateway", "comercial", "marketing", "producao"]
PREFIXOS_BUCKET = ["gateway/", "comercial/", "marketing/", "producao/"]
BUCKET_NAME = "radha-arquivos"

# Conectar ao banco
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Conectar ao S3 (DigitalOcean Spaces)
s3 = boto3.client(
    's3',
    endpoint_url='https://nyc3.digitaloceanspaces.com',
    aws_access_key_id=os.getenv('OBJECT_STORAGE_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('OBJECT_STORAGE_SECRET_KEY')
)

# Listar objetos por prefixo
s3_objects = set()
for prefixo in PREFIXOS_BUCKET:
    resp = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefixo)
    while True:
        for obj in resp.get('Contents', []):
            s3_objects.add(obj['Key'])
        if resp.get('IsTruncated'):
            resp = s3.list_objects_v2(
                Bucket=BUCKET_NAME,
                Prefix=prefixo,
                ContinuationToken=resp['NextContinuationToken']
            )
        else:
            break

# Função para buscar campos com caminhos de arquivos
erros_consulta = []

def buscar_chaves(schema):
    resultados = []
    cursor.execute("""
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = %s AND column_name ILIKE ANY (ARRAY['%pasta%', '%arquivo%', '%obj_key%'])
    """, (schema,))
    colunas = cursor.fetchall()

    if not colunas:
        return resultados

    for tabela, coluna in colunas:
        try:
            cursor.execute(f"SELECT {coluna} FROM {schema}.{tabela}")
            linhas = cursor.fetchall()
            for linha in linhas:
                if linha and isinstance(linha[0], str):
                    resultados.append({
                        "schema": schema,
                        "tabela": tabela,
                        "coluna": coluna,
                        "chave": linha[0]
                    })
        except Exception as e:
            erro_msg = f"Erro ao consultar {schema}.{tabela}.{coluna}: {e}"
            print(erro_msg)
            erros_consulta.append(erro_msg)
            continue
    return resultados

# Buscar chaves em todos os schemas
chaves_banco = []
for schema in SCHEMAS:
    chaves_banco.extend(buscar_chaves(schema))

# Comparar com objetos do bucket
divergencias = []
for registro in chaves_banco:
    chave = registro["chave"]
    if not any(chave.startswith(p) for p in PREFIXOS_BUCKET):
        for prefixo in PREFIXOS_BUCKET:
            if registro["schema"] == prefixo.strip("/"):
                chave = prefixo + chave
                break
    if chave not in s3_objects:
        divergencias.append({"tipo": "ausente no bucket", **registro})

# Verificar objetos do bucket sem registros no banco
referencias_banco = set(
    (p + r["chave"]) if not r["chave"].startswith(p) else r["chave"]
    for r in chaves_banco for p in PREFIXOS_BUCKET if r["chave"].startswith(p) or r["schema"] == p.strip("/")
)
objetos_sem_referencia = list(s3_objects - referencias_banco)

# Salvar relatório
relatorio = {
    "ausentes_no_bucket": divergencias,
    "no_bucket_sem_referencia": objetos_sem_referencia,
    "erros_consulta": erros_consulta
}

with open("relatorio_integridade.json", "w", encoding="utf-8") as f:
    json.dump(relatorio, f, indent=2, ensure_ascii=False)

print("Relatório salvo em relatorio_integridade.json")
