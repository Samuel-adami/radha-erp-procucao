"""Download de um arquivo do bucket usando variáveis de ambiente."""

import os
import boto3
from dotenv import load_dotenv

# Carrega variáveis definidas em .env, se existir
load_dotenv()

# Configuração do bucket via variáveis de ambiente
ENDPOINT = os.getenv("OBJECT_STORAGE_ENDPOINT", "https://nyc3.digitaloceanspaces.com")
ACCESS_KEY = os.getenv("OBJECT_STORAGE_ACCESS_KEY")
SECRET_KEY = os.getenv("OBJECT_STORAGE_SECRET_KEY")
BUCKET = os.getenv("OBJECT_STORAGE_BUCKET", "radha-arquivos")
PREFIX = os.getenv("OBJECT_STORAGE_PREFIX", "producao/")

session = boto3.session.Session()
s3 = session.client(
    's3',
    region_name='nyc3',
    endpoint_url=ENDPOINT,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY
)
bucket = BUCKET
prefix = PREFIX
chave_origem = prefix + "teste.txt"
arquivo_destino = "baixado.txt"

s3.download_file(bucket, chave_origem, arquivo_destino)
print(f"✅ Download concluído como '{arquivo_destino}'")
