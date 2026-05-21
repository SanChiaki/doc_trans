from __future__ import annotations

from pathlib import Path

from pypdf import PdfWriter

from app.conversion.service import ConversionService
from app.models import ConversionOptions, EmailMode, OutputKind
from app.storage.local import LocalStorage


class FakeOfficeConverter:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def convert_to_pdf(
        self,
        *,
        input_file: Path,
        output_dir: Path,
        profile_dir: Path,
        fit_spreadsheet_sheets_to_one_page: bool = False,
    ) -> Path:
        self.calls.append(
            {
                "input_file": input_file,
                "fit_spreadsheet_sheets_to_one_page": fit_spreadsheet_sheets_to_one_page,
            }
        )
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


def test_service_passes_spreadsheet_single_page_option_only_for_spreadsheets(tmp_path: Path) -> None:
    storage = LocalStorage(base_dir=tmp_path)
    office_converter = FakeOfficeConverter()
    service = ConversionService(storage=storage, office_converter=office_converter)
    xlsx_file = tmp_path / "report.xlsx"
    docx_file = tmp_path / "letter.docx"
    xlsx_file.write_bytes(b"fake xlsx")
    docx_file.write_bytes(b"fake docx")

    service.convert(
        input_file=xlsx_file,
        source_filename="report.xlsx",
        options=ConversionOptions(spreadsheet_fit_each_sheet_to_one_page=True),
    )
    service.convert(
        input_file=docx_file,
        source_filename="letter.docx",
        options=ConversionOptions(spreadsheet_fit_each_sheet_to_one_page=True),
    )

    assert [call["fit_spreadsheet_sheets_to_one_page"] for call in office_converter.calls] == [True, False]


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
