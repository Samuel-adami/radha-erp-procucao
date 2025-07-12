import boto3

# Parâmetros de acesso ao bucket para teste. Antes eram lidos do .env,
# agora ficam definidos diretamente aqui para facilitar a execução.
ENDPOINT = "https://nyc3.digitaloceanspaces.com"
ACCESS_KEY = "DO801RVLRYQAQ7ZBKxxx"
SECRET_KEY = "0D4o8nUESJUP0X3WyUuaDiO9DNysuACxJKSOCL4dxxxx"
BUCKET = "radha-arquivos"
PREFIX = "producao/"

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
