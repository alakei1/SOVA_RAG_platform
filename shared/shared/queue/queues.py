from enum import StrEnum
from typing import NotRequired, TypedDict


# Имена обменников
class ExchangeNames(StrEnum):
    MAIN = "main.exchange"
    DEAD_LETTER = "dlx.exchange"
    RETRY = "retry.exchange"
    DELAYED = "delayed.exchange"
    NOTIFICATION = "notification.exchange"
    LOGGING = "logging.exchange"
    DLX_NOTIFICATION = "dlx.notification.exchange"
    DLX_LOG = "dlx.log.exchange"


# Имена очередей
class QueueNames(StrEnum):
    MAIN = "main.queue"
    PRIORITY = "priority.queue"
    DEAD_LETTER = "dlx.queue"
    RETRY_1 = "retry.1.queue"
    RETRY_2 = "retry.2.queue"
    RETRY_3 = "retry.3.queue"
    DELAYED_5S = "delayed.5s.queue"
    DELAYED_30S = "delayed.30s.queue"
    DELAYED_1M = "delayed.1m.queue"
    TASK_PROCESS = "task.process.queue"
    TASK_ANALYZE = "task.analyze.queue"
    TASK_REPORT = "task.report.queue"
    TASK_DELETE = "task.delete.queue"
    TASK_DEAD_LETTER = "task.dlx.queue"
    NOTIFICATION_EMAIL = "notification.email.queue"
    NOTIFICATION_SMS = "notification.sms.queue"
    NOTIFICATION_PUSH = "notification.push.queue"
    LOG_ERROR = "log.error.queue"
    LOG_WARNING = "log.warning.queue"
    LOG_INFO = "log.info.queue"


# Routing keys
class RoutingKeys(StrEnum):
    TASK_ALL = "task.#"
    TASK_PROCESS = "task.process"
    TASK_ANALYZE = "task.analyze"
    TASK_REPORT = "task.report"
    DOWNLOAD = "task.download"
    VECTORIZE = "task.vectorize"
    DELETE = "task.delete"
    NOTIFICATION_ALL = "notification.#"
    NOTIFICATION_EMAIL = "notification.email"
    NOTIFICATION_SMS = "notification.sms"
    NOTIFICATION_PUSH = "notification.push"
    LOG_ALL = "log.#"
    LOG_ERROR = "log.error"
    LOG_WARNING = "log.warning"
    LOG_INFO = "log.info"
    DLX = "dlx"
    RETRY = "retry"


# Типы обменников
class ExchangeTypes(StrEnum):
    """Типы обменников RabbitMQ"""

    DIRECT = "direct"
    TOPIC = "topic"
    FANOUT = "fanout"
    HEADERS = "headers"
    DELAYED = "x-delayed-message"


# Используем альтернативный синтаксис, чтобы разрешить дефисы в ключах
QueueArguments = TypedDict(
    "QueueArguments",
    {
        "x-dead-letter-exchange": str,
        "x-dead-letter-routing-key": str,
        "x-max-priority": int,
        "x-message-ttl": int,
        "x-queue-type": str,
    },
    total=False,
)


class QueueConfig(TypedDict):
    """Структура конфигурации отдельной очереди."""

    durable: bool
    auto_delete: bool
    arguments: NotRequired[QueueArguments]


