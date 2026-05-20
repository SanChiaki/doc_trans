from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter

from app.conversion.pdf_ops import merge_pdfs, validate_pdf
from app.core.errors import AppError, ErrorCode


def make_pdf(path: Path) -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with path.open("wb") as file:
        writer.write(file)


def test_validate_pdf_accepts_readable_pdf(tmp_path: Path) -> None:
    pdf = tmp_path / "input.pdf"
    make_pdf(pdf)

    validate_pdf(pdf)


def test_validate_pdf_rejects_empty_file(tmp_path: Path) -> None:
    pdf = tmp_path / "empty.pdf"
    pdf.write_bytes(b"")

    with pytest.raises(AppError) as exc_info:
        validate_pdf(pdf)

    assert exc_info.value.code == ErrorCode.PDF_VALIDATION_FAILED


def test_merge_pdfs_combines_pages(tmp_path: Path) -> None:
    first = tmp_path / "first.pdf"
    second = tmp_path / "second.pdf"
    output = tmp_path / "merged.pdf"
    make_pdf(first)
    make_pdf(second)

    merge_pdfs([first, second], output)

    assert len(PdfReader(str(output)).pages) == 2
