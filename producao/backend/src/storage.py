import os
import io
import boto3
from botocore.client import Config

ENDPOINT = os.getenv("OBJECT_STORAGE_ENDPOINT")
ACCESS_KEY = os.getenv("OBJECT_STORAGE_ACCESS_KEY")
SECRET_KEY = os.getenv("OBJECT_STORAGE_SECRET_KEY")
BUCKET = os.getenv("OBJECT_STORAGE_BUCKET")

client = None
if ENDPOINT and ACCESS_KEY and SECRET_KEY and BUCKET:
    client = boto3.client(
        "s3",
        endpoint_url=ENDPOINT,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        config=Config(signature_version="s3v4"),
    )


def upload_file(local_path: str, object_name: str) -> None:
    if client:
        client.upload_file(local_path, BUCKET, object_name)


def download_stream(object_name: str, fallback_path: str):
    if client:
        bio = io.BytesIO()
        client.download_fileobj(BUCKET, object_name, bio)
        bio.seek(0)
        return bio
    return open(fallback_path, "rb")


def delete_file(object_name: str) -> None:
    if client:
        try:
            client.delete_object(Bucket=BUCKET, Key=object_name)
        except Exception:
            pass
