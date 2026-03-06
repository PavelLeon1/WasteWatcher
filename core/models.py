"""
Модели данных: FileInfo и ScanStats.

Датаклассы для представления информации о файлах и статистики сканирования.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from core.constants import (
    USELESS_LOW_THRESHOLD,
    USELESS_MED_THRESHOLD,
)
from utils.formatting import format_date, human_readable_size


@dataclass(slots=True)
class FileInfo:
    """
    Информация об одном файле.

    Attributes:
        path: Абсолютный путь к файлу.
        name: Имя файла.
        extension: Расширение файла (нижний регистр, например ".log").
        size_bytes: Размер файла в байтах.
        size_human: Человекочитаемый размер (например, "1.23 MB").
        atime: Дата последнего доступа к файлу.
        mtime: Дата последней модификации файла.
        ctime: Дата создания файла (или изменения метаданных на Linux).
        idle_days: Количество дней простоя (сегодня - atime).
        uselessness_index: Индекс бесполезности (size_bytes * idle_days).
        uselessness_human: Человекочитаемый индекс бесполезности.
        uselessness_level: Уровень бесполезности ("low", "medium", "high").
    """

    path: str
    name: str
    extension: str
    size_bytes: int
    size_human: str
    atime: datetime
    mtime: datetime
    ctime: datetime
    idle_days: int
    uselessness_index: float
    uselessness_human: str
    uselessness_level: str = "low"

    def to_dict(self) -> dict:
        """
        Сериализует FileInfo в словарь для JSON.

        Returns:
            Словарь с данными файла, где datetime представлены как ISO-строки.
        """
        return {
            "path": self.path,
            "name": self.name,
            "extension": self.extension,
            "size_bytes": self.size_bytes,
            "size_human": self.size_human,
            "atime": self.atime.isoformat() if self.atime else None,
            "mtime": self.mtime.isoformat() if self.mtime else None,
            "ctime": self.ctime.isoformat() if self.ctime else None,
            "idle_days": self.idle_days,
            "uselessness_index": self.uselessness_index,
            "uselessness_human": self.uselessness_human,
            "uselessness_level": self.uselessness_level,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FileInfo":
        """
        Десериализует словарь в FileInfo.

        Args:
            data: Словарь с данными файла.

        Returns:
            Экземпляр FileInfo.
        """
        return cls(
            path=data["path"],
            name=data["name"],
            extension=data["extension"],
            size_bytes=data["size_bytes"],
            size_human=data["size_human"],
            atime=datetime.fromisoformat(data["atime"]) if data.get("atime") else datetime.now(),
            mtime=datetime.fromisoformat(data["mtime"]) if data.get("mtime") else datetime.now(),
            ctime=datetime.fromisoformat(data["ctime"]) if data.get("ctime") else datetime.now(),
            idle_days=data["idle_days"],
            uselessness_index=data["uselessness_index"],
            uselessness_human=data["uselessness_human"],
            uselessness_level=data.get("uselessness_level", "low"),
        )


@dataclass(slots=True)
class ScanStats:
    """
    Статистика сканирования.

    Attributes:
        total_files: Общее количество обработанных файлов.
        total_size_bytes: Суммарный размер всех файлов в байтах.
        total_size_human: Человекочитаемый суммарный размер.
        skipped_files: Количество пропущенных файлов (ошибки доступа).
        scan_duration_sec: Длительность сканирования в секундах.
        top_useless: Топ-10 самых бесполезных файлов.
        avg_uselessness: Средний индекс бесполезности.
        oldest_file: Самый старый файл по atime (или None).
        ext_distribution: Распределение по расширениям {".log": 42, ".tmp": 17}.
        dir_sizes: Размеры директорий {"/path/dir": size_bytes}.
    """

    total_files: int = 0
    total_size_bytes: int = 0
    total_size_human: str = "0 B"
    skipped_files: int = 0
    scan_duration_sec: float = 0.0
    top_useless: list[FileInfo] = field(default_factory=list)
    avg_uselessness: float = 0.0
    oldest_file: FileInfo | None = None
    ext_distribution: dict[str, int] = field(default_factory=dict)
    dir_sizes: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """
        Сериализует ScanStats в словарь для JSON.

        Returns:
            Словарь со статистикой сканирования.
        """
        return {
            "total_files": self.total_files,
            "total_size_bytes": self.total_size_bytes,
            "total_size_human": self.total_size_human,
            "skipped_files": self.skipped_files,
            "scan_duration_sec": self.scan_duration_sec,
            "top_useless": [f.to_dict() for f in self.top_useless],
            "avg_uselessness": self.avg_uselessness,
            "oldest_file": self.oldest_file.to_dict() if self.oldest_file else None,
            "ext_distribution": self.ext_distribution,
            "dir_sizes": self.dir_sizes,
        }

    def update_total_size(self) -> None:
        """Обновляет total_size_human на основе total_size_bytes."""
        self.total_size_human = human_readable_size(self.total_size_bytes)

    def update_avg_uselessness(self, files: list[FileInfo]) -> None:
        """
        Вычисляет средний индекс бесполезности.

        Args:
            files: Список файлов для вычисления среднего.
        """
        if files:
            total = sum(f.uselessness_index for f in files)
            self.avg_uselessness = total / len(files)
        else:
            self.avg_uselessness = 0.0

    def update_ext_distribution(self, files: list[FileInfo]) -> None:
        """
        Вычисляет распределение файлов по расширениям.

        Args:
            files: Список файлов для анализа.
        """
        self.ext_distribution = {}
        for file in files:
            ext = file.extension
            self.ext_distribution[ext] = self.ext_distribution.get(ext, 0) + 1

    def update_dir_sizes(self, files: list[FileInfo]) -> None:
        """
        Вычисляет размеры директорий (сумма размеров файлов в каждой).

        Args:
            files: Список файлов для анализа.
        """
        self.dir_sizes = {}
        for file in files:
            # Берём родительскую директорию
            parent = str(Path(file.path).parent)
            self.dir_sizes[parent] = self.dir_sizes.get(parent, 0) + file.size_bytes

    def update_oldest_file(self, files: list[FileInfo]) -> None:
        """
        Находит самый старый файл по atime.

        Args:
            files: Список файлов для анализа.
        """
        if not files:
            self.oldest_file = None
            return

        oldest = min(files, key=lambda f: f.atime)
        self.oldest_file = oldest


if __name__ == "__main__":
    # Тесты для самопроверки модуля
    from datetime import datetime, timedelta

    now = datetime.now()
    week_ago = now - timedelta(days=7)

    # Тест FileInfo
    fi = FileInfo(
        path="C:/test/file.log",
        name="file.log",
        extension=".log",
        size_bytes=1_048_576,
        size_human="1.00 MB",
        atime=week_ago,
        mtime=now,
        ctime=now,
        idle_days=7,
        uselessness_index=7_340_032.0,
        uselessness_human="7.00 MB·days",
    )

    # Проверка to_dict
    fi_dict = fi.to_dict()
    assert fi_dict["path"] == "C:/test/file.log"
    assert fi_dict["size_bytes"] == 1_048_576
    assert "atime" in fi_dict
    assert isinstance(fi_dict["atime"], str)  # ISO-строка

    # Проверка from_dict
    fi_restored = FileInfo.from_dict(fi_dict)
    assert fi_restored.path == fi.path
    assert fi_restored.size_bytes == fi.size_bytes

    # Тест ScanStats
    stats = ScanStats()
    stats.total_files = 100
    stats.total_size_bytes = 1_073_741_824
    stats.update_total_size()
    assert stats.total_size_human == "1.00 GB"

    stats.update_avg_uselessness([fi])
    assert stats.avg_uselessness == 7_340_032.0

    stats.update_ext_distribution([fi])
    assert stats.ext_distribution == {".log": 1}

    stats.update_dir_sizes([fi])
    # На Windows путь будет "C:\test", на Linux "C:/test"
    assert len(stats.dir_sizes) == 1
    assert any("test" in k for k in stats.dir_sizes.keys())

    stats.update_oldest_file([fi])
    assert stats.oldest_file == fi

    # Проверка to_dict для stats
    stats_dict = stats.to_dict()
    assert stats_dict["total_files"] == 100
    assert len(stats_dict["top_useless"]) == 0  # Пустой список

    print("models: OK")
