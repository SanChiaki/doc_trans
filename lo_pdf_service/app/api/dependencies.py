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
