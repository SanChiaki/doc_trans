from functools import lru_cache
from pathlib import Path
import sys

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Aspose Document Conversion Service"
    upload_dir: Path = Path("runtime/uploads")
    output_dir: Path = Path("runtime/outputs")
    max_upload_bytes: int = Field(default=50 * 1024 * 1024, gt=0)
    aspose_license_path: Path | None = None
    word_python: str = sys.executable
    cells_python: str = sys.executable
    slides_python: str = sys.executable
    email_python: str = sys.executable
    worker_library_path: Path | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ASPOSE_SERVICE_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
