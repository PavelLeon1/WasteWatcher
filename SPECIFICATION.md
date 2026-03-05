# 📦 Disk Space Analyzer — Project Specification

## 1. Обзор проекта

**Название:** Disk Space Analyzer  
**Версия:** 1.0.0  
**Тип:** CLI-инструмент + HTML-отчёт  
**Язык:** Python 3.10+  
**Назначение:** Рекурсивный анализ дискового пространства с построением интерактивного HTML-отчёта, отсортированного по «индексу бесполезности» файлов.

---

## 2. Функциональные требования

### 2.1 Сбор данных
- Рекурсивный обход указанного каталога (и всех вложенных)
- Для каждого файла собирать:
  - Абсолютный путь
  - Имя файла и расширение
  - Размер в байтах (и человекочитаемый формат: KB / MB / GB)
  - Дата последнего доступа (`atime`)
  - Дата последней модификации (`mtime`)
  - Дата создания (`ctime`)
  - Количество дней простоя (сегодня − `atime`)
  - **Индекс бесполезности** = `size_bytes × idle_days`
- Поддержка фильтрации по:
  - Минимальному размеру файла (например, `--min-size 1MB`)
  - Расширению (например, `--ext .log .tmp`)
  - Минимальному числу дней простоя (например, `--min-idle 30`)
  - Максимальной глубине обхода (например, `--depth 5`)
- Поддержка исключения папок через `--exclude`

### 2.2 HTML-отчёт
- Полностью автономный (единственный `.html` файл, без внешних зависимостей)
- Встроенные CSS и JavaScript
- Интерактивная таблица с возможностью:
  - Сортировки по любому столбцу (клик на заголовок)
  - Глобального поиска/фильтрации
  - Пагинации (выбор: 25 / 50 / 100 / все записи)
  - Выделения строк цветом по уровню индекса бесполезности (зелёный → жёлтый → красный)
- Дашборд (карточки вверху страницы):
  - Суммарный размер всех файлов
  - Количество файлов
  - Топ-3 «мусорных» файла
  - Средний индекс бесполезности
  - Самый «старый» файл по `atime`
- Столбчатая диаграмма: распределение файлов по категориям (по расширению)
- Тепловая диаграмма (treemap): размер каталогов
- Экспорт таблицы в CSV прямо из браузера

### 2.3 CLI-интерфейс
```
analyzer.py [OPTIONS] PATH

Options:
  --output FILE        Путь к выходному HTML-файлу [default: report.html]
  --min-size SIZE      Минимальный размер файла (10B, 1KB, 5MB, 2GB)
  --min-idle DAYS      Минимальный простой в днях [default: 0]
  --ext EXT...         Фильтр по расширениям (.log .tmp)
  --exclude DIR...     Исключить директории
  --depth INT          Максимальная глубина обхода [default: unlimited]
  --top INT            Показывать топ N файлов в отчёте [default: all]
  --no-hidden          Игнорировать скрытые файлы и папки
  --verbose            Подробный вывод в консоль
  --json FILE          Дополнительно сохранить сырые данные в JSON
  --help               Показать справку
```

---

## 3. Нефункциональные требования

- Производительность: обработка 100 000+ файлов без зависания (использовать генераторы)
- Память: потоковая обработка, не хранить все файлы в RAM одновременно
- Кросс-платформенность: Windows, macOS, Linux
- Отчёт открывается офлайн в любом современном браузере (Chrome 90+, Firefox 88+, Safari 14+)
- Все исключения (PermissionError, OSError) должны логироваться, но не прерывать работу
- Код должен быть полностью покрыт типовыми аннотациями (`mypy --strict`)

---

## 4. Стек технологий

### Backend (сбор данных)
| Компонент | Инструмент | Обоснование |
|---|---|---|
| Язык | Python 3.10+ | Встроенный `os`, `pathlib`, кросс-платформенность |
| CLI | `argparse` (stdlib) | Без внешних зависимостей |
| Работа с ФС | `pathlib.Path`, `os.stat` | Нативные, быстрые |
| Дата/время | `datetime` (stdlib) | Достаточно для задачи |
| Сериализация | `json` (stdlib) | Для опциональной выгрузки данных |
| Шаблонизация | `string.Template` (stdlib) | Встраивание данных в HTML |
| Логирование | `logging` (stdlib) | Структурированный вывод |

> **Принцип Zero External Dependencies** — проект не требует `pip install` ничего, кроме стандартной библиотеки Python.