# ============================================================
# КОНФИГУРАЦИЯ ОЧЕРЕДЕЙ
# ============================================================
QUEUE_CONFIGS: dict[QueueNames, QueueConfig] = {
    QueueNames.MAIN: {
        "durable": True,
        "auto_delete": False,
        "arguments": {
            "x-dead-letter-exchange": ExchangeNames.DEAD_LETTER.value,
            "x-dead-letter-routing-key": RoutingKeys.DLX.value,
            "x-max-priority": 10,
        },
    },
    QueueNames.PRIORITY: {
        "durable": True,
        "auto_delete": False,
        "arguments": {
            "x-dead-letter-exchange": ExchangeNames.DEAD_LETTER.value,
            "x-dead-letter-routing-key": RoutingKeys.DLX.value,
            "x-max-priority": 10,
        },
    },
    QueueNames.DEAD_LETTER: {
        "durable": True,
        "auto_delete": False,
        "arguments": {
            "x-message-ttl": 86400000,  # 24 часа
        },
    },
    QueueNames.RETRY_1: {
        "durable": True,
        "auto_delete": False,
        "arguments": {
            "x-dead-letter-exchange": ExchangeNames.MAIN.value,
            "x-dead-letter-routing-key": RoutingKeys.TASK_PROCESS.value,
            "x-message-ttl": 5000,  # 5 секунд
        },
    },
    QueueNames.RETRY_2: {
        "durable": True,
        "auto_delete": False,
        "arguments": {
            "x-dead-letter-exchange": ExchangeNames.MAIN.value,
            "x-dead-letter-routing-key": RoutingKeys.TASK_PROCESS.value,
            "x-message-ttl": 30000,  # 30 секунд
        },
    },
    QueueNames.RETRY_3: {
        "durable": True,
        "auto_delete": False,
        "arguments": {
            "x-dead-letter-exchange": ExchangeNames.MAIN.value,
            "x-dead-letter-routing-key": RoutingKeys.TASK_PROCESS.value,
            "x-message-ttl": 120000,  # 2 минуты
        },
    },
    QueueNames.DELAYED_5S: {
        "durable": True,
        "auto_delete": False,
        "arguments": {
            "x-dead-letter-exchange": ExchangeNames.MAIN.value,
            "x-dead-letter-routing-key": RoutingKeys.TASK_PROCESS.value,
            "x-message-ttl": 5000,
        },
    },
    QueueNames.DELAYED_30S: {
        "durable": True,
        "auto_delete": False,
        "arguments": {
            "x-dead-letter-exchange": ExchangeNames.MAIN.value,
            "x-dead-letter-routing-key": RoutingKeys.TASK_PROCESS.value,
            "x-message-ttl": 30000,
        },
    },
    QueueNames.DELAYED_1M: {
        "durable": True,
        "auto_delete": False,
        "arguments": {
            "x-dead-letter-exchange": ExchangeNames.MAIN.value,
            "x-dead-letter-routing-key": RoutingKeys.TASK_PROCESS.value,
            "x-message-ttl": 60000,
        },
    },
    QueueNames.TASK_PROCESS: {
        "durable": True,
        "auto_delete": False,
        "arguments": {
            "x-dead-letter-exchange": ExchangeNames.DEAD_LETTER.value,
            "x-dead-letter-routing-key": RoutingKeys.DLX.value,
            "x-max-priority": 10,
        },
    },
    QueueNames.TASK_ANALYZE: {
        "durable": True,
        "auto_delete": False,
        "arguments": {
            "x-dead-letter-exchange": ExchangeNames.DEAD_LETTER.value,
            "x-dead-letter-routing-key": RoutingKeys.DLX.value,
        },
    },
    QueueNames.TASK_REPORT: {
        "durable": True,
        "auto_delete": False,
        "arguments": {
            "x-dead-letter-exchange": ExchangeNames.DEAD_LETTER.value,
            "x-dead-letter-routing-key": RoutingKeys.DLX.value,
        },
    },
    QueueNames.TASK_DELETE: {
        "durable": True,
        "auto_delete": False,
        "arguments": {
            "x-dead-letter-exchange": ExchangeNames.DEAD_LETTER.value,
            "x-dead-letter-routing-key": RoutingKeys.DLX.value,
        },
    },
    QueueNames.TASK_DEAD_LETTER: {
        "durable": True,
        "auto_delete": False,
        "arguments": {
            "x-message-ttl": 86400000,  # 24 часа
        },
    },
    QueueNames.NOTIFICATION_EMAIL: {
        "durable": True,
        "auto_delete": False,
        "arguments": {
            "x-dead-letter-exchange": ExchangeNames.DLX_NOTIFICATION.value,
            "x-dead-letter-routing-key": RoutingKeys.DLX.value,
        },
    },
    QueueNames.NOTIFICATION_SMS: {
        "durable": True,
        "auto_delete": False,
        "arguments": {
            "x-dead-letter-exchange": ExchangeNames.DLX_NOTIFICATION.value,
            "x-dead-letter-routing-key": RoutingKeys.DLX.value,
        },
    },
    QueueNames.NOTIFICATION_PUSH: {
        "durable": True,
        "auto_delete": False,
        "arguments": {
            "x-dead-letter-exchange": ExchangeNames.DLX_NOTIFICATION.value,
            "x-dead-letter-routing-key": RoutingKeys.DLX.value,
        },
    },
    QueueNames.LOG_ERROR: {
        "durable": True,
        "auto_delete": False,
        "arguments": {
            "x-dead-letter-exchange": ExchangeNames.DLX_LOG.value,
            "x-dead-letter-routing-key": RoutingKeys.DLX.value,
        },
    },
    QueueNames.LOG_WARNING: {
        "durable": True,
        "auto_delete": False,
        "arguments": {
            "x-dead-letter-exchange": ExchangeNames.DLX_LOG.value,
            "x-dead-letter-routing-key": RoutingKeys.DLX.value,
        },
    },
    QueueNames.LOG_INFO: {
        "durable": True,
        "auto_delete": False,
        "arguments": {
            "x-dead-letter-exchange": ExchangeNames.DLX_LOG.value,
            "x-dead-letter-routing-key": RoutingKeys.DLX.value,
        },
    },
}


