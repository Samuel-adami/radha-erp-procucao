import boto3

# Parâmetros do bucket S3 para o teste de download. Definidos diretamente
# aqui para eliminar a dependência de variáveis de ambiente.
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
chave_origem = prefix + "teste.txt"
arquivo_destino = "baixado.txt"

s3.download_file(bucket, chave_origem, arquivo_destino)
print(f"✅ Download concluído como '{arquivo_destino}'")
