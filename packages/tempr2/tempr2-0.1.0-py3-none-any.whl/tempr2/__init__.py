import io
from pathlib import Path
import boto3
import os
from dataclasses import dataclass
import base64
import hashlib
import httpx
import magic


@dataclass
class FileData:
    data: bytes
    content_type: str

    def get_sha256(self) -> str:
        sha256 = hashlib.sha256()
        sha256.update(self.data)
        return sha256.hexdigest()


def load_data(path: str | Path | bytes, content_type: str | None) -> FileData:
    if isinstance(path, bytes):
        if not content_type:
            raise ValueError("content_type must be provided with bytes data")
        return FileData(
            data=path, content_type=content_type or "application/octet-stream"
        )
    if isinstance(path, str):
        if path.startswith("data:"):
            content_type2 = path.split(";")[0].split(":")[1]
            if content_type and content_type != content_type2:
                raise ValueError(
                    f"content_type mismatch: {content_type} != {content_type2}"
                )
            data = base64.urlsafe_b64decode(path.split(",", 1)[1])
            return FileData(data=data, content_type=content_type2)
        if path.startswith("http://") or path.startswith("https://"):
            resp = httpx.get(path)
            resp.raise_for_status()
            content_type2 = resp.headers.get("Content-Type")
            if content_type and content_type2 and content_type != content_type2:
                raise ValueError(
                    f"content_type mismatch: {content_type} != {content_type2}"
                )
            content_type2 = content_type2 or content_type
            if not content_type2:
                raise ValueError("content_type could not be determined")
            return FileData(data=resp.content, content_type=content_type2)
    assert isinstance(path, (str, Path))
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, "rb") as f:
        data = f.read()
    if not content_type:
        content_type = magic.from_file(str(file_path), mime=True)
    return FileData(data=data, content_type=content_type)


def upload(data: str | bytes | Path, content_type: str | None = None) -> str:
    r2 = boto3.client(
        "s3",
        endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_ACCESS_KEY_SECRET"],
    )
    f = load_data(data, content_type=content_type)
    name = f.get_sha256()
    res = r2.list_objects_v2(Bucket=os.environ["R2_BUCKET"], Prefix=name, MaxKeys=1)
    if "Contents" not in res:
        r2.upload_fileobj(
            io.BytesIO(f.data),
            os.environ["R2_BUCKET"],
            name,
            ExtraArgs={"ContentType": f.content_type},
        )
    base_url = os.environ.get("R2_PUBLIC_URL")
    if base_url:
        return f"{base_url.rstrip('/')}/{name}"
    else:
        return name
