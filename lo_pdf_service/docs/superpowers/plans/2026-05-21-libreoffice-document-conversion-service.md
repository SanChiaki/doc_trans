# LibreOffice Document Conversion Service Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Linux-ready FastAPI service under `lo_pdf_service/` that converts Office, PDF, image attachments, and email files to PDF with synchronous and asynchronous execution modes.

**Architecture:** A single conversion service owns file detection and conversion orchestration. FastAPI exposes sync and async APIs; async jobs use a local filesystem-backed job store and an in-process worker so the interface can later move to Redis/Celery without changing callers.

**Tech Stack:** Python 3.11+, FastAPI, Uvicorn, LibreOffice headless, pydantic-settings, pypdf, Pillow, extract-msg, pytest, httpx.

---

## File Structure

All files for this implementation stay under `lo_pdf_service/`.

```text
lo_pdf_service/
  .gitignore
  Dockerfile
  README.md
  pyproject.toml
  app/
    __init__.py
    main.py
    api/
      __init__.py
      conversions.py
      dependencies.py
    core/
      __init__.py
      config.py
      errors.py
      logging.py
      paths.py
    conversion/
      __init__.py
      detector.py
      email_converter.py
      image_converter.py
      libreoffice.py
      manifest.py
      pdf_ops.py
      service.py
    jobs/
      __init__.py
      models.py
      store.py
      worker.py
    storage/
      __init__.py
      local.py
  tests/
    conftest.py
    fixtures/
    integration/
      test_libreoffice_smoke.py
    unit/
      test_api.py
      test_config.py
      test_detector.py
      test_email_converter.py
      test_errors.py
      test_image_converter.py
      test_job_store.py
      test_manifest.py
      test_pdf_ops.py
      test_service.py
      test_storage.py
      test_worker.py
```

## Task 1: Project Skeleton

**Files:**
- Create: `lo_pdf_service/pyproject.toml`
- Create: `lo_pdf_service/.gitignore`
- Create: `lo_pdf_service/README.md`
- Create: package `__init__.py` files under `lo_pdf_service/app/`
- Create: `lo_pdf_service/tests/conftest.py`

- [ ] **Step 1: Create package and test directories**

Run:

```bash
cd lo_pdf_service
mkdir -p app/api app/core app/conversion app/jobs app/storage tests/unit tests/integration tests/fixtures
touch app/__init__.py app/api/__init__.py app/core/__init__.py app/conversion/__init__.py app/jobs/__init__.py app/storage/__init__.py
```

Expected: directories exist and no files are created outside `lo_pdf_service/`.

- [ ] **Step 2: Create `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "libreoffice-document-conversion-service"
version = "0.1.0"
description = "FastAPI service for converting Office, PDF, image, and email files to PDF using LibreOffice."
requires-python = ">=3.11"
dependencies = [
  "beautifulsoup4>=4.12.3",
  "extract-msg>=0.48.5",
  "fastapi>=0.115.0",
  "httpx>=0.27.0",
  "olefile>=0.47",
  "pillow>=10.4.0",
  "pydantic>=2.8.0",
  "pydantic-settings>=2.4.0",
  "pypdf>=4.3.0",
  "python-multipart>=0.0.9",
  "uvicorn[standard]>=0.30.0"
]

[project.optional-dependencies]
dev = [
  "pytest>=8.3.0",
  "pytest-asyncio>=0.23.8",
  "pytest-cov>=5.0.0"
]

[tool.setuptools.packages.find]
where = ["."]
include = ["app*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
markers = [
  "integration: tests that require LibreOffice or full runtime dependencies"
]
addopts = "-q"
```

- [ ] **Step 3: Create `.gitignore`**

```gitignore
.pytest_cache/
.ruff_cache/
.venv/
*.egg-info/
__pycache__/
*.pyc
.coverage
htmlcov/
data/
work/
results/
```

- [ ] **Step 4: Create initial `README.md`**

````markdown
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
````

- [ ] **Step 5: Create `tests/conftest.py`**

```python
from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture()
def temp_settings_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    data_dir = tmp_path / "data"
    monkeypatch.setenv("LOPDF_DATA_DIR", str(data_dir))
    monkeypatch.setenv("LOPDF_MAX_UPLOAD_BYTES", "52428800")
    monkeypatch.setenv("LOPDF_MAX_EMAIL_ATTACHMENT_BYTES", "104857600")
    monkeypatch.setenv("LOPDF_MAX_ATTACHMENTS", "50")
    monkeypatch.setenv("LOPDF_REQUEST_TIMEOUT_SECONDS", "120")
    monkeypatch.setenv("LOPDF_LIBREOFFICE_TIMEOUT_SECONDS", "90")
    monkeypatch.setenv("LOPDF_MAX_CONCURRENT_LIBREOFFICE", "2")
    monkeypatch.setenv("LOPDF_JOB_RETENTION_SECONDS", "86400")
    return data_dir


@pytest.fixture(autouse=True)
def clean_lopdf_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(os.environ):
        if key.startswith("LOPDF_"):
            monkeypatch.delenv(key, raising=False)
```

- [ ] **Step 6: Verify test discovery**

Run:

```bash
cd lo_pdf_service
python -m pytest
```

Expected: pytest exits with code 5 and prints `no tests ran` because no tests have been added yet.

- [ ] **Step 7: Commit**

```bash
git add lo_pdf_service/pyproject.toml lo_pdf_service/.gitignore lo_pdf_service/README.md lo_pdf_service/app lo_pdf_service/tests/conftest.py
git commit -m "chore: scaffold libreoffice conversion service"
```

## Task 2: Configuration And Error Model

**Files:**
- Create: `lo_pdf_service/tests/unit/test_config.py`
- Create: `lo_pdf_service/tests/unit/test_errors.py`
- Create: `lo_pdf_service/app/core/config.py`
- Create: `lo_pdf_service/app/core/errors.py`

- [ ] **Step 1: Write failing config tests**

```python
from __future__ import annotations

from pathlib import Path

from app.core.config import Settings


def test_settings_use_expected_defaults(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data")

    assert settings.data_dir == tmp_path / "data"
    assert settings.max_upload_bytes == 50 * 1024 * 1024
    assert settings.max_email_attachment_bytes == 100 * 1024 * 1024
    assert settings.max_attachments == 50
    assert settings.request_timeout_seconds == 120
    assert settings.libreoffice_timeout_seconds == 90
    assert settings.max_concurrent_libreoffice == 2
    assert settings.job_retention_seconds == 24 * 60 * 60


def test_settings_create_derived_directories(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data")

    assert settings.work_dir == tmp_path / "data" / "work"
    assert settings.result_dir == tmp_path / "data" / "results"
    assert settings.job_dir == tmp_path / "data" / "jobs"
```

Run:

```bash
cd lo_pdf_service
python -m pytest tests/unit/test_config.py -q
```

Expected: FAIL because `app.core.config` does not exist.

- [ ] **Step 2: Implement config**

```python
from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LOPDF_", extra="ignore")

    data_dir: Path = Field(default=Path("data"))
    max_upload_bytes: int = Field(default=50 * 1024 * 1024)
    max_email_attachment_bytes: int = Field(default=100 * 1024 * 1024)
    max_attachments: int = Field(default=50)
    request_timeout_seconds: int = Field(default=120)
    libreoffice_timeout_seconds: int = Field(default=90)
    max_concurrent_libreoffice: int = Field(default=2)
    job_retention_seconds: int = Field(default=24 * 60 * 60)
    soffice_binary: str = Field(default="soffice")

    @property
    def work_dir(self) -> Path:
        return self.data_dir / "work"

    @property
    def result_dir(self) -> Path:
        return self.data_dir / "results"

    @property
    def job_dir(self) -> Path:
        return self.data_dir / "jobs"


def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 3: Verify config tests pass**

Run:

```bash
cd lo_pdf_service
python -m pytest tests/unit/test_config.py -q
```

Expected: PASS.

- [ ] **Step 4: Write failing error tests**

```python
from __future__ import annotations

from app.core.errors import AppError, ErrorCode


