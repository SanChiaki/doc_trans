from __future__ import annotations

from pathlib import Path

from app.core.config import Settings


def test_settings_use_expected_defaults(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data")

    assert settings.data_dir == tmp_path / "data"
    assert settings.max_upload_bytes == 50 * 1024 * 1024
    assert settings.max_email_attachment_bytes == 100 * 1024 * 1024
    assert settings.max_attachments == 50
    assert settings.request_timeout_seconds == 120
    assert settings.libreoffice_timeout_seconds == 90
    assert settings.max_concurrent_libreoffice == 2
    assert settings.job_retention_seconds == 24 * 60 * 60


def test_settings_create_derived_directories(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data")

    assert settings.work_dir == tmp_path / "data" / "work"
    assert settings.result_dir == tmp_path / "data" / "results"
    assert settings.job_dir == tmp_path / "data" / "jobs"
