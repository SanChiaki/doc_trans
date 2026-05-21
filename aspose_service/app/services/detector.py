from enum import Enum
from pathlib import Path

from app.core.errors import UnsupportedFormatError


class DocumentFamily(str, Enum):
    WORD = "word"
    EXCEL = "excel"
    PRESENTATION = "presentation"
    EMAIL = "email"


EXTENSION_FAMILIES = {
    ".doc": DocumentFamily.WORD,
    ".docx": DocumentFamily.WORD,
    ".rtf": DocumentFamily.WORD,
    ".odt": DocumentFamily.WORD,
    ".txt": DocumentFamily.WORD,
    ".html": DocumentFamily.WORD,
    ".htm": DocumentFamily.WORD,
    ".mhtml": DocumentFamily.WORD,
    ".xls": DocumentFamily.EXCEL,
    ".xlsx": DocumentFamily.EXCEL,
    ".xlsm": DocumentFamily.EXCEL,
    ".csv": DocumentFamily.EXCEL,
    ".ods": DocumentFamily.EXCEL,
    ".ppt": DocumentFamily.PRESENTATION,
    ".pptx": DocumentFamily.PRESENTATION,
    ".pps": DocumentFamily.PRESENTATION,
    ".ppsx": DocumentFamily.PRESENTATION,
    ".odp": DocumentFamily.PRESENTATION,
    ".eml": DocumentFamily.EMAIL,
    ".msg": DocumentFamily.EMAIL,
}


def detect_document_family(filename: str) -> DocumentFamily:
    extension = Path(filename).suffix.lower()
    family = EXTENSION_FAMILIES.get(extension)
    if family is None:
        raise UnsupportedFormatError(
            "Unsupported document format.",
            details={"filename": filename, "extension": extension or None},
        )
    return family
