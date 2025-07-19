"""Upload de um arquivo para o bucket configurado em variáveis de ambiente."""

import os
import boto3
from dotenv import load_dotenv

# Carrega variáveis definidas em .env, se existir
load_dotenv()

# Parâmetros de acesso ao bucket obtidos das variáveis de ambiente
ENDPOINT = os.getenv("OBJECT_STORAGE_ENDPOINT", "https://nyc3.digitaloceanspaces.com")
ACCESS_KEY = os.getenv("OBJECT_STORAGE_ACCESS_KEY")
SECRET_KEY = os.getenv("OBJECT_STORAGE_SECRET_KEY")
BUCKET = os.getenv("OBJECT_STORAGE_BUCKET", "radha-arquivos")
PREFIX = os.getenv("OBJECT_STORAGE_PREFIX", "producao/")

# Conexão S3
session = boto3.session.Session()
s3 = session.client(
    's3',
    region_name='nyc3',
    endpoint_url=ENDPOINT,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY
)

# Parâmetros do teste
bucket = BUCKET
prefix = PREFIX
arquivo_local = "teste.txt"
chave_destino = prefix + "teste.txt"

# Cria arquivo temporário
with open(arquivo_local, "w") as f:
    f.write("Arquivo de teste do Radha ERP via boto3")

# Faz upload
s3.upload_file(arquivo_local, bucket, chave_destino)
print(f"✅ Upload realizado: {chave_destino}")

# Lista para verificar se o upload deu certo
print("📂 Arquivos no prefixo:")
objetos = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
for obj in objetos.get("Contents", []):
    print(" -", obj["Key"])
