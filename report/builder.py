"""
Построитель HTML-отчёта.

Сборка финального HTML из шаблона и данных сканирования.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from string import Template

from core.models import FileInfo, ScanStats
from report.template import FILE_DATA_PLACEHOLDER, STATS_DATA_PLACEHOLDER, TEMPLATE


class ReportBuilder:
    """
    Построитель HTML-отчёта.

    Использует Template Method pattern для последовательной сборки отчёта:
    1. _prepare_data() — сериализация данных в JSON
    2. _render_template() — подстановка JSON в шаблон
    3. _write_file() — запись HTML в файл
    """

    def __init__(
        self,
        files: list[FileInfo],
        stats: ScanStats,
        output_path: Path,
        scan_path: str | None = None,
    ) -> None:
        """
        Инициализирует построитель отчёта.

        Args:
            files: Список файлов для отображения в отчёте.
            stats: Статистика сканирования.
            output_path: Путь для сохранения HTML-файла.
            scan_path: Путь сканирования (опционально, для отображения в отчёте).
        """
        self.files = files
        self.stats = stats
        self.output_path = output_path
        self.scan_path = scan_path

    def build(self) -> None:
        """
        Template Method: строит HTML-отчёт.

        Последовательность:
        1. _prepare_data()
        2. _render_template()
        3. _write_file()
        """
        file_json, stats_json = self._prepare_data()
        html = self._render_template(file_json, stats_json)
        self._write_file(html)

    def _prepare_data(self) -> tuple[str, str]:
        """
        Сериализует файлы и статистику в JSON-строки.

        Returns:
            Кортеж из двух JSON-строк: (files_json, stats_json).
        """
        # Сериализация файлов
        files_data = [file.to_dict() for file in self.files]
        files_json = json.dumps(
            files_data,
            ensure_ascii=False,
            separators=(",", ":"),
        )

        # Подготовка статистики
        stats_dict = self.stats.to_dict()
        # Добавляем путь сканирования и дату генерации
        stats_dict["scan_path"] = self.scan_path
        stats_dict["generated_at"] = datetime.now().isoformat()

        stats_json = json.dumps(
            stats_dict,
            ensure_ascii=False,
            separators=(",", ":"),
        )

        return files_json, stats_json

    def _render_template(self, file_json: str, stats_json: str) -> str:
        """
        Подставляет JSON в шаблон через string.Template.

        Args:
            file_json: JSON-строка с данными файлов.
            stats_json: JSON-строка со статистикой.

        Returns:
            Готовый HTML-документ.
        """
        template = Template(TEMPLATE)
        return template.safe_substitute(
            FILE_DATA_JSON=file_json,
            STATS_DATA_JSON=stats_json,
        )

    def _write_file(self, html: str) -> None:
        """
        Записывает HTML в output_path (UTF-8).

        Args:
            html: Готовый HTML-документ.

        Raises:
            OSError: При ошибке записи файла.
            PermissionError: При отсутствии прав на запись.
        """
        try:
            # Создаём родительские директории если нужно
            self.output_path.parent.mkdir(parents=True, exist_ok=True)

            # Записываем файл
            self.output_path.write_text(html, encoding="utf-8")

        except (OSError, PermissionError) as e:
            raise e


def generate_report(
    files: list[FileInfo],
    stats: ScanStats,
    output_path: Path,
    scan_path: str | None = None,
) -> Path:
    """
    Удобная функция для генерации отчёта.

    Args:
        files: Список файлов для отображения.
        stats: Статистика сканирования.
        output_path: Путь для сохранения HTML.
        scan_path: Путь сканирования (опционально).

    Returns:
        Путь к созданному файлу отчёта.

    Example:
        >>> from pathlib import Path
        >>> files = [...]  # список FileInfo
        >>> stats = ScanStats()
        >>> report_path = generate_report(files, stats, Path("report.html"))
    """
    builder = ReportBuilder(files, stats, output_path, scan_path)
    builder.build()
    return output_path


if __name__ == "__main__":
    # Тесты для самопроверки модуля
    import tempfile
    from datetime import datetime, timedelta

    from core.metrics import calculate_idle_days, calculate_uselessness, format_uselessness
    from utils.logging_cfg import setup_logger

    logger = setup_logger(verbose=True)

    # Создаём тестовые данные
    now = datetime.now()
    test_files = [
        FileInfo(
            path="/test/file1.log",
            name="file1.log",
            extension=".log",
            size_bytes=1024,
            size_human="1.00 KB",
            atime=now - timedelta(days=10),
            mtime=now - timedelta(days=10),
            ctime=now - timedelta(days=10),
            idle_days=10,
            uselessness_index=10240.0,
            uselessness_human="0.01 MB·days",
            uselessness_level="low",
        ),
        FileInfo(
            path="/test/file2.tmp",
            name="file2.tmp",
            extension=".tmp",
            size_bytes=1_048_576,
            size_human="1.00 MB",
            atime=now - timedelta(days=30),
            mtime=now - timedelta(days=30),
            ctime=now - timedelta(days=30),
            idle_days=30,
            uselessness_index=31_457_280.0,
            uselessness_human="30.00 MB·days",
            uselessness_level="high",
        ),
        FileInfo(
            path="/test/file3.txt",
            name="file3.txt",
            extension=".txt",
            size_bytes=512,
            size_human="512 B",
            atime=now - timedelta(days=5),
            mtime=now - timedelta(days=5),
            ctime=now - timedelta(days=5),
            idle_days=5,
            uselessness_index=2560.0,
            uselessness_human="0.00 MB·days",
            uselessness_level="low",
        ),
    ]

    # Создаём статистику
    stats = ScanStats()
    stats.total_files = len(test_files)
    stats.total_size_bytes = sum(f.size_bytes for f in test_files)
    stats.update_total_size()
    stats.scan_duration_sec = 0.123
    stats.top_useless = sorted(test_files, key=lambda f: f.uselessness_index, reverse=True)[:10]
    stats.update_avg_uselessness(test_files)
    stats.update_ext_distribution(test_files)
    stats.update_dir_sizes(test_files)
    stats.update_oldest_file(test_files)

    # Тест 1: Генерация отчёта во временный файл
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_report.html"

        builder = ReportBuilder(
            files=test_files,
            stats=stats,
            output_path=output_path,
            scan_path="/test",
        )
        builder.build()

        # Проверка что файл создан
        assert output_path.exists(), "Файл отчёта не создан"

        # Проверка размера файла (должен быть > 0)
        file_size = output_path.stat().st_size
        assert file_size > 0, "Файл отчёта пуст"

        # Проверка содержимого
        content = output_path.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert "Disk Space Analyzer Report" in content
        assert "file1.log" in content
        assert "file2.tmp" in content
        assert "file3.txt" in content
        assert "$FILE_DATA_JSON" not in content  # Плейсхолдер заменён
        assert "$STATS_DATA_JSON" not in content  # Плейсхолдер заменён
        assert "useless-high" in content  # Класс цвета
        assert "useless-low" in content  # Класс цвета

        print(f"[OK] Тест 1 пройден: файл создан ({file_size} байт)")

    # Тест 2: Функция generate_report
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "report.html"

        report_path = generate_report(
            files=test_files,
            stats=stats,
            output_path=output_path,
            scan_path="/test",
        )

        assert report_path == output_path
        assert report_path.exists()

        print(f"[OK] Тест 2 пройден: generate_report работает")

    # Тест 3: Пустой список файлов
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "empty_report.html"
        empty_stats = ScanStats()

        builder = ReportBuilder(
            files=[],
            stats=empty_stats,
            output_path=output_path,
            scan_path="/empty",
        )
        builder.build()

        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "No files found" in content or "0" in content

        print(f"[OK] Тест 3 пройден: пустой отчёт генерируется")

    # Тест 4: Создание вложенных директорий
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "subdir" / "nested" / "report.html"

        builder = ReportBuilder(
            files=test_files,
            stats=stats,
            output_path=output_path,
            scan_path="/test",
        )
        builder.build()

        assert output_path.exists()

        print(f"[OK] Тест 4 пройден: вложенные директории создаются")

    print("\nbuilder: OK")
