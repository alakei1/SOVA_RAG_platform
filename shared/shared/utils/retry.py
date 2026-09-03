import asyncio
import logging
import random
import time
from functools import wraps
from typing import Any, Callable, TypeVar

from shared import BaseConfig

# Настройка дефолтного логгера, чтобы код не падал, если logger_func=None
default_logger = logging.getLogger(__name__)

# Переменная типа для сохранения сигнатуры функций в декораторах
F = TypeVar("F", bound=Callable[..., Any])


def retry_on_exception(
    exceptions: type[Exception] | tuple[type[Exception], ...] = getattr(
        BaseConfig, "retry_exceptions", Exception
    ),
    max_attempts: int = getattr(BaseConfig, "retry_max_attempts", 3),
    delay: float | int = getattr(BaseConfig, "retry_delay", 1.0),
    backoff: float | int = getattr(BaseConfig, "retry_backoff", 2.0),
    jitter: float | int = getattr(BaseConfig, "retry_jitter", 0.1),
    retry_on_result: Callable[[Any], bool] | None = getattr(BaseConfig, "retry_on_result", None),
    max_delay: float | None = getattr(BaseConfig, "retry_max_delay", None),
    logger_func: Callable[[str], None] | None = None,
) -> Callable[[F], F]:
    """
    Декоратор для повторных попыток при возникновении исключений.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            _logger = logger_func or default_logger.warning
            _error_logger = logger_func or default_logger.error
            attempt = 1
            current_delay = float(delay)

            while True:
                try:
                    result = func(*args, **kwargs)

                    # Проверка результата
                    if retry_on_result and retry_on_result(result):
                        if attempt >= max_attempts:
                            _error_logger(
                                f"Function {func.__name__} failed result check after "
                                f"{max_attempts} attempts"
                            )
                            return result

                        _logger(
                            f"Function {func.__name__} returned invalid result, "
                            f"retrying (attempt {attempt}/{max_attempts})"
                        )
                    else:
                        return result

                except exceptions as e:
                    if attempt >= max_attempts:
                        _error_logger(
                            f"Function {func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise

                    _logger(
                        f"Function {func.__name__} failed (attempt {attempt}/{max_attempts}): {e}. "
                        f"Retrying in {current_delay:.2f}s"
                    )

                # Расчет задержки с экспоненциальным бэк-оффом и джиттером
                # (выполняется и для ошибок, и для плохих результатов)
                sleep_time = current_delay + random.uniform(-jitter, jitter)
                sleep_time = max(0.0, sleep_time)

                if max_delay is not None:
                    sleep_time = min(sleep_time, max_delay)

                time.sleep(sleep_time)

                # Обновление задержки для следующей попытки
                current_delay = min(current_delay * backoff, max_delay or float("inf"))
                attempt += 1

        return wrapper  # type: ignore

    return decorator


def async_retry_on_exception(
    exceptions: type[Exception] | tuple[type[Exception], ...] = getattr(
        BaseConfig, "retry_exceptions", Exception
    ),
    max_attempts: int = getattr(BaseConfig, "retry_max_attempts", 3),
    delay: float | int = getattr(BaseConfig, "retry_delay", 1.0),
    backoff: float | int = getattr(BaseConfig, "retry_backoff", 2.0),
    jitter: float | int = getattr(BaseConfig, "retry_jitter", 0.1),
    retry_on_result: Callable[[Any], bool] | None = getattr(BaseConfig, "retry_on_result", None),
    max_delay: float | None = getattr(BaseConfig, "retry_max_delay", None),
    logger_func: Callable[[str], None] | None = None,
) -> Callable[[F], F]:
    """
    Асинхронная версия декоратора для повторных попыток.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            _logger = logger_func or default_logger.warning
            _error_logger = logger_func or default_logger.error
            attempt = 1
            current_delay = float(delay)

            while True:
                try:
                    result = await func(*args, **kwargs)

                    if retry_on_result and retry_on_result(result):
                        if attempt >= max_attempts:
                            _error_logger(
                                f"Function {func.__name__} failed result check after "
                                f"{max_attempts} attempts"
                            )
                            return result

                        _logger(
                            f"Function {func.__name__} returned invalid result, "
                            f"retrying (attempt {attempt}/{max_attempts})"
                        )
                    else:
                        return result

                except exceptions as e:
                    if attempt >= max_attempts:
                        _error_logger(
                            f"Function {func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise

                    _logger(
                        f"Function {func.__name__} failed (attempt {attempt}/{max_attempts}): {e}. "
                        f"Retrying in {current_delay:.2f}s"
                    )

                sleep_time = current_delay + random.uniform(-jitter, jitter)
                sleep_time = max(0.0, sleep_time)

                if max_delay is not None:
                    sleep_time = min(sleep_time, max_delay)

                await asyncio.sleep(sleep_time)

                current_delay = min(current_delay * backoff, max_delay or float("inf"))
                attempt += 1

        return wrapper  # type: ignore

    return decorator


class RetryContext:
    """
    Контекстный менеджер для контроля попыток в циклах.
    Поскольку __exit__ не умеет перезапускать блок `with` заново,
    правильный паттерн использования выглядит так:

    retry = RetryContext()
    while retry.running():
        with retry:
            # Ваш код здесь
    """

    def __init__(
        self,
        exceptions: type[Exception] | tuple[type[Exception], ...] = getattr(
            BaseConfig, "retry_exceptions", Exception
        ),
        max_attempts: int = getattr(BaseConfig, "retry_max_attempts", 3),
        delay: float | int = getattr(BaseConfig, "retry_delay", 1.0),
        backoff: float | int = getattr(BaseConfig, "retry_backoff", 2.0),
        jitter: float | int = getattr(BaseConfig, "retry_jitter", 0.1),
        max_delay: float | None = getattr(BaseConfig, "retry_max_delay", None),
        logger_func: Callable[[str], None] | None = None,
    ):
        self.exceptions = exceptions
        self.max_attempts = max_attempts
        self.delay = delay
        self.backoff = backoff
        self.jitter = jitter
        self.max_delay = max_delay
        self.logger_func = logger_func or default_logger.warning

        self.attempt = 1
        self.current_delay = float(delay)
        self._active = True

    def running(self) -> bool:
        return self._active

    def __enter__(self) -> "RetryContext":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        if exc_val is None:
            self._active = False  # Успешно выполнено, выходим из цикла
            return True

        if not isinstance(exc_val, self.exceptions):
            self._active = False
            return False  # Не то исключение, пробрасываем наверх

        if self.attempt >= self.max_attempts:
            self._active = False
            default_logger.error(f"Context failed after {self.max_attempts} attempts: {exc_val}")
            return False  # Лимит попыток исчерпан, выбрасываем ошибку

        # Расчет задержки
        sleep_time = self.current_delay + random.uniform(-self.jitter, self.jitter)
        sleep_time = max(0.0, sleep_time)

        if self.max_delay is not None:
            sleep_time = min(sleep_time, self.max_delay)

        self.logger_func(
            f"Retry {self.attempt}/{self.max_attempts} in {sleep_time:.2f}s due to: {exc_val}"
        )

        time.sleep(sleep_time)

        self.current_delay = min(self.current_delay * self.backoff, self.max_delay or float("inf"))
        self.attempt += 1

        return True  # Подавляем ошибку, чтобы цикл пошел на следующую итерацию


# Вспомогательные функции для проверки результатов
def is_result_none(result: Any) -> bool:
    """Проверка результата на None"""
    return result is None


def is_result_empty(result: Any) -> bool:
    """Проверка результата на пустоту"""
    return not result


def is_result_false(result: bool) -> bool:
    """Проверка результата на False"""
    return result is False


def is_result_error(result: Any) -> bool:
    """Проверка результата на наличие ошибки"""
    if isinstance(result, dict):
        return result.get("error") is not None
    return False
