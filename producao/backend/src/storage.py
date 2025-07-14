import os
import io
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv, find_dotenv
import logging

# Carrega variáveis de ambiente do arquivo .env, se disponível. Dessa forma,
# usuários podem personalizar as credenciais sem alterar o código-fonte. Caso
# alguma variável não esteja definida, usa-se valores padrão compatíveis com o
# ambiente de desenvolvimento.
load_dotenv(find_dotenv())

ENDPOINT = os.getenv("OBJECT_STORAGE_ENDPOINT", "https://nyc3.digitaloceanspaces.com")
ACCESS_KEY = os.getenv("OBJECT_STORAGE_ACCESS_KEY")
SECRET_KEY = os.getenv("OBJECT_STORAGE_SECRET_KEY")
BUCKET = os.getenv("OBJECT_STORAGE_BUCKET", "radha-arquivos")
PREFIX = os.getenv("OBJECT_STORAGE_PREFIX", "producao/")
PUBLIC_ENDPOINT = os.getenv(
    "OBJECT_STORAGE_PUBLIC_ENDPOINT",
    "https://radha-arquivos.nyc3.digitaloceanspaces.com",
)

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
    ``False`` when the storage reports a 404/NoSuchKey,
    and ``None`` for other errors (network issues or permission problems).
    """
    full_key = _full_key(object_name)
    prefix_info = f"prefix='{PREFIX}'" if PREFIX else "prefix=''"

    if not client:
        missing_vars = [
            name
            for name in (
                "OBJECT_STORAGE_ENDPOINT",
                "OBJECT_STORAGE_ACCESS_KEY",
                "OBJECT_STORAGE_SECRET_KEY",
                "OBJECT_STORAGE_BUCKET",
            )
            if not os.getenv(name)
        ]
        logging.debug(
            "S3 client não inicializado ao checar '%s' (bucket='%s', %s, key='%s'). Variáveis indefinidas: %s",
            object_name,
            BUCKET,
            prefix_info,
            full_key,
            ", ".join(missing_vars) if missing_vars else "nenhuma",
        )
        return None

    try:
        client.head_object(Bucket=BUCKET, Key=full_key)
        logging.debug(
            "Objeto encontrado: bucket='%s', %s, key='%s'",
            BUCKET,
            prefix_info,
            full_key,
        )
        return True
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code")
        logging.debug(
            "head_object falhou: bucket='%s', %s, key='%s', codigo='%s'",
            BUCKET,
            prefix_info,
            full_key,
            code,
        )
        if code in {"404", "NoSuchKey"}:
            return False
        return None
    except Exception as e:
        logging.debug(
            "Erro inesperado em object_exists: bucket='%s', %s, key='%s' → %s",
            BUCKET,
            prefix_info,
            full_key,
            e,
        )
        return None



def get_public_url(object_name: str) -> str:
    """Retorna a URL pública para ``object_name`` no bucket."""
    return f"{PUBLIC_ENDPOINT}/{_full_key(object_name)}"
