import os
import io
import boto3
from botocore.client import Config
from dotenv import load_dotenv, find_dotenv

# Garantir que variáveis de ambiente do .env sejam carregadas antes de
# inicializar o cliente S3. Sem isso, ``client`` ficaria ``None`` quando o
# módulo fosse importado antes de ``database.py``.
load_dotenv(find_dotenv())

ENDPOINT = os.getenv("OBJECT_STORAGE_ENDPOINT")
ACCESS_KEY = os.getenv("OBJECT_STORAGE_ACCESS_KEY")
SECRET_KEY = os.getenv("OBJECT_STORAGE_SECRET_KEY")
BUCKET = os.getenv("OBJECT_STORAGE_BUCKET", "radha-arquivos")
PREFIX = os.getenv("OBJECT_STORAGE_PREFIX", "producao/")
PUBLIC_ENDPOINT = "https://radha-arquivos.nyc3.digitaloceanspaces.com"

client = None
if ENDPOINT and ACCESS_KEY and SECRET_KEY and BUCKET:
    client = boto3.client(
        "s3",
        endpoint_url=ENDPOINT,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        config=Config(signature_version="s3v4"),
    )


def _full_key(key: str) -> str:
    return key if key.startswith(PREFIX) else f"{PREFIX}{key}"


def upload_file(local_path: str, object_name: str) -> None:
    if client:
        with open(local_path, "rb") as f:
            client.upload_fileobj(f, BUCKET, _full_key(object_name))


def download_stream(object_name: str, fallback_path: str):
    if client:
        bio = io.BytesIO()
        client.download_fileobj(BUCKET, _full_key(object_name), bio)
        bio.seek(0)
        return bio
    return open(fallback_path, "rb")


def delete_file(object_name: str) -> None:
    if client:
        try:
            client.delete_object(Bucket=BUCKET, Key=_full_key(object_name))
        except Exception:
            pass


def download_file(object_name: str, local_path: str) -> None:
    if client:
        client.download_file(BUCKET, _full_key(object_name), local_path)


def object_exists(object_name: str) -> bool:
    if not client:
        return False
    try:
        client.head_object(Bucket=BUCKET, Key=_full_key(object_name))
        return True
    except Exception as e:
        print(f"[DEBUG] Erro em object_exists: {_full_key(object_name)} → {e}")
        return False


def get_public_url(object_name: str) -> str:
    """Retorna a URL pública para ``object_name`` no bucket."""
    return f"{PUBLIC_ENDPOINT}/{_full_key(object_name)}"
