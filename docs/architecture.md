# SOVA_RAG_platform

## Структура проекта
```
SOVA_RAG_platform/
├── README.md                          # Общее описание проекта
├── docker-compose.yml                 # Локальный запуск (включая MinIO, RabbitMQ, Qdrant, Redis)
├── docker-compose.prod.yml            # Продакшен-конфигурация
├── .env.example                       # Шаблон переменных окружения
├── Makefile                           # Утилиты для сборки/запуска
├── pyproject.toml                     # Общие зависимости
│
├── docs/                              # Документация
│   ├── architecture.md
│   ├── api.md
│   └── deployment.md
│
├── gateway/                           # API Gateway (Точка входа)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   ├── src/
│   │   ├── init.py
│   │   ├── main.py                    # FastAPI приложение (+ OpenTelemetry Middleware)
│   │   ├── routes/
│   │   │   ├── init.py
│   │   │   ├── upload.py              # POST /api/v1/upload (Загрузка файла и публикация в RabbitMQ)
│   │   │   ├── chat.py                # POST /api/v1/chat (Диалог с RAG-агентом через llm-service)
│   │   │   ├── search.py              # POST /api/v1/search (Чистый векторный поиск)
│   │   │   ├── delete.py              # DELETE /api/v1/delete/{document_id} (Удаление документов/чанкинга)
│   │   │   └── status.py              # GET /api/v1/status/{task_id} (Статус фоновых задач)
│   │   ├── middleware/
│   │   │   ├── init.py
│   │   │   ├── auth.py                # Аутентификация
│   │   │   ├── rate_limit.py          # Rate limiting (Redis-backed)
│   │   │   ├── tracing.py             # Сквозной сбор трассировок (X-Request-ID)
│   │   │   └── logging.py             # Структурированное логирование
│   │   ├── models/
│   │   │   ├── requests.py            # Pydantic модели запросов (включая chat, upload, delete)
│   │   │   └── responses.py           # Pydantic модели ответов
│   │   └── services/
│   │       ├── queue.py               # RabbitMQ клиент (Quorum queues)
│   │       ├── grpc_client.py         # gRPC клиент к search-service
│   │       └── llm_client.py          # Клиент шлюза к llm-service (для эндпоинта chat)
│   └── tests/
│       ├── test_routes.py
│       └── test_middleware.py
│
├── download-worker/                   # Download Worker (Скачивание файлов)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   ├── src/
│   │   ├── init.py
│   │   ├── main.py                    # Точка входа воркера
│   │   ├── worker.py                  # Основной цикл с ручным ack/nack и DLX
│   │   ├── downloaders/
│   │   │   ├── s3_downloader.py       # Скачивание из внешних источников
│   │   │   └── http_downloader.py     # Скачивание по HTTP (с retry)
│   │   ├── storage/
│   │   │   └── s3_uploader.py         # Загрузка файла в промежуточный S3/MinIO
│   │   └── queue/
│   │       └── client.py              # RabbitMQ клиент
│   └── tests/
│       └── test_downloader.py
│
├── processing-worker/                 # Processing Worker (Парсинг, чанкинг, эмбеддинги, удаление)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   ├── src/
│   │   ├── init.py
│   │   ├── main.py                    # Точка входа воркера
│   │   ├── worker.py                  # Основной цикл (ручной ack/nack, поддержка задач удаления)
│   │   ├── processors/
│   │   │   ├── s3_fetcher.py          # Скачивание файла из промежуточного S3
│   │   │   ├── text_extractor.py      # Извлечение текста (PDF / DOCX)
│   │   │   ├── chunker.py             # Разбивка текста на чанки
│   │   │   ├── embedder.py            # Генерация векторов
│   │   │   └── vector_store.py        # Идемпотентная запись и удаление точек из Qdrant
│   │   └── queue/
│   │       └── client.py              # RabbitMQ клиент
│   └── tests/
│       └── test_processors.py
│
├── search-service/                    # Search Service (gRPC, чистый векторный поиск)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   ├── proto/
│   │   └── search.proto               # gRPC протокол (включая методы поиска)
│   ├── src/
│   │   ├── init.py
│   │   ├── main.py                    # gRPC сервер
│   │   ├── server.py                  # Реализация эндпоинтов поиска
│   │   ├── services/
│   │   │   ├── embedding.py           # Эмбеддинг поискового запроса
│   │   │   └── vector_search.py       # Запрос в Qdrant с лимитами латентности
│   │   └── utils/
│   │       └── cache.py               # Кэширование результатов поиска (Redis)
│   └── tests/
│       └── test_search.py
│
├── llm-service/                       # LLM Service (Генерация ответов, RAG-оркестрация)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   ├── src/
│   │   ├── init.py
│   │   ├── main.py                    # FastAPI / gRPC сервер (обслуживает /chat запросы от Gateway)
│   │   ├── llm_client.py              # Клиент к DeepSeek API
│   │   ├── prompt_templates.py        # Шаблоны системных промптов
│   │   ├── context_builder.py         # Сборка контекста из Qdrant/Search Service
│   │   └── utils/
│   │       ├── cache.py               # Кэш ответов LLM (Redis)
│   │       └── circuit_breaker.py     # Защита от сбоев внешнего LLM-провайдера
│   └── tests/
│       └── test_llm.py
│
├── shared/                            # Общий код
│   ├── init.py
│   ├── config/
│   │   └── settings.py                # Pydantic Settings
│   ├── logging/
│   │   └── logger.py                  # JSON-логгер с поддержкой Trace ID
│   ├── models/
│   │   ├── task.py                    # Модели задач (индексация, удаление)
│   │   └── document.py                # Модели документов
│   ├── queue/
│   │   ├── client.py                  # Конфигурация quorum queues в RabbitMQ
│   │   └── queues.py                  # Константы очередей
│   └── utils/
│       └── retry.py                   # Exponential backoff декораторы
│
├── k8s/                               # Kubernetes манифесты
│   ├── namespace.yaml
│   ├── gateway/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── hpa.yaml
│   ├── download-worker/
│   │   ├── deployment.yaml
│   │   └── hpa.yaml
│   ├── processing-worker/
│   │   ├── deployment.yaml
│   │   └── hpa.yaml
│   ├── search-service/
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   ├── llm-service/
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   ├── rabbitmq/                      # StatefulSet кластер с кворум-очередями
│   │   ├── statefulset.yaml
│   │   └── service.yaml
│   ├── qdrant/                        # StatefulSet векторной базы
│   │   ├── statefulset.yaml
│   │   └── service.yaml
│   ├── minio/                         # S3-хранилище
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   ├── redis/                         # Для кэша и rate limiting
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   └── secrets.yaml                   # Секреты
│
├── scripts/                           # Скрипты автоматизации
│   ├── build.sh
│   ├── deploy.sh
│   ├── test.sh
│   ├── clean.sh
│   └── local-up.sh
│
├── tests/                             # Интеграционные тесты
│   └── e2e/
│       └── test_rag_pipeline.py
│
└── .github/                           # CI/CD пайплайны
└── workflows/
├── ci.yml
└── cd.yml
```


