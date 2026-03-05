---
name: disk-analyzer-dev
description: Навык разработки Disk Space Analyzer на Python. Использовать при написании любого модуля проекта: scanner, filters, metrics, models, report builder, HTML-шаблон, CLI. Активируется при упоминании сканирования файлов, индекса бесполезности, HTML-отчёта, фильтрации файлов, обхода директорий.
---

# Disk Space Analyzer — Контекст разработки

## Структура проекта

```
disk_analyzer/
├── analyzer.py          ← точка входа, CLI (argparse)
├── core/
│   ├── constants.py     ← ВСЕ магические числа здесь
│   ├── models.py        ← dataclasses: FileInfo, ScanStats
│   ← scanner.py        ← генератор обхода ФС
│   ├── filters.py       ← pipeline фильтров (Callable)
│   └── metrics.py       ← расчёт uselessness_index
├── report/
│   ├── builder.py       ← сборка HTML (Template Method)
│   └── template.py      ← HTML/CSS/JS как Python-строка
└── utils/
    ├── formatting.py    ← human_readable_size, parse_size_arg
    ├── logging_cfg.py   ← setup_logger()
    └── progress.py      ← ProgressReporter (без зависимостей)
```

## Формула индекса бесполезности

```
uselessness_index = size_bytes × idle_days
idle_days = (datetime.now() - atime).days  # минимум 0
```

Отображение: делить на 1_048_576 → "N.N MB·days"

## Критические правила реализации

1. **Никогда** не использовать `follow_symlinks=True` — риск бесконечного цикла
2. **Всегда** оборачивать `os.stat()` в `try/except (PermissionError, OSError)`
3. **Генератор** для `scan_directory` — не накапливать список в памяти
4. **`slots=True`** у dataclass FileInfo для производительности
5. **Плейсхолдеры** в HTML-шаблоне: `$FILE_DATA_JSON` и `$STATS_DATA_JSON`
6. **`string.Template`** для вставки JSON в шаблон (не f-string — экранирование сломает JSON)

## Кросс-платформенный ctime

```python
import platform, os

def get_creation_time(stat: os.stat_result) -> float:
    if platform.system() == "Windows":
        return stat.st_ctime          # истинная дата создания
    elif platform.system() == "Darwin":
        return getattr(stat, "st_birthtime", stat.st_ctime)
    else:
        return stat.st_ctime          # на Linux это mtime метаданных
```

## Порядок разработки (из DEVELOPMENT_STEPS.md)

Шаг 1 → структура | Шаг 2 → constants | Шаг 3 → formatting |
Шаг 4 → logging | Шаг 5 → models | Шаг 6 → metrics |
Шаг 7 → filters | Шаг 8 → scanner | Шаг 9 → HTML-шаблон |
Шаг 10 → builder | Шаг 11 → CLI | Шаг 12 → progress |
Шаг 13 → тесты | Шаг 14 → README

## Пример минимального рабочего FileInfo

```python
FileInfo(
    path="/var/log/syslog",
    name="syslog",
    extension=".log",
    size_bytes=5_242_880,
    size_human="5.00 MB",
    atime=datetime(2024, 1, 1),
    mtime=datetime(2024, 1, 1),
    ctime=datetime(2024, 1, 1),
    idle_days=90,
    uselessness_index=471_859_200.0,
    uselessness_human="450.0 MB·days"
)
```
