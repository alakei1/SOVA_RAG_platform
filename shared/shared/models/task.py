from enum import Enum
from typing import Union

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"  # Задача ждет в очереди
    PROCESSING = "processing"  # Воркер выполняет задачу прямо сейчас
    COMPLETED = "completed"  # Задача успешно завершена
    FAILED = "failed"  # Произошла ошибка (описание в поле error)


class TaskType(str, Enum):
    DOWNLOAD = "download"  # Индексация: Этап 1. Скачать и сохранить в постоянный S3
    VECTORIZE = "vectorize"  # Индексация: Этап 2. Нарезать текст на чанки и векторизовать в Qdrant
    DELETE = "delete"  # Удаление: Стереть файл из S3 и векторы из Qdrant


class DownloadTaskPayload(BaseModel):
    """Данные для этапа скачивания (для download-worker)"""

    user_id: str = Field(..., description="ID пользователя")
    project_id: str = Field(..., description="ID проекта для изоляции")
    original_filename: str = Field(..., description="Имя файла (например, document.pdf)")

    # Источник файла
    source_url: str | None = Field(
        None, description="Ссылка на файл в интернете, если скачиваем по сети"
    )
    temporary_s3_key: str | None = Field(
        None, description="Путь во временном S3, если файл загружен через API Gateway"
    )


class VectorizeTaskPayload(BaseModel):
    """Данные для этапа векторизации и индексации (для processing-worker)"""

    document_id: str = Field(..., description="Уникальный ID документа в системе")
    user_id: str = Field(..., description="ID владельца документа")
    project_id: str = Field(..., description="ID проекта")

    # Путь к постоянному файлу, который download-worker уже проверил и переложил в S3
    s3_bucket: str = Field(..., description="Постоянный бакет в MinIO")
    s3_key: str = Field(..., description="Ключ (путь) к файлу в бакете")
    file_type: str = Field(..., description="Расширение файла (pdf, txt, docx)")


class DeleteTaskPayload(BaseModel):
    """Данные для удаления документа изо всех систем (для воркеров удаления)"""

    document_id: str = Field(..., description="ID документа, который нужно стереть")
    project_id: str = Field(..., description="ID проекта, в котором лежал документ")
    s3_bucket: str = Field(..., description="Бакет, из которого нужно удалить физический файл")
    s3_key: str = Field(..., description="Ключ файла в S3 для удаления")


class Task(BaseModel):
    """Универсальная обертка для передачи задач через RabbitMQ"""

    task_id: str = Field(..., description="UUID задачи для отслеживания статуса")
    task_type: TaskType = Field(..., description="Тип задачи (download, vectorize, delete)")
    status: TaskStatus = Field(default=TaskStatus.PENDING)

    # Pydantic автоматически выберет нужную схему данных на основе переданных полей
    payload: Union[DownloadTaskPayload, VectorizeTaskPayload, DeleteTaskPayload] = Field(
        ..., description="Конкретные данные для выполнения работы"
    )

    error: str | None = Field(default=None, description="Текст ошибки, если статус FAILED")
    trace_id: str = Field(..., description="Сквозной ID для логов всей микросервисной системы")
