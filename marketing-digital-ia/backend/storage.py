import os
import io
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv, find_dotenv
import logging

load_dotenv(find_dotenv())

ENDPOINT = os.getenv("OBJECT_STORAGE_ENDPOINT", "https://nyc3.digitaloceanspaces.com")
ACCESS_KEY = os.getenv("OBJECT_STORAGE_ACCESS_KEY")
SECRET_KEY = os.getenv("OBJECT_STORAGE_SECRET_KEY")
BUCKET = os.getenv("OBJECT_STORAGE_BUCKET", "radha-arquivos")
PREFIX = os.getenv("OBJECT_STORAGE_PREFIX", "marketing/")
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


def _full_key(name: str) -> str:
    if name.startswith(PREFIX):
        return name
    if name.startswith(f"/{PREFIX}"):
        return name.lstrip("/")
    return f"{PREFIX.rstrip('/')}/{name.lstrip('/')}"


def upload_file(local_path: str, object_name: str) -> None:
    if client:
        with open(local_path, "rb") as f:
            client.upload_fileobj(f, BUCKET, _full_key(object_name))


def get_public_url(object_name: str) -> str:
    return f"{PUBLIC_ENDPOINT}/{_full_key(object_name)}"
