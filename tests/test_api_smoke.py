from pathlib import Path

from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from app.main import app
from app.services import storage


def test_health_endpoint_returns_service_status():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "ai-story-forge",
        "version": "0.6.0",
    }


def test_openapi_schema_is_available():
    client = TestClient(app)

    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "AI Story Forge API"
    assert "/health" in schema["paths"]


def test_safe_cors_defaults_are_applied():
    cors = next(middleware for middleware in app.user_middleware if middleware.cls is CORSMiddleware)

    assert cors.kwargs["allow_origins"] == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    assert cors.kwargs["allow_credentials"] is False
    assert "*" not in cors.kwargs["allow_origins"]
    assert app.debug is False


def test_upload_mount_and_storage_use_same_root():
    upload_mount = next(route for route in app.routes if getattr(route, "name", None) == "uploads")

    assert storage.UPLOAD_ROOT.resolve() == Path(upload_mount.app.directory).resolve()


def test_delete_file_rejects_paths_outside_upload_root(tmp_path, monkeypatch):
    upload_root = tmp_path / "uploads"
    upload_root.mkdir()
    outside_file = tmp_path / "keep.txt"
    outside_file.write_text("keep me", encoding="utf-8")
    monkeypatch.setattr(storage, "UPLOAD_ROOT", upload_root)

    storage.delete_file("/uploads/../keep.txt")

    assert outside_file.exists()
    assert outside_file.read_text(encoding="utf-8") == "keep me"


class ChunkedUpload:
    def __init__(self, filename, content):
        self.filename = filename
        self.content = content
        self.offset = 0

    async def read(self, size=-1):
        if size < 0:
            size = len(self.content)
        chunk = self.content[self.offset:self.offset + size]
        self.offset += len(chunk)
        return chunk


def test_save_upload_streams_valid_image(tmp_path, monkeypatch):
    import asyncio
    import uuid

    monkeypatch.setattr(storage, "UPLOAD_ROOT", tmp_path)
    folder_id = uuid.uuid4()
    upload = ChunkedUpload("reference.png", b"\x89PNG\r\n\x1a\nimage-data")

    url, original_name = asyncio.run(storage.save_upload(upload, folder_id))

    saved_file = tmp_path / str(folder_id) / url.rsplit("/", 1)[1]
    assert original_name == "reference.png"
    assert url.startswith(f"/uploads/{folder_id}/")
    assert saved_file.read_bytes() == b"\x89PNG\r\n\x1a\nimage-data"
    assert not list(saved_file.parent.glob("*.part"))


def test_save_upload_rejects_mismatched_file_signature(tmp_path, monkeypatch):
    import asyncio
    import uuid
    import pytest

    monkeypatch.setattr(storage, "UPLOAD_ROOT", tmp_path)
    upload = ChunkedUpload("not-really.png", b"this is not a PNG")

    with pytest.raises(ValueError, match="does not match"):
        asyncio.run(storage.save_upload(upload, uuid.uuid4()))

    assert not list(tmp_path.rglob("*.png"))
    assert not list(tmp_path.rglob("*.part"))


def test_save_upload_enforces_size_limit_while_streaming(tmp_path, monkeypatch):
    import asyncio
    import uuid
    import pytest

    monkeypatch.setattr(storage, "UPLOAD_ROOT", tmp_path)
    monkeypatch.setattr(storage, "MAX_FILE_SIZE", 8)
    upload = ChunkedUpload("oversized.png", b"\x89PNG\r\n\x1a\nX")

    with pytest.raises(ValueError, match="File too large"):
        asyncio.run(storage.save_upload(upload, uuid.uuid4()))

    assert not list(tmp_path.rglob("*.part"))
