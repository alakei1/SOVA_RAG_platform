
# Руководство для контрибьюторов (CONTRIBUTING.md)

Мы рады, что вы решили помочь в развитии проекта **RAG Agent**! Этот документ описывает, как настроить окружение, писать код, тестировать и отправлять изменения. Пожалуйста, внимательно ознакомьтесь с ним перед началом работы.

---

## Содержание

- [Требования к окружению](#1-требования-к-окружению)
- [Архитектура и структура монорепозитория](#2-архитектура-и-структура-монорепозитория)
- [Начало работы](#3-начало-работы)
- [Полезные команды](#4-полезные-команды)
- [Стиль кода и линтинг](#5-стиль-кода-и-линтинг)
- [Коммиты и Pull Requests](#6-коммиты-и-pull-requests)

---

## 1. Требования к окружению

Для локальной разработки и запуска сервисов вам понадобятся:

- **Python** (версии, указанной в корневом `pyproject.toml`)
- **uv** (современный менеджер пакетов Python)
- **Docker** и **Docker Compose** (для поднятия инфраструктуры: MinIO, RabbitMQ, Qdrant, Redis)
- **Git**

---

## 2. Архитектура и структура монорепозитория

Проект представляет собой монорепозиторий микросервисной архитектуры RAG-агента со следующей структурой:

```
rag-agent/
├── gateway/              # API Gateway (FastAPI, аутентификация, rate limiting, трассировка)
├── download-worker/      # Download Worker (скачивание по HTTP/S3, сохранение в MinIO)
├── processing-worker/    # Processing Worker (парсинг PDF/DOCX, чанкинг, эмбеддинги, Qdrant)
├── search-service/       # Search Service (gRPC-сервис векторного поиска с кэшем в Redis)
├── llm-service/          # LLM Service (интеграция с DeepSeek API, RAG-оркестрация)
├── shared/               # Общий код (конфиги, JSON-логгер, модели, клиент RabbitMQ)
├── k8s/                  # Kubernetes-манифесты и StatefulSet'ы инфраструктуры
├── scripts/              # Скрипты автоматизации и локального запуска
└── tests/e2e/            # Интеграционные сквозные тесты
```

### Важные правила разработки:

- **Конфигурация:** Все параметры приложения читаются через Pydantic Settings из переменных окружения (`shared/config/settings.py`).
- **Логирование:** Используйте исключительно общий структурированный JSON-логгер из `shared/logging/logger.py` с обязательным пробросом `Trace ID`. Не используйте `print`.
- **Устойчивость:** Сетевые запросы и нестабильные вызовы внешних систем должны оборачиваться в декораторы повтора с экспоненциальной задержкой (`shared/utils/retry.py`).

---

## 3. Начало работы

### Первичная настройка

1. **Форкните и клонируйте репозиторий:**
```bash
git clone <repository-url>
cd rag-agent
```

2. **Установите uv (если ещё не установлен):**
```bash
pip install uv
```

3. **Установите все зависимости:**
```bash
uv sync --dev
```

4. **Активируйте виртуальное окружение:**
```bash
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate     # Windows
```

5. **Скопируйте файл с примером переменных окружения:**
```bash
cp .env.example .env
```

6. **Настройте переменные окружения** в файле `.env` под ваши нужды.

7. **Проверьте работоспособность:**
```bash
uv run python -c "import gateway; print('✅ OK')"
```

### Запуск инфраструктуры

Поднимите локальную инфраструктурную базу (MinIO, RabbitMQ, Qdrant, Redis):
```bash
docker compose up -d
```

### Запуск микросервисов

Для разработки удобно запускать каждый сервис в отдельном терминале:

```bash
# API Gateway
uv run uvicorn gateway.app:app --reload --port 8000

# Download Worker
uv run python -m download_worker.main

# Processing Worker
uv run python -m processing_worker.main

# Search Service
uv run python -m search_service.main

# LLM Service
uv run python -m llm_service.main
```

Или используйте скрипты из `pyproject.toml`:
```bash
uv run run-gateway
uv run run-download-worker
uv run run-processing-worker
uv run run-search-service
uv run run-llm-service
```

---

## 4. Полезные команды

### Управление зависимостями

```bash
# Добавление зависимости в конкретный сервис
uv add fastapi --package gateway

# Добавление dev-зависимости
uv add --dev pytest

# Обновление всех зависимостей
uv lock --upgrade

# Проверка, что lock-файл актуален
uv lock --check

# Синхронизация зависимостей с lock-файлом
uv sync --dev
```

### Тестирование

```bash
# Запуск всех тестов
uv run pytest

# Запуск тестов с покрытием
uv run pytest --cov

# Запуск тестов конкретного сервиса
uv run pytest gateway/tests/

# Запуск E2E тестов
uv run pytest tests/e2e/
```

### Линтинг и форматирование

```bash
# Проверка стиля кода
uv run ruff check .

# Автоматическое исправление ошибок линтинга
uv run ruff check . --fix

# Форматирование кода
uv run ruff format .

# Проверка типов
uv run mypy .

# Проверка типов для конкретного сервиса
uv run mypy gateway/
```

### Pre-commit хуки

```bash
# Ручной запуск всех хуков
uv run pre-commit run --all-files

# Запуск конкретного хука
uv run pre-commit run ruff --all-files
```

### Docker и инфраструктура

```bash
# Запуск инфраструктуры
docker compose up -d

# Остановка инфраструктуры
docker compose down

# Просмотр логов
docker compose logs -f

# Очистка данных (осторожно!)
docker compose down -v
```

### Разработка и отладка

```bash
# Запуск сервиса в режиме отладки
uv run python -m debugpy --listen 5678 -m gateway.main

# Генерация миграций (если используются базы данных)
uv run alembic revision --autogenerate -m "description"

# Применение миграций
uv run alembic upgrade head
```

---

## 5. Стиль кода и линтинг

- Следуйте стандартам написания кода на Python (PEP 8).
- Весь код должен быть строго типизирован (`mypy`).
- Перед отправкой изменений запускайте статический анализ и линтеры:
```bash
uv run ruff check . && uv run ruff format . && uv run mypy .
```
- Пишите unit-тесты для новой бизнес-логики в папках `tests/` соответствующих микросервисов.
- Проверяйте работоспособность через интеграционные E2E-тесты (`tests/e2e/`).

---

## 6. Коммиты и Pull Requests

### Правила коммитов

Мы используем **Conventional Commits** для сообщений коммитов:

| Префикс | Назначение | Пример |
|---------|------------|--------|
| `feat:` | Новая функциональность | `feat: add document upload endpoint` |
| `fix:` | Исправление бага | `fix: handle empty search results` |
| `build:` | Изменения в сборке/зависимостях | `build: update pyproject.toml dependencies` |
| `chore:` | Обслуживание кода | `chore: update pre-commit hooks` |
| `ci:` | Настройка CI/CD | `ci: add GitHub Actions workflow` |
| `docs:` | Обновление документации | `docs: update contributing guide` |
| `refactor:` | Рефакторинг кода | `refactor: optimize search service` |
| `style:` | Изменения стиля кода | `style: format with ruff` |
| `test:` | Добавление/изменение тестов | `test: add unit tests for gateway` |

**Пример хорошего коммита:**
```bash
git commit -m "feat: add rate limiting to API gateway

- Implement token bucket algorithm
- Add configurable rate limits per endpoint
- Update documentation with rate limit headers"
```

### Процесс Pull Request

Мы используем ветвление **GitHub Flow**:

- Основная стабильная ветка — `main`.
- Для каждой задачи создавайте отдельную ветку с префиксом по типу:
  - `feature/TASK-X-description` — для новой функциональности.
  - `bugfix/TASK-X-description` — для исправления багов.
  - `hotfix/description` — для критических исправлений.

**Запрещено** коммитить напрямую в `main` — все изменения принимаются только через Pull Request (PR).

### Процесс PR:

1. Создайте ветку от `main`:
```bash
git checkout -b feature/add-rate-limiting
```

2. Внесите изменения, соблюдая принятые стандарты архитектуры и типизации.

3. Убедитесь, что локальные тесты и линтеры проходят успешно:
```bash
uv run ruff check . && uv run ruff format . && uv run mypy . && uv run pytest
```

4. Запушьте ветку в репозиторий и откройте Pull Request в GitHub:
```bash
git push origin feature/add-rate-limiting
```

5. В описании PR укажите:
   - Краткое описание внесённых изменений
   - Ссылку на связанный Issue / задачу
   - Скриншоты или примеры API-запросов (если применимо)
   - Checklist выполненных задач

### Шаблон описания PR:

```markdown
## Описание
Краткое описание изменений

## Связанные задачи
- Closes #123
- Related to #456

## Изменения
- [ ] Новая функциональность
- [ ] Исправление бага
- [ ] Обновление документации

## Тестирование
- [ ] Unit-тесты добавлены/обновлены
- [ ] E2E-тесты проходят локально
- [ ] Ручное тестирование выполнено

## Дополнительная информация
Любые дополнительные сведения, скриншоты, примеры API-запросов
```

---

## Полезные ссылки

- [Документация uv](https://docs.astral.sh/uv/)
- [Документация FastAPI](https://fastapi.tiangolo.com/)
- [Документация Qdrant](https://qdrant.tech/documentation/)
- [Документация Docker Compose](https://docs.docker.com/compose/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [PEP 8 — Style Guide](https://peps.python.org/pep-0008/)

---

## Вопросы и поддержка

Если у вас возникли вопросы по разработке, создайте Issue или обратитесь к команде в чате проекта.

**Благодарим за ваш вклад в развитие RAG Agent!** 🚀



6. Дождитесь прохождения автоматических CI-пайплайнов (`ci.yml`) и результатов code review. После аппрува изменения будут смержены в основную ветку.
