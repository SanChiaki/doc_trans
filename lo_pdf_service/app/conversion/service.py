from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from app.conversion.detector import FileCategory, detect_file_type
from app.conversion.email_converter import EmailConverter
from app.conversion.image_converter import image_to_pdf
from app.conversion.pdf_ops import validate_pdf
from app.models import ConversionOptions, ConversionResult, OutputKind
from app.storage.local import LocalStorage


class ConversionService:
    def __init__(self, *, storage: LocalStorage, office_converter: object) -> None:
        self.storage = storage
        self.office_converter = office_converter
        self.email_converter = EmailConverter(office_converter=office_converter)

    def convert(
        self,
        *,
        input_file: Path,
        source_filename: str,
        options: ConversionOptions,
        workspace_id: str | None = None,
    ) -> ConversionResult:
        workspace = self.storage.create_workspace(workspace_id or uuid.uuid4().hex)
        source_path = workspace.input_dir / source_filename
        shutil.copy2(input_file, source_path)
        detected = detect_file_type(source_filename)

        if detected.category == FileCategory.OFFICE:
            pdf = self.office_converter.convert_to_pdf(
                input_file=source_path,
                output_dir=workspace.output_dir,
                profile_dir=workspace.profile_dir,
            )
            return ConversionResult(
                output_path=pdf,
                output_kind=OutputKind.PDF,
                media_type="application/pdf",
                filename=pdf.name,
            )

        if detected.category == FileCategory.PDF:
            validate_pdf(source_path)
            output = workspace.output_dir / source_path.name
            shutil.copy2(source_path, output)
            return ConversionResult(
                output_path=output,
                output_kind=OutputKind.PDF,
                media_type="application/pdf",
                filename=output.name,
            )

        if detected.category == FileCategory.IMAGE:
            output = workspace.output_dir / f"{source_path.stem}.pdf"
            image_to_pdf(source_path, output)
            return ConversionResult(
                output_path=output,
                output_kind=OutputKind.PDF,
                media_type="application/pdf",
                filename=output.name,
            )

        return self.email_converter.convert(
            input_file=source_path,
            output_dir=workspace.output_dir,
            profile_dir=workspace.profile_dir,
            options=options,
        )
