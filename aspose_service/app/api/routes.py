from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse, Response

from app.core.config import Settings, get_settings
from app.core.errors import BadRequestError, PayloadTooLargeError
from app.models import ResponseMode, StoredFileResponse
from app.services.aspose_adapters import AsposeAdapters
from app.services.converter import DocumentConverter
from app.services.storage import LocalStorage

router = APIRouter(prefix="/api/v1")


def get_storage(settings: Annotated[Settings, Depends(get_settings)]) -> LocalStorage:
    return LocalStorage(upload_dir=settings.upload_dir, output_dir=settings.output_dir)


def get_converter(settings: Annotated[Settings, Depends(get_settings)]) -> DocumentConverter:
    adapters = AsposeAdapters(
        license_path=settings.aspose_license_path,
        word_python=settings.word_python,
        cells_python=settings.cells_python,
        slides_python=settings.slides_python,
        email_python=settings.email_python,
        worker_library_path=settings.worker_library_path,
    )
    adapters.apply_licenses()
    return DocumentConverter(adapters=adapters, work_dir=settings.upload_dir)


@router.post("/convert", response_model=StoredFileResponse)
async def convert_document(
    file: Annotated[UploadFile, File()],
    response_mode: Annotated[ResponseMode, Form()] = ResponseMode.STREAM,
    include_email_attachments: Annotated[bool, Form()] = False,
    settings: Annotated[Settings, Depends(get_settings)] = None,
    storage: Annotated[LocalStorage, Depends(get_storage)] = None,
    converter: Annotated[DocumentConverter, Depends(get_converter)] = None,
):
    if include_email_attachments:
        raise BadRequestError("Email attachment conversion is not available in this version.")

    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise PayloadTooLargeError("Uploaded file exceeds configured size limit.")

    source_path = storage.save_upload(file.filename or "upload.bin", content)
    try:
        pdf_bytes = converter.convert_to_pdf(source_path=source_path, source_filename=file.filename or source_path.name)
    finally:
        storage.cleanup_temp_file(source_path)

    pdf_filename = storage.pdf_filename_for(file.filename or "converted")
    if response_mode is ResponseMode.FILE:
        stored = storage.persist_pdf(source_filename=file.filename or "converted", pdf_bytes=pdf_bytes)
        return StoredFileResponse(
            file_id=stored.file_id,
            download_url=f"/api/v1/files/{stored.file_id}",
            filename=stored.download_filename,
        )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{pdf_filename}"'},
    )


@router.get("/files/{file_id}")
async def download_file(file_id: str, storage: Annotated[LocalStorage, Depends(get_storage)]):
    output_path = storage.resolve_output(file_id)
    return FileResponse(path=output_path, media_type="application/pdf", filename=output_path.name)