# Полное описание каждого файла в архитектуре SOVA_RAG_platform

##  Корневые файлы

| Файл | Описание |
|------|----------|
| **README.md** | Общее описание проекта: цели, требования, быстрый старт, архитектура, ссылки на документацию |
| **docker-compose.yml** | Локальный запуск всех сервисов: MinIO, RabbitMQ, Qdrant, Redis с настройками портов и volume'ов |
| **docker-compose.prod.yml** | Продакшен-конфигурация с репликами, лимитами ресурсов, переменными окружения |
| **.env.example** | Шаблон всех переменных окружения с комментариями (API ключи, порты, настройки) |
| **Makefile** | Утилиты: `make build`, `make up`, `make down`, `make test`, `make clean`, `make logs` |
| **pyproject.toml** | Общие зависимости Python с версиями, настройки black/isort/mypy |

---

##  docs/ - Документация

| Файл | Описание |
|------|----------|
| **architecture.md** | Детальное описание архитектуры: компоненты, взаимодействие, потоки данных, диаграммы |
| **api.md** | Swagger/OpenAPI спецификация всех эндпоинтов с примерами запросов/ответов |
| **deployment.md** | Инструкции по деплою: Kubernetes, Docker, настройки для разных окружений |

---

##  gateway/ - API Gateway

| Файл/Папка | Описание |
|------------|----------|
| **Dockerfile** | Многоступенчатый билд: Python 3.11 slim, установка зависимостей, копирование кода, запуск через uvicorn |
| **requirements.txt** | Зависимости: fastapi, uvicorn, pika, redis, grpcio, opentelemetry, python-multipart |
| **.env.example** | Специфичные переменные: PORT, RABBITMQ_URL, REDIS_URL, SEARCH_SERVICE_URL, LLM_SERVICE_URL |

### src/main.py
Точка входа FastAPI приложения:
- Инициализация middleware (аутентификация, rate limit, tracing, logging)
- Регистрация роутеров
- Настройка CORS
- OpenTelemetry инициация
- Health check эндпоинты

