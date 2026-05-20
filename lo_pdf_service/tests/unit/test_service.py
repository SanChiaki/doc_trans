from __future__ import annotations

from pathlib import Path

from pypdf import PdfWriter

from app.conversion.service import ConversionService
from app.models import ConversionOptions, EmailMode, OutputKind
from app.storage.local import LocalStorage


class FakeOfficeConverter:
    def convert_to_pdf(self, *, input_file: Path, output_dir: Path, profile_dir: Path) -> Path:
        output = output_dir / f"{input_file.stem}.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        with output.open("wb") as file:
            writer.write(file)
        return output


def test_service_converts_office_file_to_pdf(tmp_path: Path) -> None:
    storage = LocalStorage(base_dir=tmp_path)
    service = ConversionService(storage=storage, office_converter=FakeOfficeConverter())
    input_file = tmp_path / "input.txt"
    input_file.write_text("hello", encoding="utf-8")

    result = service.convert(input_file=input_file, source_filename="input.txt", options=ConversionOptions())

    assert result.output_kind == OutputKind.PDF
    assert result.output_path.exists()


def test_service_routes_email_to_email_converter(tmp_path: Path) -> None:
    storage = LocalStorage(base_dir=tmp_path)
    service = ConversionService(storage=storage, office_converter=FakeOfficeConverter())
    input_file = tmp_path / "message.eml"
    input_file.write_text("From: a@example.com\nTo: b@example.com\nSubject: Hi\n\nBody", encoding="utf-8")

    result = service.convert(
        input_file=input_file,
        source_filename="message.eml",
        options=ConversionOptions(email_mode=EmailMode.SPLIT),
    )

    assert result.output_kind == OutputKind.ZIP
