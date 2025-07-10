import os
import boto3
from dotenv import load_dotenv

load_dotenv()

session = boto3.session.Session()
s3 = session.client(
    's3',
    region_name='nyc3',
    endpoint_url=os.getenv("OBJECT_STORAGE_ENDPOINT"),
    aws_access_key_id=os.getenv("OBJECT_STORAGE_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("OBJECT_STORAGE_SECRET_KEY")
)

bucket = os.getenv("OBJECT_STORAGE_BUCKET")
prefix = os.getenv("OBJECT_STORAGE_PREFIX") or ""
chave_origem = prefix + "teste.txt"
arquivo_destino = "baixado.txt"

s3.download_file(bucket, chave_origem, arquivo_destino)
print(f"✅ Download concluído como '{arquivo_destino}'")