### Frontend (HTML-отчёт, всё inline)
| Компонент | Инструмент | Версия |
|---|---|---|
| Стили | Pure CSS (CSS Variables, Flexbox, Grid) | — |
| Таблица | Vanilla JS | ES2020 |
| Графики | Chart.js | 4.x (CDN → inline bundle) |
| Иконки | Unicode символы / SVG inline | — |
| Шрифты | System UI stack | — |

> Chart.js встраивается в HTML как inline `<script>` — отчёт работает без интернета.

---

## 5. Архитектура

```
disk_analyzer/
├── analyzer.py          # Точка входа, CLI
├── core/
│   ├── __init__.py
│   ├── scanner.py       # Сканирование ФС, генератор FileInfo
│   ├── models.py        # Датаклассы: FileInfo, ScanStats
│   ├── filters.py       # Фильтрация и применение правил
│   └── metrics.py       # Вычисление индекса бесполезности
├── report/
│   ├── __init__.py
│   ├── builder.py       # Сборка HTML из шаблона
│   └── template.py      # HTML/CSS/JS шаблон как Python-строка
└── utils/
    ├── __init__.py
    ├── formatting.py    # human_readable_size(), format_date()
    └── logging_cfg.py   # Настройка логгера
```

### Поток данных
```
CLI args
   │
   ▼
Scanner (генератор)
   │  yield FileInfo
   ▼
FilterPipeline
   │  yield FileInfo (отфильтрованный)
   ▼
MetricsCalculator
   │  список FileInfo с uselessness_index
   ▼
ReportBuilder
   │  JSON → вставка в шаблон
   ▼
HTML-файл
```

---

## 6. Модели данных

### `FileInfo` (dataclass)
```python
@dataclass
class FileInfo:
    path: str                    # Абсолютный путь
    name: str                    # Имя файла
    extension: str               # Расширение (нижний регистр)
    size_bytes: int              # Размер в байтах
    size_human: str              # "1.23 MB"
    atime: datetime              # Последний доступ
    mtime: datetime              # Последняя модификация
    ctime: datetime              # Создание / метаизменение
    idle_days: int               # Дней с последнего доступа
    uselessness_index: float     # size_bytes * idle_days
    uselessness_human: str       # Нормализованное значение для отображения
```

### `ScanStats` (dataclass)
```python
@dataclass
class ScanStats:
    total_files: int
    total_size_bytes: int
    total_size_human: str
    skipped_files: int           # PermissionError и т.д.
    scan_duration_sec: float
    top_useless: list[FileInfo]  # Топ-10
    avg_uselessness: float
    oldest_file: FileInfo | None
    ext_distribution: dict[str, int]   # {'.log': 42, '.tmp': 17}
    dir_sizes: dict[str, int]          # {'/path/dir': size_bytes}
```

---

## 7. Ключевые алгоритмы

### 7.1 Индекс бесполезности
```
uselessness_index = size_bytes × idle_days
```
- `idle_days` = `(datetime.now() - atime).days`
- Нормализация для отображения: делить на `(1024 * 1024)` чтобы получить "МБ·дней"
- Цветовое кодирование: квантиль 0–33% → зелёный, 33–66% → жёлтый, 66–100% → красный

### 7.2 Потоковое сканирование (генератор)
```python
def scan(root: Path, ...) -> Generator[FileInfo, None, None]:
    for entry in os.scandir(root):
        if entry.is_dir(follow_symlinks=False):
            yield from scan(entry.path, ...)   # рекурсия
        elif entry.is_file(follow_symlinks=False):
            yield build_file_info(entry)
```
Это гарантирует O(1) использование памяти относительно числа файлов.

### 7.3 Обход ошибок
```python
try:
    stat = entry.stat()
except (PermissionError, OSError) as e:
    logger.warning("Skipped %s: %s", entry.path, e)
    stats.skipped_files += 1
    return None
```

---

## 8. HTML-шаблон — структура и поведение

### Разделы страницы
1. **Header** — заголовок, дата генерации, сканируемый путь
2. **Dashboard** — 5 карточек со статистикой
3. **Charts Row** — Bar chart (расширения) + Treemap (директории)
4. **Controls** — поиск, фильтры по расширению, кнопка экспорта CSV
5. **Table** — интерактивная таблица файлов
6. **Footer** — версия инструмента, время генерации отчёта

### Встраивание данных
Данные передаются через inline `<script>`:
```html
<script>
  const FILE_DATA = /* JSON_PLACEHOLDER */;
  const STATS_DATA = /* STATS_PLACEHOLDER */;
</script>
```
Python заменяет плейсхолдеры на сериализованный JSON.

### Сортировка таблицы
- Клик по заголовку — сортировка ASC, повторный клик — DESC
- Визуальный индикатор (стрелка) на активном столбце
- Default sort: `uselessness_index DESC`

