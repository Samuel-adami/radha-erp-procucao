import os
import uuid
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
import boto3
from botocore.config import Config

load_dotenv(find_dotenv())

ENDPOINT = os.getenv("OBJECT_STORAGE_ENDPOINT")
ACCESS_KEY = os.getenv("OBJECT_STORAGE_ACCESS_KEY")
SECRET_KEY = os.getenv("OBJECT_STORAGE_SECRET_KEY")
BUCKET = os.getenv("OBJECT_STORAGE_BUCKET", "radha-arquivos")
PREFIX = os.getenv("OBJECT_STORAGE_PREFIX", "")
PUBLIC_ENDPOINT = os.getenv(
    "OBJECT_STORAGE_PUBLIC_ENDPOINT",
    ENDPOINT if ENDPOINT else f"https://{BUCKET}.s3.amazonaws.com",
)
REGION = os.getenv("OBJECT_STORAGE_REGION", "us-east-1")

client = None
if ENDPOINT and ACCESS_KEY and SECRET_KEY:
    client = boto3.client(
        "s3",
        region_name=REGION,
        endpoint_url=ENDPOINT,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        config=Config(signature_version="s3v4"),
    )


def _full_key(name: str) -> str:
    if PREFIX:
        return f"{PREFIX.rstrip('/')}/{name.lstrip('/')}"
    return name.lstrip("/")


def upload_fileobj(fileobj, filename: str) -> str:
    """Envia ``fileobj`` para o bucket e retorna a chave gerada."""
    if not client:
        return ""
    key = _full_key(f"ocorrencias/{uuid.uuid4()}_{Path(filename).name}")
    client.upload_fileobj(fileobj, BUCKET, key)
    return key


def delete_file(key: str) -> None:
    if client and key:
        try:
            client.delete_object(Bucket=BUCKET, Key=_full_key(key))
        except Exception:
            pass


def get_public_url(key: str) -> str:
    if not key:
        return ""
    base = PUBLIC_ENDPOINT.rstrip("/")
    return f"{base}/{_full_key(key)}"
