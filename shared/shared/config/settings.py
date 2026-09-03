from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, ClassVar, Literal, Tuple, Type, TypeVar, Union

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

    # --- НАСТРОЙКИ RABBITMQ (Брокер очередей) ---
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"
    rabbitmq_virtual_host: str = "/"
    rabbitmq_heartbeat: int = 600
    rabbitmq_timeout: int = 300

    # Дополнительные настройки RabbitMQ
    rabbitmq_management_port: int = 15672
    rabbitmq_connection_attempts: int = 3
    rabbitmq_retry_delay: float | int = 2.0
    rabbitmq_max_retries: int = 5
    rabbitmq_prefetch_count: int = 10

    # Настройки для очередей
    rabbitmq_queue_ttl_ms: int = 86400000  # 24 часа
    rabbitmq_retry_1_ttl_ms: int = 5000  # 5 секунд
    rabbitmq_retry_2_ttl_ms: int = 30000  # 30 секунд
    rabbitmq_retry_3_ttl_ms: int = 120000  # 2 минуты

    # --- НАСТРОЙКИ ДЛЯ ВОРКЕРОВ ---
    worker_max_retries: int = 3
    worker_concurrency: int = 4
    worker_prefetch_count: int = 1
    worker_heartbeat_interval: int = 30

    # --- НАСТРОЙКИ retry ----
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

        # --- НАСТРОЙКИ RABBITMQ (Брокер очередей) ---
        rabbitmq_host: str = "localhost"
        rabbitmq_port: int = 5672
        rabbitmq_user: str = "guest"
        rabbitmq_password: str = "guest"
        rabbitmq_virtual_host: str = "/"
        rabbitmq_heartbeat: int = 600
        rabbitmq_timeout: int = 300

        # Дополнительные настройки RabbitMQ
        rabbitmq_management_port: int = 15672
        rabbitmq_connection_attempts: int = 3
        rabbitmq_retry_delay: float | int = 2.0
        rabbitmq_max_retries: int = 5
        rabbitmq_prefetch_count: int = 10

        # Настройки для очередей
        rabbitmq_queue_ttl_ms: int = 86400000  # 24 часа
        rabbitmq_retry_1_ttl_ms: int = 5000  # 5 секунд
        rabbitmq_retry_2_ttl_ms: int = 30000  # 30 секунд
        rabbitmq_retry_3_ttl_ms: int = 120000  # 2 минуты

        # --- НАСТРОЙКИ ДЛЯ ВОРКЕРОВ ---
        worker_max_retries: int = 3
        worker_concurrency: int = 4
        worker_prefetch_count: int = 1
        worker_heartbeat_interval: int = 30

        # --- НАСТРОЙКИ retry ----
        retry_exceptions: ClassVar[Union[Type[Exception], Tuple[Type[Exception], ...]]] = Exception
        retry_max_attempts: int = 3
        retry_delay: float | int = 1
        retry_backoff: float | int = 2
        retry_jitter: float | int = 0.1
        retry_on_result: Callable[[Any], bool] | None = None
        retry_max_delay: float | None = None


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


def _load_config_uncached(config_class: Type[T], service_name: str) -> T:
    load_env_file(service_name)
    return config_class()


@lru_cache(maxsize=None)
def get_gateway_config() -> GatewayConfig:
    return _load_config_uncached(GatewayConfig, "gateway")


@lru_cache(maxsize=None)
def get_llm_service_config() -> LLMServiceConfig:
    return _load_config_uncached(LLMServiceConfig, "llm-service")


@lru_cache(maxsize=None)
def get_process_worker_config() -> ProcessWorkerConfig:
    return _load_config_uncached(ProcessWorkerConfig, "processing-worker")


@lru_cache(maxsize=None)
def get_search_service_config() -> SearchServiceConfig:
    return _load_config_uncached(SearchServiceConfig, "search-service")


@lru_cache(maxsize=None)
def get_download_worker_config() -> DownloadWorkerConfig:
    return _load_config_uncached(DownloadWorkerConfig, "download-worker")
