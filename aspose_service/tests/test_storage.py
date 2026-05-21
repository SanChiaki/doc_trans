from pathlib import Path

import pytest

from app.core.errors import BadRequestError
from app.services.storage import LocalStorage


def test_save_upload_writes_bytes_with_safe_extension(tmp_path):
    storage = LocalStorage(upload_dir=tmp_path / "uploads", output_dir=tmp_path / "outputs")

    saved_path = storage.save_upload("Quarter Report.DOCX", b"source-bytes")

    assert saved_path.exists()
    assert saved_path.read_bytes() == b"source-bytes"
    assert saved_path.suffix == ".docx"
    assert saved_path.parent == tmp_path / "uploads"


def test_save_upload_rejects_empty_content(tmp_path):
    storage = LocalStorage(upload_dir=tmp_path / "uploads", output_dir=tmp_path / "outputs")

    with pytest.raises(BadRequestError) as exc_info:
        storage.save_upload("empty.docx", b"")

    assert "Uploaded file is empty" in exc_info.value.message


def test_persist_pdf_creates_file_id_and_download_name(tmp_path):
    storage = LocalStorage(upload_dir=tmp_path / "uploads", output_dir=tmp_path / "outputs")

    stored = storage.persist_pdf(source_filename="report.docx", pdf_bytes=b"%PDF-1.7")

    assert stored.path.exists()
    assert stored.path.read_bytes() == b"%PDF-1.7"
    assert stored.path.suffix == ".pdf"
    assert stored.download_filename == "report.pdf"
    assert storage.resolve_output(stored.file_id) == stored.path


def test_resolve_output_rejects_missing_file_id(tmp_path):
    storage = LocalStorage(upload_dir=tmp_path / "uploads", output_dir=tmp_path / "outputs")

    with pytest.raises(BadRequestError) as exc_info:
        storage.resolve_output("missing")

    assert "File not found" in exc_info.value.message


def test_cleanup_removes_existing_temp_file(tmp_path):
    storage = LocalStorage(upload_dir=tmp_path / "uploads", output_dir=tmp_path / "outputs")
    temp_file = Path(storage.save_upload("sample.docx", b"abc"))

    storage.cleanup_temp_file(temp_file)

    assert not temp_file.exists()
