from __future__ import annotations

from enum import StrEnum
from typing import Any


class ErrorCode(StrEnum):
    UNSUPPORTED_FILE_TYPE = "unsupported_file_type"
    FILE_TOO_LARGE = "file_too_large"
    EMAIL_TOO_LARGE = "email_too_large"
    TOO_MANY_ATTACHMENTS = "too_many_attachments"
    EMAIL_PARSE_FAILED = "email_parse_failed"
    CONVERSION_TIMEOUT = "conversion_timeout"
    LIBREOFFICE_FAILED = "libreoffice_failed"
    PDF_VALIDATION_FAILED = "pdf_validation_failed"
    ATTACHMENT_CONVERSION_FAILED = "attachment_conversion_failed"
    JOB_NOT_FOUND = "job_not_found"
    JOB_NOT_READY = "job_not_ready"
    JOB_EXPIRED = "job_expired"


class AppError(Exception):
    def __init__(
        self,
        *,
        code: ErrorCode,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code.value,
                "message": self.message,
                "details": self.details,
            }
        }
