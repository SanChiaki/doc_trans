from __future__ import annotations

from email.message import EmailMessage
from pathlib import Path
from zipfile import ZipFile

import pytest
from pypdf import PdfReader, PdfWriter

from app.conversion.email_converter import EmailAttachment, EmailConverter, ParsedEmail
from app.core.errors import AppError, ErrorCode
from app.models import ConversionOptions, EmailMode, OutputKind


class FakeOfficeConverter:
    def convert_to_pdf(self, *, input_file: Path, output_dir: Path, profile_dir: Path) -> Path:
        output = output_dir / f"{input_file.stem}.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        with output.open("wb") as file:
            writer.write(file)
        return output


def write_message(path: Path) -> None:
    message = EmailMessage()
    message["From"] = "sender@example.com"
    message["To"] = "receiver@example.com"
    message["Subject"] = "Quarterly report"
    message.set_content("Plain body")
    message.add_attachment(
        b"attachment text",
        maintype="text",
        subtype="plain",
        filename="notes.txt",
    )
    path.write_bytes(message.as_bytes())


def test_email_split_creates_zip_with_message_attachment_and_manifest(tmp_path: Path) -> None:
    source = tmp_path / "message.eml"
    output_dir = tmp_path / "out"
    profile_dir = tmp_path / "profile"
    write_message(source)
    output_dir.mkdir()
    profile_dir.mkdir()

    converter = EmailConverter(office_converter=FakeOfficeConverter())
    result = converter.convert(
        input_file=source,
        output_dir=output_dir,
        profile_dir=profile_dir,
        options=ConversionOptions(email_mode=EmailMode.SPLIT),
    )

    assert result.output_kind == OutputKind.ZIP
    with ZipFile(result.output_path) as archive:
        names = set(archive.namelist())
    assert "message.pdf" in names
    assert "attachments/notes.pdf" in names
    assert "manifest.json" in names


def test_email_rejects_too_many_attachments(tmp_path: Path) -> None:
    source = tmp_path / "message.eml"
    output_dir = tmp_path / "out"
    profile_dir = tmp_path / "profile"
    write_message(source)
    output_dir.mkdir()
    profile_dir.mkdir()

    converter = EmailConverter(office_converter=FakeOfficeConverter())
    with pytest.raises(AppError) as exc_info:
        converter.convert(
            input_file=source,
            output_dir=output_dir,
            profile_dir=profile_dir,
            options=ConversionOptions(email_mode=EmailMode.SPLIT, max_attachments=0),
        )

    assert exc_info.value.code == ErrorCode.TOO_MANY_ATTACHMENTS


def test_email_merged_creates_single_pdf(tmp_path: Path) -> None:
    source = tmp_path / "message.eml"
    output_dir = tmp_path / "out"
    profile_dir = tmp_path / "profile"
    write_message(source)
    output_dir.mkdir()
    profile_dir.mkdir()

    converter = EmailConverter(office_converter=FakeOfficeConverter())
    result = converter.convert(
        input_file=source,
        output_dir=output_dir,
        profile_dir=profile_dir,
        options=ConversionOptions(email_mode=EmailMode.MERGED),
    )

    assert result.output_kind == OutputKind.PDF
    assert len(PdfReader(str(result.output_path)).pages) == 2


def test_msg_parser_path_is_used_for_msg_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "message.msg"
    output_dir = tmp_path / "out"
    profile_dir = tmp_path / "profile"
    source.write_bytes(b"fake msg")
    output_dir.mkdir()
    profile_dir.mkdir()

    def fake_parse_msg(self: EmailConverter, input_file: Path) -> ParsedEmail:
        message = EmailMessage()
        message["From"] = "sender@example.com"
        message["To"] = "receiver@example.com"
        message["Subject"] = "MSG body"
        message.set_content("Body from msg")
        return ParsedEmail(
            message=message,
            attachments=[EmailAttachment(filename="notes.txt", payload=b"attachment text")],
        )

    monkeypatch.setattr(EmailConverter, "_parse_msg", fake_parse_msg)

    converter = EmailConverter(office_converter=FakeOfficeConverter())
    result = converter.convert(
        input_file=source,
        output_dir=output_dir,
        profile_dir=profile_dir,
        options=ConversionOptions(email_mode=EmailMode.SPLIT),
    )

    assert result.output_kind == OutputKind.ZIP
    with ZipFile(result.output_path) as archive:
        assert "attachments/notes.pdf" in set(archive.namelist())
