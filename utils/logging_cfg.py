"""
Настройка логирования проекта.

Централизованная конфигурация logging для всего приложения.
"""

import logging
import sys

from core.constants import LOG_DATE_FORMAT, LOG_FORMAT


def setup_logger(
    verbose: bool = False,
    log_file: str | None = None,
) -> logging.Logger:
    """
    Настраивает и возвращает корневой логгер проекта.

    Args:
        verbose: Если True — уровень логирования DEBUG, иначе WARNING.
        log_file: Путь к файлу для записи логов (опционально).

    Returns:
        Настроенный логгер с handlers для stdout и опционально файла.

    Example:
        >>> logger = setup_logger(verbose=True)
        >>> logger.debug("debug message")  # Выведется в stdout
        >>> logger.warning("warning message")  # Выведется в stdout
    """
    # Определяем уровень логирования
    level = logging.DEBUG if verbose else logging.WARNING

    # Получаем корневой логгер проекта
    logger = logging.getLogger("disk_analyzer")
    logger.setLevel(level)

    # Очищаем существующие handlers (для избежания дублирования)
    logger.handlers.clear()

    # Форматтер для всех handlers
    formatter = logging.Formatter(
        fmt=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
    )

    # Handler для stdout — всегда добавляем
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler для файла — только если передан log_file
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (OSError, PermissionError) as e:
            # Если не удалось создать файл лога — логируем предупреждение
            # и продолжаем работу только с консольным handler
            console_handler.setLevel(logging.WARNING)
            logger.warning(f"Failed to create log file '{log_file}': {e}")

    return logger


if __name__ == "__main__":
    # Тесты для самопроверки модуля
    print("=== Тест 1: verbose=True (DEBUG) ===")
    logger_debug = setup_logger(verbose=True)
    logger_debug.debug("Debug message (должен видеть)")
    logger_debug.info("Info message (должен видеть)")
    logger_debug.warning("Warning message (должен видеть)")
    logger_debug.error("Error message (должен видеть)")

    print("\n=== Тест 2: verbose=False (WARNING) ===")
    logger_warning = setup_logger(verbose=False)
    logger_warning.debug("Debug message (НЕ должен видеть)")
    logger_warning.info("Info message (НЕ должен видеть)")
    logger_warning.warning("Warning message (должен видеть)")
    logger_warning.error("Error message (должен видеть)")

    print("\n=== Тест 3: С записью в файл ===")
    logger_file = setup_logger(verbose=True, log_file="test_logger.log")
    logger_file.info("Message from test (должен видеть в stdout и файле)")

    # Закрываем все handlers чтобы освободить файл
    for handler in logger_file.handlers:
        handler.close()

    print("\n=== Проверка файла test_logger.log ===")
    try:
        with open("test_logger.log", "r", encoding="utf-8") as f:
            print(f.read())
    except FileNotFoundError:
        print("Файл не создан (возможно, нет прав)")

    # Очистка тестового файла
    import os
    import time

    time.sleep(0.1)  # Пауза для освобождения файла

    if os.path.exists("test_logger.log"):
        try:
            os.remove("test_logger.log")
        except (OSError, PermissionError):
            pass  # Файл заблокирован — не критично

    print("\nlogging_cfg: OK")
