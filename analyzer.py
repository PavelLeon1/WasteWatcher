"""
Disk Space Analyzer — точка входа CLI.

Рекурсивный анализ дискового пространства с построением
интерактивного HTML-отчёта, отсортированного по индексу бесполезности файлов.
"""

import argparse
import sys
import time
from pathlib import Path

from core.filters import build_filter_pipeline
from core.metrics import assign_uselessness_levels, compute_file_metrics
from core.models import ScanStats
from core.scanner import scan_directory
from report.builder import generate_report
from utils.formatting import human_readable_size, parse_size_arg
from utils.logging_cfg import setup_logger


def parse_args() -> argparse.Namespace:
    """
    Парсит аргументы командной строки.

    Returns:
        Пространство имён с аргументами.
    """
    parser = argparse.ArgumentParser(
        prog="analyzer.py",
        description="Disk Space Analyzer — рекурсивный анализ дискового пространства "
                    "с построением интерактивного HTML-отчёта.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s ~/Documents --output report.html
  %(prog)s /var/log --min-size 1MB --min-idle 30 --output old_logs.html
  %(prog)s /home --exclude /home/.cache /home/.local --depth 4 --verbose
  %(prog)s /data --json raw_data.json --output report.html
        """,
    )

    # Обязательный аргумент — путь для сканирования
    parser.add_argument(
        "path",
        type=str,
        help="Путь к директории для сканирования",
    )

    # Опции вывода
    parser.add_argument(
        "--output",
        type=str,
        default="report.html",
        help="Путь к выходному HTML-файлу (по умолчанию: report.html)",
    )

    parser.add_argument(
        "--json",
        type=str,
        default=None,
        help="Путь к JSON-файлу для сохранения сырых данных (опционально)",
    )

    # Фильтры
    parser.add_argument(
        "--min-size",
        type=str,
        default=None,
        help="Минимальный размер файла (10B, 1KB, 5MB, 2GB)",
    )

    parser.add_argument(
        "--min-idle",
        type=int,
        default=0,
        help="Минимальный простой в днях (по умолчанию: 0)",
    )

    parser.add_argument(
        "--ext",
        type=str,
        nargs="+",
        default=None,
        help="Фильтр по расширениям (.log .tmp .bak)",
    )

    parser.add_argument(
        "--exclude",
        type=str,
        nargs="+",
        default=None,
        help="Исключить директории (пути через пробел)",
    )

    parser.add_argument(
        "--depth",
        type=int,
        default=None,
        help="Максимальная глубина обхода (по умолчанию: без ограничений)",
    )

    parser.add_argument(
        "--top",
        type=int,
        default=0,
        help="Показывать топ N файлов в отчёте (0 = все файлы)",
    )

    # Поведение
    parser.add_argument(
        "--no-hidden",
        action="store_true",
        help="Игнорировать скрытые файлы и папки",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Подробный вывод в консоль",
    )

    return parser.parse_args()


def main() -> int:
    """
    Точка входа приложения.

    Returns:
        Код выхода (0 = успех, 1 = ошибка).
    """
    args = parse_args()

    # Настройка логгера
    logger = setup_logger(verbose=args.verbose)

    # Валидация пути сканирования
    scan_path = Path(args.path).resolve()
    if not scan_path.exists():
        logger.error(f"Путь не существует: {scan_path}")
        return 1

    if not scan_path.is_dir():
        logger.error(f"Путь не является директорией: {scan_path}")
        return 1

    # Построение конвейера фильтров
    min_size_bytes = None
    if args.min_size:
        try:
            min_size_bytes = parse_size_arg(args.min_size)
        except ValueError as e:
            logger.error(f"Некорректный --min-size: {e}")
            return 1

    filters = build_filter_pipeline(
        min_size=min_size_bytes,
        extensions=args.ext,
        min_idle=args.min_idle if args.min_idle > 0 else None,
        exclude_hidden=args.no_hidden,
        max_depth=args.depth,
    )

    # Исключаемые директории
    exclude_dirs = set()
    if args.exclude:
        for exc_path in args.exclude:
            exc = Path(exc_path).resolve()
            if exc.exists():
                exclude_dirs.add(str(exc))
            else:
                logger.warning(f"Исключаемый путь не существует: {exc_path}")

    # Создание объекта статистики
    stats = ScanStats()

    # Запуск сканирования
    logger.info(f"Начало сканирования: {scan_path}")
    start_time = time.perf_counter()

    try:
        # Генератор сканирования
        raw_files = scan_directory(
            root=scan_path,
            exclude_dirs=exclude_dirs,
            max_depth=args.depth,
            no_hidden=args.no_hidden,
            logger=logger,
            stats=stats,
        )

        # Применение фильтров и метрик
        filtered = apply_filters_and_metrics(raw_files, filters)

        # Материализация списка (нужен для квантилей)
        files: list = list(filtered)

    except KeyboardInterrupt:
        logger.warning("Сканирование прервано пользователем")
        return 130

    # Время сканирования
    scan_duration = time.perf_counter() - start_time
    stats.scan_duration_sec = scan_duration

    logger.info(f"Сканирование завершено за {scan_duration:.2f}с")
    logger.info(f"Найдено файлов: {len(files)}")

    if not files:
        logger.warning("Файлы не найдены после применения фильтров")

    # Назначение уровней бесполезности
    assign_uselessness_levels(files)

    # Сортировка по uselessness_index DESC
    files.sort(key=lambda f: f.uselessness_index, reverse=True)

    # Применение --top N
    if args.top and args.top > 0:
        files = files[: args.top]
        logger.info(f"Ограничено до топ-{args.top} файлов")

    # Дополнение статистики
    stats.top_useless = files[:10]
    stats.update_avg_uselessness(files)
    stats.update_ext_distribution(files)
    stats.update_dir_sizes(files)
    stats.update_oldest_file(files)

    # Вывод сводки
    logger.info("=" * 50)
    logger.info(f"Файлов: {len(files)}")
    logger.info(f"Размер: {stats.total_size_human}")
    logger.info(f"Время сканирования: {scan_duration:.2f}с")
    logger.info(f"Пропущено файлов: {stats.skipped_files}")
    if stats.top_useless:
        logger.info(f"Топ бесполезных: {stats.top_useless[0].name} "
                    f"({stats.top_useless[0].uselessness_human})")
    logger.info("=" * 50)

    # Построение отчёта
    output_path = Path(args.output)
    logger.info(f"Генерация отчёта: {output_path}")

    try:
        generate_report(
            files=files,
            stats=stats,
            output_path=output_path,
            scan_path=str(scan_path),
        )
        logger.info(f"Отчёт сохранён: {output_path}")
    except (OSError, PermissionError) as e:
        logger.error(f"Ошибка записи отчёта: {e}")
        return 1

    # Опциональный JSON экспорт
    if args.json:
        json_path = Path(args.json)
        logger.info(f"Сохранение JSON: {json_path}")
        try:
            save_json_report(files, stats, json_path, str(scan_path))
            logger.info(f"JSON сохранён: {json_path}")
        except (OSError, PermissionError) as e:
            logger.error(f"Ошибка записи JSON: {e}")
            return 1

    return 0


def apply_filters_and_metrics(files, filters):
    """
    Применяет фильтры и вычисляет метрики для каждого файла.

    Args:
        files: Генератор FileInfo из сканера.
        filters: Список фильтров.

    Yields:
        FileInfo с применёнными фильтрами и вычисленными метриками.
    """
    for file in files:
        # Применение фильтров (AND-логика)
        if filters and not all(f(file) for f in filters):
            continue

        # Вычисление метрик (если ещё не вычислены)
        if file.idle_days == 0 and file.uselessness_index == 0:
            compute_file_metrics(file)

        yield file


def save_json_report(
    files: list,
    stats: ScanStats,
    output_path: Path,
    scan_path: str,
) -> None:
    """
    Сохраняет сырые данные в JSON.

    Args:
        files: Список файлов.
        stats: Статистика сканирования.
        output_path: Путь для JSON-файла.
        scan_path: Путь сканирования.
    """
    import json
    from datetime import datetime

    data = {
        "scan_path": scan_path,
        "generated_at": datetime.now().isoformat(),
        "stats": stats.to_dict(),
        "files": [f.to_dict() for f in files],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


if __name__ == "__main__":
    sys.exit(main())
