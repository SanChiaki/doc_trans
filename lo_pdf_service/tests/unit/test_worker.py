from __future__ import annotations

from pathlib import Path

from pypdf import PdfWriter

from app.jobs.models import JobStatus
from app.jobs.store import LocalJobStore
from app.jobs.worker import ConversionJob, InProcessWorker
from app.models import ConversionOptions, ConversionResult, OutputKind


class FakeService:
    def convert(
        self, *, input_file: Path, source_filename: str, options: ConversionOptions, workspace_id: str | None = None
    ) -> ConversionResult:
        result = input_file.parent / "result.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        with result.open("wb") as file:
            writer.write(file)
        return ConversionResult(
            output_path=result,
            output_kind=OutputKind.PDF,
            media_type="application/pdf",
            filename="result.pdf",
        )


def test_worker_processes_job_successfully(tmp_path: Path) -> None:
    store = LocalJobStore(job_dir=tmp_path / "jobs")
    source = tmp_path / "input.txt"
    source.write_text("hello", encoding="utf-8")
    job = store.create_job(source_filename="input.txt")
    worker = InProcessWorker(service=FakeService(), store=store)

    worker.process_one(
        ConversionJob(
            job_id=job.job_id,
            input_file=source,
            source_filename="input.txt",
            options=ConversionOptions(),
        )
    )

    finished = store.get_job(job.job_id)
    assert finished.status == JobStatus.SUCCEEDED
    assert finished.result_path is not None
