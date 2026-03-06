"""
Утилиты форматирования данных.

Функции для человеко-читаемого отображения размеров, дат, путей.
"""

from datetime import datetime

from core.constants import (
    BYTES_IN_GB,
    BYTES_IN_KB,
    BYTES_IN_MB,
    DATE_FORMAT,
    MAX_PATH_DISPLAY,
)


def human_readable_size(size_bytes: int) -> str:
    """
    Преобразует размер в байтах в человекочитаемый формат.

    Args:
        size_bytes: Размер в байтах (неотрицательное целое число).

    Returns:
        Строка формата "0 B", "512 B", "1.23 KB", "45.67 MB", "1.23 GB".

    Examples:
        >>> human_readable_size(0)
        '0 B'
        >>> human_readable_size(1023)
        '1023 B'
        >>> human_readable_size(1024)
        '1.00 KB'
        >>> human_readable_size(1_048_576)
        '1.00 MB'
    """
    if size_bytes < 0:
        raise ValueError(f"size_bytes must be non-negative, got {size_bytes}")

    if size_bytes < BYTES_IN_KB:
        return f"{size_bytes} B"
    elif size_bytes < BYTES_IN_MB:
        return f"{size_bytes / BYTES_IN_KB:.2f} KB"
    elif size_bytes < BYTES_IN_GB:
        return f"{size_bytes / BYTES_IN_MB:.2f} MB"
    else:
        return f"{size_bytes / BYTES_IN_GB:.2f} GB"


def format_date(dt: datetime | None) -> str:
    """
    Форматирует дату/время в строку согласно DATE_FORMAT.

    Args:
        dt: Объект datetime или None.

    Returns:
        Отформатированная строка даты или "—" если dt is None.

    Examples:
        >>> from datetime import datetime
        >>> format_date(datetime(2025, 1, 15, 10, 30))
        '2025-01-15 10:30'
        >>> format_date(None)
        '—'
    """
    if dt is None:
        return "—"
    return dt.strftime(DATE_FORMAT)


def truncate_path(path: str, max_len: int = MAX_PATH_DISPLAY) -> str:
    """
    Обрезает длинный путь, оставляя конец (имя файла важнее).

    Args:
        path: Полный путь к файлу или директории.
        max_len: Максимальная длина строки для отображения.

    Returns:
        Путь, обрезанный до max_len символов с префиксом "..." если необходимо.

    Examples:
        >>> truncate_path("C:/short/path.txt", 80)
        'C:/short/path.txt'
        >>> truncate_path("C:/very/long/path/that/exceeds/limit/file.txt", 20)
        '...ds/limit/file.txt'
    """
    if len(path) <= max_len:
        return path
    # Оставляем только конец пути, добавляем префикс "..."
    return f"...{path[-(max_len - 3):]}"


def parse_size_arg(size_str: str) -> int:
    """
    Парсит строку размера из CLI-аргумента в байты.

    Поддерживает суффиксы: B, KB, MB, GB (регистронезависимо).

    Args:
        size_str: Строка формата "10B", "5KB", "2MB", "1GB".

    Returns:
        Размер в байтах (целое число).

    Raises:
        ValueError: Если формат строки некорректен.

    Examples:
        >>> parse_size_arg("10B")
        10
        >>> parse_size_arg("5KB")
        5120
        >>> parse_size_arg("2MB")
        2097152
        >>> parse_size_arg("1GB")
        1073741824
    """
    size_str = size_str.strip().upper()

    if not size_str:
        raise ValueError("Size argument cannot be empty")

    # Определяем суффикс и числовое значение
    if size_str.endswith("GB"):
        multiplier = BYTES_IN_GB
        number_part = size_str[:-2]
    elif size_str.endswith("MB"):
        multiplier = BYTES_IN_MB
        number_part = size_str[:-2]
    elif size_str.endswith("KB"):
        multiplier = BYTES_IN_KB
        number_part = size_str[:-2]
    elif size_str.endswith("B"):
        multiplier = 1
        number_part = size_str[:-1]
    else:
        raise ValueError(
            f"Invalid size format: '{size_str}'. "
            f"Expected format: number followed by B, KB, MB, or GB (e.g., '10B', '5KB', '2MB', '1GB')."
        )

    try:
        number = int(number_part)
    except ValueError:
        raise ValueError(
            f"Invalid number in size argument: '{number_part}'. "
            f"Expected integer value."
        )

    if number < 0:
        raise ValueError(f"Size cannot be negative: {number}")

    return number * multiplier


if __name__ == "__main__":
    # Тесты для самопроверки модуля
    assert human_readable_size(0) == "0 B"
    assert human_readable_size(1023) == "1023 B"
    assert human_readable_size(1024) == "1.00 KB"
    assert human_readable_size(1_048_576) == "1.00 MB"
    assert human_readable_size(1_073_741_824) == "1.00 GB"

    assert format_date(None) == "—"

    assert truncate_path("C:/short/path.txt", 80) == "C:/short/path.txt"
    truncated = truncate_path("C:/very/long/path/that/exceeds/limit/file.txt", 20)
    assert truncated == "...ds/limit/file.txt"

    assert parse_size_arg("10B") == 10
    assert parse_size_arg("5KB") == 5_120
    assert parse_size_arg("2MB") == 2_097_152
    assert parse_size_arg("1GB") == 1_073_741_824

    # Проверка обработки ошибок
    try:
        parse_size_arg("invalid")
        assert False, "Expected ValueError"
    except ValueError:
        pass

    try:
        parse_size_arg("-5KB")
        assert False, "Expected ValueError"
    except ValueError:
        pass

    print("formatting: OK")
