from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class ExecutionMode(StrEnum):
    SYNC = "sync"
    ASYNC = "async"


class EmailMode(StrEnum):
    MERGED = "merged"
    SPLIT = "split"


class OutputKind(StrEnum):
    PDF = "pdf"
    ZIP = "zip"


@dataclass(frozen=True)
class ConversionOptions:
    email_mode: EmailMode = EmailMode.MERGED
    include_attachments: bool = True
    timeout_seconds: int | None = None
    max_email_attachment_bytes: int | None = None
    max_attachments: int | None = None


@dataclass(frozen=True)
class ConversionResult:
    output_path: Path
    output_kind: OutputKind
    media_type: str
    filename: str
    manifest: dict[str, object] = field(default_factory=dict)
