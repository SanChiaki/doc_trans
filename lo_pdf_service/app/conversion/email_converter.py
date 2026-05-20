from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from email import policy
from email.message import EmailMessage, Message
from email.parser import BytesParser
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import extract_msg

from app.conversion.detector import FileCategory, detect_file_type
from app.conversion.image_converter import image_to_pdf
from app.conversion.manifest import AttachmentRecord, ConversionManifest
from app.conversion.pdf_ops import merge_pdfs, validate_pdf
from app.core.errors import AppError, ErrorCode
from app.models import ConversionOptions, ConversionResult, EmailMode, OutputKind


SAFE_NAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


def safe_stem(filename: str) -> str:
    stem = Path(filename).stem or "attachment"
    cleaned = SAFE_NAME_PATTERN.sub("_", stem).strip("._")
    return cleaned or "attachment"


@dataclass(frozen=True)
class EmailAttachment:
    filename: str
    payload: bytes


@dataclass(frozen=True)
class ParsedEmail:
    message: Message
    attachments: list[EmailAttachment]


class EmailConverter:
    def __init__(self, *, office_converter: object) -> None:
        self.office_converter = office_converter

    def convert(
        self,
        *,
        input_file: Path,
        output_dir: Path,
        profile_dir: Path,
        options: ConversionOptions,
    ) -> ConversionResult:
        parsed = self._parse_message(input_file)
        message = parsed.message
        manifest = ConversionManifest(
            source_filename=input_file.name,
            output_kind=OutputKind.ZIP if options.email_mode == EmailMode.SPLIT else OutputKind.PDF,
        )
        message_pdf = self._render_message_pdf(message, output_dir, profile_dir)
        manifest.add_output("message", Path("message.pdf"))
        attachment_pdfs = self._convert_attachments(parsed.attachments, output_dir, profile_dir, options, manifest)

        if options.email_mode == EmailMode.SPLIT:
            zip_path = output_dir / f"{input_file.stem}.zip"
            self._write_split_zip(zip_path, message_pdf, attachment_pdfs, manifest)
            return ConversionResult(
                output_path=zip_path,
                output_kind=OutputKind.ZIP,
                media_type="application/zip",
                filename=zip_path.name,
                manifest=manifest.to_dict(),
            )

        merged_path = output_dir / f"{input_file.stem}.pdf"
        merge_pdfs([message_pdf, *attachment_pdfs], merged_path)
        return ConversionResult(
            output_path=merged_path,
            output_kind=OutputKind.PDF,
            media_type="application/pdf",
            filename=merged_path.name,
            manifest=manifest.to_dict(),
        )

    def _parse_message(self, input_file: Path) -> ParsedEmail:
        if input_file.suffix.lower() == ".msg":
            return self._parse_msg(input_file)
        return self._parse_eml(input_file)

    def _parse_eml(self, input_file: Path) -> ParsedEmail:
        try:
            message = BytesParser(policy=policy.default).parsebytes(input_file.read_bytes())
            attachments = [
                EmailAttachment(
                    filename=part.get_filename() or "attachment",
                    payload=part.get_payload(decode=True) or b"",
                )
                for part in message.iter_attachments()
            ]
            return ParsedEmail(message=message, attachments=attachments)
        except Exception as exc:
            raise AppError(
                code=ErrorCode.EMAIL_PARSE_FAILED,
                message="Email file could not be parsed.",
                details={"input_file": str(input_file), "reason": str(exc)},
            ) from exc

    def _parse_msg(self, input_file: Path) -> ParsedEmail:
        try:
            msg = extract_msg.Message(str(input_file))
            message = EmailMessage(policy=policy.default)
            message["From"] = msg.sender or ""
            message["To"] = msg.to or ""
            message["Cc"] = msg.cc or ""
            message["Subject"] = msg.subject or ""
            message["Date"] = str(msg.date or "")
            if msg.htmlBody:
                html_body = (
                    msg.htmlBody.decode("utf-8", errors="replace")
                    if isinstance(msg.htmlBody, bytes)
                    else str(msg.htmlBody)
                )
                message.set_content(msg.body or "")
                message.add_alternative(html_body, subtype="html")
            else:
                message.set_content(msg.body or "")
            attachments: list[EmailAttachment] = []
            for index, attachment in enumerate(msg.attachments):
                filename = attachment.longFilename or attachment.shortFilename or f"attachment-{index + 1}"
                data = attachment.data or b""
                attachments.append(EmailAttachment(filename=filename, payload=data))
            return ParsedEmail(message=message, attachments=attachments)
        except Exception as exc:
            raise AppError(
                code=ErrorCode.EMAIL_PARSE_FAILED,
                message="MSG email file could not be parsed.",
                details={"input_file": str(input_file), "reason": str(exc)},
            ) from exc

    def _render_message_pdf(self, message: Message, output_dir: Path, profile_dir: Path) -> Path:
        html_path = output_dir / "message.html"
        body = self._extract_body(message)
        headers = {
            "From": str(message.get("From", "")),
            "To": str(message.get("To", "")),
            "Cc": str(message.get("Cc", "")),
            "Subject": str(message.get("Subject", "")),
            "Date": str(message.get("Date", "")),
        }
        header_rows = "\n".join(
            f"<tr><th>{html.escape(key)}</th><td>{html.escape(value)}</td></tr>"
            for key, value in headers.items()
            if value
        )
        html_path.write_text(
            "<html><head><meta charset='utf-8'><style>"
            "body{font-family:sans-serif;font-size:12pt;}"
            "table{border-collapse:collapse;margin-bottom:24px;}"
            "th{text-align:left;padding:4px 12px 4px 0;}"
            "td{padding:4px;}"
            "</style></head><body>"
            f"<table>{header_rows}</table><div>{body}</div>"
            "</body></html>",
            encoding="utf-8",
        )
        pdf_path = self.office_converter.convert_to_pdf(
            input_file=html_path,
            output_dir=output_dir,
            profile_dir=profile_dir,
        )
        target = output_dir / "message.pdf"
        if pdf_path != target:
            pdf_path.replace(target)
        validate_pdf(target)
        return target

    def _extract_body(self, message: Message) -> str:
        if message.is_multipart():
            html_part = None
            text_part = None
            for part in message.walk():
                if part.get_content_disposition() == "attachment":
                    continue
                content_type = part.get_content_type()
                if content_type == "text/html" and html_part is None:
                    html_part = part
                elif content_type == "text/plain" and text_part is None:
                    text_part = part
            selected = html_part or text_part
            if selected is None:
                return ""
            content = selected.get_content()
            if selected.get_content_type() == "text/html":
                return str(content)
            return f"<pre>{html.escape(str(content))}</pre>"
        content = message.get_content()
        if message.get_content_type() == "text/html":
            return str(content)
        return f"<pre>{html.escape(str(content))}</pre>"

    def _convert_attachments(
        self,
        attachments: list[EmailAttachment],
        output_dir: Path,
        profile_dir: Path,
        options: ConversionOptions,
        manifest: ConversionManifest,
    ) -> list[Path]:
        if not options.include_attachments:
            return []
        attachment_outputs: list[Path] = []
        attachments_dir = output_dir / "attachments"
        attachments_dir.mkdir(parents=True, exist_ok=True)
        if options.max_attachments is not None and len(attachments) > options.max_attachments:
            raise AppError(
                code=ErrorCode.TOO_MANY_ATTACHMENTS,
                message="Email contains too many attachments.",
                details={"max_attachments": options.max_attachments, "actual_attachments": len(attachments)},
            )
        total_attachment_bytes = 0
        for attachment in attachments:
            filename = attachment.filename
            payload = attachment.payload
            total_attachment_bytes += len(payload)
            if (
                options.max_email_attachment_bytes is not None
                and total_attachment_bytes > options.max_email_attachment_bytes
            ):
                raise AppError(
                    code=ErrorCode.EMAIL_TOO_LARGE,
                    message="Email attachments exceed the configured size limit.",
                    details={
                        "max_email_attachment_bytes": options.max_email_attachment_bytes,
                        "actual_attachment_bytes": total_attachment_bytes,
                    },
                )
            input_path = attachments_dir / filename
            input_path.write_bytes(payload)
            output_name = f"{safe_stem(filename)}.pdf"
            output_path = attachments_dir / output_name
            try:
                detected = detect_file_type(filename)
                if detected.category == FileCategory.OFFICE:
                    converted = self.office_converter.convert_to_pdf(
                        input_file=input_path,
                        output_dir=attachments_dir,
                        profile_dir=profile_dir,
                    )
                    if converted != output_path:
                        converted.replace(output_path)
                elif detected.category == FileCategory.PDF:
                    validate_pdf(input_path)
                    input_path.replace(output_path)
                elif detected.category == FileCategory.IMAGE:
                    image_to_pdf(input_path, output_path)
                else:
                    raise AppError(
                        code=ErrorCode.UNSUPPORTED_FILE_TYPE,
                        message="Unsupported attachment file type.",
                        details={"filename": filename},
                    )
                validate_pdf(output_path)
                attachment_outputs.append(output_path)
                manifest.add_attachment(
                    AttachmentRecord(
                        original_filename=filename,
                        output_filename=f"attachments/{output_name}",
                        status="converted",
                        reason=None,
                    )
                )
            except AppError as exc:
                manifest.add_attachment(
                    AttachmentRecord(
                        original_filename=filename,
                        output_filename=None,
                        status="skipped",
                        reason=exc.code.value,
                    )
                )
        return attachment_outputs

    def _write_split_zip(
        self,
        zip_path: Path,
        message_pdf: Path,
        attachment_pdfs: list[Path],
        manifest: ConversionManifest,
    ) -> None:
        with ZipFile(zip_path, "w", ZIP_DEFLATED) as archive:
            archive.write(message_pdf, "message.pdf")
            for attachment_pdf in attachment_pdfs:
                archive.write(attachment_pdf, f"attachments/{attachment_pdf.name}")
            archive.writestr("manifest.json", json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2))
