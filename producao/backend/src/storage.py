import os
import io
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

# Configurações fixas de acesso ao bucket S3. Estes valores eram lidos do
# ``.env`` em tempo de execução, porém para evitar falhas devido ao
# carregamento incorreto do arquivo agora ficam definidos diretamente no
# código.
ENDPOINT = "https://nyc3.digitaloceanspaces.com"
ACCESS_KEY = "DO801RVLRYQAQ7ZBKxxx"
SECRET_KEY = "0D4o8nUESJUP0X3WyUuaDiO9DNysuACxJKSOCL4dxxxx"
BUCKET = "radha-arquivos"
PREFIX = "producao/"
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


def _full_key(name: str) -> str:
    """Retorna ``name`` acrescido do prefixo configurado.

    Caso ``name`` já comece com ``PREFIX`` ele é retornado sem alterações
    para evitar duplicação do prefixo.
    """
    if name.startswith(PREFIX):
        return name
    return f"{PREFIX.rstrip('/')}/{name.lstrip('/')}"


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


def object_exists(object_name: str) -> bool | None:
    """Check if ``object_name`` exists in the bucket.

    Returns ``True`` when the object is confirmed in the bucket,
    ``False`` when the storage reports a 404/NoSuchKey, and ``None``
    for other errors (network issues or permission problems).
    """
    if not client:
        return False
    try:
        client.head_object(Bucket=BUCKET, Key=_full_key(object_name))
        return True
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code")
        if code in {"404", "NoSuchKey"}:
            return False
        print(f"[DEBUG] Erro em object_exists: {_full_key(object_name)} → {code}")
        return None
    except Exception as e:
        print(f"[DEBUG] Erro inesperado em object_exists: {_full_key(object_name)} → {e}")
        return None


def get_public_url(object_name: str) -> str:
    """Retorna a URL pública para ``object_name`` no bucket."""
    return f"{PUBLIC_ENDPOINT}/{_full_key(object_name)}"
