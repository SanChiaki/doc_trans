from __future__ import annotations

from pathlib import Path

from app.conversion.manifest import AttachmentRecord, ConversionManifest
from app.models import OutputKind


def test_manifest_records_converted_and_skipped_attachments() -> None:
    manifest = ConversionManifest(source_filename="message.eml", output_kind=OutputKind.ZIP)
    manifest.add_output("message", Path("message.pdf"))
    manifest.add_attachment(
        AttachmentRecord(
            original_filename="invoice.docx",
            output_filename="attachments/invoice.pdf",
            status="converted",
            reason=None,
        )
    )
    manifest.add_attachment(
        AttachmentRecord(
            original_filename="archive.zip",
            output_filename=None,
            status="skipped",
            reason="unsupported_file_type",
        )
    )

    payload = manifest.to_dict()

    assert payload["source_filename"] == "message.eml"
    assert payload["output_kind"] == "zip"
    assert payload["outputs"] == [{"name": "message", "path": "message.pdf"}]
    assert payload["attachments"][0]["status"] == "converted"
    assert payload["attachments"][1]["reason"] == "unsupported_file_type"
