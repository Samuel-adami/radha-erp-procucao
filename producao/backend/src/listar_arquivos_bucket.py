import boto3

# Parâmetros de acesso ao bucket S3. Antes eram obtidos do ambiente,
# agora ficam definidos diretamente aqui para evitar falhas em ambientes
# sem variáveis configuradas.
ENDPOINT = "https://nyc3.digitaloceanspaces.com"
ACCESS_KEY = "DO801RVLRYQAQ7ZBKxxx"
SECRET_KEY = "0D4o8nUESJUP0X3WyUuaDiO9DNysuACxJKSOCL4dxxxx"
BUCKET = "radha-arquivos"
PREFIX = "producao/"

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
