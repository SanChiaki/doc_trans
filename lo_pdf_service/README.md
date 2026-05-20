# LibreOffice PDF Conversion Service

FastAPI service for converting Office documents, PDFs, images, and email files to PDF with LibreOffice headless.

This implementation is isolated under `lo_pdf_service/`.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest
```

## Linux Runtime Check

```bash
soffice --headless --version
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
