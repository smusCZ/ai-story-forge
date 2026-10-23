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
    assert "*" not in cors.options["allow_origins"]
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
