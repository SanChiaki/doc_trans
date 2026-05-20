# LibreOffice Document Conversion Service Design

## Goal

Build a Linux-ready HTTP service that converts Office documents, PDFs, and email files to PDF using Python and LibreOffice. The service supports both synchronous and asynchronous execution through request parameters, and this implementation lives entirely under `lo_pdf_service/` so it stays separate from other conversion approaches in the repository.

## Target Environment

- Production target: Linux container.
- Local validation target: WSL on the developer machine.
- Runtime: Python 3.11+.
- Core renderer: LibreOffice in headless mode.
- API framework: FastAPI.
- Worker model: in-process async job queue for the first version, with interfaces shaped so Redis/Celery/RQ can replace it later.

The Docker image should install LibreOffice, common CJK fonts, Microsoft-compatible fonts when available, and system libraries required for image and PDF processing. WSL validation should run the same Python tests and a real `soffice --headless` smoke test.

## Supported File Scope

### Guaranteed Initial Support

- Word: `.doc`, `.docx`, `.dot`, `.dotx`, `.rtf`, `.odt`
- Excel: `.xls`, `.xlsx`, `.xlsm`, `.xlt`, `.xltx`, `.csv`, `.tsv`, `.ods`
- PowerPoint: `.ppt`, `.pptx`, `.pps`, `.ppsx`, `.odp`
- Text and HTML: `.txt`, `.html`, `.htm`
- PDF: `.pdf`
- Email: `.eml`, `.msg`
- Image attachments: `.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.tif`, `.tiff`

### Explicitly Out of Scope for the First Version

- Password-protected or encrypted Office/PDF files.
- Damaged files.
- OCR.
- Dynamic Office content that depends on macros, external links, or live data refresh.
- Recursive conversion of nested `.eml` or `.msg` attachments.
- Visio, Project, AutoCAD, WPS-specific formats, and other formats not reliably handled by LibreOffice.

## API Design

### Create Conversion

`POST /v1/conversions`

Request format: `multipart/form-data`

Fields:

- `file`: uploaded source file.
- `execution`: `sync` or `async`.
- `email_mode`: `merged` or `split`; only applies to email files. Default: `merged`.
- `include_attachments`: boolean. Default: `true`.
- `timeout_seconds`: optional per-request timeout, capped by service configuration.

Synchronous behavior:

- `execution=sync`.
- The request waits for conversion to finish.
- Office and PDF inputs return one PDF.
- Email with `email_mode=merged` returns one merged PDF.
- Email with `email_mode=split` returns a ZIP containing separate PDFs and a manifest.

Asynchronous behavior:

- `execution=async`.
- The upload returns immediately with:

```json
{
  "job_id": "01HX0000000000000000000000",
  "status": "queued"
}
```

### Get Job Status

`GET /v1/conversions/{job_id}`

Response:

```json
{
  "job_id": "01HX0000000000000000000000",
  "status": "running",
  "created_at": "2026-05-21T00:00:00Z",
  "updated_at": "2026-05-21T00:00:05Z",
  "result": null,
  "error": null
}
```

Status values:

- `queued`
- `running`
- `succeeded`
- `failed`
- `expired`

### Download Result

`GET /v1/conversions/{job_id}/result`

Returns the generated PDF or ZIP when the job has succeeded.

### Delete Job

`DELETE /v1/conversions/{job_id}`

Deletes metadata and generated files for the job.

## Output Shapes

### Non-Email Inputs

The service returns one PDF.

### Email Merged Mode

For `.eml` and `.msg`, `email_mode=merged` produces one PDF:

1. Mail header and body rendered as `message.pdf`.
2. Convertible attachments rendered to PDFs.
3. Existing PDF attachments validated and appended.
4. Images converted to PDF pages.
5. All successful PDFs merged in message-first order.
6. Skipped attachments are listed in the final manifest metadata. They do not fail the job unless policy later requires strict mode.

### Email Split Mode

For `.eml` and `.msg`, `email_mode=split` returns a ZIP:

```text
message.pdf
attachments/
  original-attachment-name.pdf
manifest.json
```

The manifest records:

- source filename and detected type.
- output files.
- converted attachments.
- skipped attachments with reason.
- conversion warnings.

## Internal Architecture

```text
lo_pdf_service/
  app/
    main.py
    api/
      conversions.py
    core/
      config.py
      errors.py
      logging.py
      paths.py
    conversion/
      service.py
      detector.py
      libreoffice.py
      email_converter.py
      image_converter.py
      pdf_ops.py
      manifest.py
    jobs/
      models.py
      store.py
      worker.py
    storage/
      local.py
  tests/
    unit/
    integration/
  Dockerfile
  pyproject.toml
  README.md
```

