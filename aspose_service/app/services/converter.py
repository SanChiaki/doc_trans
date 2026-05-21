from pathlib import Path
from uuid import uuid4

from app.core.errors import ConversionFailedError
from app.services.detector import DocumentFamily, detect_document_family


class DocumentConverter:
    def __init__(self, adapters: object, work_dir: Path) -> None:
        self.adapters = adapters
        self.work_dir = work_dir
        self.work_dir.mkdir(parents=True, exist_ok=True)

    def convert_to_pdf(self, source_path: Path, source_filename: str) -> bytes:
        family = detect_document_family(source_filename)
        output_path = self.work_dir / f"{uuid4().hex}.pdf"

        try:
            self._convert_by_family(family, source_path, output_path)
            pdf_bytes = output_path.read_bytes()
        except ConversionFailedError:
            raise
        except Exception as exc:
            raise ConversionFailedError("Document conversion failed.", details={"error": str(exc)}) from exc
        finally:
            output_path.unlink(missing_ok=True)

        if not pdf_bytes:
            raise ConversionFailedError("Document conversion produced an empty PDF.")
        return pdf_bytes

    def _convert_by_family(self, family: DocumentFamily, source_path: Path, output_path: Path) -> None:
        if family is DocumentFamily.WORD:
            self.adapters.convert_word(source_path, output_path)
        elif family is DocumentFamily.EXCEL:
            self.adapters.convert_excel(source_path, output_path)
        elif family is DocumentFamily.PRESENTATION:
            self.adapters.convert_presentation(source_path, output_path)
        elif family is DocumentFamily.EMAIL:
            self.adapters.convert_email(source_path, output_path)
        else:
            raise ConversionFailedError("Unsupported document family.", details={"family": family.value})