def test_app_error_serializes_to_response_payload() -> None:
    error = AppError(
        code=ErrorCode.CONVERSION_TIMEOUT,
        message="Conversion exceeded the configured timeout.",
        details={"source_filename": "input.docx"},
    )

    assert error.to_dict() == {
        "error": {
            "code": "conversion_timeout",
            "message": "Conversion exceeded the configured timeout.",
            "details": {"source_filename": "input.docx"},
        }
    }


def test_app_error_uses_empty_details_by_default() -> None:
    error = AppError(code=ErrorCode.JOB_NOT_FOUND, message="Job not found.")

    assert error.to_dict()["error"]["details"] == {}
```

Run:

```bash
cd lo_pdf_service
python -m pytest tests/unit/test_errors.py -q
```

Expected: FAIL because `app.core.errors` is incomplete.

- [ ] **Step 5: Implement errors**

```python
from __future__ import annotations

from enum import StrEnum
from typing import Any


class ErrorCode(StrEnum):
    UNSUPPORTED_FILE_TYPE = "unsupported_file_type"
    FILE_TOO_LARGE = "file_too_large"
    EMAIL_TOO_LARGE = "email_too_large"
    TOO_MANY_ATTACHMENTS = "too_many_attachments"
    EMAIL_PARSE_FAILED = "email_parse_failed"
    CONVERSION_TIMEOUT = "conversion_timeout"
    LIBREOFFICE_FAILED = "libreoffice_failed"
    PDF_VALIDATION_FAILED = "pdf_validation_failed"
    ATTACHMENT_CONVERSION_FAILED = "attachment_conversion_failed"
    JOB_NOT_FOUND = "job_not_found"
    JOB_NOT_READY = "job_not_ready"
    JOB_EXPIRED = "job_expired"


class AppError(Exception):
    def __init__(
        self,
        *,
        code: ErrorCode,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code.value,
                "message": self.message,
                "details": self.details,
            }
        }
```

- [ ] **Step 6: Verify task tests pass**

Run:

```bash
cd lo_pdf_service
python -m pytest tests/unit/test_config.py tests/unit/test_errors.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add lo_pdf_service/app/core/config.py lo_pdf_service/app/core/errors.py lo_pdf_service/tests/unit/test_config.py lo_pdf_service/tests/unit/test_errors.py
git commit -m "feat: add service configuration and errors"
```

## Task 3: File Type Detection

**Files:**
- Create: `lo_pdf_service/tests/unit/test_detector.py`
- Create: `lo_pdf_service/app/conversion/detector.py`

- [ ] **Step 1: Write failing detector tests**

```python
from __future__ import annotations

import pytest

from app.conversion.detector import FileCategory, detect_file_type
from app.core.errors import AppError, ErrorCode


@pytest.mark.parametrize(
    ("filename", "category"),
    [
        ("letter.doc", FileCategory.OFFICE),
        ("letter.docx", FileCategory.OFFICE),
        ("sheet.xlsx", FileCategory.OFFICE),
        ("slides.pptx", FileCategory.OFFICE),
        ("notes.txt", FileCategory.OFFICE),
        ("page.html", FileCategory.OFFICE),
        ("report.pdf", FileCategory.PDF),
        ("mail.eml", FileCategory.EMAIL),
        ("mail.msg", FileCategory.EMAIL),
        ("scan.png", FileCategory.IMAGE),
        ("photo.jpeg", FileCategory.IMAGE),
    ],
)
def test_detect_supported_file_categories(filename: str, category: FileCategory) -> None:
    detected = detect_file_type(filename)

    assert detected.category == category
    assert detected.extension == filename.rsplit(".", 1)[1].lower()


def test_detection_is_case_insensitive() -> None:
    assert detect_file_type("REPORT.PDF").category == FileCategory.PDF


def test_rejects_unsupported_extension() -> None:
    with pytest.raises(AppError) as exc_info:
        detect_file_type("drawing.vsdx")

    assert exc_info.value.code == ErrorCode.UNSUPPORTED_FILE_TYPE
```

Run:

```bash
cd lo_pdf_service
python -m pytest tests/unit/test_detector.py -q
```

Expected: FAIL because detector does not exist.

- [ ] **Step 2: Implement detector**

```python
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from app.core.errors import AppError, ErrorCode


class FileCategory(StrEnum):
    OFFICE = "office"
    PDF = "pdf"
    EMAIL = "email"
    IMAGE = "image"


OFFICE_EXTENSIONS = {
    "doc", "docx", "dot", "dotx", "rtf", "odt",
    "xls", "xlsx", "xlsm", "xlt", "xltx", "csv", "tsv", "ods",
    "ppt", "pptx", "pps", "ppsx", "odp",
    "txt", "html", "htm",
}
PDF_EXTENSIONS = {"pdf"}
EMAIL_EXTENSIONS = {"eml", "msg"}
IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "bmp", "tif", "tiff"}


@dataclass(frozen=True)
class DetectedFile:
    filename: str
    extension: str
    category: FileCategory


def detect_file_type(filename: str) -> DetectedFile:
    suffix = Path(filename).suffix.lower().lstrip(".")
    if suffix in OFFICE_EXTENSIONS:
        return DetectedFile(filename=filename, extension=suffix, category=FileCategory.OFFICE)
    if suffix in PDF_EXTENSIONS:
        return DetectedFile(filename=filename, extension=suffix, category=FileCategory.PDF)
    if suffix in EMAIL_EXTENSIONS:
        return DetectedFile(filename=filename, extension=suffix, category=FileCategory.EMAIL)
    if suffix in IMAGE_EXTENSIONS:
        return DetectedFile(filename=filename, extension=suffix, category=FileCategory.IMAGE)
    raise AppError(
        code=ErrorCode.UNSUPPORTED_FILE_TYPE,
        message="Unsupported file type.",
        details={"filename": filename, "extension": suffix},
    )
```

- [ ] **Step 3: Verify detector tests pass**

Run:

```bash
cd lo_pdf_service
python -m pytest tests/unit/test_detector.py -q
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add lo_pdf_service/app/conversion/detector.py lo_pdf_service/tests/unit/test_detector.py
git commit -m "feat: detect supported conversion file types"
```

## Task 4: Conversion Models And Manifest

**Files:**
- Create: `lo_pdf_service/tests/unit/test_manifest.py`
- Create: `lo_pdf_service/app/conversion/manifest.py`
- Create: `lo_pdf_service/app/models.py`

- [ ] **Step 1: Write failing manifest tests**

```python
from __future__ import annotations

from pathlib import Path

from app.conversion.manifest import AttachmentRecord, ConversionManifest
from app.models import OutputKind


def test_manifest_records_converted_and_skipped_attachments() -> None:
    manifest = ConversionManifest(source_filename="message.eml", output_kind=OutputKind.ZIP)
    manifest.add_output("message", Path("message.pdf"))
    manifest.add_attachment(
        AttachmentRecord(
            original_filename="invoice.docx",
            output_filename="attachments/invoice.pdf",
            status="converted",
            reason=None,
        )
    )
    manifest.add_attachment(
        AttachmentRecord(
            original_filename="archive.zip",
            output_filename=None,
            status="skipped",
            reason="unsupported_file_type",
        )
    )

    payload = manifest.to_dict()

    assert payload["source_filename"] == "message.eml"
    assert payload["output_kind"] == "zip"
    assert payload["outputs"] == [{"name": "message", "path": "message.pdf"}]
    assert payload["attachments"][0]["status"] == "converted"
    assert payload["attachments"][1]["reason"] == "unsupported_file_type"
```

Run:

```bash
cd lo_pdf_service
python -m pytest tests/unit/test_manifest.py -q
```

Expected: FAIL because manifest and models do not exist.

- [ ] **Step 2: Implement models**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class ExecutionMode(StrEnum):
    SYNC = "sync"
    ASYNC = "async"


class EmailMode(StrEnum):
    MERGED = "merged"
    SPLIT = "split"


class OutputKind(StrEnum):
    PDF = "pdf"
    ZIP = "zip"


@dataclass(frozen=True)
class ConversionOptions:
    email_mode: EmailMode = EmailMode.MERGED
    include_attachments: bool = True
    timeout_seconds: int | None = None
    max_email_attachment_bytes: int | None = None
    max_attachments: int | None = None


@dataclass(frozen=True)
class ConversionResult:
    output_path: Path
    output_kind: OutputKind
    media_type: str
    filename: str
    manifest: dict[str, object] = field(default_factory=dict)
```

