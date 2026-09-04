from loguru import logger

from shared import BaseConfig, setup_logging

config = BaseConfig(service="gateway")

setup_logging(config=config)


# 3. Используем logger в любом месте проекта
def main() -> None:
    logger.info("Приложение запускается...")

    try:
        # Имитация работы
        1 / 0
    except ZeroDivisionError:
        logger.exception("Произошла ошибка при вычислениях")


if __name__ == "__main__":
    main()