### Module Responsibilities

- `app/api/conversions.py`: HTTP request parsing, validation, response streaming, and mapping application errors to HTTP responses.
- `app/conversion/service.py`: single entry point for all conversion work. It accepts an input file and options, then returns a result descriptor.
- `app/conversion/detector.py`: file extension and MIME classification.
- `app/conversion/libreoffice.py`: safe `soffice` invocation, per-task profile directory, timeout handling, and output validation.
- `app/conversion/email_converter.py`: `.eml` and `.msg` parsing, body normalization, attachment extraction, and orchestration of merged/split behavior.
- `app/conversion/image_converter.py`: image-to-PDF conversion for email attachments.
- `app/conversion/pdf_ops.py`: PDF validation and merging.
- `app/jobs/store.py`: local filesystem-backed job metadata and result storage.
- `app/jobs/worker.py`: background worker loop for async jobs.
- `app/storage/local.py`: workspace directory creation, cleanup, and atomic result placement.

## Conversion Flow

### Office Document Flow

1. Store upload in a request/job-specific workspace.
2. Detect source type.
3. Run LibreOffice with:

```bash
soffice --headless --nologo --nofirststartwizard \
  --env:UserInstallation=file:///tmp/profile-<id> \
  --convert-to pdf --outdir <output-dir> <input-file>
```

4. Enforce process timeout.
5. Validate that one non-empty PDF exists.
6. Return result metadata.

### Email Flow

1. Parse `.eml` with Python `email` package or `.msg` with `extract-msg`.
2. Extract normalized headers: From, To, Cc, Subject, Date.
3. Prefer HTML body when available; otherwise convert plain text to safe HTML.
4. Render body HTML to `message.pdf`.
5. If attachments are enabled, classify each attachment:
   - Office/text/HTML: convert through LibreOffice.
   - PDF: validate and include.
   - image: render to PDF.
   - unsupported: record skipped reason.
6. Produce merged PDF or split ZIP according to `email_mode`.

## Resource Limits

Default limits:

- Upload size: 50 MB.
- Email total attachment size: 100 MB.
- Max attachments per email: 50.
- Request timeout: 120 seconds.
- LibreOffice process timeout: 90 seconds.
- Max concurrent LibreOffice conversions: configurable semaphore, default 2.
- Job result retention: configurable, default 24 hours.

Every conversion uses an isolated workspace and a unique LibreOffice profile directory to avoid profile lock conflicts.

## Error Handling

Errors are returned in a structured shape:

```json
{
  "error": {
    "code": "conversion_timeout",
    "message": "Conversion exceeded the configured timeout.",
    "details": {
      "source_filename": "input.docx"
    }
  }
}
```

Initial error codes:

- `unsupported_file_type`
- `file_too_large`
- `email_too_large`
- `too_many_attachments`
- `email_parse_failed`
- `conversion_timeout`
- `libreoffice_failed`
- `pdf_validation_failed`
- `attachment_conversion_failed`
- `job_not_found`
- `job_not_ready`
- `job_expired`

Attachment conversion failures in email mode are warnings by default and are recorded in `manifest.json`. The main job fails only when the email body cannot be rendered or no requested output can be produced.

## Testing Strategy

Unit tests:

- Type detection for every supported extension.
- API parameter validation.
- Job status transitions.
- Manifest generation.
- Email parsing using small `.eml` fixtures.
- Error mapping.

Integration tests:

- Real LibreOffice conversion for a simple DOCX, XLSX, PPTX, and CSV.
- PDF passthrough and validation.
- Email merged mode with a body and one convertible attachment.
- Email split mode with manifest and separate attachment output.
- Timeout handling using a controlled subprocess wrapper where possible.

WSL validation commands should include:

```bash
python -m pytest
soffice --headless --version
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Docker validation should include:

```bash
docker build -t lo-pdf-service .
docker run --rm -p 8000:8000 lo-pdf-service
```

## Implementation Constraints

- Keep all implementation files under `lo_pdf_service/`.
- Do not modify `aspose_service/` or root-level design/plan docs for this implementation.
- Prefer small modules with clear ownership.
- Do not introduce Redis, Celery, object storage, authentication, or OCR in the first version.
- Keep the async API interface compatible with a future external queue.
- Use test-first development for production code.