### Пагинация
- State: `{page: 1, perPage: 50, totalPages: N}`
- Кнопки: «← Пред», номера страниц (до 7 видимых), «След →»

---

## 9. Принципы и паттерны разработки

### Архитектурные принципы
- **SRP (Single Responsibility Principle)** — каждый модуль отвечает только за одно
- **Pipeline Pattern** — данные проходят цепочку: scan → filter → metrics → report
- **Generator Pattern** — для обхода ФС (экономия памяти)
- **Template Method** — `ReportBuilder.build()` вызывает шаги в строгом порядке

### Качество кода
- **Type Annotations** — 100% аннотации, проверка через `mypy --strict`
- **Dataclasses** — для моделей вместо словарей (явность + автогенерация `__repr__`)
- **Guard Clauses** — ранний `return`/`continue` вместо вложенных `if`
- **Константы** — все магические числа в `constants.py` (например, `BYTES_IN_MB = 1_048_576`)
- **f-strings** — форматирование строк только через f-strings (не `%` и не `.format()`)
- **Docstrings** — Google-style для всех публичных функций и классов

### Обработка ошибок
- **Never Silent Fail** — все исключения логируются с уровнем `WARNING` или `ERROR`
- **Graceful Degradation** — ошибка доступа к одному файлу не останавливает весь скан

### Тестируемость
- Чистые функции без побочных эффектов там, где возможно
- `Scanner` принимает `root: Path` — легко мокается в тестах
- `ReportBuilder` принимает данные, не зависит от ФС

---

## 10. Улучшения (сверх базового ТЗ)

| # | Улучшение | Ценность |
|---|---|---|
| 1 | **Дубликаты файлов** — поиск файлов с одинаковым хешем (MD5) | Реально помогает освободить место |
| 2 | **Сравнительный отчёт** — передать два пути `--compare A B`, показать дельту | Удобно для мониторинга роста |
| 3 | **Категоризация по типу** — медиа / документы / архивы / код / прочее | Наглядно видно «что занимает место» |
| 4 | **Прогресс-бар в CLI** — через `sys.stdout.write` без зависимостей | UX при сканировании больших дисков |
| 5 | **Кеширование** — сохранять результат скана в `.cache.json`, при повторном запуске — инкрементальное обновление | Скорость на больших каталогах |
| 6 | **Dark mode** — автоматически через `@media (prefers-color-scheme: dark)` | Комфорт при использовании |
| 7 | **Permalink** — кнопка «Скопировать путь» рядом с каждым файлом | Удобно при ручной чистке |
| 8 | **Watch mode** — `--watch` для автоматического пересканирования каждые N минут | Для мониторинга в реальном времени |

---

## 11. Тестирование

### Unit-тесты (stdlib `unittest` или `pytest`)
- `test_metrics.py` — проверка формулы uselessness_index
- `test_filters.py` — фильтрация по размеру, расширению, idle_days
- `test_formatting.py` — human_readable_size (граничные значения: 0, 1023, 1024, 1_000_000_000)
- `test_scanner.py` — мок временной директории с `tempfile.TemporaryDirectory`

### Integration-тесты
- Полный прогон на тестовой директории с известной структурой
- Проверка, что HTML-файл генерируется и содержит корректный JSON

### Граничные случаи
- Пустая директория
- Директория с одним файлом
- Файлы с нулевым размером
- Симлинки (не следовать)
- Файлы без прав на чтение
- Очень длинные пути (> 260 символов — Windows)

---

## 12. Совместимость

| ОС | Особенности |
|---|---|
| Linux | `ctime` = время изменения метаданных, не создания |
| macOS | `st_birthtime` доступен для истинной даты создания |
| Windows | `ctime` = истинная дата создания; пути могут быть Unicode |

Использовать `platform.system()` для ветвления при получении `ctime`.

---

## 13. Пример запуска

```bash
# Базовый анализ домашней папки
python analyzer.py ~/Documents --output report.html

# Только большие файлы, не трогавшиеся 90+ дней
python analyzer.py /var/log --min-size 1MB --min-idle 90 --output old_logs.html

# Анализ с исключениями и лимитом глубины
python analyzer.py /home --exclude /home/.cache /home/.local --depth 4 --verbose

# С экспортом сырых данных
python analyzer.py /data --json raw_data.json --output report.html
```

---

## 14. Выходные артефакты

| Файл | Описание |
|---|---|
| `report.html` | Автономный HTML-отчёт |
| `raw_data.json` | (опционально) Сырые данные в JSON |
| `analyzer.log` | Лог-файл (если включён `--verbose`) |
