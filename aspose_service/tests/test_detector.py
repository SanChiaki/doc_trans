import pytest

from app.core.errors import UnsupportedFormatError
from app.services.detector import DocumentFamily, detect_document_family


@pytest.mark.parametrize("filename", ["sample.doc", "sample.docx", "sample.rtf", "sample.odt", "sample.txt", "sample.html", "sample.htm", "sample.mhtml"])
def test_detects_word_family(filename):
    assert detect_document_family(filename) is DocumentFamily.WORD


@pytest.mark.parametrize("filename", ["sample.xls", "sample.xlsx", "sample.xlsm", "sample.csv", "sample.ods"])
def test_detects_excel_family(filename):
    assert detect_document_family(filename) is DocumentFamily.EXCEL


@pytest.mark.parametrize("filename", ["sample.ppt", "sample.pptx", "sample.pps", "sample.ppsx", "sample.odp"])
def test_detects_presentation_family(filename):
    assert detect_document_family(filename) is DocumentFamily.PRESENTATION


@pytest.mark.parametrize("filename", ["sample.eml", "sample.msg"])
def test_detects_email_family(filename):
    assert detect_document_family(filename) is DocumentFamily.EMAIL


def test_detection_is_case_insensitive():
    assert detect_document_family("Quarterly.Report.DOCX") is DocumentFamily.WORD


@pytest.mark.parametrize("filename", ["archive.zip", "no_extension", ".hidden"])
def test_rejects_unsupported_or_missing_extensions(filename):
    with pytest.raises(UnsupportedFormatError) as exc_info:
        detect_document_family(filename)

    assert "Unsupported document format" in exc_info.value.message
