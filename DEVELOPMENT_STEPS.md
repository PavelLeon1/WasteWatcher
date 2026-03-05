# 🛠️ Disk Space Analyzer — Пошаговый план разработки

> **Инструкция для агентной нейросети.**  
> Разрабатывай строго по шагам. Не переходи к следующему шагу, пока текущий полностью не реализован и не проверен. После каждого шага запускай указанные проверки.

---

## Подготовка

Перед началом прочти `SPECIFICATION.md` полностью.  
Убедись, что используешь **Python 3.10+**.  
Все файлы создавай с кодировкой **UTF-8**.  
Используй **только стандартную библиотеку Python** — никаких `pip install`.

---

## Шаг 1 — Структура проекта

**Задача:** Создать скелет директорий и пустые файлы.

```
disk_analyzer/
├── analyzer.py
├── core/
│   ├── __init__.py
│   ├── scanner.py
│   ├── models.py
│   ├── filters.py
│   ├── metrics.py
│   └── constants.py
├── report/
│   ├── __init__.py
│   ├── builder.py
│   └── template.py
└── utils/
    ├── __init__.py
    ├── formatting.py
    └── logging_cfg.py
```

**Действия:**
1. Создай все директории
2. Создай все `__init__.py` (пустые)
3. Создай остальные файлы с заглушками (docstring модуля + `pass`)

**Проверка:**
```bash
python -c "import disk_analyzer.core; print('OK')"
```

---

## Шаг 2 — Константы (`core/constants.py`)

**Задача:** Вынести все магические числа и строки в одно место.

**Реализуй:**
```python
# Размеры
BYTES_IN_KB: int = 1_024
BYTES_IN_MB: int = 1_048_576
BYTES_IN_GB: int = 1_073_741_824

# Форматирование
DATE_FORMAT: str = "%Y-%m-%d %H:%M"

# Отчёт
DEFAULT_OUTPUT: str = "report.html"
DEFAULT_TOP_N: int = 0          # 0 = все файлы
MAX_PATH_DISPLAY: int = 80      # Обрезка длинных путей в таблице

# Цвета индекса бесполезности (CSS-классы)
USELESS_LOW_THRESHOLD: float = 0.33     # < 33% перцентиль → green
USELESS_MED_THRESHOLD: float = 0.66     # < 66% перцентиль → yellow
                                         # >= 66% перцентиль → red

# Версия
VERSION: str = "1.0.0"
```

**Проверка:** Импортируй константы в REPL, убедись что нет синтаксических ошибок.

---

## Шаг 3 — Утилиты форматирования (`utils/formatting.py`)

**Задача:** Чистые функции для отображения данных.

**Реализуй следующие функции:**

### `human_readable_size(size_bytes: int) -> str`
- 0 → `"0 B"`
- < 1024 → `"512 B"`
- < 1MB → `"1.23 KB"`
- < 1GB → `"45.67 MB"`
- иначе → `"1.23 GB"`

### `format_date(dt: datetime) -> str`
- Возвращает строку в формате `DATE_FORMAT` из constants
- Если `dt is None` → возвращает `"—"`

### `truncate_path(path: str, max_len: int = MAX_PATH_DISPLAY) -> str`
- Если путь длиннее `max_len` символов → `"...хвост_пути"`
- Обрезай с начала, оставляй конец (имя файла важнее)

### `parse_size_arg(size_str: str) -> int`
- Парсит CLI-аргумент вида `"10B"`, `"5KB"`, `"2MB"`, `"1GB"`
- Возвращает количество байт (`int`)
- При ошибке формата → `raise ValueError` с понятным сообщением

**Проверка — напиши мини-тесты прямо в файле под `if __name__ == "__main__"`:**
```python
assert human_readable_size(0) == "0 B"
assert human_readable_size(1023) == "1023 B"
assert human_readable_size(1024) == "1.00 KB"
assert human_readable_size(1_048_576) == "1.00 MB"
assert parse_size_arg("2MB") == 2_097_152
print("formatting: OK")
```

---

## Шаг 4 — Настройка логирования (`utils/logging_cfg.py`)

**Задача:** Централизованная настройка логгера.

**Реализуй:**
```python
def setup_logger(verbose: bool = False, log_file: str | None = None) -> logging.Logger:
    """
    Настраивает и возвращает корневой логгер проекта.
    
    - verbose=True → уровень DEBUG, иначе WARNING
    - log_file → дополнительно пишет в файл
    - Формат: [LEVEL] YYYY-MM-DD HH:MM:SS — message
    """
```

**Требования:**
- Handler для `stdout` всегда
- Handler для файла — только если передан `log_file`
- Используй `logging.Formatter` с временными метками

**Проверка:**
```python
logger = setup_logger(verbose=True)
logger.debug("debug test")
logger.warning("warning test")
```

