from __future__ import annotations

from pathlib import Path

import pytest

from app.core.errors import AppError, ErrorCode
from app.jobs.models import JobStatus
from app.jobs.store import LocalJobStore


def test_job_store_creates_and_updates_job(tmp_path: Path) -> None:
    store = LocalJobStore(job_dir=tmp_path)
    job = store.create_job(source_filename="input.docx")

    assert job.status == JobStatus.QUEUED

    updated = store.mark_running(job.job_id)
    assert updated.status == JobStatus.RUNNING

    result_path = tmp_path / "result.pdf"
    result_path.write_bytes(b"pdf")
    succeeded = store.mark_succeeded(
        job.job_id, result_path=result_path, media_type="application/pdf", filename="result.pdf"
    )

    assert succeeded.status == JobStatus.SUCCEEDED
    assert store.get_job(job.job_id).result_path == result_path


def test_job_store_raises_for_missing_job(tmp_path: Path) -> None:
    store = LocalJobStore(job_dir=tmp_path)

    with pytest.raises(AppError) as exc_info:
        store.get_job("missing")

    assert exc_info.value.code == ErrorCode.JOB_NOT_FOUND
