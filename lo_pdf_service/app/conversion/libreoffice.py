from __future__ import annotations

import subprocess
from pathlib import Path

from app.conversion.pdf_ops import validate_pdf
from app.core.errors import AppError, ErrorCode

SPREADSHEET_SINGLE_PAGE_EXPORT_FILTER = (
    'pdf:calc_pdf_Export:{"SinglePageSheets":{"type":"boolean","value":"true"}}'
)


class LibreOfficeConverter:
    def __init__(self, *, soffice_binary: str, timeout_seconds: int) -> None:
        self.soffice_binary = soffice_binary
        self.timeout_seconds = timeout_seconds

    def convert_to_pdf(
        self,
        *,
        input_file: Path,
        output_dir: Path,
        profile_dir: Path,
        fit_spreadsheet_sheets_to_one_page: bool = False,
    ) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        profile_dir.mkdir(parents=True, exist_ok=True)
        expected_output = output_dir / f"{input_file.stem}.pdf"
        command = [
            self.soffice_binary,
            "--headless",
            "--nologo",
            "--nofirststartwizard",
            f"-env:UserInstallation={profile_dir.as_uri()}",
            "--convert-to",
            SPREADSHEET_SINGLE_PAGE_EXPORT_FILTER if fit_spreadsheet_sheets_to_one_page else "pdf",
            "--outdir",
            str(output_dir),
            str(input_file),
        ]
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise AppError(
                code=ErrorCode.CONVERSION_TIMEOUT,
                message="LibreOffice conversion exceeded the configured timeout.",
                details={"input_file": str(input_file), "timeout_seconds": self.timeout_seconds},
            ) from exc

        if completed.returncode != 0:
            raise AppError(
                code=ErrorCode.LIBREOFFICE_FAILED,
                message="LibreOffice conversion failed.",
                details={
                    "input_file": str(input_file),
                    "stdout": completed.stdout,
                    "stderr": completed.stderr,
                },
            )

        if not expected_output.exists():
            pdf_outputs = sorted(output_dir.glob("*.pdf"))
            if len(pdf_outputs) == 1:
                expected_output = pdf_outputs[0]
            else:
                raise AppError(
                    code=ErrorCode.LIBREOFFICE_FAILED,
                    message="LibreOffice did not produce a PDF output.",
                    details={"input_file": str(input_file), "output_dir": str(output_dir)},
                )
        validate_pdf(expected_output)
        return expected_output