# ============================================================
# БИНДИНГИ ОЧЕРЕДЕЙ К ОБМЕННИКАМ
# ============================================================
BINDINGS: list[tuple[QueueNames, ExchangeNames, RoutingKeys]] = [
    # Dead Letter
    (QueueNames.DEAD_LETTER, ExchangeNames.DEAD_LETTER, RoutingKeys.DLX),
    (QueueNames.TASK_DEAD_LETTER, ExchangeNames.DEAD_LETTER, RoutingKeys.DLX),
    # Основные задачи
    (QueueNames.TASK_PROCESS, ExchangeNames.MAIN, RoutingKeys.TASK_PROCESS),
    (QueueNames.TASK_PROCESS, ExchangeNames.MAIN, RoutingKeys.DOWNLOAD),
    (QueueNames.TASK_PROCESS, ExchangeNames.MAIN, RoutingKeys.VECTORIZE),
    (QueueNames.TASK_ANALYZE, ExchangeNames.MAIN, RoutingKeys.TASK_ANALYZE),
    (QueueNames.TASK_REPORT, ExchangeNames.MAIN, RoutingKeys.TASK_REPORT),
    (QueueNames.TASK_DELETE, ExchangeNames.MAIN, RoutingKeys.DELETE),
    # Нотификации
    (QueueNames.NOTIFICATION_EMAIL, ExchangeNames.NOTIFICATION, RoutingKeys.NOTIFICATION_EMAIL),
    (QueueNames.NOTIFICATION_SMS, ExchangeNames.NOTIFICATION, RoutingKeys.NOTIFICATION_SMS),
    (QueueNames.NOTIFICATION_PUSH, ExchangeNames.NOTIFICATION, RoutingKeys.NOTIFICATION_PUSH),
    # Логи
    (QueueNames.LOG_ERROR, ExchangeNames.LOGGING, RoutingKeys.LOG_ERROR),
    (QueueNames.LOG_WARNING, ExchangeNames.LOGGING, RoutingKeys.LOG_WARNING),
    (QueueNames.LOG_INFO, ExchangeNames.LOGGING, RoutingKeys.LOG_INFO),
]


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ МАППИНГИ И ФУНКЦИИ
# ============================================================

TASK_TYPE_ROUTING_MAP: dict[str, RoutingKeys] = {
    "download": RoutingKeys.DOWNLOAD,
    "vectorize": RoutingKeys.VECTORIZE,
    "delete": RoutingKeys.DELETE,
    "process": RoutingKeys.TASK_PROCESS,
    "analyze": RoutingKeys.TASK_ANALYZE,
    "report": RoutingKeys.TASK_REPORT,
}

TASK_TYPE_QUEUE_MAP: dict[str, QueueNames] = {
    "download": QueueNames.TASK_PROCESS,
    "vectorize": QueueNames.TASK_PROCESS,
    "delete": QueueNames.TASK_DELETE,
    "analyze": QueueNames.TASK_ANALYZE,
    "report": QueueNames.TASK_REPORT,
}

