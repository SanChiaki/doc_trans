from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from app.core.errors import AppError, ErrorCode


class FileCategory(StrEnum):
    OFFICE = "office"
    PDF = "pdf"
    EMAIL = "email"
    IMAGE = "image"


OFFICE_EXTENSIONS = {
    "doc",
    "docx",
    "dot",
    "dotx",
    "rtf",
    "odt",
    "xls",
    "xlsx",
    "xlsm",
    "xlt",
    "xltx",
    "csv",
    "tsv",
    "ods",
    "ppt",
    "pptx",
    "pps",
    "ppsx",
    "odp",
    "txt",
    "html",
    "htm",
}
SPREADSHEET_EXTENSIONS = {"xls", "xlsx", "xlsm", "xlt", "xltx", "csv", "tsv", "ods"}
PDF_EXTENSIONS = {"pdf"}
EMAIL_EXTENSIONS = {"eml", "msg"}
IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "bmp", "tif", "tiff"}


@dataclass(frozen=True)
class DetectedFile:
    filename: str
    extension: str
    category: FileCategory


def detect_file_type(filename: str) -> DetectedFile:
    suffix = Path(filename).suffix.lower().lstrip(".")
    if suffix in OFFICE_EXTENSIONS:
        return DetectedFile(filename=filename, extension=suffix, category=FileCategory.OFFICE)
    if suffix in PDF_EXTENSIONS:
        return DetectedFile(filename=filename, extension=suffix, category=FileCategory.PDF)
    if suffix in EMAIL_EXTENSIONS:
        return DetectedFile(filename=filename, extension=suffix, category=FileCategory.EMAIL)
    if suffix in IMAGE_EXTENSIONS:
        return DetectedFile(filename=filename, extension=suffix, category=FileCategory.IMAGE)
    raise AppError(
        code=ErrorCode.UNSUPPORTED_FILE_TYPE,
        message="Unsupported file type.",
        details={"filename": filename, "extension": suffix},
    )


def is_spreadsheet_file(filename: str) -> bool:
    return Path(filename).suffix.lower().lstrip(".") in SPREADSHEET_EXTENSIONS
