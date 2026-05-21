from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from pypdf import PdfWriter

from app.api.dependencies import get_conversion_service, get_job_store, get_settings_dependency, get_worker
from app.core.config import Settings
from app.jobs.store import LocalJobStore
from app.jobs.worker import InProcessWorker
from app.main import app
from app.models import ConversionOptions, ConversionResult, OutputKind


class FakeService:
    def __init__(self) -> None:
        self.options: list[ConversionOptions] = []

    def convert(
        self, *, input_file: Path, source_filename: str, options: ConversionOptions, workspace_id: str | None = None
    ) -> ConversionResult:
        self.options.append(options)
        result = input_file.parent / "result.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        with result.open("wb") as file:
            writer.write(file)
        return ConversionResult(
            output_path=result,
            output_kind=OutputKind.PDF,
            media_type="application/pdf",
            filename="result.pdf",
        )


def test_sync_conversion_returns_pdf(tmp_path: Path) -> None:
    app.dependency_overrides[get_conversion_service] = lambda: FakeService()
    client = TestClient(app)

    response = client.post(
        "/v1/conversions",
        data={"execution": "sync", "email_mode": "merged", "include_attachments": "true"},
        files={"file": ("input.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    app.dependency_overrides.clear()


def test_api_accepts_spreadsheet_single_page_option(tmp_path: Path) -> None:
    service = FakeService()
    app.dependency_overrides[get_conversion_service] = lambda: service
    client = TestClient(app)

    response = client.post(
        "/v1/conversions",
        data={
            "execution": "sync",
            "email_mode": "merged",
            "include_attachments": "true",
            "spreadsheet_fit_each_sheet_to_one_page": "true",
        },
        files={"file": ("input.xlsx", b"fake", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    assert response.status_code == 200
    assert service.options[0].spreadsheet_fit_each_sheet_to_one_page is True
    app.dependency_overrides.clear()


def test_async_conversion_returns_job_id(tmp_path: Path) -> None:
    store = LocalJobStore(job_dir=tmp_path / "jobs")
    worker = InProcessWorker(service=FakeService(), store=store)
    app.dependency_overrides[get_conversion_service] = lambda: FakeService()
    app.dependency_overrides[get_job_store] = lambda: store
    app.dependency_overrides[get_worker] = lambda: worker
    client = TestClient(app)

    response = client.post(
        "/v1/conversions",
        data={"execution": "async", "email_mode": "merged", "include_attachments": "true"},
        files={"file": ("input.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "queued"
    assert "job_id" in payload
    app.dependency_overrides.clear()


def test_upload_larger_than_configured_limit_is_rejected(tmp_path: Path) -> None:
    app.dependency_overrides[get_settings_dependency] = lambda: Settings(
        data_dir=tmp_path / "data",
        max_upload_bytes=4,
    )
    app.dependency_overrides[get_conversion_service] = lambda: FakeService()
    client = TestClient(app)

    response = client.post(
        "/v1/conversions",
        data={"execution": "sync", "email_mode": "merged", "include_attachments": "true"},
        files={"file": ("input.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "file_too_large"
    app.dependency_overrides.clear()