ROUTING_KEY_QUEUE_MAP: dict[RoutingKeys, QueueNames] = {
    RoutingKeys.DOWNLOAD: QueueNames.TASK_PROCESS,
    RoutingKeys.VECTORIZE: QueueNames.TASK_PROCESS,
    RoutingKeys.DELETE: QueueNames.TASK_DELETE,
    RoutingKeys.TASK_PROCESS: QueueNames.TASK_PROCESS,
    RoutingKeys.TASK_ANALYZE: QueueNames.TASK_ANALYZE,
    RoutingKeys.TASK_REPORT: QueueNames.TASK_REPORT,
    RoutingKeys.NOTIFICATION_EMAIL: QueueNames.NOTIFICATION_EMAIL,
    RoutingKeys.NOTIFICATION_SMS: QueueNames.NOTIFICATION_SMS,
    RoutingKeys.NOTIFICATION_PUSH: QueueNames.NOTIFICATION_PUSH,
    RoutingKeys.LOG_ERROR: QueueNames.LOG_ERROR,
    RoutingKeys.LOG_WARNING: QueueNames.LOG_WARNING,
    RoutingKeys.LOG_INFO: QueueNames.LOG_INFO,
}

QUEUE_DLX_MAP: dict[QueueNames, ExchangeNames] = {
    QueueNames.MAIN: ExchangeNames.DEAD_LETTER,
    QueueNames.PRIORITY: ExchangeNames.DEAD_LETTER,
    QueueNames.TASK_PROCESS: ExchangeNames.DEAD_LETTER,
    QueueNames.TASK_ANALYZE: ExchangeNames.DEAD_LETTER,
    QueueNames.TASK_REPORT: ExchangeNames.DEAD_LETTER,
    QueueNames.TASK_DELETE: ExchangeNames.DEAD_LETTER,
    QueueNames.NOTIFICATION_EMAIL: ExchangeNames.DLX_NOTIFICATION,
    QueueNames.NOTIFICATION_SMS: ExchangeNames.DLX_NOTIFICATION,
    QueueNames.NOTIFICATION_PUSH: ExchangeNames.DLX_NOTIFICATION,
    QueueNames.LOG_ERROR: ExchangeNames.DLX_LOG,
    QueueNames.LOG_WARNING: ExchangeNames.DLX_LOG,
    QueueNames.LOG_INFO: ExchangeNames.DLX_LOG,
}

RETRY_QUEUE_MAP: dict[int, QueueNames] = {
    1: QueueNames.RETRY_1,
    2: QueueNames.RETRY_2,
    3: QueueNames.RETRY_3,
}

RETRY_TTL_MAP: dict[int, int] = {
    1: 5000,
    2: 30000,
    3: 120000,
}


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================


def get_routing_key_for_task_type(task_type: str) -> str:
    """Получить routing key для типа задачи"""
    routing_key = TASK_TYPE_ROUTING_MAP.get(task_type)
    if routing_key is None:
        return RoutingKeys.TASK_PROCESS.value
    return routing_key.value


def get_queue_for_task_type(task_type: str) -> str:
    """Получить очередь для типа задачи"""
    queue = TASK_TYPE_QUEUE_MAP.get(task_type)
    if queue is None:
        return QueueNames.TASK_PROCESS.value
    return queue.value


def get_queue_for_routing_key(routing_key: str) -> str:
    """Получить очередь для routing key"""
    try:
        routing_key_enum = RoutingKeys(routing_key)
        queue = ROUTING_KEY_QUEUE_MAP.get(routing_key_enum)
        if queue is None:
            return QueueNames.MAIN.value
        return queue.value
    except ValueError:
        return QueueNames.MAIN.value


def get_dlx_for_queue(queue_name: str) -> str:
    """Получить Dead Letter Exchange для очереди"""
    try:
        queue_enum = QueueNames(queue_name)
        dlx = QUEUE_DLX_MAP.get(queue_enum)
        if dlx is None:
            return ExchangeNames.DEAD_LETTER.value
        return dlx.value
    except ValueError:
        return ExchangeNames.DEAD_LETTER.value


def get_retry_queue_for_attempt(attempt: int) -> str:
    """Получить очередь для повторной попытки по номеру"""
    queue = RETRY_QUEUE_MAP.get(attempt, QueueNames.RETRY_3)
    return queue.value


def get_retry_ttl_for_attempt(attempt: int) -> int:
    """Получить TTL для повторной попытки по номеру"""
    return RETRY_TTL_MAP.get(attempt, 120000)
