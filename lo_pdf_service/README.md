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

## API

Synchronous conversion:

```bash
curl -F "execution=sync" -F "email_mode=merged" -F "file=@sample.docx" \
  http://localhost:8000/v1/conversions --output result.pdf
```

Asynchronous conversion:

```bash
curl -F "execution=async" -F "email_mode=split" -F "file=@message.eml" \
  http://localhost:8000/v1/conversions
```

## WSL Validation

```bash
sudo apt-get update
sudo apt-get install -y libreoffice fonts-noto-cjk
cd lo_pdf_service
python -m pip install -e ".[dev]"
python -m pytest
soffice --headless --version
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Docker Validation

```bash
cd lo_pdf_service
docker build -t lo-pdf-service .
docker run --rm -p 8000:8000 lo-pdf-service
```
