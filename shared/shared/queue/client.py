import json
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from types import TracebackType
from typing import Any, Self, cast

import pika
from loguru import logger
from pika.exceptions import AMQPConnectionError, ChannelError
from pika.exchange_type import ExchangeType

from shared.config.settings import BaseConfig
from shared.utils.retry import retry_on_exception

from .queues import ExchangeTypes


class RabbitMQClient:
    """Базовый клиент для работы с RabbitMQ"""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        virtual_host: str | None = None,
        username: str | None = None,
        password: str | None = None,
        heartbeat: int | None = None,
        blocked_connection_timeout: int | None = None,
    ) -> None:

        self.host = host if host is not None else getattr(BaseConfig, "rabbitmq_host", "localhost")
        self.port = port if port is not None else getattr(BaseConfig, "rabbitmq_port", 5672)
        self.virtual_host = (
            virtual_host
            if virtual_host is not None
            else getattr(BaseConfig, "rabbitmq_virtual_host", "/")
        )
        self.username = (
            username if username is not None else getattr(BaseConfig, "rabbitmq_user", "guest")
        )
        self.password = (
            password if password is not None else getattr(BaseConfig, "rabbitmq_password", "guest")
        )
        self.heartbeat = (
            heartbeat if heartbeat is not None else getattr(BaseConfig, "rabbitmq_heartbeat", 600)
        )

        self.blocked_connection_timeout = (
            blocked_connection_timeout
            if blocked_connection_timeout is not None
            else getattr(BaseConfig, "rabbitmq_timeout", 300)
        )

        self._connection: pika.BlockingConnection | None = None
        self._channel: pika.adapters.blocking_connection.BlockingChannel | None = None

    def _get_connection_params(self) -> pika.ConnectionParameters:
        """Создание параметров подключения"""
        credentials = pika.PlainCredentials(self.username, self.password)
        return pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            virtual_host=self.virtual_host,
            credentials=credentials,
            heartbeat=self.heartbeat,
            blocked_connection_timeout=self.blocked_connection_timeout,
            connection_attempts=3,
            retry_delay=2.0,
        )

    @retry_on_exception(
        exceptions=(AMQPConnectionError, ConnectionError),
        max_attempts=3,
        delay=1.0,
        backoff=2.0,
        jitter=0.1,
    )
    def connect(self) -> None:
        """Установка соединения с RabbitMQ"""
        try:
            params = self._get_connection_params()
            self._connection = pika.BlockingConnection(params)

            assert self._connection is not None, "Соединение с RabbitMQ не установлено"
            self._channel = self._connection.channel()
            logger.info(f"Connected to RabbitMQ at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def disconnect(self) -> None:
        """Закрытие соединения"""
        try:
            if self._channel and self._channel.is_open:
                self._channel.close()
            if self._connection and self._connection.is_open:
                self._connection.close()
            logger.info("Disconnected from RabbitMQ")
        except Exception as e:
            logger.error(f"Error while disconnecting: {e}")

    @property
    def channel(self) -> pika.adapters.blocking_connection.BlockingChannel:
        """Получение канала (с автоматическим переподключением)."""
        if not self._channel or not self._channel.is_open:
            self.reconnect()

        channel = self._channel
        if channel is None:
            raise RuntimeError("Не удалось восстановить соединение с RabbitMQ")

        return channel

    @retry_on_exception(exceptions=(AMQPConnectionError, ChannelError), max_attempts=2, delay=0.5)
    def reconnect(self) -> None:
        """Переподключение к RabbitMQ"""
        self.disconnect()
        self.connect()
        logger.info("Reconnected to RabbitMQ")

    @contextmanager
    def get_channel(self) -> Iterator[pika.adapters.blocking_connection.BlockingChannel]:
        """Контекстный менеджер для работы с каналом"""
        try:
            yield self.channel
        except Exception as e:
            logger.error(f"Error in channel context: {e}")
            raise

    def declare_exchange(
        self,
        exchange_name: str,
        exchange_type: str = ExchangeTypes.DIRECT,
        durable: bool = True,
        auto_delete: bool = False,
        arguments: dict[str, Any] | None = None,
    ) -> None:
        """Объявление обменника"""
        with self.get_channel() as channel:
            channel.exchange_declare(
                exchange=exchange_name,
                exchange_type=cast(ExchangeType, cast(Any, exchange_type)),
                durable=durable,
                auto_delete=auto_delete,
                arguments=arguments or {},
            )
            logger.debug(f"Declared exchange: {exchange_name} (type: {exchange_type})")

    def declare_queue(
        self,
        queue_name: str,
        durable: bool = True,
        exclusive: bool = False,
        auto_delete: bool = False,
        arguments: dict[str, Any] | None = None,
    ) -> None:
        """Объявление очереди"""
        with self.get_channel() as channel:
            channel.queue_declare(
                queue=queue_name,
                durable=durable,
                exclusive=exclusive,
                auto_delete=auto_delete,
                arguments=arguments or {},
            )
            logger.debug(f"Declared queue: {queue_name}")

    def bind_queue(self, queue_name: str, exchange_name: str, routing_key: str) -> None:
        """Привязка очереди к обменнику"""
        with self.get_channel() as channel:
            channel.queue_bind(queue=queue_name, exchange=exchange_name, routing_key=routing_key)
            logger.debug(f"Bound queue {queue_name} to {exchange_name} with key {routing_key}")

    def publish(
        self,
        exchange_name: str,
        routing_key: str,
        message: Any,
        properties: pika.BasicProperties | None = None,
        mandatory: bool = False,
    ) -> None:
        """Публикация сообщения"""
        with self.get_channel() as channel:
            if not isinstance(message, bytes | str):
                message = json.dumps(message, ensure_ascii=False)

            if isinstance(message, str):
                message = message.encode("utf-8")

            channel.basic_publish(
                exchange=exchange_name,
                routing_key=routing_key,
                body=message,
                properties=properties
                or pika.BasicProperties(
                    delivery_mode=2,  # persistent
                    content_type="application/json",
                ),
                mandatory=mandatory,
            )
            logger.debug(f"Published message to {exchange_name}/{routing_key}")

    def consume(
        self,
        queue_name: str,
        callback: Callable[..., Any],
        auto_ack: bool = False,
        prefetch_count: int = 1,
        consumer_tag: str | None = None,
    ) -> str:
        """Начало потребления сообщений"""
        with self.get_channel() as channel:
            channel.basic_qos(prefetch_count=prefetch_count)

            def wrapped_callback(
                ch: pika.adapters.blocking_connection.BlockingChannel,
                method: pika.spec.Basic.Deliver,
                properties: pika.spec.BasicProperties,
                body: bytes,
            ) -> None:
                assert method.delivery_tag is not None, "Delivery tag is missing"
                try:
                    callback(ch, method, properties, body)
                    if auto_ack:
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    if not auto_ack:
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                    raise

            assigned_tag = channel.basic_consume(
                queue=queue_name,
                on_message_callback=wrapped_callback,
                auto_ack=auto_ack,
                consumer_tag=consumer_tag,
            )
            logger.info(f"Started consuming from {queue_name} (tag: {assigned_tag})")
            return assigned_tag

    def ack_message(self, delivery_tag: int) -> None:
        """Подтверждение обработки сообщения"""
        with self.get_channel() as channel:
            channel.basic_ack(delivery_tag=delivery_tag)

    def nack_message(self, delivery_tag: int, requeue: bool = False) -> None:
        """Отрицательное подтверждение сообщения"""
        with self.get_channel() as channel:
            channel.basic_nack(delivery_tag=delivery_tag, requeue=requeue)

    def reject_message(self, delivery_tag: int, requeue: bool = False) -> None:
        """Отклонение сообщения"""
        with self.get_channel() as channel:
            channel.basic_reject(delivery_tag=delivery_tag, requeue=requeue)

    def start_consuming(self) -> None:
        """Запуск цикла потребления (блокирующий)"""
        if self._channel:
            self._channel.start_consuming()

    def stop_consuming(self, consumer_tag: str) -> None:
        """Остановка потребления"""
        with self.get_channel() as channel:
            channel.basic_cancel(consumer_tag=str(consumer_tag))
            logger.info(f"Stopped consuming with tag: {consumer_tag}")

    def __enter__(self) -> Self:
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.disconnect()
