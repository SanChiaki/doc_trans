from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

from app.core.errors import AppError, ErrorCode
from app.jobs.models import JobRecord, JobStatus, utc_now


class LocalJobStore:
    def __init__(self, *, job_dir: Path) -> None:
        self.job_dir = job_dir
        self.job_dir.mkdir(parents=True, exist_ok=True)

    def create_job(self, *, source_filename: str) -> JobRecord:
        now = utc_now()
        job = JobRecord(
            job_id=uuid.uuid4().hex,
            source_filename=source_filename,
            status=JobStatus.QUEUED,
            created_at=now,
            updated_at=now,
        )
        self._write(job)
        return job

    def get_job(self, job_id: str) -> JobRecord:
        path = self._path(job_id)
        if not path.exists():
            raise AppError(code=ErrorCode.JOB_NOT_FOUND, message="Job not found.", details={"job_id": job_id})
        payload = json.loads(path.read_text(encoding="utf-8"))
        return JobRecord(
            job_id=payload["job_id"],
            source_filename=payload["source_filename"],
            status=JobStatus(payload["status"]),
            created_at=datetime.fromisoformat(payload["created_at"]),
            updated_at=datetime.fromisoformat(payload["updated_at"]),
            result_path=Path(payload["result"]["path"]) if payload["result"] else None,
            media_type=payload["result"]["media_type"] if payload["result"] else None,
            filename=payload["result"]["filename"] if payload["result"] else None,
            error=payload["error"],
        )

    def mark_running(self, job_id: str) -> JobRecord:
        job = self.get_job(job_id)
        updated = JobRecord(
            job_id=job.job_id,
            source_filename=job.source_filename,
            status=JobStatus.RUNNING,
            created_at=job.created_at,
            updated_at=utc_now(),
        )
        self._write(updated)
        return updated

    def mark_succeeded(self, job_id: str, *, result_path: Path, media_type: str, filename: str) -> JobRecord:
        job = self.get_job(job_id)
        updated = JobRecord(
            job_id=job.job_id,
            source_filename=job.source_filename,
            status=JobStatus.SUCCEEDED,
            created_at=job.created_at,
            updated_at=utc_now(),
            result_path=result_path,
            media_type=media_type,
            filename=filename,
        )
        self._write(updated)
        return updated

    def mark_failed(self, job_id: str, *, error: dict[str, object]) -> JobRecord:
        job = self.get_job(job_id)
        updated = JobRecord(
            job_id=job.job_id,
            source_filename=job.source_filename,
            status=JobStatus.FAILED,
            created_at=job.created_at,
            updated_at=utc_now(),
            error=error,
        )
        self._write(updated)
        return updated

    def delete_job(self, job_id: str) -> None:
        self._path(job_id).unlink(missing_ok=True)

    def _path(self, job_id: str) -> Path:
        return self.job_dir / f"{job_id}.json"

    def _write(self, job: JobRecord) -> None:
        self.job_dir.mkdir(parents=True, exist_ok=True)
        self._path(job.job_id).write_text(json.dumps(job.to_dict(), indent=2), encoding="utf-8")
