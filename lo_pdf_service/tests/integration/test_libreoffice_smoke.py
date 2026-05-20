from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from app.conversion.libreoffice import LibreOfficeConverter
from app.conversion.pdf_ops import validate_pdf


@pytest.mark.integration
def test_libreoffice_converts_text_file_to_pdf(tmp_path: Path) -> None:
    if shutil.which("soffice") is None:
        pytest.skip("LibreOffice soffice binary is not installed")
    input_file = tmp_path / "input.txt"
    output_dir = tmp_path / "out"
    profile_dir = tmp_path / "profile"
    input_file.write_text("Hello from LibreOffice", encoding="utf-8")

    converter = LibreOfficeConverter(soffice_binary="soffice", timeout_seconds=30)
    output = converter.convert_to_pdf(input_file=input_file, output_dir=output_dir, profile_dir=profile_dir)

    validate_pdf(output)
