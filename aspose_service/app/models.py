from enum import Enum

from pydantic import BaseModel


class ResponseMode(str, Enum):
    STREAM = "stream"
    FILE = "file"


class StoredFileResponse(BaseModel):
    file_id: str
    download_url: str
    filename: str
    content_type: str = "application/pdf"


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: dict | None = None