### src/routes/upload.py
`POST /api/v1/upload`
- Принимает файл (multipart/form-data)
- Генерирует уникальный document_id
- Публикует задачу в RabbitMQ (quorum queue)
- Возвращает task_id для отслеживания статуса

### src/routes/chat.py
`POST /api/v1/chat`
- Принимает вопрос пользователя
- Отправляет запрос в llm-service через gRPC/REST
- Возвращает сгенерированный ответ с источниками

### src/routes/search.py
`POST /api/v1/search`
- Принимает поисковый запрос
- Вызывает search-service через gRPC
- Возвращает найденные чанки с релевантностью

### src/routes/delete.py
`DELETE /api/v1/delete/{document_id}`
- Публикует задачу на удаление в RabbitMQ
- Возвращает статус операции

### src/routes/status.py
`GET /api/v1/status/{task_id}`
- Проверяет статус задачи в Redis
- Возвращает: pending, processing, completed, failed с деталями

### src/middleware/auth.py
- Проверка JWT токенов или API ключей
- Извлечение user_id из токена
- Добавление user_id в request.state

### src/middleware/rate_limit.py
- Rate limiting на основе Redis (sliding window)
- Настройка лимитов на эндпоинт и пользователя
- Возврат 429 Too Many Requests

### src/middleware/tracing.py
- Генерация X-Request-ID для каждого запроса
- Передача trace_id в заголовках к downstream сервисам
- Интеграция с OpenTelemetry

### src/middleware/logging.py
- Структурированное логирование в JSON формате
- Добавление request_id, user_id, endpoint, method, status_code
- Ротация логов

### src/models/requests.py
Pydantic модели для запросов:
- `UploadRequest`: file, metadata
- `ChatRequest`: query, history, temperature
- `SearchRequest`: query, limit, filter
- `DeleteRequest`: document_id, force

### src/models/responses.py
Pydantic модели для ответов:
- `TaskResponse`: task_id, status, created_at
- `ChatResponse`: answer, sources, tokens_used
- `SearchResponse`: results, total, time_ms
- `StatusResponse`: status, progress, error

### src/services/queue.py
RabbitMQ клиент:
- Подключение с retry
- Публикация сообщений в quorum очереди
- Управление каналами

### src/services/grpc_client.py
gRPC клиент к search-service:
- Каналы с keepalive
- Таймауты и retry
- Передача trace_id в метаданных

### src/services/llm_client.py
Клиент к llm-service:
- REST/gRPC вызовы
- Таймауты
- Обработка ошибок и fallback

### tests/
- **test_routes.py**: Юнит-тесты эндпоинтов с моками
- **test_middleware.py**: Тесты middleware (rate limit, auth)

---

##  download-worker/ - Download Worker

| Файл/Папка | Описание |
|------------|----------|
| **Dockerfile** | Легковесный образ с Python и необходимыми библиотеками |
| **requirements.txt** | Зависимости: boto3, aiohttp, pika, tenacity |
| **.env.example** | MINIO_ACCESS_KEY, MINIO_SECRET_KEY, RABBITMQ_URL |

### src/main.py
Точка входа:
- Парсинг аргументов
- Инициализация логирования
- Запуск воркера

### src/worker.py
Основной цикл:
- Подключение к RabbitMQ
- Потребление из очереди `download_queue`
- Ручной ack/nack
- Отправка в DLX при ошибках
- Передача задачи downloader'у

### src/downloaders/s3_downloader.py
Скачивание из внешних S3/MinIO:
- Проверка доступа
- Стриминг больших файлов
- Retry на 5xx ошибки

### src/downloaders/http_downloader.py
Скачивание по HTTP/HTTPS:
- Поддержка заголовков (авторизация)
- Chunked download для больших файлов
- Прогресс-бар
- Retry с exponential backoff

### src/storage/s3_uploader.py
Загрузка в промежуточный S3:
- Multipart upload для больших файлов
- Генерация уникального ключа
- Проверка целостности (ETag)

### src/queue/client.py
RabbitMQ клиент для воркера:
- Потребление с ручным подтверждением
- Настройка prefetch_count
- Обработка ошибок подключения

### tests/test_downloader.py
Тесты скачивания:
- Моки S3 и HTTP
- Проверка retry механизма
- Тесты ошибок

---

##  processing-worker/ - Processing Worker

