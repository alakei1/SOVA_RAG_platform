from __future__ import annotations

import sys

from loguru import logger

from shared import BaseConfig


def setup_logging(config: BaseConfig) -> None:
    """Универсальная настройка логирования для продакшена."""

    logger.remove()

    is_prod = config.env == "production"

    # Настройка вывода в консоль (stdout)
    logger.add(
        sys.stdout,
        level=config.log_level.upper(),
        format=config.log_format,
        serialize=is_prod,
        enqueue=True,
    )

    # Добавляем глобальный контекст (имя сервиса) ко всем логам
    logger.configure(extra={"service": config.service})

    # Настройка записи в файл (если включено в конфигурации)
    if config.log_to_file:
        logger.add(
            f"logs/{config.service}.log",
            level=config.log_level.upper(),
            rotation="10 MB",
            retention="10 days",
            compression="zip",
            serialize=is_prod,
            enqueue=True,
        )

    logger.info(f"Loguru успешно инициализирован для сервиса: {config.service}")