- [ ] **Step 3: Implement manifest**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.models import OutputKind


@dataclass(frozen=True)
class AttachmentRecord:
    original_filename: str
    output_filename: str | None
    status: str
    reason: str | None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "original_filename": self.original_filename,
            "output_filename": self.output_filename,
            "status": self.status,
            "reason": self.reason,
        }


@dataclass
class ConversionManifest:
    source_filename: str
    output_kind: OutputKind
    outputs: list[dict[str, str]] = field(default_factory=list)
    attachments: list[AttachmentRecord] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_output(self, name: str, path: Path) -> None:
        self.outputs.append({"name": name, "path": path.as_posix()})

    def add_attachment(self, record: AttachmentRecord) -> None:
        self.attachments.append(record)

    def add_warning(self, warning: str) -> None:
        self.warnings.append(warning)

    def to_dict(self) -> dict[str, object]:
        return {
            "source_filename": self.source_filename,
            "output_kind": self.output_kind.value,
            "outputs": self.outputs,
            "attachments": [record.to_dict() for record in self.attachments],
            "warnings": self.warnings,
        }
```

- [ ] **Step 4: Verify tests pass**

Run:

```bash
cd lo_pdf_service
python -m pytest tests/unit/test_manifest.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add lo_pdf_service/app/models.py lo_pdf_service/app/conversion/manifest.py lo_pdf_service/tests/unit/test_manifest.py
git commit -m "feat: add conversion result models and manifest"
```

## Task 5: Local Workspace Storage

**Files:**
- Create: `lo_pdf_service/tests/unit/test_storage.py`
- Create: `lo_pdf_service/app/storage/local.py`
- Create: `lo_pdf_service/app/core/paths.py`

- [ ] **Step 1: Write failing storage tests**

```python
from __future__ import annotations

from pathlib import Path

from app.storage.local import LocalStorage


def test_create_workspace_makes_isolated_directories(tmp_path: Path) -> None:
    storage = LocalStorage(base_dir=tmp_path)

    workspace = storage.create_workspace("job-1")

    assert workspace.root == tmp_path / "work" / "job-1"
    assert workspace.input_dir.is_dir()
    assert workspace.output_dir.is_dir()
    assert workspace.profile_dir.is_dir()


def test_cleanup_workspace_removes_only_workspace(tmp_path: Path) -> None:
    storage = LocalStorage(base_dir=tmp_path)
    workspace = storage.create_workspace("job-1")
    outside = tmp_path / "outside.txt"
    outside.write_text("keep", encoding="utf-8")

    storage.cleanup_workspace(workspace)

    assert not workspace.root.exists()
    assert outside.read_text(encoding="utf-8") == "keep"
```

Run:

```bash
cd lo_pdf_service
python -m pytest tests/unit/test_storage.py -q
```

Expected: FAIL because storage does not exist.

- [ ] **Step 2: Implement path safety helper**

```python
from __future__ import annotations

from pathlib import Path


def ensure_child_path(parent: Path, child: Path) -> Path:
    resolved_parent = parent.resolve()
    resolved_child = child.resolve()
    if resolved_child != resolved_parent and resolved_parent not in resolved_child.parents:
        raise ValueError(f"Path {resolved_child} is not inside {resolved_parent}")
    return resolved_child
```

- [ ] **Step 3: Implement local storage**

```python
from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from app.core.paths import ensure_child_path


@dataclass(frozen=True)
class Workspace:
    root: Path
    input_dir: Path
    output_dir: Path
    profile_dir: Path


class LocalStorage:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.work_root = base_dir / "work"
        self.result_root = base_dir / "results"
        self.job_root = base_dir / "jobs"

    def create_workspace(self, workspace_id: str) -> Workspace:
        root = ensure_child_path(self.work_root, self.work_root / workspace_id)
        input_dir = root / "input"
        output_dir = root / "output"
        profile_dir = root / "lo-profile"
        input_dir.mkdir(parents=True, exist_ok=False)
        output_dir.mkdir(parents=True, exist_ok=False)
        profile_dir.mkdir(parents=True, exist_ok=False)
        self.result_root.mkdir(parents=True, exist_ok=True)
        self.job_root.mkdir(parents=True, exist_ok=True)
        return Workspace(root=root, input_dir=input_dir, output_dir=output_dir, profile_dir=profile_dir)

    def cleanup_workspace(self, workspace: Workspace) -> None:
        ensure_child_path(self.work_root, workspace.root)
        shutil.rmtree(workspace.root, ignore_errors=True)
```

- [ ] **Step 4: Verify storage tests pass**

Run:

```bash
cd lo_pdf_service
python -m pytest tests/unit/test_storage.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add lo_pdf_service/app/core/paths.py lo_pdf_service/app/storage/local.py lo_pdf_service/tests/unit/test_storage.py
git commit -m "feat: manage isolated conversion workspaces"
```

## Task 6: PDF And Image Operations

**Files:**
- Create: `lo_pdf_service/tests/unit/test_pdf_ops.py`
- Create: `lo_pdf_service/tests/unit/test_image_converter.py`
- Create: `lo_pdf_service/app/conversion/pdf_ops.py`
- Create: `lo_pdf_service/app/conversion/image_converter.py`

- [ ] **Step 1: Write failing PDF operation tests**

```python
from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter

from app.conversion.pdf_ops import merge_pdfs, validate_pdf
from app.core.errors import AppError, ErrorCode


def make_pdf(path: Path) -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with path.open("wb") as file:
        writer.write(file)


def test_validate_pdf_accepts_readable_pdf(tmp_path: Path) -> None:
    pdf = tmp_path / "input.pdf"
    make_pdf(pdf)

    validate_pdf(pdf)


def test_validate_pdf_rejects_empty_file(tmp_path: Path) -> None:
    pdf = tmp_path / "empty.pdf"
    pdf.write_bytes(b"")

    with pytest.raises(AppError) as exc_info:
        validate_pdf(pdf)

    assert exc_info.value.code == ErrorCode.PDF_VALIDATION_FAILED


def test_merge_pdfs_combines_pages(tmp_path: Path) -> None:
    first = tmp_path / "first.pdf"
    second = tmp_path / "second.pdf"
    output = tmp_path / "merged.pdf"
    make_pdf(first)
    make_pdf(second)

    merge_pdfs([first, second], output)

    assert len(PdfReader(str(output)).pages) == 2
```

Run:

```bash
cd lo_pdf_service
python -m pytest tests/unit/test_pdf_ops.py -q
```

Expected: FAIL because `pdf_ops` does not exist.

- [ ] **Step 2: Implement PDF operations**

```python
from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader, PdfWriter

from app.core.errors import AppError, ErrorCode


def validate_pdf(path: Path) -> None:
    if not path.exists() or path.stat().st_size == 0:
        raise AppError(
            code=ErrorCode.PDF_VALIDATION_FAILED,
            message="PDF file is missing or empty.",
            details={"path": str(path)},
        )
    try:
        reader = PdfReader(str(path))
        if len(reader.pages) == 0:
            raise ValueError("PDF has no pages")
    except Exception as exc:
        raise AppError(
            code=ErrorCode.PDF_VALIDATION_FAILED,
            message="PDF file could not be read.",
            details={"path": str(path), "reason": str(exc)},
        ) from exc


def merge_pdfs(inputs: list[Path], output: Path) -> None:
    writer = PdfWriter()
    for input_path in inputs:
        validate_pdf(input_path)
        reader = PdfReader(str(input_path))
        for page in reader.pages:
            writer.add_page(page)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as file:
        writer.write(file)
    validate_pdf(output)
```

- [ ] **Step 3: Write failing image conversion tests**

```python
from __future__ import annotations

from pathlib import Path

from PIL import Image
from pypdf import PdfReader

from app.conversion.image_converter import image_to_pdf


