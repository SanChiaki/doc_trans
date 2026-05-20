from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    EXPIRED = "expired"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class JobRecord:
    job_id: str
    source_filename: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    result_path: Path | None = None
    media_type: str | None = None
    filename: str | None = None
    error: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "job_id": self.job_id,
            "source_filename": self.source_filename,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "result": None
            if self.result_path is None
            else {
                "path": str(self.result_path),
                "media_type": self.media_type,
                "filename": self.filename,
            },
            "error": self.error,
        }
