# Aspose Document Conversion Service Design

## Goal

Build a Linux-compatible HTTP service that converts Office and email documents to PDF with Aspose for Python. This implementation lives entirely under `aspose_service/` so other conversion approaches can be added beside it without sharing application code.

## Scope

The first version exposes a synchronous FastAPI API. It accepts one uploaded file, converts it to PDF, and either streams the PDF back to the caller or stores it locally and returns a download URL. Email conversion supports `.eml` and `.msg` message body, common headers, and attachment names. Attachment conversion and PDF merging are intentionally left as an extension point.

## Supported Formats

- Word-like: `.doc`, `.docx`, `.rtf`, `.odt`, `.txt`, `.html`, `.htm`, `.mhtml`
- Excel-like: `.xls`, `.xlsx`, `.xlsm`, `.csv`, `.ods`
- PowerPoint-like: `.ppt`, `.pptx`, `.pps`, `.ppsx`, `.odp`
- Email: `.eml`, `.msg`

## Architecture

`aspose_service/app/main.py` creates the FastAPI app and mounts versioned routes. `aspose_service/app/api/routes.py` handles uploads, validates request options, calls the conversion service, and returns either a streaming PDF response or local-file metadata. The conversion service in `aspose_service/app/services/converter.py` detects the file family and delegates to focused Aspose adapters.

The service keeps temporary upload files separate from persisted output files. `LocalStorage` owns these paths, file IDs, and download lookup. This keeps HTTP routing independent from storage layout and leaves room for object storage later.

## Aspose Strategy

- `aspose-words` loads Word-like files and saves PDF.
- `aspose-cells` loads Excel-like files and saves PDF.
- `aspose-slides` loads PowerPoint-like files and saves PDF.
- `aspose-email` loads `.eml` and `.msg`, saves an intermediate MHTML document, then `aspose-words` saves that as PDF.

Aspose imports run inside subprocess workers so the FastAPI process does not load multiple Aspose native products into one interpreter. This matters because current Aspose Python via .NET packages share native modules under the `aspose` namespace and can conflict when installed together. Each worker Python executable can be configured separately, allowing production deployments to use isolated virtual environments or containers per product. Missing Aspose dependencies raise a clear application error.

## API

`POST /api/v1/convert`

- Multipart field `file`: source document.
- Form field `response_mode`: `stream` or `file`, default `stream`.
- Form field `include_email_attachments`: accepted for forward compatibility. Version one rejects `true` with a clear validation error.

For `stream`, the response is `application/pdf` with a download filename. For `file`, the response is JSON containing `file_id`, `download_url`, `filename`, and `content_type`.

`GET /api/v1/files/{file_id}` downloads a previously persisted PDF.

`GET /health` returns service health and configured runtime information.

## Error Handling

Unsupported formats return `415`. Empty files, unsupported response modes, and unsupported attachment conversion requests return `400`. Oversized uploads return `413`. Conversion failures return `422`. Unexpected errors return `500`. Error bodies use `code`, `message`, and optional `details`.

## Linux Runtime

The service targets Python 3.10+ on Linux. Runtime images or WSL environments should include common font packages and `fontconfig`; for Chinese documents, install CJK fonts such as Noto CJK. Some Aspose Python via .NET packages also require OpenSSL 1.1 compatibility libraries even on Ubuntu releases that default to OpenSSL 3. The local bootstrap script can extract those libraries under `runtime/compat` without sudo and configure `ASPOSE_SERVICE_WORKER_LIBRARY_PATH`. Aspose license loading is configured through `ASPOSE_SERVICE_ASPOSE_LICENSE_PATH`. Without a license, Aspose can still run in evaluation mode with vendor limitations.

## Testing

Unit tests cover format detection, response mode behavior, storage behavior, and conversion dispatch using fake adapters. Integration conversion tests are opt-in because they require Aspose packages, fonts, and sample Office files in the Linux environment.
