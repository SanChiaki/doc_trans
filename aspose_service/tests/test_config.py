from pathlib import Path

from app.core.config import Settings
from app.models import ResponseMode


def test_settings_defaults_use_local_runtime_directories():
    settings = Settings()

    assert settings.app_name == "Aspose Document Conversion Service"
    assert settings.upload_dir == Path("runtime/uploads")
    assert settings.output_dir == Path("runtime/outputs")
    assert settings.max_upload_bytes == 50 * 1024 * 1024


def test_response_mode_values_match_api_contract():
    assert ResponseMode.STREAM.value == "stream"
    assert ResponseMode.FILE.value == "file"
