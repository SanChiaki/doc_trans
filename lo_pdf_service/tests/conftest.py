from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture()
def temp_settings_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    data_dir = tmp_path / "data"
    monkeypatch.setenv("LOPDF_DATA_DIR", str(data_dir))
    monkeypatch.setenv("LOPDF_MAX_UPLOAD_BYTES", "52428800")
    monkeypatch.setenv("LOPDF_MAX_EMAIL_ATTACHMENT_BYTES", "104857600")
    monkeypatch.setenv("LOPDF_MAX_ATTACHMENTS", "50")
    monkeypatch.setenv("LOPDF_REQUEST_TIMEOUT_SECONDS", "120")
    monkeypatch.setenv("LOPDF_LIBREOFFICE_TIMEOUT_SECONDS", "90")
    monkeypatch.setenv("LOPDF_MAX_CONCURRENT_LIBREOFFICE", "2")
    monkeypatch.setenv("LOPDF_JOB_RETENTION_SECONDS", "86400")
    return data_dir


@pytest.fixture(autouse=True)
def clean_lopdf_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(os.environ):
        if key.startswith("LOPDF_"):
            monkeypatch.delenv(key, raising=False)
