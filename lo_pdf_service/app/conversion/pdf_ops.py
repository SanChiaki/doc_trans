from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader, PdfWriter

from app.core.errors import AppError, ErrorCode


def validate_pdf(path: Path) -> None:
    if not path.exists() or path.stat().st_size == 0:
        raise AppError(
            code=ErrorCode.PDF_VALIDATION_FAILED,
            message="PDF file is missing or empty.",
            details={"path": str(path)},
        )
    try:
        reader = PdfReader(str(path))
        if len(reader.pages) == 0:
            raise ValueError("PDF has no pages")
    except Exception as exc:
        raise AppError(
            code=ErrorCode.PDF_VALIDATION_FAILED,
            message="PDF file could not be read.",
            details={"path": str(path), "reason": str(exc)},
        ) from exc


def merge_pdfs(inputs: list[Path], output: Path) -> None:
    writer = PdfWriter()
    for input_path in inputs:
        validate_pdf(input_path)
        reader = PdfReader(str(input_path))
        for page in reader.pages:
            writer.add_page(page)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as file:
        writer.write(file)
    validate_pdf(output)
