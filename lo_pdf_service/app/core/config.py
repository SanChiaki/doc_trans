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
