# Aspose Document Conversion Service

FastAPI service for converting Office and email documents to PDF with Aspose for Python via .NET.

## Supported Inputs

- Word-like: `.doc`, `.docx`, `.rtf`, `.odt`, `.txt`, `.html`, `.htm`, `.mhtml`
- Excel-like: `.xls`, `.xlsx`, `.xlsm`, `.csv`, `.ods`
- PowerPoint-like: `.ppt`, `.pptx`, `.pps`, `.ppsx`, `.odp`
- Email: `.eml`, `.msg`

Email conversion in this version converts the message body and metadata to PDF. Attachments are listed by Aspose's email rendering path when supported by the vendor output, but attachment-to-PDF merging is not implemented yet and `include_email_attachments=true` is rejected.

## Linux/WSL Setup

Use Python 3.10+ on Linux. For Chinese Office documents, install CJK fonts in the runtime image or WSL distribution.

```bash
sudo apt-get update
sudo apt-get install -y fontconfig fonts-noto-cjk libgdiplus
cd /mnt/d/Workspace/demos/doc_trans/aspose_service
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev,aspose]'
```

Aspose's Python via .NET packages load native shared modules under the same `aspose` namespace. In current Linux packages this can cause product-to-product conflicts when Words, Slides, Email, and Cells are all installed in one Python environment. The service therefore runs conversion inside worker subprocesses, and each worker Python executable can be configured independently:

```bash
export ASPOSE_SERVICE_WORD_PYTHON=/opt/aspose-word/.venv/bin/python
export ASPOSE_SERVICE_CELLS_PYTHON=/opt/aspose-cells/.venv/bin/python
export ASPOSE_SERVICE_SLIDES_PYTHON=/opt/aspose-slides/.venv/bin/python
export ASPOSE_SERVICE_EMAIL_PYTHON=/opt/aspose-email/.venv/bin/python
```

For production, use separate virtual environments or separate container images per Aspose product if combined installation fails. On Ubuntu 22.04+, some Aspose Python via .NET builds can also require OpenSSL 1.1 compatibility libraries; a plain Ubuntu 22.04 WSL image only ships OpenSSL 3 by default and can fail with `No usable version of libssl was found`.

For local WSL validation without sudo, run the bootstrap script. It downloads and extracts the Ubuntu OpenSSL 1.1 compatibility package under `runtime/compat`, creates isolated Aspose worker virtual environments under `runtime/aspose_envs`, and writes `runtime/.env.runtime`:

```bash
bash scripts/bootstrap_aspose_workers.sh
source runtime/.env.runtime
```

If you only need to run unit tests that do not perform real Aspose conversions:

```bash
python -m pip install -e '.[dev]'
pytest tests -q
```

Aspose license loading is optional and configured through:

```bash
export ASPOSE_SERVICE_ASPOSE_LICENSE_PATH=/absolute/path/to/Aspose.Total.Python.NET.lic
```

Without a license, Aspose runs in evaluation mode with vendor limitations.

## Run the Service

```bash
cd aspose_service
. .venv/bin/activate
source runtime/.env.runtime
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

Stream a converted PDF:

```bash
curl -X POST http://localhost:8000/api/v1/convert \
  -F response_mode=stream \
  -F file=@sample.docx \
  --output sample.pdf
```

Persist a converted PDF and return metadata:

```bash
curl -X POST http://localhost:8000/api/v1/convert \
  -F response_mode=file \
  -F file=@sample.docx
```

Download a persisted PDF:

```bash
curl -OJ http://localhost:8000/api/v1/files/<file_id>
```

## Verification

Run unit tests:

```bash
pytest tests -q
```

Run a WSL end-to-end smoke test that creates a DOCX with Aspose Words, converts it through the worker, starts the API, and verifies `/api/v1/convert` returns a PDF:

```bash
bash scripts/e2e_smoke.sh
```

## API Summary

- `POST /api/v1/convert`
  - `file`: multipart upload
  - `response_mode`: `stream` or `file`, default `stream`
  - `include_email_attachments`: reserved for future attachment merging; `true` is rejected
- `GET /api/v1/files/{file_id}`
- `GET /health`

Errors use:

```json
{
  "code": "bad_request",
  "message": "Invalid request.",
  "details": {}
}
```
