from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from app.core.errors import BadRequestError


@dataclass(frozen=True)
class StoredPdf:
    file_id: str
    path: Path
    download_filename: str


class LocalStorage:
    def __init__(self, upload_dir: Path, output_dir: Path) -> None:
        self.upload_dir = upload_dir
        self.output_dir = output_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save_upload(self, filename: str, content: bytes) -> Path:
        if not content:
            raise BadRequestError("Uploaded file is empty.")

        source_name = Path(filename or "upload.bin")
        suffix = source_name.suffix.lower() or ".bin"
        upload_path = self.upload_dir / f"{uuid4().hex}{suffix}"
        upload_path.write_bytes(content)
        return upload_path

    def persist_pdf(self, source_filename: str, pdf_bytes: bytes) -> StoredPdf:
        if not pdf_bytes:
            raise BadRequestError("Converted PDF is empty.")

        file_id = uuid4().hex
        output_path = self.output_dir / f"{file_id}.pdf"
        output_path.write_bytes(pdf_bytes)
        return StoredPdf(
            file_id=file_id,
            path=output_path,
            download_filename=self.pdf_filename_for(source_filename),
        )

    def resolve_output(self, file_id: str) -> Path:
        if not file_id or "/" in file_id or "\\" in file_id:
            raise BadRequestError("File not found.")

        output_path = self.output_dir / f"{file_id}.pdf"
        if not output_path.exists():
            raise BadRequestError("File not found.", details={"file_id": file_id})
        return output_path

    def cleanup_temp_file(self, path: Path) -> None:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass

    @staticmethod
    def pdf_filename_for(source_filename: str) -> str:
        source_path = Path(source_filename or "converted")
        stem = source_path.stem or "converted"
        return f"{stem}.pdf"
