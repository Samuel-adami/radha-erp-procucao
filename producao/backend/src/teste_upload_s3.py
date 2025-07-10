import os
import boto3
from dotenv import load_dotenv

# Carrega variáveis do .env local
load_dotenv()

# Conexão S3
session = boto3.session.Session()
s3 = session.client(
    's3',
    region_name='nyc3',
    endpoint_url=os.getenv("OBJECT_STORAGE_ENDPOINT"),
    aws_access_key_id=os.getenv("OBJECT_STORAGE_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("OBJECT_STORAGE_SECRET_KEY")
)

# Parâmetros do teste
bucket = os.getenv("OBJECT_STORAGE_BUCKET")
prefix = os.getenv("OBJECT_STORAGE_PREFIX") or ""
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
