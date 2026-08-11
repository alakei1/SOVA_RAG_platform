from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal, Type, TypeVar, cast

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


def load_env_file(service_name: str) -> None:
    """Загружает .env файл из папки конкретного сервиса."""
    env_path = Path(service_name) / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)


BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_ENV_PATH = BASE_DIR / "env"


class BaseConfig(BaseSettings):
    """Общие настройки для всех конфигураций."""

    model_config = SettingsConfigDict(
        extra="ignore",
        case_sensitive=False,
        env_file=ROOT_ENV_PATH,
        env_file_encoding="utf-8",
        env_ignore_empty=True,
    )

    env: Literal["development", "testing", "production"] = "development"
    version: str = "1.0.0"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<cyan>[{extra[service]}]</cyan> | "
        "<level>{level: <8}</level> | "
        "<magenta>{name}:{line}</magenta> - "
        "<level>{message}</level>"
    )
    service: str = ""
    log_to_file: bool = False

    # --- НАСТРОЙКИ MINIO (S3 Хранилище файлов) ---
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False  # True, если на проде поверх стоит SSL/HTTPS
    minio_default_bucket: str = "documents"

    # --- НАСТРОЙКИ QDRANT (Векторная база данных под LaBSE) ---
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: str | None = None
    qdrant_vector_size: int = 768
    qdrant_vector_distance: str = "Cosine"

    # --- НАСТРОЙКИ RABBITMQ (Брокер очередей для воркеров) ---
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"


class GatewayConfig(BaseConfig):
    service: str = "gateway"


class LLMServiceConfig(BaseConfig):
    service: str = "llm-service"


class ProcessWorkerConfig(BaseConfig):
    service: str = "processing-worker"


class SearchServiceConfig(BaseConfig):
    service: str = "search-service"


class DownloadWorkerConfig(BaseConfig):
    service: str = "download-worker"


T = TypeVar("T", bound=BaseConfig)


@lru_cache(maxsize=None)
def _get_config(config_class: Type[T], service_name: str) -> T:
    load_env_file(service_name)
    return config_class()


def get_gateway_config() -> GatewayConfig:
    return cast(GatewayConfig, _get_config(GatewayConfig, "gateway"))


def get_llm_service_config() -> LLMServiceConfig:
    # Явно подсказываем mypy, что Any на самом деле является LLMServiceConfig
    return cast(LLMServiceConfig, _get_config(LLMServiceConfig, "llm-service"))


def get_process_worker_config() -> ProcessWorkerConfig:
    return cast(ProcessWorkerConfig, _get_config(ProcessWorkerConfig, "processing-worker"))


def get_search_service_config() -> SearchServiceConfig:
    return cast(SearchServiceConfig, _get_config(SearchServiceConfig, "search-service"))


def get_download_worker_config() -> DownloadWorkerConfig:
    return cast(DownloadWorkerConfig, _get_config(DownloadWorkerConfig, "download-worker"))
