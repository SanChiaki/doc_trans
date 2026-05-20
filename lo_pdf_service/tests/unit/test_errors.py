from __future__ import annotations

from app.core.errors import AppError, ErrorCode


def test_app_error_serializes_to_response_payload() -> None:
    error = AppError(
        code=ErrorCode.CONVERSION_TIMEOUT,
        message="Conversion exceeded the configured timeout.",
        details={"source_filename": "input.docx"},
    )

    assert error.to_dict() == {
        "error": {
            "code": "conversion_timeout",
            "message": "Conversion exceeded the configured timeout.",
            "details": {"source_filename": "input.docx"},
        }
    }


def test_app_error_uses_empty_details_by_default() -> None:
    error = AppError(code=ErrorCode.JOB_NOT_FOUND, message="Job not found.")

    assert error.to_dict()["error"]["details"] == {}
