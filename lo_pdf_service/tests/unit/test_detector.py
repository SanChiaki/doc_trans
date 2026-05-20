from __future__ import annotations

import pytest

from app.conversion.detector import FileCategory, detect_file_type
from app.core.errors import AppError, ErrorCode


@pytest.mark.parametrize(
    ("filename", "category"),
    [
        ("letter.doc", FileCategory.OFFICE),
        ("letter.docx", FileCategory.OFFICE),
        ("sheet.xlsx", FileCategory.OFFICE),
        ("slides.pptx", FileCategory.OFFICE),
        ("notes.txt", FileCategory.OFFICE),
        ("page.html", FileCategory.OFFICE),
        ("report.pdf", FileCategory.PDF),
        ("mail.eml", FileCategory.EMAIL),
        ("mail.msg", FileCategory.EMAIL),
        ("scan.png", FileCategory.IMAGE),
        ("photo.jpeg", FileCategory.IMAGE),
    ],
)
def test_detect_supported_file_categories(filename: str, category: FileCategory) -> None:
    detected = detect_file_type(filename)

    assert detected.category == category
    assert detected.extension == filename.rsplit(".", 1)[1].lower()


def test_detection_is_case_insensitive() -> None:
    assert detect_file_type("REPORT.PDF").category == FileCategory.PDF


def test_rejects_unsupported_extension() -> None:
    with pytest.raises(AppError) as exc_info:
        detect_file_type("drawing.vsdx")

    assert exc_info.value.code == ErrorCode.UNSUPPORTED_FILE_TYPE
