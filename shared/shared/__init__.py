# shared/__init__.py
from .config import (
    BaseConfig,
    get_download_worker_config,
    get_gateway_config,
    get_llm_service_config,
    get_process_worker_config,
    get_search_service_config,
)
from .logging import setup_logging
from .models import (
    DeleteTaskPayload,
    DownloadTaskPayload,
    Task,
    TaskStatus,
    TaskType,
    VectorizeTaskPayload,
)
from .queue import (
    BINDINGS,
    QUEUE_CONFIGS,
    QUEUE_DLX_MAP,
    RETRY_QUEUE_MAP,
    RETRY_TTL_MAP,
    ROUTING_KEY_QUEUE_MAP,
    TASK_TYPE_QUEUE_MAP,
    TASK_TYPE_ROUTING_MAP,
    ExchangeNames,
    ExchangeTypes,
    QueueArguments,
    QueueConfig,
    QueueNames,
    RabbitMQClient,
    RoutingKeys,
    TaskConsumer,
    TaskPublisher,
    get_dlx_for_queue,
    get_queue_for_routing_key,
    get_queue_for_task_type,
    get_retry_queue_for_attempt,
    get_retry_ttl_for_attempt,
    get_routing_key_for_task_type,
)
from .utils import (
    RetryContext,
    async_retry_on_exception,
    is_result_empty,
    is_result_error,
    is_result_false,
    is_result_none,
    retry_on_exception,
)

__all__ = [
    # Конфигурации сервисов
    "BaseConfig",
    "get_gateway_config",
    "get_llm_service_config",
    "get_process_worker_config",
    "get_search_service_config",
    "get_download_worker_config",
    # Логирование
    "setup_logging",
    # Модели
    "DeleteTaskPayload",
    "DownloadTaskPayload",
    "Task",
    "TaskStatus",
    "TaskType",
    "VectorizeTaskPayload",
    # Утилиты и повторные попытки (Retry)
    "RetryContext",
    "async_retry_on_exception",
    "is_result_empty",
    "is_result_error",
    "is_result_false",
    "is_result_none",
    "retry_on_exception",
    # Enum классы (RabbitMQ)
    "ExchangeNames",
    "QueueNames",
    "RoutingKeys",
    "ExchangeTypes",
    # TypedDict классы
    "QueueConfig",
    "QueueArguments",
    # Конфигурации и маппинги очередей
    "QUEUE_CONFIGS",
    "BINDINGS",
    "TASK_TYPE_ROUTING_MAP",
    "TASK_TYPE_QUEUE_MAP",
    "ROUTING_KEY_QUEUE_MAP",
    "QUEUE_DLX_MAP",
    "RETRY_QUEUE_MAP",
    "RETRY_TTL_MAP",
    # Вспомогательные функции маршрутизации
    "get_routing_key_for_task_type",
    "get_queue_for_task_type",
    "get_queue_for_routing_key",
    "get_dlx_for_queue",
    "get_retry_queue_for_attempt",
    "get_retry_ttl_for_attempt",
    # RabbitMQ клиент
    "RabbitMQClient",
    # Publisher и Consumer
    "TaskPublisher",
    "TaskConsumer",
]
