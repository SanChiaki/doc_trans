import subprocess
from pathlib import Path

import pytest

from app.core.errors import ConversionDependencyError, ConversionFailedError
from app.services.aspose_adapters import AsposeAdapters


def test_convert_word_runs_worker_with_configured_python(monkeypatch, tmp_path):
    calls = []
    adapter = AsposeAdapters(word_python="/opt/aspose-word/bin/python")

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        Path(command[5]).write_bytes(b"%PDF")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    adapter.convert_word(tmp_path / "sample.docx", tmp_path / "sample.pdf")

    command, kwargs = calls[0]
    assert command[:4] == ["/opt/aspose-word/bin/python", "-m", "app.workers.aspose_convert", "word"]
    assert Path(command[4]).name == "sample.docx"
    assert Path(command[5]).name == "sample.pdf"
    assert kwargs["cwd"].name == "aspose_service"
    assert "PYTHONPATH" in kwargs["env"]


def test_worker_receives_configured_library_path(monkeypatch, tmp_path):
    calls = []
    library_path = tmp_path / "compat"
    adapter = AsposeAdapters(word_python="/opt/aspose-word/bin/python", worker_library_path=library_path)

    def fake_run(command, **kwargs):
        calls.append(kwargs)
        Path(command[5]).write_bytes(b"%PDF")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    adapter.convert_word(tmp_path / "sample.docx", tmp_path / "sample.pdf")

    assert str(library_path) in calls[0]["env"]["LD_LIBRARY_PATH"]


def test_convert_email_uses_email_worker_then_word_worker(monkeypatch, tmp_path):
    calls = []
    adapter = AsposeAdapters(
        word_python="/opt/aspose-word/bin/python",
        email_python="/opt/aspose-email/bin/python",
    )

    def fake_run(command, **kwargs):
        calls.append(command)
        Path(command[5]).write_bytes(b"converted")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    adapter.convert_email(tmp_path / "message.eml", tmp_path / "message.pdf")

    assert calls[0][:4] == ["/opt/aspose-email/bin/python", "-m", "app.workers.aspose_convert", "email-mhtml"]
    assert Path(calls[0][5]).suffix == ".mhtml"
    assert calls[1][:4] == ["/opt/aspose-word/bin/python", "-m", "app.workers.aspose_convert", "word"]
    assert Path(calls[1][4]).suffix == ".mhtml"
    assert Path(calls[1][5]).name == "message.pdf"


def test_worker_dependency_failure_raises_clear_error(monkeypatch, tmp_path):
    adapter = AsposeAdapters(word_python="/opt/aspose-word/bin/python")

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 2, stdout="", stderr="Missing Aspose dependency: aspose-words")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(ConversionDependencyError) as exc_info:
        adapter.convert_word(tmp_path / "sample.docx", tmp_path / "sample.pdf")

    assert "Missing Aspose dependency" in exc_info.value.message


def test_worker_conversion_failure_raises_conversion_error(monkeypatch, tmp_path):
    adapter = AsposeAdapters(word_python="/opt/aspose-word/bin/python")

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="bad input")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(ConversionFailedError) as exc_info:
        adapter.convert_word(tmp_path / "sample.docx", tmp_path / "sample.pdf")

    assert "Aspose worker failed" in exc_info.value.message


def test_apply_license_is_deferred_to_workers(tmp_path):
    adapter = AsposeAdapters(license_path=tmp_path / "missing.lic")

    adapter.apply_licenses()
