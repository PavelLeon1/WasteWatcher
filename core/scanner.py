"""
Рекурсивный сканер файловой системы.

Генератор для обхода директорий с обработкой ошибок доступа.
"""

import logging
import os
import sys
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from core.metrics import calculate_idle_days, calculate_uselessness, format_uselessness
from core.models import FileInfo, ScanStats


def get_file_ctime(stat_result: os.stat_result) -> datetime:
    """
    Получает дату создания файла с учётом платформы.

    На Windows ctime — это время создания.
    На macOS/Linux ctime — время изменения метаданных.
    Для macOS пытаемся получить истинное время рождения (birthtime).

    Args:
        stat_result: Результат os.stat().

    Returns:
        datetime создания файла (или изменения метаданных на Linux).
    """
    # Пытаемся получить birthtime (macOS)
    if hasattr(stat_result, "st_birthtime") and stat_result.st_birthtime is not None:
        return datetime.fromtimestamp(stat_result.st_birthtime)

    # Fallback: используем ctime
    return datetime.fromtimestamp(stat_result.st_ctime)


def build_file_info(
    entry: os.DirEntry[str],
    logger: logging.Logger,
) -> FileInfo | None:
    """
    Строит FileInfo для одного файла.

    Args:
        entry: Запись из os.scandir().
        logger: Логгер для записи ошибок.

    Returns:
        FileInfo или None при ошибке доступа.
    """
    try:
        stat_result = entry.stat(follow_symlinks=False)
    except (PermissionError, OSError) as e:
        logger.warning(f"Skipped {entry.path}: {e}")
        return None

    try:
        # Получаем даты
        atime = datetime.fromtimestamp(stat_result.st_atime)
        mtime = datetime.fromtimestamp(stat_result.st_mtime)
        ctime = get_file_ctime(stat_result)

        # Размер
        size_bytes = stat_result.st_size

        # Расширение (нижний регистр)
        _, ext = os.path.splitext(entry.name)
        extension = ext.lower() if ext else ""

        # Вычисляем метрики
        idle_days = calculate_idle_days(atime)
        uselessness_index = calculate_uselessness(size_bytes, idle_days)
        uselessness_human = format_uselessness(uselessness_index)

        # Импортируем здесь для избежания циклического импорта
        from utils.formatting import human_readable_size

        size_human = human_readable_size(size_bytes)

        return FileInfo(
            path=os.path.abspath(entry.path),
            name=entry.name,
            extension=extension,
            size_bytes=size_bytes,
            size_human=size_human,
            atime=atime,
            mtime=mtime,
            ctime=ctime,
            idle_days=idle_days,
            uselessness_index=uselessness_index,
            uselessness_human=uselessness_human,
            uselessness_level="low",  # Будет пересчитано в metrics.py
        )

    except (PermissionError, OSError) as e:
        logger.warning(f"Skipped {entry.path}: {e}")
        return None


def scan_directory(
    root: Path,
    exclude_dirs: set[str] | None = None,
    max_depth: int | None = None,
    no_hidden: bool = False,
    logger: logging.Logger | None = None,
    stats: ScanStats | None = None,
    current_depth: int = 0,
) -> Iterable[FileInfo]:
    """
    Рекурсивно сканирует директорию и возвращает FileInfo через генератор.

    Args:
        root: Корневая директория для сканирования.
        exclude_dirs: Множество путей директорий для исключения.
        max_depth: Максимальная глубина обхода (None = без ограничений).
        no_hidden: Игнорировать скрытые файлы и директории.
        logger: Логгер для записи ошибок.
        stats: Объект статистики для обновления.
        current_depth: Текущая глубина (для рекурсии).

    Yields:
        FileInfo для каждого найденного файла.

    Example:
        >>> from pathlib import Path
        >>> import logging
        >>> logger = logging.getLogger(__name__)
        >>> stats = ScanStats()
        >>> files = list(scan_directory(Path("."), logger=logger, stats=stats))
    """
    if logger is None:
        logger = logging.getLogger("disk_analyzer")

    if stats is None:
        stats = ScanStats()

    if exclude_dirs is None:
        exclude_dirs = set()

    # Guard clause: превышена максимальная глубина
    if max_depth is not None and current_depth > max_depth:
        return

    # Нормализуем корневой путь
    root_path = str(root.resolve())

    # Проверяем, не исключена ли эта директория
    if root_path in exclude_dirs:
        logger.debug(f"Excluded directory: {root_path}")
        return

    try:
        entries = list(os.scandir(root_path))
    except (PermissionError, OSError) as e:
        logger.warning(f"Skipped directory {root_path}: {e}")
        stats.skipped_files += 1
        return

    # Сортируем: сначала директории, потом файлы (для предсказуемого порядка)
    dirs = []
    files = []

    for entry in entries:
        try:
            # Проверка на скрытые файлы/директории
            if no_hidden and entry.name.startswith("."):
                continue

            # Проверка на симлинки — не следуем им
            if entry.is_symlink():
                continue

            if entry.is_dir(follow_symlinks=False):
                dirs.append(entry)
            elif entry.is_file(follow_symlinks=False):
                files.append(entry)
        except (PermissionError, OSError) as e:
            logger.warning(f"Skipped {entry.path}: {e}")
            stats.skipped_files += 1

    # Обрабатываем файлы в текущей директории
    for entry in files:
        file_info = build_file_info(entry, logger)
        if file_info is not None:
            stats.total_files += 1
            stats.total_size_bytes += file_info.size_bytes
            yield file_info

    # Рекурсивно обрабатываем поддиректории
    for entry in dirs:
        dir_path = entry.path
        if dir_path in exclude_dirs:
            logger.debug(f"Excluded directory: {dir_path}")
            continue

        # Обновляем статистику по директориям
        try:
            dir_stat = entry.stat(follow_symlinks=False)
            # Размер директории пока не считаем — будет вычислено в ScanStats
        except (PermissionError, OSError):
            pass

        # Рекурсивный вызов
        yield from scan_directory(
            root=Path(dir_path),
            exclude_dirs=exclude_dirs,
            max_depth=max_depth,
            no_hidden=no_hidden,
            logger=logger,
            stats=stats,
            current_depth=current_depth + 1,
        )