| Файл/Папка | Описание |
|------------|----------|
| **Dockerfile** | Образ с Python и системными зависимостями (poppler, libreoffice) |
| **requirements.txt** | Зависимости: pypdf, python-docx, sentence-transformers, qdrant-client, boto3 |
| **.env.example** | QDRANT_URL, EMBEDDING_MODEL, CHUNK_SIZE, OVERLAP |

### src/main.py
Точка входа:
- Инициализация процессора
- Запуск worker loop

### src/worker.py
Основной цикл:
- Потребление из `processing_queue`
- Поддержка двух типов задач: index и delete
- Ручной ack/nack
- Идемпотентность операций

### src/processors/s3_fetcher.py
Скачивание файла из промежуточного S3:
- Получение по ключу
- Сохранение во временную директорию
- Очистка после обработки

### src/processors/text_extractor.py
Извлечение текста:
- **PDF**: pypdf, pdfplumber (с таблицами)
- **DOCX**: python-docx
- Поддержка OCR (опционально, Tesseract)
- Нормализация текста

### src/processors/chunker.py
Разбивка на чанки:
- RecursiveCharacterTextSplitter
- Настройка: chunk_size, chunk_overlap
- Сохранение метаданных (page, section)
- Поддержка разных стратегий (semantic, fixed)

### src/processors/embedder.py
Генерация эмбеддингов:
- Использование sentence-transformers или API (OpenAI, Cohere)
- Batch processing для оптимизации
- Кэширование эмбеддингов в Redis
- Нормализация векторов

### src/processors/vector_store.py
Работа с Qdrant:
- Идемпотентная запись (upsert)
- Удаление всех точек для document_id
- Создание коллекции с настройками
- Метрики (cosine, dot product)

### src/queue/client.py
RabbitMQ клиент:
- Потребление с QoS (prefetch=1)
- Обработка DLX сообщений

### tests/test_processors.py
Тесты процессоров:
- Извлечение текста из разных форматов
- Чанкинг с разными параметрами
- Интеграция с Qdrant (мок)

---

##  search-service/ - Search Service

| Файл/Папка | Описание |
|------------|----------|
| **Dockerfile** | Образ с Python и gRPC |
| **requirements.txt** | grpcio, grpcio-tools, qdrant-client, redis, sentence-transformers |
| **.env.example** | QDRANT_URL, REDIS_URL, EMBEDDING_MODEL, CACHE_TTL |

### proto/search.proto
gRPC протокол:
```protobuf
service Search {
    rpc Search(SearchRequest) returns (SearchResponse);
}
```
Структуры: SearchRequest (query, limit, filter), SearchResponse (results, total)

### src/main.py
gRPC сервер:
- Инициализация сервера
- Регистрация сервиса
- Graceful shutdown
- Health проверка

### src/server.py
Реализация эндпоинтов:
- Search метод
- Валидация запроса
- Вызов vector_search
- Формирование ответа

### src/services/embedding.py
Эмбеддинг поискового запроса:
- Использование той же модели, что в processing
- Кэширование частых запросов
- Batch для нескольких запросов

### src/services/vector_search.py
Поиск в Qdrant:
- Построение фильтров (metadata)
- Поиск с лимитами latency
- Payload filtering
- Сортировка по score

### src/utils/cache.py
Кэширование результатов:
- Redis кэш (TTL 5 минут)
- Ключ: hash(query + filter)
- Инвалидация при обновлении данных

### tests/test_search.py
Тесты поиска:
- Проверка точности
- Тесты фильтрации
- Бенчмарки

---

##  llm-service/ - LLM Service

| Файл/Папка | Описание |
|------------|----------|
| **Dockerfile** | Образ с Python |
| **requirements.txt** | openai, httpx, tenacity, fastapi (если REST), grpcio |
| **.env.example** | DEEPSEEK_API_KEY, DEEPSEEK_MODEL, TEMPERATURE, MAX_TOKENS |

### src/main.py
FastAPI/gRPC сервер:
- Инициализация приложения
- Эндпоинт /chat
- Интеграция с circuit breaker

### src/llm_client.py
Клиент к DeepSeek API:
- Авторизация через API key
- Retry с exponential backoff
- Streaming ответов (опционально)
- Обработка rate limits
- Логирование токенов

### src/prompt_templates.py
Шаблоны промптов:
- Системный промпт для RAG
- Форматирование контекста
- Инструкции по формату ответа
- Примеры few-shot

### src/context_builder.py
Сборка контекста:
- Получение чанков из search-service
- Форматирование: [doc_id] текст
- Ограничение по токенам
- Сортировка по релевантности

### src/utils/cache.py
Кэш ответов LLM:
- Хэш: question + context_hash
- TTL: 1 час
- Redis бэкенд

