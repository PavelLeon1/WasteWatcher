"""
Конвейер фильтрации файлов.

Composable pipeline для применения правил фильтрации.
"""

from collections.abc import Callable, Iterable

from core.models import FileInfo

# Тип для функции-фильтра
FileFilter = Callable[[FileInfo], bool]


def min_size_filter(min_bytes: int) -> FileFilter:
    """
    Создаёт фильтр по минимальному размеру файла.

    Args:
        min_bytes: Минимальный размер в байтах.

    Returns:
        Функция-фильтр, возвращающая True для файлов >= min_bytes.

    Example:
        >>> filter_func = min_size_filter(1024)
        >>> # filter_func(file) вернёт True если file.size_bytes >= 1024
    """

    def _filter(file: FileInfo) -> bool:
        return file.size_bytes >= min_bytes

    return _filter


def extension_filter(extensions: list[str]) -> FileFilter:
    """
    Создаёт фильтр по расширениям файлов.

    Args:
        extensions: Список расширений для включения (например, [".log", ".tmp"]).
                    Сравнение регистронезависимое.

    Returns:
        Функция-фильтр, возвращающая True для файлов с указанными расширениями.

    Example:
        >>> filter_func = extension_filter([".log", ".tmp"])
        >>> # filter_func(file) вернёт True если file.extension в [".log", ".tmp"]
    """
    # Нормализуем расширения к нижнему регистру
    normalized = [ext.lower() for ext in extensions]

    def _filter(file: FileInfo) -> bool:
        return file.extension.lower() in normalized

    return _filter


def min_idle_filter(min_days: int) -> FileFilter:
    """
    Создаёт фильтр по минимальному времени простоя.

    Args:
        min_days: Минимальное количество дней простоя.

    Returns:
        Функция-фильтр, возвращающая True для файлов с idle_days >= min_days.

    Example:
        >>> filter_func = min_idle_filter(30)
        >>> # filter_func(file) вернёт True если file.idle_days >= 30
    """

    def _filter(file: FileInfo) -> bool:
        return file.idle_days >= min_days

    return _filter


def exclude_hidden_filter() -> FileFilter:
    """
    Создаёт фильтр, исключающий скрытые файлы и директории.

    Скрытыми считаются файлы/директории, имя которых начинается с ".".

    Returns:
        Функция-фильтр, возвращающая True для не-скрытых файлов.

    Example:
        >>> filter_func = exclude_hidden_filter()
        >>> # filter_func(file) вернёт False если file.name начинается с "."
    """

    def _filter(file: FileInfo) -> bool:
        return not file.name.startswith(".")

    return _filter


def max_depth_filter(max_depth: int) -> FileFilter:
    """
    Создаёт фильтр по максимальной глубине вложенности.

    Args:
        max_depth: Максимальная глубина (количество уровней вложенности).

    Returns:
        Функция-фильтр, возвращающая True для файлов на глубине <= max_depth.

    Note:
        Этот фильтр требует, чтобы у FileInfo было поле depth.
        В текущей реализации используется как заглушка для совместимости.
    """

    def _filter(file: FileInfo) -> bool:
        # Глубина определяется количеством разделителей пути
        from pathlib import Path

        depth = len(Path(file.path).parts) - 1
        return depth <= max_depth

    return _filter


def apply_filters(
    files: Iterable[FileInfo],
    filters: list[FileFilter],
) -> Iterable[FileInfo]:
    """
    Применяет все фильтры последовательно (AND-логика).

    Функция-генератор для экономии памяти — не создаёт промежуточных списков.

    Args:
        files: Итерируемый объект с FileInfo.
        filters: Список фильтров для применения.

    Yields:
        FileInfo, прошедшие все фильтры.

    Example:
        >>> filters = [min_size_filter(1024), extension_filter([".log"])]
        >>> filtered = apply_filters(files, filters)
        >>> for file in filtered:
        ...     print(file.name)
    """
    if not filters:
        # Если фильтров нет, возвращаем все файлы
        yield from files
        return

    for file in files:
        if all(f(file) for f in filters):
            yield file


