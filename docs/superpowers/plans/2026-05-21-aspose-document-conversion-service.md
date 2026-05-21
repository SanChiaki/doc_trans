# Aspose Document Conversion Service Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a FastAPI-based Aspose document-to-PDF service isolated under `aspose_service/`.

**Architecture:** The service exposes HTTP endpoints, stores uploads and generated PDFs locally, detects file families by extension, and delegates conversion to isolated Aspose adapters. Aspose imports stay inside adapter methods so most tests run without Aspose installed.

**Tech Stack:** Python 3.10+, FastAPI, Pydantic Settings, pytest, Aspose for Python via .NET packages.

---

## File Structure

- Create `aspose_service/pyproject.toml` for package metadata, runtime dependencies, and pytest config.
- Create `aspose_service/README.md` for Linux/WSL setup and API usage.
- Create `aspose_service/.env.example` for local configuration.
- Create `aspose_service/app/main.py` for FastAPI app creation and exception handlers.
- Create `aspose_service/app/core/config.py` for settings.
- Create `aspose_service/app/core/errors.py` for typed service errors.
- Create `aspose_service/app/models.py` for response DTOs and enums.
- Create `aspose_service/app/api/routes.py` for API endpoints.
- Create `aspose_service/app/services/detector.py` for extension-based format detection.
- Create `aspose_service/app/services/storage.py` for local file persistence.
- Create `aspose_service/app/services/converter.py` for conversion orchestration.
- Create `aspose_service/app/services/aspose_adapters.py` for subprocess-based Aspose worker orchestration.
- Create `aspose_service/app/workers/aspose_convert.py` for isolated Aspose product imports.
- Create `aspose_service/scripts/bootstrap_aspose_workers.sh` for Linux worker environment setup.
- Create `aspose_service/scripts/e2e_smoke.sh` for WSL/API smoke verification.
- Create `aspose_service/tests/` for unit tests.
- Create root `.gitignore` and `README.md` to document sibling implementations.

## Tasks

### Task 1: Project Skeleton and Configuration

**Files:**
- Create: `aspose_service/pyproject.toml`
- Create: `aspose_service/app/__init__.py`
- Create: `aspose_service/app/core/config.py`
- Create: `aspose_service/app/core/errors.py`
- Create: `aspose_service/app/models.py`
- Create: `aspose_service/tests/test_config.py`

- [ ] Write tests for default settings and response mode enum.
- [ ] Run `pytest aspose_service/tests/test_config.py -q` and confirm missing modules fail.
- [ ] Implement settings, errors, and models.
- [ ] Run the same test and confirm it passes.

### Task 2: Format Detection

**Files:**
- Create: `aspose_service/app/services/detector.py`
- Create: `aspose_service/tests/test_detector.py`

- [ ] Write tests for Word, Excel, PowerPoint, email, and unsupported extensions.
- [ ] Run `pytest aspose_service/tests/test_detector.py -q` and confirm detector import fails.
- [ ] Implement `detect_document_family(filename: str)`.
- [ ] Run detector tests and confirm they pass.

### Task 3: Local Storage

**Files:**
- Create: `aspose_service/app/services/storage.py`
- Create: `aspose_service/tests/test_storage.py`

- [ ] Write tests for temporary upload creation, PDF persistence, and missing file lookup.
- [ ] Run `pytest aspose_service/tests/test_storage.py -q` and confirm missing implementation fails.
- [ ] Implement `LocalStorage`.
- [ ] Run storage tests and confirm they pass.

### Task 4: Conversion Orchestration

**Files:**
- Create: `aspose_service/app/services/converter.py`
- Create: `aspose_service/tests/test_converter.py`

- [ ] Write tests using fake adapters for dispatching each document family and rejecting unsupported files.
- [ ] Run `pytest aspose_service/tests/test_converter.py -q` and confirm missing implementation fails.
- [ ] Implement `DocumentConverter`.
- [ ] Run converter tests and confirm they pass.

### Task 5: Aspose Adapters and Workers

**Files:**
- Create: `aspose_service/app/services/aspose_adapters.py`
- Create: `aspose_service/app/workers/aspose_convert.py`
- Create: `aspose_service/tests/test_aspose_adapters.py`
- Create: `aspose_service/tests/test_aspose_worker.py`

- [ ] Write tests that monkeypatch subprocess execution and assert missing Aspose packages become `ConversionDependencyError`.
- [ ] Run `pytest aspose_service/tests/test_aspose_adapters.py -q` and confirm missing adapter fails.
- [ ] Implement Word, Cells, Slides, and Email adapter methods as worker subprocess calls.
- [ ] Implement the worker CLI with isolated product imports.
- [ ] Run adapter tests and confirm they pass.

### Task 6: HTTP API

**Files:**
- Create: `aspose_service/app/api/routes.py`
- Create: `aspose_service/app/api/__init__.py`
- Create: `aspose_service/app/main.py`
- Create: `aspose_service/tests/test_api.py`

- [ ] Write API tests with dependency overrides for stream mode, file mode, unsupported attachment conversion, and file download.
- [ ] Run `pytest aspose_service/tests/test_api.py -q` and confirm route implementation fails.
- [ ] Implement FastAPI routes and exception handling.
- [ ] Run API tests and confirm they pass.

### Task 7: Documentation and Linux Verification

**Files:**
- Create: `.gitignore`
- Create: `README.md`
- Create: `aspose_service/README.md`
- Create: `aspose_service/.env.example`
- Create: `aspose_service/scripts/bootstrap_aspose_workers.sh`
- Create: `aspose_service/scripts/e2e_smoke.sh`

- [ ] Document sibling implementation layout and Aspose service setup.
- [ ] Run `pytest aspose_service/tests -q` in Windows Python if available.
- [ ] Run `wsl -d Ubuntu-22.04 -- bash -lc "cd /mnt/d/Workspace/demos/doc_trans/aspose_service && python3 -m pytest tests -q"` after installing test dependencies if needed.
- [ ] Run `bash scripts/bootstrap_aspose_workers.sh` in WSL to create isolated Aspose worker environments.
- [ ] Run `bash scripts/e2e_smoke.sh` in WSL and confirm worker and API conversion return PDFs.
- [ ] Record Linux dependency limitations and bootstrap commands clearly.

## Self-Review

The plan covers the agreed API service shape, stream/file output modes, email body-only support with attachment merge reserved, Linux/WSL validation, and isolation under `aspose_service/`. No implementation step writes outside `aspose_service/` except root README and `.gitignore`.