### src/utils/circuit_breaker.py
Защита от сбоев:
- Отслеживание ошибок к DeepSeek
- Fallback ответы
- Полуоткрытое состояние для проверки

### tests/test_llm.py
Тесты:
- Мок DeepSeek API
- Тесты промптов
- Тесты circuit breaker

---

##  shared/ - Общий код

| Файл/Папка | Описание |
|------------|----------|
| **config/settings.py** | Pydantic Settings: загрузка из .env, валидация, типизация |
| **logging/logger.py** | JSON-логгер с Trace ID, структурные поля, уровни логирования |
| **models/task.py** | Task модели: TaskType (INDEX, DELETE), TaskStatus (PENDING, PROCESSING, COMPLETED, FAILED) |
| **models/document.py** | Document модели: Document, Chunk, Metadata |
| **queue/client.py** | Базовый RabbitMQ клиент: подключение, каналы, обменники |
| **queue/queues.py** | Константы: QUEUE_NAMES, EXCHANGE_NAMES, ROUTING_KEYS, DLX_NAMES |
| **utils/retry.py** | Декораторы: @retry_on_exception, exponential backoff, jitter |

---

##  k8s/ - Kubernetes манифесты

| Файл/Папка | Описание |
|------------|----------|
| **namespace.yaml** | Создание namespace `sova-rag` |
| **gateway/deployment.yaml** | Deployment: 2 реплики, liveness/readiness probes, ресурсы, переменные |
| **gateway/service.yaml** | ClusterIP сервис на порту 80, с селектором |
| **gateway/hpa.yaml** | HorizontalPodAutoscaler: по CPU (50%) и RPS |
| **download-worker/deployment.yaml** | Deployment с 1 репликой, переменные, secrets |
| **download-worker/hpa.yaml** | HPA по длине очереди RabbitMQ (custom metrics) |
| **processing-worker/deployment.yaml** | Deployment с 2 репликами, приоритет класс |
| **processing-worker/hpa.yaml** | HPA по длине очереди |
| **search-service/deployment.yaml** | Deployment с 3 репликами, gRPC порт |
| **search-service/service.yaml** | ClusterIP для gRPC |
| **llm-service/deployment.yaml** | Deployment с переменными для DeepSeek |
| **llm-service/service.yaml** | ClusterIP сервис |
| **rabbitmq/statefulset.yaml** | StatefulSet с 3 нодами, persistent volumes, quorum queues |
| **rabbitmq/service.yaml** | Headless service для кластеризации |
| **qdrant/statefulset.yaml** | StatefulSet с PVC, настройки памяти |
| **qdrant/service.yaml** | ClusterIP на порту 6333 (REST) и 6334 (gRPC) |
| **minio/deployment.yaml** | Deployment с 1 репликой, PVC |
| **minio/service.yaml** | ClusterIP для S3 API |
| **redis/deployment.yaml** | Deployment с Redis Sentinel (опционально) |
| **redis/service.yaml** | ClusterIP на порту 6379 |
| **secrets.yaml** | Зашифрованные secrets: API keys, пароли, JWT secret |

---

##  scripts/ - Скрипты автоматизации

| Файл | Описание |
|------|----------|
| **build.sh** | Сборка всех Docker образов с тегами |
| **deploy.sh** | Деплой в Kubernetes: apply манифестов, проверка статуса |
| **test.sh** | Запуск всех тестов: unit, integration, e2e с покрытием |
| **clean.sh** | Очистка: удаление контейнеров, volumes, кэша |
| **local-up.sh** | Быстрый локальный запуск: docker-compose up с билдом |

---

##  tests/e2e/ - E2E тесты

| Файл | Описание |
|------|----------|
| **test_rag_pipeline.py** | Сквозной тест: загрузка → обработка → поиск → чат. Проверка всего пайплайна |

---

##  .github/workflows/ - CI/CD

| Файл | Описание |
|------|----------|
| **ci.yml** | CI пайплайн: linting, unit tests, integration tests, сборка образов, push в registry |
| **cd.yml** | CD пайплайн: деплой на staging/production, миграции, smoke-тесты, rollback |

---

## Потоки данных

```
1. Upload: Gateway → RabbitMQ (download_queue)
2. Download: Worker → S3 (temp) → RabbitMQ (processing_queue)
3. Processing: Worker → Qdrant (вектора) → RabbitMQ (status)
4. Search: Gateway → gRPC Search → Qdrant
5. Chat: Gateway → LLM Service → Search Service → DeepSeek
6. Delete: Gateway → RabbitMQ → Processing Worker → Qdrant
```