if __name__ == "__main__":
    # Тесты для самопроверки модуля
    import tempfile

    # Настраиваем логгер для тестов
    from utils.logging_cfg import setup_logger

    test_logger = setup_logger(verbose=True)

    # Создаём временную директорию с тестовой структурой
    with tempfile.TemporaryDirectory() as tmpdir:
        # Создаём файлы
        test_file1 = os.path.join(tmpdir, "test1.txt")
        test_file2 = os.path.join(tmpdir, "test2.log")
        subdir = os.path.join(tmpdir, "subdir")
        os.makedirs(subdir)
        test_file3 = os.path.join(subdir, "nested.txt")

        with open(test_file1, "w") as f:
            f.write("Hello, World!")  # 13 bytes

        with open(test_file2, "w") as f:
            f.write("Log content" * 100)  # 1100 bytes

        with open(test_file3, "w") as f:
            f.write("Nested file")  # 11 bytes

        # Тест сканирования
        stats = ScanStats()
        files = list(
            scan_directory(
                root=Path(tmpdir),
                exclude_dirs=set(),
                max_depth=None,
                no_hidden=False,
                logger=test_logger,
                stats=stats,
            )
        )

        # Проверки
        assert len(files) == 3, f"Expected 3 files, got {len(files)}"
        assert stats.total_files == 3
        assert stats.total_size_bytes == 13 + 1100 + 11

        # Проверка имён файлов
        names = {f.name for f in files}
        assert names == {"test1.txt", "test2.log", "nested.txt"}

        # Проверка путей
        paths = {os.path.basename(f.path) for f in files}
        assert paths == names

        # Проверка расширений
        extensions = {f.extension for f in files}
        assert extensions == {".txt", ".log"}

        # Проверка метрик
        for f in files:
            assert f.idle_days >= 0
            assert f.uselessness_index >= 0
            assert "MB·days" in f.uselessness_human

    # Тест с exclude_dirs
    with tempfile.TemporaryDirectory() as tmpdir:
        excluded_dir = os.path.join(tmpdir, "excluded")
        os.makedirs(excluded_dir)
        with open(os.path.join(excluded_dir, "skip.txt"), "w") as f:
            f.write("skip")

        with open(os.path.join(tmpdir, "keep.txt"), "w") as f:
            f.write("keep")

        stats = ScanStats()
        files = list(
            scan_directory(
                root=Path(tmpdir),
                exclude_dirs={excluded_dir},
                logger=test_logger,
                stats=stats,
            )
        )

        assert len(files) == 1
        assert files[0].name == "keep.txt"

    # Тест с no_hidden
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, ".hidden"), "w") as f:
            f.write("hidden")
        with open(os.path.join(tmpdir, "visible.txt"), "w") as f:
            f.write("visible")

        stats = ScanStats()
        files = list(
            scan_directory(
                root=Path(tmpdir),
                no_hidden=True,
                logger=test_logger,
                stats=stats,
            )
        )

        assert len(files) == 1
        assert files[0].name == "visible.txt"

    # Тест с max_depth
    with tempfile.TemporaryDirectory() as tmpdir:
        level1 = os.path.join(tmpdir, "level1")
        level2 = os.path.join(level1, "level2")
        os.makedirs(level2)

        with open(os.path.join(tmpdir, "root.txt"), "w") as f:
            f.write("root")
        with open(os.path.join(level1, "l1.txt"), "w") as f:
            f.write("l1")
        with open(os.path.join(level2, "l2.txt"), "w") as f:
            f.write("l2")

        stats = ScanStats()
        files_depth1 = list(
            scan_directory(
                root=Path(tmpdir),
                max_depth=1,
                logger=test_logger,
                stats=stats,
            )
        )

        # Должны быть root.txt и l1.txt, но не l2.txt
        names = {f.name for f in files_depth1}
        assert "root.txt" in names
        assert "l1.txt" in names
        assert "l2.txt" not in names

    print("scanner: OK")
