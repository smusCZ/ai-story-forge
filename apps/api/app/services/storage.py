"""
Image storage service.
MVP: local filesystem under /uploads
Production-ready: easily switchable to MinIO / S3 (already in docker-compose).
"""
import os
import uuid
from pathlib import Path
from fastapi import UploadFile

UPLOAD_ROOT = Path(os.getenv("UPLOAD_ROOT", "/tmp/ai-story-forge/uploads"))
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB


def _safe_ext(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}. Allowed: {ALLOWED_EXTENSIONS}")
    return ext


async def save_upload(file: UploadFile, folder_id: uuid.UUID) -> tuple[str, str]:
    """
    Saves uploaded file and returns (public_url, original_filename).
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
    """Best-effort delete of local file."""
    if url.startswith("/uploads/"):
        path = UPLOAD_ROOT / url.replace("/uploads/", "", 1)
        if path.exists():
            path.unlink(missing_ok=True)