def test_image_to_pdf_creates_readable_pdf(tmp_path: Path) -> None:
    image_path = tmp_path / "photo.png"
    output_path = tmp_path / "photo.pdf"
    Image.new("RGB", (120, 80), color="white").save(image_path)

    image_to_pdf(image_path, output_path)

    assert output_path.exists()
    assert len(PdfReader(str(output_path)).pages) == 1
```

Run:

```bash
cd lo_pdf_service
python -m pytest tests/unit/test_image_converter.py -q
```

Expected: FAIL because `image_converter` does not exist.

- [ ] **Step 4: Implement image conversion**

```python
from __future__ import annotations

from pathlib import Path

from PIL import Image

from app.conversion.pdf_ops import validate_pdf


def image_to_pdf(input_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(input_path) as image:
        rgb_image = image.convert("RGB")
        rgb_image.save(output_path, "PDF", resolution=100.0)
    validate_pdf(output_path)
```

- [ ] **Step 5: Verify PDF and image tests pass**

Run:

```bash
cd lo_pdf_service
python -m pytest tests/unit/test_pdf_ops.py tests/unit/test_image_converter.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add lo_pdf_service/app/conversion/pdf_ops.py lo_pdf_service/app/conversion/image_converter.py lo_pdf_service/tests/unit/test_pdf_ops.py lo_pdf_service/tests/unit/test_image_converter.py
git commit -m "feat: add pdf and image conversion helpers"
```

## Task 7: LibreOffice Wrapper

**Files:**
- Create: `lo_pdf_service/tests/unit/test_libreoffice.py`
- Create: `lo_pdf_service/tests/integration/test_libreoffice_smoke.py`
- Create: `lo_pdf_service/app/conversion/libreoffice.py`

- [ ] **Step 1: Write failing unit tests for command construction and failure mapping**

```python
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from app.conversion.libreoffice import LibreOfficeConverter
from app.core.errors import AppError, ErrorCode


def test_libreoffice_uses_isolated_profile_and_validates_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    input_file = tmp_path / "input.docx"
    output_dir = tmp_path / "out"
    profile_dir = tmp_path / "profile"
    input_file.write_bytes(b"fake")
    output_dir.mkdir()
    profile_dir.mkdir()

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        assert "--headless" in command
        assert f"--env:UserInstallation={profile_dir.as_uri()}" in command
        assert str(input_file) in command
        (output_dir / "input.pdf").write_bytes(b"%PDF-1.4\n%fake\n")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr("app.conversion.libreoffice.validate_pdf", lambda path: None)

    converter = LibreOfficeConverter(soffice_binary="soffice", timeout_seconds=10)
    result = converter.convert_to_pdf(input_file=input_file, output_dir=output_dir, profile_dir=profile_dir)

    assert result == output_dir / "input.pdf"


def test_libreoffice_timeout_maps_to_app_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    input_file = tmp_path / "input.docx"
    output_dir = tmp_path / "out"
    profile_dir = tmp_path / "profile"
    input_file.write_bytes(b"fake")
    output_dir.mkdir()
    profile_dir.mkdir()

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(command, timeout=1)

    monkeypatch.setattr(subprocess, "run", fake_run)

    converter = LibreOfficeConverter(soffice_binary="soffice", timeout_seconds=1)
    with pytest.raises(AppError) as exc_info:
        converter.convert_to_pdf(input_file=input_file, output_dir=output_dir, profile_dir=profile_dir)

    assert exc_info.value.code == ErrorCode.CONVERSION_TIMEOUT
```

Run:

```bash
cd lo_pdf_service
python -m pytest tests/unit/test_libreoffice.py -q
```

Expected: FAIL because `libreoffice.py` does not exist.

- [ ] **Step 2: Implement LibreOffice wrapper**

```python
from __future__ import annotations

import subprocess
from pathlib import Path

from app.conversion.pdf_ops import validate_pdf
from app.core.errors import AppError, ErrorCode


class LibreOfficeConverter:
    def __init__(self, *, soffice_binary: str, timeout_seconds: int) -> None:
        self.soffice_binary = soffice_binary
        self.timeout_seconds = timeout_seconds

    def convert_to_pdf(self, *, input_file: Path, output_dir: Path, profile_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        profile_dir.mkdir(parents=True, exist_ok=True)
        expected_output = output_dir / f"{input_file.stem}.pdf"
        command = [
            self.soffice_binary,
            "--headless",
            "--nologo",
            "--nofirststartwizard",
            f"--env:UserInstallation={profile_dir.as_uri()}",
            "--convert-to",
            "pdf",
            "--outdir",
            str(output_dir),
            str(input_file),
        ]
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise AppError(
                code=ErrorCode.CONVERSION_TIMEOUT,
                message="LibreOffice conversion exceeded the configured timeout.",
                details={"input_file": str(input_file), "timeout_seconds": self.timeout_seconds},
            ) from exc

        if completed.returncode != 0:
            raise AppError(
                code=ErrorCode.LIBREOFFICE_FAILED,
                message="LibreOffice conversion failed.",
                details={
                    "input_file": str(input_file),
                    "stdout": completed.stdout,
                    "stderr": completed.stderr,
                },
            )

        if not expected_output.exists():
            pdf_outputs = sorted(output_dir.glob("*.pdf"))
            if len(pdf_outputs) == 1:
                expected_output = pdf_outputs[0]
            else:
                raise AppError(
                    code=ErrorCode.LIBREOFFICE_FAILED,
                    message="LibreOffice did not produce a PDF output.",
                    details={"input_file": str(input_file), "output_dir": str(output_dir)},
                )
        validate_pdf(expected_output)
        return expected_output
```

- [ ] **Step 3: Verify unit tests pass**

Run:

```bash
cd lo_pdf_service
python -m pytest tests/unit/test_libreoffice.py -q
```

Expected: PASS.

- [ ] **Step 4: Write integration smoke test requiring LibreOffice**

```python
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from app.conversion.libreoffice import LibreOfficeConverter
from app.conversion.pdf_ops import validate_pdf


@pytest.mark.integration
def test_libreoffice_converts_text_file_to_pdf(tmp_path: Path) -> None:
    if shutil.which("soffice") is None:
        pytest.skip("LibreOffice soffice binary is not installed")
    input_file = tmp_path / "input.txt"
    output_dir = tmp_path / "out"
    profile_dir = tmp_path / "profile"
    input_file.write_text("Hello from LibreOffice", encoding="utf-8")

    converter = LibreOfficeConverter(soffice_binary="soffice", timeout_seconds=30)
    output = converter.convert_to_pdf(input_file=input_file, output_dir=output_dir, profile_dir=profile_dir)

    validate_pdf(output)
```

- [ ] **Step 5: Run unit suite and optional integration test**

Run:

```bash
cd lo_pdf_service
python -m pytest tests/unit/test_libreoffice.py -q
python -m pytest tests/integration/test_libreoffice_smoke.py -q -m integration
```

Expected: unit PASS; integration PASS on Linux/WSL with LibreOffice installed or SKIP when `soffice` is unavailable.

- [ ] **Step 6: Commit**

```bash
git add lo_pdf_service/app/conversion/libreoffice.py lo_pdf_service/tests/unit/test_libreoffice.py lo_pdf_service/tests/integration/test_libreoffice_smoke.py
git commit -m "feat: wrap libreoffice headless conversion"
```

## Task 8: Email Conversion

**Files:**
- Create: `lo_pdf_service/tests/unit/test_email_converter.py`
- Create: `lo_pdf_service/app/conversion/email_converter.py`

- [ ] **Step 1: Write failing email parsing and split output tests**

```python
from __future__ import annotations

from email.message import EmailMessage
from pathlib import Path
from zipfile import ZipFile

import pytest
from pypdf import PdfWriter

from app.conversion.email_converter import EmailConverter
from app.core.errors import AppError, ErrorCode
from app.models import ConversionOptions, EmailMode, OutputKind


class FakeOfficeConverter:
    def convert_to_pdf(self, *, input_file: Path, output_dir: Path, profile_dir: Path) -> Path:
        output = output_dir / f"{input_file.stem}.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        with output.open("wb") as file:
            writer.write(file)
        return output


def write_message(path: Path) -> None:
    message = EmailMessage()
    message["From"] = "sender@example.com"
    message["To"] = "receiver@example.com"
    message["Subject"] = "Quarterly report"
    message.set_content("Plain body")
    message.add_attachment(
        b"attachment text",
        maintype="text",
        subtype="plain",
        filename="notes.txt",
    )
    path.write_bytes(message.as_bytes())


def test_email_split_creates_zip_with_message_attachment_and_manifest(tmp_path: Path) -> None:
    source = tmp_path / "message.eml"
    output_dir = tmp_path / "out"
    profile_dir = tmp_path / "profile"
    write_message(source)
    output_dir.mkdir()
    profile_dir.mkdir()

    converter = EmailConverter(office_converter=FakeOfficeConverter())
    result = converter.convert(
        input_file=source,
        output_dir=output_dir,
        profile_dir=profile_dir,
        options=ConversionOptions(email_mode=EmailMode.SPLIT),
    )

    assert result.output_kind == OutputKind.ZIP
    with ZipFile(result.output_path) as archive:
        names = set(archive.namelist())
    assert "message.pdf" in names
    assert "attachments/notes.pdf" in names
    assert "manifest.json" in names


def test_email_rejects_too_many_attachments(tmp_path: Path) -> None:
    source = tmp_path / "message.eml"
    output_dir = tmp_path / "out"
    profile_dir = tmp_path / "profile"
    write_message(source)
    output_dir.mkdir()
    profile_dir.mkdir()

    converter = EmailConverter(office_converter=FakeOfficeConverter())
    with pytest.raises(AppError) as exc_info:
        converter.convert(
            input_file=source,
            output_dir=output_dir,
            profile_dir=profile_dir,
            options=ConversionOptions(email_mode=EmailMode.SPLIT, max_attachments=0),
        )

    assert exc_info.value.code == ErrorCode.TOO_MANY_ATTACHMENTS
```

Run:

```bash
cd lo_pdf_service
python -m pytest tests/unit/test_email_converter.py -q
```

Expected: FAIL because `email_converter.py` does not exist.

- [ ] **Step 2: Implement email converter**

```python
from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from email import policy
from email.message import EmailMessage, Message
from email.parser import BytesParser
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

import extract_msg

from app.conversion.detector import FileCategory, detect_file_type
from app.conversion.image_converter import image_to_pdf
from app.conversion.manifest import AttachmentRecord, ConversionManifest
from app.conversion.pdf_ops import merge_pdfs, validate_pdf
from app.core.errors import AppError, ErrorCode
from app.models import ConversionOptions, ConversionResult, EmailMode, OutputKind


SAFE_NAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


def safe_stem(filename: str) -> str:
    stem = Path(filename).stem or "attachment"
    cleaned = SAFE_NAME_PATTERN.sub("_", stem).strip("._")
    return cleaned or "attachment"


@dataclass(frozen=True)
class EmailAttachment:
    filename: str
    payload: bytes


@dataclass(frozen=True)
class ParsedEmail:
    message: Message
    attachments: list[EmailAttachment]


class EmailConverter:
    def __init__(self, *, office_converter: object) -> None:
        self.office_converter = office_converter

    def convert(
        self,
        *,
        input_file: Path,
        output_dir: Path,
        profile_dir: Path,
        options: ConversionOptions,
    ) -> ConversionResult:
        parsed = self._parse_message(input_file)
        message = parsed.message
        manifest = ConversionManifest(
            source_filename=input_file.name,
            output_kind=OutputKind.ZIP if options.email_mode == EmailMode.SPLIT else OutputKind.PDF,
        )
        message_pdf = self._render_message_pdf(message, output_dir, profile_dir)
        manifest.add_output("message", Path("message.pdf"))
        attachment_pdfs = self._convert_attachments(parsed.attachments, output_dir, profile_dir, options, manifest)

        if options.email_mode == EmailMode.SPLIT:
            zip_path = output_dir / f"{input_file.stem}.zip"
            self._write_split_zip(zip_path, message_pdf, attachment_pdfs, manifest)
            return ConversionResult(
                output_path=zip_path,
                output_kind=OutputKind.ZIP,
                media_type="application/zip",
                filename=zip_path.name,
                manifest=manifest.to_dict(),
            )

        merged_path = output_dir / f"{input_file.stem}.pdf"
        merge_pdfs([message_pdf, *attachment_pdfs], merged_path)
        return ConversionResult(
            output_path=merged_path,
            output_kind=OutputKind.PDF,
            media_type="application/pdf",
            filename=merged_path.name,
            manifest=manifest.to_dict(),
        )

    def _parse_message(self, input_file: Path) -> ParsedEmail:
        if input_file.suffix.lower() == ".msg":
            return self._parse_msg(input_file)
        return self._parse_eml(input_file)

    def _parse_eml(self, input_file: Path) -> ParsedEmail:
        try:
            message = BytesParser(policy=policy.default).parsebytes(input_file.read_bytes())
            attachments = [
                EmailAttachment(
                    filename=part.get_filename() or "attachment",
                    payload=part.get_payload(decode=True) or b"",
                )
                for part in message.iter_attachments()
            ]
            return ParsedEmail(message=message, attachments=attachments)
        except Exception as exc:
            raise AppError(
                code=ErrorCode.EMAIL_PARSE_FAILED,
                message="Email file could not be parsed.",
                details={"input_file": str(input_file), "reason": str(exc)},
            ) from exc

    def _parse_msg(self, input_file: Path) -> ParsedEmail:
        try:
            msg = extract_msg.Message(str(input_file))
            message = EmailMessage(policy=policy.default)
            message["From"] = msg.sender or ""
            message["To"] = msg.to or ""
            message["Cc"] = msg.cc or ""
            message["Subject"] = msg.subject or ""
            message["Date"] = str(msg.date or "")
            if msg.htmlBody:
                html_body = msg.htmlBody.decode("utf-8", errors="replace") if isinstance(msg.htmlBody, bytes) else str(msg.htmlBody)
                message.set_content(msg.body or "")
                message.add_alternative(html_body, subtype="html")
            else:
                message.set_content(msg.body or "")
            attachments: list[EmailAttachment] = []
            for index, attachment in enumerate(msg.attachments):
                filename = attachment.longFilename or attachment.shortFilename or f"attachment-{index + 1}"
                data = attachment.data or b""
                attachments.append(EmailAttachment(filename=filename, payload=data))
            return ParsedEmail(message=message, attachments=attachments)
        except Exception as exc:
            raise AppError(
                code=ErrorCode.EMAIL_PARSE_FAILED,
                message="MSG email file could not be parsed.",
                details={"input_file": str(input_file), "reason": str(exc)},
            ) from exc

    def _render_message_pdf(self, message: Message, output_dir: Path, profile_dir: Path) -> Path:
        html_path = output_dir / "message.html"
        body = self._extract_body(message)
        headers = {
            "From": str(message.get("From", "")),
            "To": str(message.get("To", "")),
            "Cc": str(message.get("Cc", "")),
            "Subject": str(message.get("Subject", "")),
            "Date": str(message.get("Date", "")),
        }
        header_rows = "\n".join(
            f"<tr><th>{html.escape(key)}</th><td>{html.escape(value)}</td></tr>"
            for key, value in headers.items()
            if value
        )
        html_path.write_text(
            "<html><head><meta charset='utf-8'><style>"
            "body{font-family:sans-serif;font-size:12pt;}"
            "table{border-collapse:collapse;margin-bottom:24px;}"
            "th{text-align:left;padding:4px 12px 4px 0;}"
            "td{padding:4px;}"
            "</style></head><body>"
            f"<table>{header_rows}</table><div>{body}</div>"
            "</body></html>",
            encoding="utf-8",
        )
        pdf_path = self.office_converter.convert_to_pdf(
            input_file=html_path,
            output_dir=output_dir,
            profile_dir=profile_dir,
        )
        target = output_dir / "message.pdf"
        if pdf_path != target:
            pdf_path.replace(target)
        validate_pdf(target)
        return target

    def _extract_body(self, message: Message) -> str:
        if message.is_multipart():
            html_part = None
            text_part = None
            for part in message.walk():
                if part.get_content_disposition() == "attachment":
                    continue
                content_type = part.get_content_type()
                if content_type == "text/html" and html_part is None:
                    html_part = part
                elif content_type == "text/plain" and text_part is None:
                    text_part = part
            selected = html_part or text_part
            if selected is None:
                return ""
            content = selected.get_content()
            if selected.get_content_type() == "text/html":
                return str(content)
            return f"<pre>{html.escape(str(content))}</pre>"
        content = message.get_content()
        if message.get_content_type() == "text/html":
            return str(content)
        return f"<pre>{html.escape(str(content))}</pre>"

    def _convert_attachments(
        self,
        attachments: list[EmailAttachment],
        output_dir: Path,
        profile_dir: Path,
        options: ConversionOptions,
        manifest: ConversionManifest,
    ) -> list[Path]:
        if not options.include_attachments:
            return []
        attachment_outputs: list[Path] = []
        attachments_dir = output_dir / "attachments"
        attachments_dir.mkdir(parents=True, exist_ok=True)
        if options.max_attachments is not None and len(attachments) > options.max_attachments:
            raise AppError(
                code=ErrorCode.TOO_MANY_ATTACHMENTS,
                message="Email contains too many attachments.",
                details={"max_attachments": options.max_attachments, "actual_attachments": len(attachments)},
            )
        total_attachment_bytes = 0
        for attachment in attachments:
            filename = attachment.filename
            payload = attachment.payload
            total_attachment_bytes += len(payload)
            if (
                options.max_email_attachment_bytes is not None
                and total_attachment_bytes > options.max_email_attachment_bytes
            ):
                raise AppError(
                    code=ErrorCode.EMAIL_TOO_LARGE,
                    message="Email attachments exceed the configured size limit.",
                    details={
                        "max_email_attachment_bytes": options.max_email_attachment_bytes,
                        "actual_attachment_bytes": total_attachment_bytes,
                    },
                )
            input_path = attachments_dir / filename
            input_path.write_bytes(payload)
            output_name = f"{safe_stem(filename)}.pdf"
            output_path = attachments_dir / output_name
            try:
                detected = detect_file_type(filename)
                if detected.category == FileCategory.OFFICE:
                    converted = self.office_converter.convert_to_pdf(
                        input_file=input_path,
                        output_dir=attachments_dir,
                        profile_dir=profile_dir,
                    )
                    if converted != output_path:
                        converted.replace(output_path)
                elif detected.category == FileCategory.PDF:
                    validate_pdf(input_path)
                    input_path.replace(output_path)
                elif detected.category == FileCategory.IMAGE:
                    image_to_pdf(input_path, output_path)
                else:
                    raise AppError(
                        code=ErrorCode.UNSUPPORTED_FILE_TYPE,
                        message="Unsupported attachment file type.",
                        details={"filename": filename},
                    )
                validate_pdf(output_path)
                attachment_outputs.append(output_path)
                manifest.add_attachment(
                    AttachmentRecord(
                        original_filename=filename,
                        output_filename=f"attachments/{output_name}",
                        status="converted",
                        reason=None,
                    )
                )
            except AppError as exc:
                manifest.add_attachment(
                    AttachmentRecord(
                        original_filename=filename,
                        output_filename=None,
                        status="skipped",
                        reason=exc.code.value,
                    )
                )
        return attachment_outputs

    def _write_split_zip(
        self,
        zip_path: Path,
        message_pdf: Path,
        attachment_pdfs: list[Path],
        manifest: ConversionManifest,
    ) -> None:
        with ZipFile(zip_path, "w", ZIP_DEFLATED) as archive:
            archive.write(message_pdf, "message.pdf")
            for attachment_pdf in attachment_pdfs:
                archive.write(attachment_pdf, f"attachments/{attachment_pdf.name}")
            archive.writestr("manifest.json", json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2))
```

- [ ] **Step 3: Verify split test passes**

Run:

```bash
cd lo_pdf_service
python -m pytest tests/unit/test_email_converter.py -q
```

Expected: PASS.

- [ ] **Step 4: Add merged mode test**

Append to `tests/unit/test_email_converter.py`:

```python
from pypdf import PdfReader


def test_email_merged_creates_single_pdf(tmp_path: Path) -> None:
    source = tmp_path / "message.eml"
    output_dir = tmp_path / "out"
    profile_dir = tmp_path / "profile"
    write_message(source)
    output_dir.mkdir()
    profile_dir.mkdir()

    converter = EmailConverter(office_converter=FakeOfficeConverter())
    result = converter.convert(
        input_file=source,
        output_dir=output_dir,
        profile_dir=profile_dir,
        options=ConversionOptions(email_mode=EmailMode.MERGED),
    )

    assert result.output_kind == OutputKind.PDF
    assert len(PdfReader(str(result.output_path)).pages) == 2
```

Run:

```bash
cd lo_pdf_service
python -m pytest tests/unit/test_email_converter.py::test_email_merged_creates_single_pdf -q
```

Expected: PASS because merged mode is already implemented.

- [ ] **Step 5: Add MSG parser unit test**

Append to `tests/unit/test_email_converter.py`:

```python
from app.conversion.email_converter import EmailAttachment, ParsedEmail


def test_msg_parser_path_is_used_for_msg_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "message.msg"
    output_dir = tmp_path / "out"
    profile_dir = tmp_path / "profile"
    source.write_bytes(b"fake msg")
    output_dir.mkdir()
    profile_dir.mkdir()

    def fake_parse_msg(self: EmailConverter, input_file: Path) -> ParsedEmail:
        message = EmailMessage()
        message["From"] = "sender@example.com"
        message["To"] = "receiver@example.com"
        message["Subject"] = "MSG body"
        message.set_content("Body from msg")
        return ParsedEmail(
            message=message,
            attachments=[EmailAttachment(filename="notes.txt", payload=b"attachment text")],
        )

    monkeypatch.setattr(EmailConverter, "_parse_msg", fake_parse_msg)

    converter = EmailConverter(office_converter=FakeOfficeConverter())
    result = converter.convert(
        input_file=source,
        output_dir=output_dir,
        profile_dir=profile_dir,
        options=ConversionOptions(email_mode=EmailMode.SPLIT),
    )

    assert result.output_kind == OutputKind.ZIP
    with ZipFile(result.output_path) as archive:
        assert "attachments/notes.pdf" in set(archive.namelist())
```

Run:

```bash
cd lo_pdf_service
python -m pytest tests/unit/test_email_converter.py::test_msg_parser_path_is_used_for_msg_files -q
```

Expected: PASS because `.msg` is routed through `_parse_msg`.

- [ ] **Step 6: Commit**

```bash
git add lo_pdf_service/app/conversion/email_converter.py lo_pdf_service/tests/unit/test_email_converter.py
git commit -m "feat: convert email messages and attachments"
```

## Task 9: Conversion Service Orchestration

**Files:**
- Create: `lo_pdf_service/tests/unit/test_service.py`
- Create: `lo_pdf_service/app/conversion/service.py`

- [ ] **Step 1: Write failing service tests**

```python
from __future__ import annotations

from pathlib import Path

from pypdf import PdfWriter

from app.conversion.service import ConversionService
from app.models import ConversionOptions, EmailMode, OutputKind
from app.storage.local import LocalStorage


class FakeOfficeConverter:
    def convert_to_pdf(self, *, input_file: Path, output_dir: Path, profile_dir: Path) -> Path:
        output = output_dir / f"{input_file.stem}.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        with output.open("wb") as file:
            writer.write(file)
        return output


def test_service_converts_office_file_to_pdf(tmp_path: Path) -> None:
    storage = LocalStorage(base_dir=tmp_path)
    service = ConversionService(storage=storage, office_converter=FakeOfficeConverter())
    input_file = tmp_path / "input.txt"
    input_file.write_text("hello", encoding="utf-8")

    result = service.convert(input_file=input_file, source_filename="input.txt", options=ConversionOptions())

    assert result.output_kind == OutputKind.PDF
    assert result.output_path.exists()


def test_service_routes_email_to_email_converter(tmp_path: Path) -> None:
    storage = LocalStorage(base_dir=tmp_path)
    service = ConversionService(storage=storage, office_converter=FakeOfficeConverter())
    input_file = tmp_path / "message.eml"
    input_file.write_text("From: a@example.com\nTo: b@example.com\nSubject: Hi\n\nBody", encoding="utf-8")

    result = service.convert(
        input_file=input_file,
        source_filename="message.eml",
        options=ConversionOptions(email_mode=EmailMode.SPLIT),
    )

    assert result.output_kind == OutputKind.ZIP
```

Run:

```bash
cd lo_pdf_service
python -m pytest tests/unit/test_service.py -q
```

Expected: FAIL because `service.py` does not exist.

- [ ] **Step 2: Implement conversion service**

```python
from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from app.conversion.detector import FileCategory, detect_file_type
from app.conversion.email_converter import EmailConverter
from app.conversion.image_converter import image_to_pdf
from app.conversion.pdf_ops import validate_pdf
from app.models import ConversionOptions, ConversionResult, OutputKind
from app.storage.local import LocalStorage


class ConversionService:
    def __init__(self, *, storage: LocalStorage, office_converter: object) -> None:
        self.storage = storage
        self.office_converter = office_converter
        self.email_converter = EmailConverter(office_converter=office_converter)

    def convert(
        self,
        *,
        input_file: Path,
        source_filename: str,
        options: ConversionOptions,
        workspace_id: str | None = None,
    ) -> ConversionResult:
        workspace = self.storage.create_workspace(workspace_id or uuid.uuid4().hex)
        source_path = workspace.input_dir / source_filename
        shutil.copy2(input_file, source_path)
        detected = detect_file_type(source_filename)

        if detected.category == FileCategory.OFFICE:
            pdf = self.office_converter.convert_to_pdf(
                input_file=source_path,
                output_dir=workspace.output_dir,
                profile_dir=workspace.profile_dir,
            )
            return ConversionResult(
                output_path=pdf,
                output_kind=OutputKind.PDF,
                media_type="application/pdf",
                filename=pdf.name,
            )

        if detected.category == FileCategory.PDF:
            validate_pdf(source_path)
            output = workspace.output_dir / source_path.name
            shutil.copy2(source_path, output)
            return ConversionResult(
                output_path=output,
                output_kind=OutputKind.PDF,
                media_type="application/pdf",
                filename=output.name,
            )

        if detected.category == FileCategory.IMAGE:
            output = workspace.output_dir / f"{source_path.stem}.pdf"
            image_to_pdf(source_path, output)
            return ConversionResult(
                output_path=output,
                output_kind=OutputKind.PDF,
                media_type="application/pdf",
                filename=output.name,
            )

        return self.email_converter.convert(
            input_file=source_path,
            output_dir=workspace.output_dir,
            profile_dir=workspace.profile_dir,
            options=options,
        )
```

- [ ] **Step 3: Verify service tests pass**

Run:

```bash
cd lo_pdf_service
python -m pytest tests/unit/test_service.py -q
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add lo_pdf_service/app/conversion/service.py lo_pdf_service/tests/unit/test_service.py
git commit -m "feat: orchestrate document conversion"
```

## Task 10: Job Store

**Files:**
- Create: `lo_pdf_service/tests/unit/test_job_store.py`
- Create: `lo_pdf_service/app/jobs/models.py`
- Create: `lo_pdf_service/app/jobs/store.py`

- [ ] **Step 1: Write failing job store tests**

```python
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
    succeeded = store.mark_succeeded(job.job_id, result_path=result_path, media_type="application/pdf", filename="result.pdf")

    assert succeeded.status == JobStatus.SUCCEEDED
    assert store.get_job(job.job_id).result_path == result_path


def test_job_store_raises_for_missing_job(tmp_path: Path) -> None:
    store = LocalJobStore(job_dir=tmp_path)

    with pytest.raises(AppError) as exc_info:
        store.get_job("missing")

    assert exc_info.value.code == ErrorCode.JOB_NOT_FOUND
```

Run:

```bash
cd lo_pdf_service
python -m pytest tests/unit/test_job_store.py -q
```

Expected: FAIL because job modules do not exist.

- [ ] **Step 2: Implement job models**

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    EXPIRED = "expired"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class JobRecord:
    job_id: str
    source_filename: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    result_path: Path | None = None
    media_type: str | None = None
    filename: str | None = None
    error: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "job_id": self.job_id,
            "source_filename": self.source_filename,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "result": None
            if self.result_path is None
            else {
                "path": str(self.result_path),
                "media_type": self.media_type,
                "filename": self.filename,
            },
            "error": self.error,
        }
```

- [ ] **Step 3: Implement local job store**

```python
from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

from app.core.errors import AppError, ErrorCode
from app.jobs.models import JobRecord, JobStatus, utc_now


class LocalJobStore:
    def __init__(self, *, job_dir: Path) -> None:
        self.job_dir = job_dir
        self.job_dir.mkdir(parents=True, exist_ok=True)

    def create_job(self, *, source_filename: str) -> JobRecord:
        now = utc_now()
        job = JobRecord(
            job_id=uuid.uuid4().hex,
            source_filename=source_filename,
            status=JobStatus.QUEUED,
            created_at=now,
            updated_at=now,
        )
        self._write(job)
        return job

    def get_job(self, job_id: str) -> JobRecord:
        path = self._path(job_id)
        if not path.exists():
            raise AppError(code=ErrorCode.JOB_NOT_FOUND, message="Job not found.", details={"job_id": job_id})
        payload = json.loads(path.read_text(encoding="utf-8"))
        return JobRecord(
            job_id=payload["job_id"],
            source_filename=payload["source_filename"],
            status=JobStatus(payload["status"]),
            created_at=datetime.fromisoformat(payload["created_at"]),
            updated_at=datetime.fromisoformat(payload["updated_at"]),
            result_path=Path(payload["result"]["path"]) if payload["result"] else None,
            media_type=payload["result"]["media_type"] if payload["result"] else None,
            filename=payload["result"]["filename"] if payload["result"] else None,
            error=payload["error"],
        )

    def mark_running(self, job_id: str) -> JobRecord:
        job = self.get_job(job_id)
        updated = JobRecord(
            job_id=job.job_id,
            source_filename=job.source_filename,
            status=JobStatus.RUNNING,
            created_at=job.created_at,
            updated_at=utc_now(),
        )
        self._write(updated)
        return updated

    def mark_succeeded(self, job_id: str, *, result_path: Path, media_type: str, filename: str) -> JobRecord:
        job = self.get_job(job_id)
        updated = JobRecord(
            job_id=job.job_id,
            source_filename=job.source_filename,
            status=JobStatus.SUCCEEDED,
            created_at=job.created_at,
            updated_at=utc_now(),
            result_path=result_path,
            media_type=media_type,
            filename=filename,
        )
        self._write(updated)
        return updated

    def mark_failed(self, job_id: str, *, error: dict[str, object]) -> JobRecord:
        job = self.get_job(job_id)
        updated = JobRecord(
            job_id=job.job_id,
            source_filename=job.source_filename,
            status=JobStatus.FAILED,
            created_at=job.created_at,
            updated_at=utc_now(),
            error=error,
        )
        self._write(updated)
        return updated

    def delete_job(self, job_id: str) -> None:
        self._path(job_id).unlink(missing_ok=True)

    def _path(self, job_id: str) -> Path:
        return self.job_dir / f"{job_id}.json"

    def _write(self, job: JobRecord) -> None:
        self.job_dir.mkdir(parents=True, exist_ok=True)
        self._path(job.job_id).write_text(json.dumps(job.to_dict(), indent=2), encoding="utf-8")
```

- [ ] **Step 4: Verify job store tests pass**

Run:

```bash
cd lo_pdf_service
python -m pytest tests/unit/test_job_store.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add lo_pdf_service/app/jobs/models.py lo_pdf_service/app/jobs/store.py lo_pdf_service/tests/unit/test_job_store.py
git commit -m "feat: store async conversion jobs locally"
```

## Task 11: Background Worker

**Files:**
- Create: `lo_pdf_service/tests/unit/test_worker.py`
- Create: `lo_pdf_service/app/jobs/worker.py`

- [ ] **Step 1: Write failing worker tests**

```python
from __future__ import annotations

from pathlib import Path

from pypdf import PdfWriter

from app.jobs.models import JobStatus
from app.jobs.store import LocalJobStore
from app.jobs.worker import ConversionJob, InProcessWorker
from app.models import ConversionOptions, ConversionResult, OutputKind


class FakeService:
    def convert(self, *, input_file: Path, source_filename: str, options: ConversionOptions, workspace_id: str | None = None) -> ConversionResult:
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
```

Run:

```bash
cd lo_pdf_service
python -m pytest tests/unit/test_worker.py -q
```

Expected: FAIL because worker does not exist.

- [ ] **Step 2: Implement worker**

```python
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
```

- [ ] **Step 3: Verify worker test passes**

Run:

```bash
cd lo_pdf_service
python -m pytest tests/unit/test_worker.py -q
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add lo_pdf_service/app/jobs/worker.py lo_pdf_service/tests/unit/test_worker.py
git commit -m "feat: process async conversion jobs"
```

## Task 12: FastAPI HTTP API

**Files:**
- Create: `lo_pdf_service/tests/unit/test_api.py`
- Create: `lo_pdf_service/app/api/dependencies.py`
- Create: `lo_pdf_service/app/api/conversions.py`
- Create: `lo_pdf_service/app/main.py`

- [ ] **Step 1: Write failing API tests**

```python
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from pypdf import PdfWriter

from app.api.dependencies import get_conversion_service, get_job_store, get_settings_dependency, get_worker
from app.core.config import Settings
from app.jobs.store import LocalJobStore
from app.jobs.worker import InProcessWorker
from app.main import app
from app.models import ConversionOptions, ConversionResult, OutputKind


class FakeService:
    def convert(self, *, input_file: Path, source_filename: str, options: ConversionOptions, workspace_id: str | None = None) -> ConversionResult:
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


def test_sync_conversion_returns_pdf(tmp_path: Path) -> None:
    app.dependency_overrides[get_conversion_service] = lambda: FakeService()
    client = TestClient(app)

    response = client.post(
        "/v1/conversions",
        data={"execution": "sync", "email_mode": "merged", "include_attachments": "true"},
        files={"file": ("input.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    app.dependency_overrides.clear()


def test_async_conversion_returns_job_id(tmp_path: Path) -> None:
    store = LocalJobStore(job_dir=tmp_path / "jobs")
    worker = InProcessWorker(service=FakeService(), store=store)
    app.dependency_overrides[get_conversion_service] = lambda: FakeService()
    app.dependency_overrides[get_job_store] = lambda: store
    app.dependency_overrides[get_worker] = lambda: worker
    client = TestClient(app)

    response = client.post(
        "/v1/conversions",
        data={"execution": "async", "email_mode": "merged", "include_attachments": "true"},
        files={"file": ("input.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "queued"
    assert "job_id" in payload
    app.dependency_overrides.clear()


def test_upload_larger_than_configured_limit_is_rejected(tmp_path: Path) -> None:
    app.dependency_overrides[get_settings_dependency] = lambda: Settings(
        data_dir=tmp_path / "data",
        max_upload_bytes=4,
    )
    app.dependency_overrides[get_conversion_service] = lambda: FakeService()
    client = TestClient(app)

    response = client.post(
        "/v1/conversions",
        data={"execution": "sync", "email_mode": "merged", "include_attachments": "true"},
        files={"file": ("input.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "file_too_large"
    app.dependency_overrides.clear()
```

Run:

```bash
cd lo_pdf_service
python -m pytest tests/unit/test_api.py -q
```

Expected: FAIL because API modules do not exist.

- [ ] **Step 2: Implement dependencies**

```python
from __future__ import annotations

from functools import lru_cache

from app.conversion.libreoffice import LibreOfficeConverter
from app.conversion.service import ConversionService
from app.core.config import Settings, get_settings
from app.jobs.store import LocalJobStore
from app.jobs.worker import InProcessWorker
from app.storage.local import LocalStorage


@lru_cache
def get_cached_settings() -> Settings:
    return get_settings()


def get_settings_dependency() -> Settings:
    return get_cached_settings()


def get_storage() -> LocalStorage:
    settings = get_cached_settings()
    return LocalStorage(base_dir=settings.data_dir)


def get_office_converter() -> LibreOfficeConverter:
    settings = get_cached_settings()
    return LibreOfficeConverter(
        soffice_binary=settings.soffice_binary,
        timeout_seconds=settings.libreoffice_timeout_seconds,
    )


def get_conversion_service() -> ConversionService:
    return ConversionService(storage=get_storage(), office_converter=get_office_converter())


def get_job_store() -> LocalJobStore:
    return LocalJobStore(job_dir=get_cached_settings().job_dir)


def get_worker() -> InProcessWorker:
    return InProcessWorker(service=get_conversion_service(), store=get_job_store())
```

- [ ] **Step 3: Implement API routes**

```python
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
```

- [ ] **Step 4: Implement app entry point**

```python
from __future__ import annotations

from fastapi import FastAPI

from app.api.conversions import router as conversions_router

app = FastAPI(title="LibreOffice PDF Conversion Service", version="0.1.0")
app.include_router(conversions_router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 5: Verify API tests pass**

Run:

```bash
cd lo_pdf_service
python -m pytest tests/unit/test_api.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add lo_pdf_service/app/api lo_pdf_service/app/main.py lo_pdf_service/tests/unit/test_api.py
git commit -m "feat: expose sync and async conversion api"
```

## Task 13: Runtime Packaging And Verification

**Files:**
- Create: `lo_pdf_service/Dockerfile`
- Modify: `lo_pdf_service/README.md`

- [ ] **Step 1: Create Dockerfile**

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      libreoffice \
      libreoffice-writer \
      libreoffice-calc \
      libreoffice-impress \
      fonts-dejavu \
      fonts-liberation \
      fonts-noto-cjk \
      fontconfig \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md ./
COPY app ./app
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Update README with WSL and Docker validation commands**

Append:

```markdown
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
```

- [ ] **Step 3: Run full test suite**

Run:

```bash
cd lo_pdf_service
python -m pytest
```

Expected: PASS, with LibreOffice integration skipped if `soffice` is unavailable.

- [ ] **Step 4: Run WSL LibreOffice smoke test**

Run inside WSL:

```bash
cd /mnt/d/Workspace/demos/doc_trans/lo_pdf_service
soffice --headless --version
python -m pytest tests/integration/test_libreoffice_smoke.py -q -m integration
```

Expected: PASS when LibreOffice is installed in WSL.

- [ ] **Step 5: Run API manually in WSL**

Run:

```bash
cd /mnt/d/Workspace/demos/doc_trans/lo_pdf_service
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

In another shell:

```bash
curl http://localhost:8000/healthz
```

Expected:

```json
{"status":"ok"}
```

- [ ] **Step 6: Build Docker image**

Run:

```bash
cd lo_pdf_service
docker build -t lo-pdf-service .
```

Expected: image builds successfully.

- [ ] **Step 7: Commit**

```bash
git add lo_pdf_service/Dockerfile lo_pdf_service/README.md
git commit -m "chore: add linux runtime packaging"
```

## Final Verification

- [ ] Run all unit tests:

```bash
cd lo_pdf_service
python -m pytest tests/unit -q
```

- [ ] Run integration smoke test in WSL:

```bash
cd /mnt/d/Workspace/demos/doc_trans/lo_pdf_service
python -m pytest tests/integration/test_libreoffice_smoke.py -q -m integration
```

- [ ] Check no files outside `lo_pdf_service/` were changed by this implementation:

```bash
git status --short
```

Expected changed paths for this plan begin with `lo_pdf_service/`.

- [ ] Confirm service starts:

```bash
cd lo_pdf_service
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Expected: Uvicorn starts and `/healthz` returns `{"status":"ok"}`.
