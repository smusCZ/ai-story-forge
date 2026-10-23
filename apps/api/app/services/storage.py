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


def _safe_ext(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}. Allowed: {sorted(ALLOWED_EXTENSIONS)}")
    return ext


async def save_upload(file: UploadFile, folder_id: uuid.UUID) -> tuple[str, str]:
    """
    Save an uploaded file and return (public_url, original_filename).

    Note: this MVP validates extensions only. Content-signature validation and
    streaming size enforcement remain separate hardening work.
    """
    if not file.filename:
        raise ValueError("Filename is required")

    ext = _safe_ext(file.filename)
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise ValueError(f"File too large (max {MAX_FILE_SIZE // 1024 // 1024} MB)")

    folder_path = UPLOAD_ROOT / str(folder_id)
    folder_path.mkdir(parents=True, exist_ok=True)

    new_name = f"{uuid.uuid4().hex}{ext}"
    dest = folder_path / new_name
    dest.write_bytes(content)

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
