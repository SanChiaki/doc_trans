from pathlib import Path

import app.workers.aspose_convert as worker


def test_worker_rejects_invalid_arguments(capsys):
    exit_code = worker.main(["aspose_convert"])

    assert exit_code == 64
    assert "Usage:" in capsys.readouterr().err


def test_worker_dispatches_word_conversion(monkeypatch, tmp_path):
    calls = []

    def fake_convert(source_path, output_path, license_path):
        calls.append((source_path, output_path, license_path))

    monkeypatch.setattr(worker, "convert_word", fake_convert)

    exit_code = worker.main(["aspose_convert", "word", str(tmp_path / "source.docx"), str(tmp_path / "out.pdf")])

    assert exit_code == 0
    assert calls == [(tmp_path / "source.docx", tmp_path / "out.pdf", None)]


def test_worker_dispatches_email_mhtml_conversion(monkeypatch, tmp_path):
    calls = []
    license_path = tmp_path / "license.lic"

    def fake_convert(source_path, output_path, provided_license_path):
        calls.append((source_path, output_path, provided_license_path))

    monkeypatch.setattr(worker, "convert_email_to_mhtml", fake_convert)

    exit_code = worker.main(
        [
            "aspose_convert",
            "email-mhtml",
            str(tmp_path / "message.eml"),
            str(tmp_path / "message.mhtml"),
            str(license_path),
        ]
    )

    assert exit_code == 0
    assert calls == [(tmp_path / "message.eml", tmp_path / "message.mhtml", license_path)]


def test_worker_returns_dependency_code_for_import_error(monkeypatch, tmp_path, capsys):
    def fake_convert(source_path: Path, output_path: Path, license_path: Path | None):
        raise ImportError("aspose.words")

    monkeypatch.setattr(worker, "convert_word", fake_convert)

    exit_code = worker.main(["aspose_convert", "word", str(tmp_path / "source.docx"), str(tmp_path / "out.pdf")])

    assert exit_code == 2
    assert "Missing Aspose dependency" in capsys.readouterr().err
