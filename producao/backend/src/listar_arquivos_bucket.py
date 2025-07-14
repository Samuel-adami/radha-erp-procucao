import os
import boto3
from dotenv import load_dotenv

load_dotenv()

# Parâmetros de acesso ao bucket S3 obtidos das variáveis de ambiente
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

response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

print(f"📦 Arquivos dentro do bucket '{bucket}' com prefixo '{prefix}':")
for obj in response.get("Contents", []):
    print(f" - {obj['Key']} ({obj['Size']} bytes)")