def build_filter_pipeline(
    min_size: int | None = None,
    extensions: list[str] | None = None,
    min_idle: int | None = None,
    exclude_hidden: bool = False,
    max_depth: int | None = None,
) -> list[FileFilter]:
    """
    Строит конвейер фильтров из параметров.

    Args:
        min_size: Минимальный размер файла в байтах (или None).
        extensions: Список расширений для включения (или None).
        min_idle: Минимальный простой в днях (или None).
        exclude_hidden: Исключать скрытые файлы.
        max_depth: Максимальная глубина вложенности (или None).

    Returns:
        Список функций-фильтров для передачи в apply_filters.

    Example:
        >>> pipeline = build_filter_pipeline(
        ...     min_size=1024,
        ...     extensions=[".log", ".tmp"],
        ...     min_idle=30,
        ... )
        >>> filtered = apply_filters(files, pipeline)
    """
    filters: list[FileFilter] = []

    if min_size is not None and min_size > 0:
        filters.append(min_size_filter(min_size))

    if extensions:
        filters.append(extension_filter(extensions))

    if min_idle is not None and min_idle > 0:
        filters.append(min_idle_filter(min_idle))

    if exclude_hidden:
        filters.append(exclude_hidden_filter())

    if max_depth is not None:
        filters.append(max_depth_filter(max_depth))

    return filters


if __name__ == "__main__":
    # Тесты для самопроверки модуля
    from datetime import datetime, timedelta

    now = datetime.now()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # Создаём тестовые файлы
    test_files = [
        FileInfo(
            path="/small.log",
            name="small.log",
            extension=".log",
            size_bytes=512,
            size_human="512 B",
            atime=now,
            mtime=now,
            ctime=now,
            idle_days=0,
            uselessness_index=0.0,
            uselessness_human="0.00 MB·days",
        ),
        FileInfo(
            path="/large.log",
            name="large.log",
            extension=".log",
            size_bytes=2048,
            size_human="2.00 KB",
            atime=month_ago,
            mtime=month_ago,
            ctime=month_ago,
            idle_days=30,
            uselessness_index=2048 * 30,
            uselessness_human="0.06 MB·days",
        ),
        FileInfo(
            path="/hidden.tmp",
            name=".hidden.tmp",
            extension=".tmp",
            size_bytes=1024,
            size_human="1.00 KB",
            atime=week_ago,
            mtime=week_ago,
            ctime=week_ago,
            idle_days=7,
            uselessness_index=1024 * 7,
            uselessness_human="0.01 MB·days",
        ),
        FileInfo(
            path="/data.txt",
            name="data.txt",
            extension=".txt",
            size_bytes=5000,
            size_human="4.88 KB",
            atime=month_ago,
            mtime=month_ago,
            ctime=month_ago,
            idle_days=30,
            uselessness_index=5000 * 30,
            uselessness_human="0.14 MB·days",
        ),
    ]

    # Тест min_size_filter
    size_filter = min_size_filter(1024)
    assert size_filter(test_files[0]) is False  # 512 < 1024
    assert size_filter(test_files[1]) is True  # 2048 >= 1024
    assert size_filter(test_files[3]) is True  # 5000 >= 1024

    # Тест extension_filter
    ext_filter = extension_filter([".log"])
    assert ext_filter(test_files[0]) is True
    assert ext_filter(test_files[3]) is False

    # Тест min_idle_filter
    idle_filter = min_idle_filter(30)
    assert idle_filter(test_files[0]) is False  # 0 < 30
    assert idle_filter(test_files[1]) is True  # 30 >= 30
    assert idle_filter(test_files[3]) is True  # 30 >= 30

    # Тест exclude_hidden_filter
    hidden_filter = exclude_hidden_filter()
    assert hidden_filter(test_files[0]) is True
    assert hidden_filter(test_files[2]) is False  # .hidden.tmp

    # Тест apply_filters с несколькими фильтрами
    filters = [min_size_filter(1024), extension_filter([".log"])]
    filtered = list(apply_filters(test_files, filters))
    assert len(filtered) == 1
    assert filtered[0].name == "large.log"

    # Тест build_filter_pipeline
    pipeline = build_filter_pipeline(
        min_size=1000,
        extensions=[".log", ".txt"],
        min_idle=7,
        exclude_hidden=True,
    )
    filtered = list(apply_filters(test_files, pipeline))
    assert len(filtered) == 2
    assert filtered[0].name == "large.log"
    assert filtered[1].name == "data.txt"

    # Тест пустого списка фильтров
    all_files = list(apply_filters(test_files, []))
    assert len(all_files) == len(test_files)

    print("filters: OK")
