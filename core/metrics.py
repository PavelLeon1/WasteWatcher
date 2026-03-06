"""
Вычисление метрик: индекс бесполезности, дни простоя.

Функции для расчёта uselessness_index и связанных величин.
"""

from datetime import datetime

from core.constants import (
    BYTES_IN_MB,
    USELESS_LOW_THRESHOLD,
    USELESS_MED_THRESHOLD,
)
from core.models import FileInfo


def calculate_idle_days(atime: datetime) -> int:
    """
    Вычисляет количество дней простоя файла.

    Args:
        atime: Дата последнего доступа к файлу.

    Returns:
        Количество дней с момента последнего доступа (неотрицательное целое).

    Example:
        >>> from datetime import datetime, timedelta
        >>> week_ago = datetime.now() - timedelta(days=7)
        >>> calculate_idle_days(week_ago)
        7
    """
    delta = datetime.now() - atime
    return max(0, delta.days)


def calculate_uselessness(size_bytes: int, idle_days: int) -> float:
    """
    Вычисляет индекс бесполезности файла.

    Формула: size_bytes × idle_days

    Args:
        size_bytes: Размер файла в байтах.
        idle_days: Количество дней простоя.

    Returns:
        Индекс бесполезности (float).

    Example:
        >>> calculate_uselessness(1_048_576, 30)
        31457280.0
    """
    return float(size_bytes * idle_days)


def format_uselessness(value: float) -> str:
    """
    Форматирует индекс бесполезности в человекочитаемый вид.

    Делит значение на BYTES_IN_MB и возвращает строку формата "N.NN MB·days".

    Args:
        value: Индекс бесполезности (size_bytes × idle_days).

    Returns:
        Человекочитаемая строка, например "30.00 MB·days".

    Example:
        >>> format_uselessness(31_457_280.0)
        '30.00 MB·days'
    """
    mb_days = value / BYTES_IN_MB
    return f"{mb_days:.2f} MB·days"


def assign_uselessness_levels(
    files: list[FileInfo],
    low_q: float = USELESS_LOW_THRESHOLD,
    high_q: float = USELESS_MED_THRESHOLD,
) -> list[FileInfo]:
    """
    Проставляет уровни бесполезности файлам на основе квантилей.

    Распределяет файлы по уровням:
    - "low" — нижние 33% (менее бесполезные)
    - "medium" — средние 33-66%
    - "high" — верхние 33% (наиболее бесполезные)

    Args:
        files: Список файлов для анализа (мутируется in-place).
        low_q: Порог низкого уровня (по умолчанию 0.33).
        high_q: Порог высокого уровня (по умолчанию 0.66).

    Returns:
        Тот же список файлов с проставленными uselessness_level.

    Example:
        >>> files = [
        ...     FileInfo(path="/1", name="1", extension="", size_bytes=100,
        ...              size_human="100 B", atime=datetime.now(),
        ...              mtime=datetime.now(), ctime=datetime.now(),
        ...              idle_days=1, uselessness_index=100.0,
        ...              uselessness_human="0.00 MB·days"),
        ...     FileInfo(path="/2", name="2", extension="", size_bytes=1000000,
        ...              size_human="1.00 MB", atime=datetime.now(),
        ...              mtime=datetime.now(), ctime=datetime.now(),
        ...              idle_days=100, uselessness_index=100_000_000.0,
        ...              uselessness_human="95.37 MB·days"),
        ... ]
        >>> assign_uselessness_levels(files)
        >>> files[0].uselessness_level  # Файл с низким индексом
        'low'
        >>> files[1].uselessness_level  # Файл с высоким индексом
        'high'
    """
    if not files:
        return files

    n = len(files)

    # Сортируем файлы по индексу бесполезности для вычисления квантилей
    sorted_files = sorted(files, key=lambda f: f.uselessness_index)

    # Вычисляем индексы квантилей
    # Для малого числа файлов гарантируем хотя бы по одному в каждой категории
    if n <= 3:
        # Для 1-3 файлов: первый → low, второй → medium, третий → high
        for i, file in enumerate(sorted_files):
            if i == 0:
                file.uselessness_level = "low"
            elif i == 1:
                file.uselessness_level = "medium"
            else:
                file.uselessness_level = "high"
        return files

    # Для большего числа файлов используем квантили
    low_idx = int(n * low_q)
    high_idx = int(n * high_q)

    # Гарантируем корректные индексы
    low_idx = max(0, min(low_idx, n - 2))
    high_idx = max(low_idx + 1, min(high_idx, n - 1))

    # Получаем пороговые значения
    low_threshold = sorted_files[low_idx].uselessness_index
    high_threshold = sorted_files[high_idx].uselessness_index

    # Проставляем уровни
    for file in files:
        if file.uselessness_index <= low_threshold:
            file.uselessness_level = "low"
        elif file.uselessness_index <= high_threshold:
            file.uselessness_level = "medium"
        else:
            file.uselessness_level = "high"

    return files


