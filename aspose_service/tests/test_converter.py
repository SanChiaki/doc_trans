from pathlib import Path

import pytest

from app.core.errors import UnsupportedFormatError
from app.services.converter import DocumentConverter


class FakeAsposeAdapters:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Path, Path]] = []

    def convert_word(self, source_path: Path, output_path: Path) -> None:
        self.calls.append(("word", source_path, output_path))
        output_path.write_bytes(b"word-pdf")

    def convert_excel(self, source_path: Path, output_path: Path) -> None:
        self.calls.append(("excel", source_path, output_path))
        output_path.write_bytes(b"excel-pdf")

    def convert_presentation(self, source_path: Path, output_path: Path) -> None:
        self.calls.append(("presentation", source_path, output_path))
        output_path.write_bytes(b"presentation-pdf")

    def convert_email(self, source_path: Path, output_path: Path) -> None:
        self.calls.append(("email", source_path, output_path))
        output_path.write_bytes(b"email-pdf")


@pytest.mark.parametrize(
    ("filename", "expected_family", "expected_pdf"),
    [
        ("sample.docx", "word", b"word-pdf"),
        ("sample.xlsx", "excel", b"excel-pdf"),
        ("sample.pptx", "presentation", b"presentation-pdf"),
        ("sample.eml", "email", b"email-pdf"),
    ],
)
def test_convert_dispatches_by_document_family(tmp_path, filename, expected_family, expected_pdf):
    source_path = tmp_path / filename
    source_path.write_bytes(b"input")
    adapters = FakeAsposeAdapters()
    converter = DocumentConverter(adapters=adapters, work_dir=tmp_path / "work")

    result = converter.convert_to_pdf(source_path=source_path, source_filename=filename)

    assert result == expected_pdf
    assert adapters.calls[0][0] == expected_family
    assert adapters.calls[0][1] == source_path
    assert adapters.calls[0][2].suffix == ".pdf"


def test_convert_rejects_unsupported_extension(tmp_path):
    source_path = tmp_path / "sample.zip"
    source_path.write_bytes(b"input")
    converter = DocumentConverter(adapters=FakeAsposeAdapters(), work_dir=tmp_path / "work")

    with pytest.raises(UnsupportedFormatError):
        converter.convert_to_pdf(source_path=source_path, source_filename="sample.zip")