---

## Шаг 5 — Модели данных (`core/models.py`)

**Задача:** Определить датаклассы `FileInfo` и `ScanStats`.

**Требования к `FileInfo`:**
- Использовать `@dataclass(frozen=False, slots=True)` для производительности
- Все поля с аннотациями типов
- Добавить метод `to_dict(self) -> dict` для сериализации в JSON
- Добавить `@property uselessness_level(self) -> str` → `"low"` / `"medium"` / `"high"` (на основе абсолютного значения, пороги вычисляются снаружи — передать как параметр или оставить для `ReportBuilder`)

**Требования к `ScanStats`:**
- `@dataclass`
- Все поля с дефолтными значениями (через `field(default_factory=...)`)
- Метод `to_dict(self) -> dict`

**Проверка:**
```python
from datetime import datetime
fi = FileInfo(path="/tmp/test.log", name="test.log", extension=".log",
              size_bytes=1_048_576, size_human="1.00 MB",
              atime=datetime.now(), mtime=datetime.now(), ctime=datetime.now(),
              idle_days=30, uselessness_index=31_457_280.0,
              uselessness_human="30.0 MB·days")
print(fi.to_dict())
```

---

## Шаг 6 — Метрики (`core/metrics.py`)

**Задача:** Функции вычисления индекса бесполезности.

**Реализуй:**

### `calculate_idle_days(atime: datetime) -> int`
- `(datetime.now() - atime).days`
- Не может быть отрицательным (guard clause: `max(0, ...)`)

### `calculate_uselessness(size_bytes: int, idle_days: int) -> float`
- `float(size_bytes * idle_days)`

### `format_uselessness(value: float) -> str`
- Делит на `BYTES_IN_MB`, возвращает `"N.N MB·days"`

### `assign_uselessness_levels(files: list[FileInfo], low_q: float = 0.33, high_q: float = 0.66) -> list[FileInfo]`
- Вычисляет квантили по `uselessness_index` среди переданного списка
- Проставляет каждому `FileInfo` поле `uselessness_level` (`"low"` / `"medium"` / `"high"`)
- Возвращает тот же список (мутирует in-place)

**Проверка:**
```python
assert calculate_idle_days(datetime.now()) == 0
assert calculate_uselessness(1_048_576, 30) == 31_457_280.0
```

---

## Шаг 7 — Фильтры (`core/filters.py`)

**Задача:** Composable pipeline фильтрации.

**Реализуй:**

### Тип
```python
FileFilter = Callable[[FileInfo], bool]
```

### Фабричные функции (каждая возвращает `FileFilter`):
```python
def min_size_filter(min_bytes: int) -> FileFilter: ...
def extension_filter(extensions: list[str]) -> FileFilter: ...
def min_idle_filter(min_days: int) -> FileFilter: ...
```

### Pipeline
```python
def apply_filters(files: Iterable[FileInfo], filters: list[FileFilter]) -> Generator[FileInfo, None, None]:
    """Применяет все фильтры последовательно (AND-логика)."""
    for file in files:
        if all(f(file) for f in filters):
            yield file
```

**Проверка:**
```python
filters = [min_size_filter(1024), extension_filter([".log"])]
test_file = FileInfo(...)   # size_bytes=2048, extension=".log"
assert all(f(test_file) for f in filters) == True
```

---

## Шаг 8 — Сканер (`core/scanner.py`)

**Задача:** Рекурсивный обход ФС с обработкой ошибок.

**Реализуй:**

### `build_file_info(entry: os.DirEntry, logger: logging.Logger) -> FileInfo | None`
- Получает `os.stat()` для `entry`
- Обрабатывает `PermissionError`, `OSError` → логирует, возвращает `None`
- На Windows/macOS/Linux — корректно получает `ctime` (см. Спецификацию, раздел 12)
- Создаёт и возвращает `FileInfo`

### `scan_directory(...) -> Generator[FileInfo, None, None]`
```python
def scan_directory(
    root: Path,
    exclude_dirs: set[str],
    max_depth: int | None,
    no_hidden: bool,
    logger: logging.Logger,
    stats: ScanStats,
    current_depth: int = 0,
) -> Generator[FileInfo, None, None]:
```
- Guard clause: если `current_depth > max_depth` → `return`
- `os.scandir()` в блоке `try/except PermissionError`
- Сортировка записей: сначала директории, потом файлы (для красивого прогресса)
- Пропуск скрытых файлов/папок если `no_hidden=True` (имя начинается с `.`)
- Инкремент `stats.total_files` и `stats.total_size_bytes` по ходу обхода

