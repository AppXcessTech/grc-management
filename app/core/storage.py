import os
import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile

UPLOAD_DIR = Path("data/uploads")

# S3/MinIO configuration from environment
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "")
S3_BUCKET = os.getenv("S3_BUCKET", "appxcess-evidence")
S3_REGION = os.getenv("S3_REGION", "us-east-1")

_use_s3 = bool(S3_ENDPOINT and S3_ACCESS_KEY and S3_SECRET_KEY)
_s3_client = None


def _get_s3_client():
    global _s3_client
    if _s3_client is None:
        import boto3
        _s3_client = boto3.client(
            "s3",
            endpoint_url=S3_ENDPOINT,
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY,
            region_name=S3_REGION,
        )
    return _s3_client


def save_upload_file(upload_file: UploadFile, sub_dir: str = "") -> str:
    if _use_s3:
        return _save_to_s3(upload_file, sub_dir)
    return _save_to_local(upload_file, sub_dir)


def _save_to_local(upload_file: UploadFile, sub_dir: str = "") -> str:
    dest_dir = UPLOAD_DIR / sub_dir
    dest_dir.mkdir(parents=True, exist_ok=True)

    file_extension = Path(upload_file.filename or "file").suffix
    file_name = f"{uuid.uuid4()}{file_extension}"
    file_path = dest_dir / file_name

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    return str(file_path)


def _save_to_s3(upload_file: UploadFile, sub_dir: str = "") -> str:
    file_extension = Path(upload_file.filename or "file").suffix
    file_name = f"{uuid.uuid4()}{file_extension}"
    key = f"{sub_dir}/{file_name}" if sub_dir else file_name
    key = key.lstrip("/")

    client = _get_s3_client()
    client.upload_fileobj(upload_file.file, S3_BUCKET, key)

    return f"s3://{S3_BUCKET}/{key}"


def get_file_url(file_path: str) -> str:
    if file_path.startswith("s3://"):
        return _get_s3_url(file_path)
    return file_path


def _get_s3_url(s3_path: str) -> str:
    key = s3_path.replace(f"s3://{S3_BUCKET}/", "")
    client = _get_s3_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": key},
        ExpiresIn=3600,
    )


def delete_file(file_path: str):
    if file_path.startswith("s3://"):
        return _delete_from_s3(file_path)
    path = Path(file_path)
    if path.exists():
        os.remove(path)


def _delete_from_s3(s3_path: str):
    key = s3_path.replace(f"s3://{S3_BUCKET}/", "")
    client = _get_s3_client()
    client.delete_object(Bucket=S3_BUCKET, Key=key)
