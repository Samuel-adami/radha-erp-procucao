import os
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

REGION = os.getenv("OBJECT_STORAGE_REGION", "nyc3")

client = None
if ENDPOINT and ACCESS_KEY and SECRET_KEY and BUCKET:
    client = boto3.client(
        "s3",
        region_name=REGION,
        endpoint_url=ENDPOINT,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        config=Config(signature_version="s3v4"),
    )


def storage_config_summary() -> str:
    """Return a short string describing the configured storage."""
    ak = "set" if ACCESS_KEY else "missing"
    sk = "set" if SECRET_KEY else "missing"
    return (
        f"endpoint='{ENDPOINT}', bucket='{BUCKET}', prefix='{PREFIX}', "
        f"access_key={ak}, secret_key={sk}"
    )


def _full_key(name: str) -> str:
    if name.startswith(PREFIX):
        return name  # já tem o prefixo, não adiciona novamente
    if name.startswith(f"/{PREFIX}"):
        return name.lstrip("/")
    # Garante que não duplica prefixo nem barra
    return f"{PREFIX.rstrip('/')}/{name.lstrip('/')}"



def upload_file(local_path: str, object_name: str) -> None:
    if client:
        with open(local_path, "rb") as f:
            client.upload_fileobj(f, BUCKET, _full_key(object_name))


def upload_bytes(data: bytes, object_name: str) -> None:
    """Envia o conteúdo de ``data`` diretamente para ``object_name`` no bucket.

    A função ignora silenciosamente caso o cliente não esteja configurado,
    permitindo que ambientes de desenvolvimento sem credenciais funcionem
    normalmente.
    """
    if client:
        client.put_object(Bucket=BUCKET, Key=_full_key(object_name), Body=data)


def download_stream(object_name: str, fallback_path: str):
    """Fetch ``object_name`` from storage and return a readable stream.

    Para evitar o consumo excessivo de memória em arquivos grandes, o
    conteúdo é baixado para ``fallback_path`` e lido diretamente do disco.
    Caso o cliente S3 não esteja configurado ou o download falhe, o caminho
    local é utilizado como está.
    """

    if client:
        try:
            client.download_file(BUCKET, _full_key(object_name), fallback_path)
        except Exception:
            pass
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
        logging.warning(
            "S3 client não inicializado ao checar '%s' (bucket='%s', %s, key='%s'). Variáveis indefinidas: %s",
            object_name,
            BUCKET,
            prefix_info,
            full_key,
            ", ".join(missing_vars) if missing_vars else "nenhuma",
        )
    return None

def get_object_size(object_name: str) -> int | None:
    """Retorna o tamanho (em bytes) do objeto, ou None se não disponível."""
    if client:
        try:
            resp = client.head_object(Bucket=BUCKET, Key=_full_key(object_name))
            return resp.get("ContentLength")
        except Exception:
            return None
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
        logging.warning(
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
        logging.warning(
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