**Проверка:**
```python
import tempfile, os
with tempfile.TemporaryDirectory() as tmpdir:
    open(os.path.join(tmpdir, "test.txt"), "w").write("hello")
    files = list(scan_directory(Path(tmpdir), set(), None, False, logger, ScanStats()))
    assert len(files) == 1
    assert files[0].name == "test.txt"
```

---

## Шаг 9 — HTML-шаблон (`report/template.py`)

**Задача:** Создать полный HTML/CSS/JS шаблон как Python-строку.

**Структура HTML:**
```html
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Disk Analyzer Report</title>
  <style>/* INLINE CSS */</style>
</head>
<body>
  <!-- HEADER -->
  <!-- DASHBOARD CARDS -->
  <!-- CHARTS ROW -->
  <!-- TABLE CONTROLS -->
  <!-- TABLE -->
  <!-- FOOTER -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
  <!-- ЛИБО встроенный bundle если нужен офлайн -->
  <script>
    const FILE_DATA = $FILE_DATA_JSON;
    const STATS_DATA = $STATS_DATA_JSON;
    /* INLINE JS */
  </script>
</body>
</html>
```

**CSS — обязательные стили:**
- CSS Variables: `--color-primary`, `--color-danger`, `--color-warning`, `--color-success`, `--bg`, `--surface`, `--text`
- Dark mode через `@media (prefers-color-scheme: dark)` — переопределяй только переменные
- `.useless-low` → зелёный фон строки (прозрачный, 10% opacity)
- `.useless-medium` → жёлтый фон строки
- `.useless-high` → красный фон строки
- Sticky header таблицы (`position: sticky; top: 0`)
- Responsive: на мобильных таблица скроллится горизонтально

**JS — обязательный функционал:**
1. Инициализация таблицы из `FILE_DATA`
2. Функция `renderTable(data, page, perPage)` — рендерит строки
3. Функция `sortBy(column)` — сортировка с запоминанием направления
4. Функция `filterTable(query)` — живой поиск по всем текстовым полям
5. Функция `exportCSV()` — скачать текущую выборку как `.csv`
6. Пагинация: `renderPagination(totalItems, page, perPage)`
7. Chart.js: Bar chart по расширениям + Doughnut по категориям
8. Карточки дашборда: заполнить из `STATS_DATA`

**Плейсхолдеры для Python:**
```python
TEMPLATE: str = """...$FILE_DATA_JSON...$STATS_DATA_JSON..."""
```

**Проверка:** Открой сгенерированный HTML в браузере, убедись что таблица рендерится.

---

## Шаг 10 — Построитель отчёта (`report/builder.py`)

**Задача:** Склеить данные и шаблон, записать HTML-файл.

**Реализуй:**

### `class ReportBuilder`
```python
class ReportBuilder:
    def __init__(self, files: list[FileInfo], stats: ScanStats, output_path: Path): ...
    
    def build(self) -> None:
        """
        Template Method:
        1. _prepare_data()
        2. _render_template()
        3. _write_file()
        """
    
    def _prepare_data(self) -> tuple[str, str]:
        """Сериализует files и stats в JSON-строки."""
    
    def _render_template(self, file_json: str, stats_json: str) -> str:
        """Подставляет JSON в шаблон через string.Template."""
    
    def _write_file(self, html: str) -> None:
        """Записывает HTML в output_path (UTF-8)."""
```

**Сериализация `FileInfo`:**
- Вызывает `fi.to_dict()` для каждого файла
- `datetime` → ISO-строка через `.isoformat()`
- Использует `json.dumps(..., ensure_ascii=False, separators=(',', ':'))` для компактности

**Проверка:**
```python
builder = ReportBuilder(files=[], stats=ScanStats(), output_path=Path("test.html"))
builder.build()
assert Path("test.html").exists()
```

---

## Шаг 11 — CLI (`analyzer.py`)

**Задача:** Точка входа, парсинг аргументов, оркестрация.

**Реализуй функцию `main()`:**

```python
def main() -> None:
    args = parse_args()
    logger = setup_logger(verbose=args.verbose)
    
    # 1. Собрать фильтры
    filters = build_filters(args)
    
    # 2. Создать ScanStats
    stats = ScanStats()
    
    # 3. Запустить сканирование (генератор)
    start_time = time.perf_counter()
    raw_files = scan_directory(Path(args.path), ...)
    
    # 4. Применить фильтры
    filtered = apply_filters(raw_files, filters)
    
    # 5. Материализовать список (нужен для квантилей)
    files: list[FileInfo] = list(filtered)
    
    # 6. Назначить уровни бесполезности
    assign_uselessness_levels(files)
    
    # 7. Сортировка по uselessness_index DESC
    files.sort(key=lambda f: f.uselessness_index, reverse=True)
    
    # 8. Применить --top N
    if args.top:
        files = files[:args.top]
    
    # 9. Дополнить stats
    stats.scan_duration_sec = time.perf_counter() - start_time
    stats.top_useless = files[:10]
    # ... остальные поля stats
    
    # 10. Опциональный JSON
    if args.json:
        save_json(files, stats, Path(args.json))
    
    # 11. Построить отчёт
    ReportBuilder(files, stats, Path(args.output)).build()
    
    print(f"✅ Отчёт сохранён: {args.output}")
    print(f"   Файлов: {len(files)} | Размер: {stats.total_size_human}")
    print(f"   Время сканирования: {stats.scan_duration_sec:.2f}с")
```

