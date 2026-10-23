"""
Image storage service.
MVP: local filesystem under /uploads.
The API mount and this service share UPLOAD_ROOT from application settings.
"""
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings

UPLOAD_ROOT = Path(get_settings().upload_root).expanduser()
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB
CHUNK_SIZE = 1024 * 1024

_IMAGE_SIGNATURES = {
    ".jpg": lambda data: data.startswith(b"\xff\xd8\xff"),
    ".jpeg": lambda data: data.startswith(b"\xff\xd8\xff"),
    ".png": lambda data: data.startswith(b"\x89PNG\r\n\x1a\n"),
    ".gif": lambda data: data.startswith((b"GIF87a", b"GIF89a")),
    ".bmp": lambda data: data.startswith(b"BM"),
    ".webp": lambda data: len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP",
}


def _safe_ext(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}. Allowed: {sorted(ALLOWED_EXTENSIONS)}")
    return ext


async def save_upload(file: UploadFile, folder_id: uuid.UUID) -> tuple[str, str]:
    """
    Stream an upload to disk with a hard size limit and basic file-signature
    validation. Signature checks are a first filter, not full image decoding.
    """
    if not file.filename:
        raise ValueError("Filename is required")

    ext = _safe_ext(file.filename)
    folder_path = UPLOAD_ROOT / str(folder_id)
    folder_path.mkdir(parents=True, exist_ok=True)

    new_name = f"{uuid.uuid4().hex}{ext}"
    dest = folder_path / new_name
    temp_path = folder_path / f".{new_name}.part"
    size = 0
    header = bytearray()

    try:
        with temp_path.open("wb") as output:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break

                size += len(chunk)
                if size > MAX_FILE_SIZE:
                    raise ValueError(
                        f"File too large (max {MAX_FILE_SIZE // 1024 // 1024} MB)"
                    )

                if len(header) < 12:
                    header.extend(chunk[:12 - len(header)])
                output.write(chunk)

        if not _IMAGE_SIGNATURES[ext](bytes(header)):
            raise ValueError("File content does not match an allowed image type")

        temp_path.replace(dest)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise

    public_url = f"/uploads/{folder_id}/{new_name}"
    return public_url, file.filename


def delete_file(url: str) -> None:
    """Best-effort delete of a file stored under the uploads URL prefix."""
    if url.startswith("/uploads/"):
        relative_path = url.removeprefix("/uploads/")
        path = (UPLOAD_ROOT / relative_path).resolve()
        root = UPLOAD_ROOT.resolve()
        if path != root and root in path.parents and path.exists():
            path.unlink(missing_ok=True)
