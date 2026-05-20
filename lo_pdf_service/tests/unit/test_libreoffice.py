from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from app.conversion.libreoffice import LibreOfficeConverter
from app.core.errors import AppError, ErrorCode


def test_libreoffice_uses_isolated_profile_and_validates_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    input_file = tmp_path / "input.docx"
    output_dir = tmp_path / "out"
    profile_dir = tmp_path / "profile"
    input_file.write_bytes(b"fake")
    output_dir.mkdir()
    profile_dir.mkdir()

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        assert "--headless" in command
        assert f"-env:UserInstallation={profile_dir.as_uri()}" in command
        assert str(input_file) in command
        (output_dir / "input.pdf").write_bytes(b"%PDF-1.4\n%fake\n")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr("app.conversion.libreoffice.validate_pdf", lambda path: None)

    converter = LibreOfficeConverter(soffice_binary="soffice", timeout_seconds=10)
    result = converter.convert_to_pdf(input_file=input_file, output_dir=output_dir, profile_dir=profile_dir)

    assert result == output_dir / "input.pdf"


def test_libreoffice_timeout_maps_to_app_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    input_file = tmp_path / "input.docx"
    output_dir = tmp_path / "out"
    profile_dir = tmp_path / "profile"
    input_file.write_bytes(b"fake")
    output_dir.mkdir()
    profile_dir.mkdir()

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(command, timeout=1)

    monkeypatch.setattr(subprocess, "run", fake_run)

    converter = LibreOfficeConverter(soffice_binary="soffice", timeout_seconds=1)
    with pytest.raises(AppError) as exc_info:
        converter.convert_to_pdf(input_file=input_file, output_dir=output_dir, profile_dir=profile_dir)

    assert exc_info.value.code == ErrorCode.CONVERSION_TIMEOUT
