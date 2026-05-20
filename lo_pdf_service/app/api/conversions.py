from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse

from app.api.dependencies import get_conversion_service, get_job_store, get_settings_dependency, get_worker
from app.core.config import Settings
from app.core.errors import AppError, ErrorCode
from app.jobs.models import JobStatus
from app.jobs.store import LocalJobStore
from app.jobs.worker import ConversionJob, InProcessWorker
from app.models import ConversionOptions, EmailMode, ExecutionMode

router = APIRouter(prefix="/v1/conversions", tags=["conversions"])


@router.post("")
async def create_conversion(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    execution: ExecutionMode = Form(default=ExecutionMode.SYNC),
    email_mode: EmailMode = Form(default=EmailMode.MERGED),
    include_attachments: bool = Form(default=True),
    timeout_seconds: int | None = Form(default=None),
    settings: Settings = Depends(get_settings_dependency),
    service: object = Depends(get_conversion_service),
    store: LocalJobStore = Depends(get_job_store),
    worker: InProcessWorker = Depends(get_worker),
):
    source_filename = file.filename or "upload"
    upload_dir = Path(tempfile.mkdtemp(prefix="lopdf-upload-"))
    upload_path = upload_dir / source_filename
    total_bytes = 0
    with upload_path.open("wb") as output:
        while chunk := file.file.read(1024 * 1024):
            total_bytes += len(chunk)
            if total_bytes > settings.max_upload_bytes:
                error = AppError(
                    code=ErrorCode.FILE_TOO_LARGE,
                    message="Uploaded file exceeds the configured size limit.",
                    details={"max_upload_bytes": settings.max_upload_bytes, "actual_bytes": total_bytes},
                )
                return JSONResponse(status_code=413, content=error.to_dict())
            output.write(chunk)
    options = ConversionOptions(
        email_mode=email_mode,
        include_attachments=include_attachments,
        timeout_seconds=timeout_seconds,
        max_email_attachment_bytes=settings.max_email_attachment_bytes,
        max_attachments=settings.max_attachments,
    )

    if execution == ExecutionMode.SYNC:
        try:
            result = service.convert(input_file=upload_path, source_filename=source_filename, options=options)
        except AppError as exc:
            return JSONResponse(status_code=400, content=exc.to_dict())
        return FileResponse(path=result.output_path, media_type=result.media_type, filename=result.filename)

    job = store.create_job(source_filename=source_filename)
    background_tasks.add_task(
        worker.process_one,
        ConversionJob(
            job_id=job.job_id,
            input_file=upload_path,
            source_filename=source_filename,
            options=options,
        ),
    )
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content={"job_id": job.job_id, "status": job.status.value})


@router.get("/{job_id}")
def get_conversion(job_id: str, store: LocalJobStore = Depends(get_job_store)):
    try:
        return store.get_job(job_id).to_dict()
    except AppError as exc:
        return JSONResponse(status_code=404, content=exc.to_dict())


@router.get("/{job_id}/result")
def get_conversion_result(job_id: str, store: LocalJobStore = Depends(get_job_store)):
    try:
        job = store.get_job(job_id)
    except AppError as exc:
        return JSONResponse(status_code=404, content=exc.to_dict())
    if job.status != JobStatus.SUCCEEDED or job.result_path is None:
        error = AppError(code=ErrorCode.JOB_NOT_READY, message="Job result is not ready.", details={"job_id": job_id})
        return JSONResponse(status_code=409, content=error.to_dict())
    return FileResponse(path=job.result_path, media_type=job.media_type, filename=job.filename)


@router.delete("/{job_id}", status_code=204)
def delete_conversion(job_id: str, store: LocalJobStore = Depends(get_job_store)):
    store.delete_job(job_id)
    return None
