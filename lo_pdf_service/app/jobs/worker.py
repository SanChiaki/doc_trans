from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.errors import AppError
from app.jobs.store import LocalJobStore
from app.models import ConversionOptions


@dataclass(frozen=True)
class ConversionJob:
    job_id: str
    input_file: Path
    source_filename: str
    options: ConversionOptions


class InProcessWorker:
    def __init__(self, *, service: object, store: LocalJobStore) -> None:
        self.service = service
        self.store = store

    def process_one(self, job: ConversionJob) -> None:
        self.store.mark_running(job.job_id)
        try:
            result = self.service.convert(
                input_file=job.input_file,
                source_filename=job.source_filename,
                options=job.options,
                workspace_id=job.job_id,
            )
        except AppError as exc:
            self.store.mark_failed(job.job_id, error=exc.to_dict()["error"])
            return
        except Exception as exc:
            self.store.mark_failed(
                job.job_id,
                error={
                    "code": "unexpected_error",
                    "message": "Unexpected conversion failure.",
                    "details": {"reason": str(exc)},
                },
            )
            return

        self.store.mark_succeeded(
            job.job_id,
            result_path=result.output_path,
            media_type=result.media_type,
            filename=result.filename,
        )
