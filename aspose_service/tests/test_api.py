from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes import get_converter, get_storage
from app.main import create_app
from app.services.storage import LocalStorage


class FakeConverter:
    def __init__(self) -> None:
        self.calls: list[tuple[Path, str]] = []

    def convert_to_pdf(self, source_path: Path, source_filename: str) -> bytes:
        self.calls.append((source_path, source_filename))
        return b"%PDF-1.7\nfake"


def make_client(tmp_path):
    app = create_app()
    converter = FakeConverter()
    storage = LocalStorage(upload_dir=tmp_path / "uploads", output_dir=tmp_path / "outputs")
    app.dependency_overrides[get_converter] = lambda: converter
    app.dependency_overrides[get_storage] = lambda: storage
    return TestClient(app), converter, storage


def test_health_endpoint(tmp_path):
    client, _, _ = make_client(tmp_path)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_convert_stream_returns_pdf_response(tmp_path):
    client, converter, _ = make_client(tmp_path)

    response = client.post(
        "/api/v1/convert",
        data={"response_mode": "stream"},
        files={"file": ("sample.docx", b"source", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "sample.pdf" in response.headers["content-disposition"]
    assert response.content == b"%PDF-1.7\nfake"
    assert converter.calls[0][1] == "sample.docx"


def test_convert_file_mode_persists_pdf_and_returns_download_metadata(tmp_path):
    client, _, storage = make_client(tmp_path)

    response = client.post(
        "/api/v1/convert",
        data={"response_mode": "file"},
        files={"file": ("sample.xlsx", b"source", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["filename"] == "sample.pdf"
    assert payload["content_type"] == "application/pdf"
    assert payload["download_url"].startswith("/api/v1/files/")
    assert storage.resolve_output(payload["file_id"]).read_bytes() == b"%PDF-1.7\nfake"


def test_download_persisted_file(tmp_path):
    client, _, storage = make_client(tmp_path)
    stored = storage.persist_pdf("sample.docx", b"%PDF-1.7\nfake")

    response = client.get(f"/api/v1/files/{stored.file_id}")

    assert response.status_code == 200
    assert response.content == b"%PDF-1.7\nfake"
    assert response.headers["content-type"] == "application/pdf"


def test_convert_rejects_email_attachment_merge_flag(tmp_path):
    client, _, _ = make_client(tmp_path)

    response = client.post(
        "/api/v1/convert",
        data={"response_mode": "stream", "include_email_attachments": "true"},
        files={"file": ("message.eml", b"source", "message/rfc822")},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "bad_request"
    assert "Email attachment conversion is not available" in response.json()["message"]


def test_convert_rejects_empty_upload(tmp_path):
    client, _, _ = make_client(tmp_path)

    response = client.post(
        "/api/v1/convert",
        data={"response_mode": "stream"},
        files={"file": ("empty.docx", b"", "application/octet-stream")},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "bad_request"
