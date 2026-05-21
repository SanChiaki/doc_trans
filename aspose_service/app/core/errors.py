class DocumentConversionError(Exception):
    status_code = 500
    code = "conversion_error"

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class BadRequestError(DocumentConversionError):
    status_code = 400
    code = "bad_request"


class PayloadTooLargeError(DocumentConversionError):
    status_code = 413
    code = "payload_too_large"


class UnsupportedFormatError(DocumentConversionError):
    status_code = 415
    code = "unsupported_format"


class ConversionFailedError(DocumentConversionError):
    status_code = 422
    code = "conversion_failed"


class ConversionDependencyError(ConversionFailedError):
    code = "conversion_dependency_missing"