**Парсер аргументов** — реализуй `parse_args()` с полным набором из Спецификации раздел 2.3.

**Проверка:**
```bash
python analyzer.py . --output test_report.html --verbose
# Должен создать test_report.html
```

---

## Шаг 12 — Прогресс-бар в CLI (улучшение)

**Задача:** Показывать прогресс сканирования без внешних библиотек.

**Реализуй `utils/progress.py`:**
```python
class ProgressReporter:
    def __init__(self, verbose: bool): ...
    
    def update(self, count: int, current_path: str) -> None:
        """Обновляет строку в stdout через \r."""
        if not self.verbose:
            return
        line = f"\r  Сканировано: {count:>8,} файлов | {current_path[:60]:<60}"
        sys.stdout.write(line)
        sys.stdout.flush()
    
    def done(self) -> None:
        sys.stdout.write("\n")
        sys.stdout.flush()
```

Вызывай `reporter.update()` каждые 100 файлов в `scan_directory`.

---

## Шаг 13 — Финальная проверка и интеграционный тест

**Задача:** Убедиться что всё работает вместе.

### Тест 1: Пустая директория
```bash
mkdir /tmp/empty_test
python analyzer.py /tmp/empty_test --output /tmp/test1.html
# Ожидание: файл создан, "Файлов: 0"
```

### Тест 2: Нет прав доступа
```bash
python analyzer.py /root --output /tmp/test2.html 2>&1 | grep -i "skipped\|warning"
# Ожидание: предупреждения в логе, скрипт не падает
```

### Тест 3: Фильтрация
```bash
python analyzer.py ~/Downloads --min-size 10MB --min-idle 30 --output /tmp/test3.html
# Ожидание: только файлы > 10MB И простой > 30 дней
```

### Тест 4: Полный прогон
```bash
python analyzer.py /tmp --ext .log .tmp --top 50 --json /tmp/data.json --output /tmp/full.html --verbose
# Ожидание: HTML + JSON созданы, в консоли прогресс
```

### Тест 5: Проверка HTML
Открой сгенерированный HTML в браузере:
- [ ] Карточки показывают корректную статистику
- [ ] Таблица отсортирована по убыванию индекса бесполезности
- [ ] Клик по заголовку столбца меняет сортировку
- [ ] Поиск фильтрует строки в реальном времени
- [ ] Кнопка «Экспорт CSV» скачивает файл
- [ ] Графики отображаются корректно
- [ ] Dark mode работает (если ОС в тёмной теме)

---

## Шаг 14 — Документация

**Задача:** Добавить `README.md` в корень проекта.

**Содержание README:**
1. Краткое описание (2–3 предложения)
2. Требования (Python 3.10+, никаких зависимостей)
3. Установка (просто `git clone`)
4. Использование — 3–5 примеров команд
5. Описание HTML-отчёта (скриншот или ASCII-схема)
6. Описание индекса бесполезности (формула)
7. Известные ограничения (симлинки, права доступа, `ctime` на Linux)

---

## Чеклист перед финальной сдачей

```
[ ] Все модули импортируются без ошибок
[ ] Все функции имеют аннотации типов
[ ] Все публичные функции имеют docstring
[ ] Нет print() вне analyzer.py (используй logger)
[ ] Нет жёстко прописанных путей (только Path и аргументы CLI)
[ ] HTML-отчёт работает офлайн (либо Chart.js встроен, либо есть fallback)
[ ] Обработаны: PermissionError, OSError, пустые директории, 0-байтные файлы
[ ] Тест на Windows: пути с обратными слэшами не ломают JSON
[ ] Тест на MacOS/Linux: unicode в именах файлов корректно отображается
[ ] README.md написан и понятен
```

---

## Порядок коммитов (рекомендация)

```
feat: project structure and constants
feat: utils - formatting and logging
feat: core models FileInfo and ScanStats  
feat: core metrics - uselessness index
feat: core filters - pipeline pattern
feat: core scanner - recursive directory walk
feat: report template - HTML/CSS/JS
feat: report builder - data injection
feat: CLI - argument parsing and orchestration
feat: progress reporter
fix: cross-platform ctime handling
docs: README and inline docstrings
```
