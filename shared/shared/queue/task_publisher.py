import uuid
from typing import Optional

import pika
from loguru import logger

from shared import (
    DeleteTaskPayload,
    DownloadTaskPayload,
    ExchangeNames,
    RabbitMQClient,
    RoutingKeys,
    Task,
    TaskStatus,
    TaskType,
    VectorizeTaskPayload,
)


class TaskPublisher:
    """Публикатор задач в RabbitMQ"""

    def __init__(self, rabbitmq_client: RabbitMQClient):
        self.client = rabbitmq_client

    def publish_download_task(
        self,
        user_id: str,
        project_id: str,
        original_filename: str,
        trace_id: str,
        source_url: Optional[str] = None,
        temporary_s3_key: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> Task:
        """Публикация задачи на скачивание"""
        task_id = task_id or str(uuid.uuid4())

        payload = DownloadTaskPayload(
            user_id=user_id,
            project_id=project_id,
            original_filename=original_filename,
            source_url=source_url,
            temporary_s3_key=temporary_s3_key,
        )

        task = Task(
            task_id=task_id,
            task_type=TaskType.DOWNLOAD,
            status=TaskStatus.PENDING,
            payload=payload,
            trace_id=trace_id,
        )
        self._publish_task(task, RoutingKeys.DOWNLOAD.value)
        logger.info(f"Published DOWNLOAD task {task_id} for user {user_id}")
        return task

    def publish_vectorize_task(
        self,
        document_id: str,
        user_id: str,
        project_id: str,
        s3_bucket: str,
        s3_key: str,
        file_type: str,
        trace_id: str,
        task_id: Optional[str] = None,
    ) -> Task:
        """Публикация задачи на векторизацию"""
        task_id = task_id or str(uuid.uuid4())

        payload = VectorizeTaskPayload(
            document_id=document_id,
            user_id=user_id,
            project_id=project_id,
            s3_bucket=s3_bucket,
            s3_key=s3_key,
            file_type=file_type,
        )

        task = Task(
            task_id=task_id,
            task_type=TaskType.VECTORIZE,
            status=TaskStatus.PENDING,
            payload=payload,
            trace_id=trace_id,
        )

        self._publish_task(task, RoutingKeys.VECTORIZE.value)
        logger.info(f"Published VECTORIZE task {task_id} for document {document_id}")
        return task

    def publish_delete_task(
        self,
        document_id: str,
        project_id: str,
        s3_bucket: str,
        s3_key: str,
        trace_id: str,
        task_id: Optional[str] = None,
    ) -> Task:
        """Публикация задачи на удаление"""
        task_id = task_id or str(uuid.uuid4())

        payload = DeleteTaskPayload(
            document_id=document_id, project_id=project_id, s3_bucket=s3_bucket, s3_key=s3_key
        )

        task = Task(
            task_id=task_id,
            task_type=TaskType.DELETE,
            status=TaskStatus.PENDING,
            payload=payload,
            trace_id=trace_id,
        )

        self._publish_task(task, RoutingKeys.DELETE.value)
        logger.info(f"Published DELETE task {task_id} for document {document_id}")
        return task

    def _publish_task(self, task: Task, routing_key: str) -> None:
        """Публикация задачи в RabbitMQ"""
        message = task.model_dump_json()

        properties = pika.BasicProperties(
            delivery_mode=2,
            content_type="application/json",
            headers={
                "task_id": task.task_id,
                "task_type": task.task_type.value,
                "trace_id": task.trace_id,
            },
        )

        self.client.publish(
            exchange_name=ExchangeNames.MAIN.value,
            routing_key=routing_key,
            message=message,
            properties=properties,
        )
