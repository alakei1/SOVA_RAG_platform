# queue/task_consumer.py
import json
from typing import Callable, Dict, Optional

import pika
from loguru import logger

from shared.models import Task, TaskStatus, TaskType

from .client import RabbitMQClient
from .queues import ExchangeNames, RoutingKeys, get_routing_key_for_task_type


class TaskConsumer:
    """Потребитель задач из RabbitMQ"""

    def __init__(
        self,
        rabbitmq_client: RabbitMQClient,
        queue_name: str,
        task_type: TaskType,
        prefetch_count: int = 1,
        max_retries: int = 3,
    ):
        self.client = rabbitmq_client
        self.queue_name = queue_name
        self.task_type = task_type
        self.prefetch_count = prefetch_count
        self.max_retries = max_retries
        self.consumer_tag: Optional[str] = None
        self._handlers: Dict[TaskType, Callable[..., None]] = {}

    def register_handler(self, task_type: TaskType, handler: Callable[[Task], None]) -> None:
        """Регистрация обработчика для конкретного типа задач"""
        self._handlers[task_type] = handler
        logger.info(f"Registered handler for {task_type.value} tasks")

    def start(self) -> None:
        """Запуск потребления задач"""
        if not self._handlers:
            logger.warning(f"No handlers registered for {self.task_type.value} tasks")
            return

        self.consumer_tag = self.client.consume(
            queue_name=self.queue_name,
            callback=self._process_message,
            auto_ack=False,
            prefetch_count=self.prefetch_count,
        )

        logger.info(f"Started consuming {self.task_type.value} tasks from {self.queue_name}")
        self.client.start_consuming()

    def stop(self) -> None:
        """Остановка потребления"""
        if self.consumer_tag:
            self.client.stop_consuming(self.consumer_tag)
            self.consumer_tag = None
            logger.info(f"Stopped consuming {self.task_type.value} tasks")

    def _process_message(
        self,
        channel: pika.adapters.blocking_connection.BlockingChannel,
        method: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties,
        body: bytes,
    ) -> None:
        """Обработка полученного сообщения"""
        if properties.reply_to:
            logger.info(f"Received reply from {properties.reply_to}")
        try:
            task_data = json.loads(body.decode("utf-8"))
            task = Task(**task_data)

            logger.info(
                f"Processing {task.task_type.value} task {task.task_id} (trace_id: {task.trace_id})"
            )

            if task.task_type != self.task_type:
                logger.warning(
                    f"Task type mismatch: expected {self.task_type}, got {task.task_type}"
                )
                self._send_to_dead_letter(channel, method, task, "Task type mismatch")
                return

            handler = self._handlers.get(task.task_type)
            if not handler:
                logger.error(f"No handler for {task.task_type.value} tasks")
                self._send_to_dead_letter(
                    channel, method, task, f"No handler for {task.task_type.value}"
                )
                return

            handler(task)
            assert method.delivery_tag is not None
            channel.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"Successfully processed task {task.task_id}")

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)

            try:
                task_data = json.loads(body.decode("utf-8"))
                task = Task(**task_data)
                retry_count = task_data.get("retry_count", 0)

                if retry_count < self.max_retries:
                    logger.warning(
                        f"Sending task {task.task_id} to retry (attempt {retry_count + 1}/{self.max_retries})"  # noqa: E501
                    )
                    self._publish_retry(task, retry_count + 1)
                    assert method.delivery_tag is not None
                    channel.basic_ack(delivery_tag=method.delivery_tag)
                else:
                    logger.error(f"Task {task.task_id} failed after {self.max_retries} attempts")
                    self._send_to_dead_letter(
                        channel, method, task, f"Failed after {self.max_retries} attempts: {str(e)}"
                    )
                    assert method.delivery_tag is not None
                    channel.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as parse_error:
                logger.error(f"Failed to parse task for retry: {parse_error}")
                assert method.delivery_tag is not None
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    @staticmethod
    def _send_to_dead_letter(
        channel: pika.adapters.blocking_connection.BlockingChannel,
        method: pika.spec.Basic.Deliver,
        task: Task,
        error_message: str,
    ) -> None:
        """Отправка задачи в Dead Letter очередь"""
        task.status = TaskStatus.FAILED
        task.error = error_message

        message = task.model_dump_json()

        channel.basic_publish(
            exchange=ExchangeNames.DEAD_LETTER.value,
            routing_key=RoutingKeys.DLX.value,
            body=message.encode("utf-8"),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
                headers={
                    "task_id": task.task_id,
                    "error": error_message,
                    "trace_id": task.trace_id,
                },
            ),
        )
        assert method.delivery_tag is not None, "Delivery tag cannot be None"
        channel.basic_ack(delivery_tag=method.delivery_tag)
        logger.warning(f"Task {task.task_id} sent to DLX: {error_message}")

    def _publish_retry(self, task: Task, retry_count: int) -> None:
        """Публикация задачи на повторную попытку"""
        from .queues import get_retry_queue_for_attempt

        retry_queue = get_retry_queue_for_attempt(retry_count)

        task_dict = task.model_dump()
        task_dict["retry_count"] = retry_count
        task_dict["original_routing_key"] = get_routing_key_for_task_type(task.task_type.value)

        message = json.dumps(task_dict, default=str)

        self.client.publish(
            exchange_name=ExchangeNames.RETRY.value,
            routing_key=RoutingKeys.RETRY.value,
            message=message,
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
                headers={
                    "task_id": task.task_id,
                    "retry_count": retry_count,
                    "trace_id": task.trace_id,
                },
            ),
        )

        logger.info(f"Published retry task {task.task_id} (attempt {retry_count}) to {retry_queue}")