def compute_file_metrics(file_info: FileInfo) -> FileInfo:
    """
    Вычисляет и проставляет метрики для одного файла.

    Args:
        file_info: FileInfo с базовыми данными (atime, size_bytes).

    Returns:
        Тот же FileInfo с заполненными idle_days, uselessness_index,
        uselessness_human.
    """
    file_info.idle_days = calculate_idle_days(file_info.atime)
    file_info.uselessness_index = calculate_uselessness(
        file_info.size_bytes, file_info.idle_days
    )
    file_info.uselessness_human = format_uselessness(file_info.uselessness_index)
    return file_info


if __name__ == "__main__":
    # Тесты для самопроверки модуля
    from datetime import datetime, timedelta

    # Тест calculate_idle_days
    now = datetime.now()
    week_ago = now - timedelta(days=7)
    assert calculate_idle_days(now) == 0
    assert calculate_idle_days(week_ago) == 7

    # Тест на отрицательное значение (если atime в будущем)
    future = now + timedelta(days=5)
    assert calculate_idle_days(future) == 0  # guard clause

    # Тест calculate_uselessness
    assert calculate_uselessness(1_048_576, 30) == 31_457_280.0
    assert calculate_uselessness(0, 100) == 0.0
    assert calculate_uselessness(1000, 0) == 0.0

    # Тест format_uselessness
    assert format_uselessness(31_457_280.0) == "30.00 MB·days"
    assert format_uselessness(0.0) == "0.00 MB·days"
    assert format_uselessness(1_048_576.0) == "1.00 MB·days"

    # Тест assign_uselessness_levels с малым числом файлов (n <= 3)
    files_small = [
        FileInfo(
            path="/file1.log",
            name="file1.log",
            extension=".log",
            size_bytes=100,
            size_human="100 B",
            atime=now,
            mtime=now,
            ctime=now,
            idle_days=0,
            uselessness_index=0.0,
            uselessness_human="0.00 MB·days",
        ),
        FileInfo(
            path="/file2.log",
            name="file2.log",
            extension=".log",
            size_bytes=1000,
            size_human="1000 B",
            atime=week_ago,
            mtime=week_ago,
            ctime=week_ago,
            idle_days=7,
            uselessness_index=7000.0,
            uselessness_human="0.01 MB·days",
        ),
        FileInfo(
            path="/file3.log",
            name="file3.log",
            extension=".log",
            size_bytes=1_000_000,
            size_human="1.00 MB",
            atime=now - timedelta(days=100),
            mtime=now - timedelta(days=100),
            ctime=now - timedelta(days=100),
            idle_days=100,
            uselessness_index=100_000_000.0,
            uselessness_human="95.37 MB·days",
        ),
    ]

    assign_uselessness_levels(files_small)

    # file1 должен быть low (наименьший индекс)
    assert files_small[0].uselessness_level == "low", f"Got {files_small[0].uselessness_level}"
    # file2 должен быть medium
    assert files_small[1].uselessness_level == "medium", f"Got {files_small[1].uselessness_level}"
    # file3 должен быть high (наибольший индекс)
    assert files_small[2].uselessness_level == "high", f"Got {files_small[2].uselessness_level}"

    # Тест assign_uselessness_levels с большим числом файлов
    files_large = []
    for i in range(10):
        files_large.append(
            FileInfo(
                path=f"/file{i}.log",
                name=f"file{i}.log",
                extension=".log",
                size_bytes=100 * (i + 1),
                size_human=f"{100 * (i + 1)} B",
                atime=now - timedelta(days=i),
                mtime=now - timedelta(days=i),
                ctime=now - timedelta(days=i),
                idle_days=i,
                uselessness_index=100 * (i + 1) * i,
                uselessness_human=f"{100 * (i + 1) * i / BYTES_IN_MB:.2f} MB·days",
            )
        )

    assign_uselessness_levels(files_large)
    levels = [f.uselessness_level for f in files_large]
    assert "low" in levels
    assert "medium" in levels
    assert "high" in levels

    # Тест compute_file_metrics
    test_file = FileInfo(
        path="/test.log",
        name="test.log",
        extension=".log",
        size_bytes=2_097_152,
        size_human="2.00 MB",
        atime=week_ago,
        mtime=week_ago,
        ctime=week_ago,
        idle_days=0,  # Будет перезаписано
        uselessness_index=0.0,  # Будет перезаписано
        uselessness_human="",  # Будет перезаписано
    )

    compute_file_metrics(test_file)
    assert test_file.idle_days == 7
    assert test_file.uselessness_index == 2_097_152 * 7
    assert "MB·days" in test_file.uselessness_human

    print("metrics: OK")
