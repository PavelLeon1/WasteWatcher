# 🔧 Code Review — Исправления найденных багов

Все баги найдены при анализе кода. Исправляй по порядку.
После каждого исправления запускай самопроверку модуля (`python -m core.filters` и т.д.).

---

## Баг #CR-1 — Импорт внутри горячей функции (`core/scanner.py`)

### Серьёзность: 🟡 Средняя

### Проблема

```python
# scanner.py — функция build_file_info()
def build_file_info(entry, logger):
    ...
    from utils.formatting import human_readable_size  # ← внутри функции!
    size_human = human_readable_size(size_bytes)
```

`build_file_info` вызывается для **каждого файла** при сканировании.
Python кеширует модули, поэтому падения нет — но при каждом вызове
интерпретатор всё равно делает lookup в `sys.modules`. На 100k файлов
это 100k лишних словарных обращений. Кроме того, такой стиль
— признак скрытой проблемы с круговыми импортами, которую агент
обошёл симптоматически вместо того чтобы решить по-настоящему.

### Исправление

Перенести импорт на уровень модуля в начало `scanner.py`:

```python
# БЫЛО — импорт внутри функции build_file_info():
from utils.formatting import human_readable_size

# СТАЛО — в начало файла, после остальных импортов:
import logging
import os
import sys
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from core.constants import SCANNER_BATCH_SIZE
from core.metrics import calculate_idle_days, calculate_uselessness, format_uselessness
from core.models import FileInfo, ScanStats
from utils.formatting import human_readable_size  # ← сюда
```

Внутри `build_file_info` строку `from utils.formatting import human_readable_size` — удалить.

### Проверка

```bash
python -c "from core.scanner import scan_directory; print('OK')"
```

Если был циклический импорт — он проявится здесь. Если OK — баг устранён.

---

## Баг #CR-2 — Импорт внутри цикла (`core/models.py`)

### Серьёзность: 🟡 Средняя

### Проблема

```python
# models.py — метод update_dir_sizes()
def update_dir_sizes(self, files: list[FileInfo]) -> None:
    self.dir_sizes = {}
    for file in files:
        from pathlib import Path  # ← импорт на каждой итерации цикла!
        parent = str(Path(file.path).parent)
        ...
```

Та же проблема что в CR-1, только хуже — импорт внутри цикла
по всем файлам. `pathlib` уже используется в других местах проекта,
поэтому это явное недоразумение.

### Исправление

```python
# В начало models.py добавить (если ещё нет):
from pathlib import Path

# Метод update_dir_sizes — убрать импорт из цикла:
def update_dir_sizes(self, files: list[FileInfo]) -> None:
    """
    Вычисляет размеры директорий (сумма размеров файлов в каждой).

    Args:
        files: Список файлов для анализа.
    """
    self.dir_sizes = {}
    for file in files:
        parent = str(Path(file.path).parent)  # Path уже импортирован выше
        self.dir_sizes[parent] = self.dir_sizes.get(parent, 0) + file.size_bytes
```

### Проверка

```bash
python -m core.models
# Вывод: models: OK
```

---

## Баг #CR-3 — Бессмысленный try/except теряет traceback (`report/builder.py`)

### Серьёзность: 🔴 Высокая

### Проблема

```python
# builder.py — метод _write_file()
def _write_file(self, html: str) -> None:
    try:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(html, encoding="utf-8")
    except (OSError, PermissionError) as e:
        raise e  # ← АНТИПАТТЕРН: теряет оригинальный traceback!
```

`raise e` вместо `raise` — классическая ошибка. При `raise e` Python
создаёт **новый** traceback, начиная с этой строки, скрывая реальное
место ошибки. В логах при падении будет видна строка `raise e`
вместо строки где реально произошла `OSError`.

Пример разницы в traceback:
```
# С raise e — вводит в заблуждение:
  File "builder.py", line 89, in _write_file
    raise e

# С raise — показывает реальное место:
  File "builder.py", line 87, in _write_file
    self.output_path.write_text(html, encoding="utf-8")
PermissionError: [Errno 13] Permission denied: 'report.html'
```

### Исправление

```python
def _write_file(self, html: str) -> None:
    """
    Записывает HTML в output_path (UTF-8).

    Args:
        html: Готовый HTML-документ.

    Raises:
        OSError: При ошибке записи файла.
        PermissionError: При отсутствии прав на запись.
    """
    # Создаём родительские директории если нужно
    self.output_path.parent.mkdir(parents=True, exist_ok=True)
    # Записываем файл — исключения пробрасываются выше без обёртки
    self.output_path.write_text(html, encoding="utf-8")
```

Обработка `OSError` и `PermissionError` уже есть в `analyzer.py`
который вызывает `generate_report` — там она осмысленная (логирует и
возвращает код ошибки). Дублировать её в `_write_file` не нужно.

### Проверка

```bash
python -m report.builder
# Вывод: builder: OK

# Дополнительно — проверь что ошибка пробрасывается корректно:
python -c "
from pathlib import Path
from report.builder import ReportBuilder
from core.models import ScanStats
b = ReportBuilder([], ScanStats(), Path('/нет/такого/пути/x/y/z/r.html'))
try:
    b._write_file('test')
except OSError as e:
    print(f'OK — ошибка поймана корректно: {type(e).__name__}')
"
```

---

## Баг #CR-4 — `max_depth_filter` считает абсолютную глубину вместо относительной (`core/filters.py`)

### Серьёзность: 🔴 Высокая (неверное поведение фича `--depth`)

### Проблема

```python
# filters.py — функция max_depth_filter()
def _filter(file: FileInfo) -> bool:
    from pathlib import Path
    depth = len(Path(file.path).parts) - 1  # ← абсолютная глубина!
    return depth <= max_depth
```

Для файла `D:\Projects\WasteWatcher\core\models.py`:
```
Path(...).parts = ('D:\\', 'Projects', 'WasteWatcher', 'core', 'models.py')
depth = 5 - 1 = 4
```

При запуске `python analyzer.py D:\Projects\WasteWatcher --depth 2`
пользователь ожидает увидеть файлы на 2 уровня вглубь от `WasteWatcher`.
Но фильтр не знает корневой путь и сравнивает `4 <= 2` → файл пропускается.

В результате `--depth` на Windows с длинными путями может вернуть **0 файлов**,
а на Linux с короткими путями работать случайно правильно.

### Исправление

Фильтр должен знать корневой путь сканирования. Есть два варианта:

**Вариант A (рекомендуется) — передавать `root_path` в фабрику:**

```python
def max_depth_filter(max_depth: int, root_path: str) -> FileFilter:
    """
    Создаёт фильтр по максимальной глубине вложенности относительно корня.

    Args:
        max_depth: Максимальная глубина (количество уровней от root_path).
        root_path: Абсолютный путь корневой директории сканирования.

    Returns:
        Функция-фильтр.

    Example:
        >>> f = max_depth_filter(2, "/home/user")
        >>> # /home/user/a/b.txt → depth 1 → True
        >>> # /home/user/a/b/c/d.txt → depth 3 → False
    """
    root = Path(root_path)

    def _filter(file: FileInfo) -> bool:
        try:
            relative = Path(file.path).relative_to(root)
            # parts у относительного пути: ('core', 'models.py') → глубина 1
            depth = len(relative.parts) - 1
            return depth <= max_depth
        except ValueError:
            # Файл не является дочерним для root — пропускаем
            return False

    return _filter
```

**Обновить `build_filter_pipeline`** — добавить параметр `root_path`:

```python
def build_filter_pipeline(
    min_size: int | None = None,
    extensions: list[str] | None = None,
    min_idle: int | None = None,
    exclude_hidden: bool = False,
    max_depth: int | None = None,
    root_path: str | None = None,   # ← добавить
) -> list[FileFilter]:
    ...
    if max_depth is not None and root_path is not None:
        filters.append(max_depth_filter(max_depth, root_path))
    elif max_depth is not None:
        import logging
        logging.getLogger("disk_analyzer").warning(
            "--depth задан без root_path, фильтр по глубине не применяется"
        )

    return filters
```

**Обновить вызов в `analyzer.py`:**

```python
filters = build_filter_pipeline(
    min_size=min_size_bytes,
    extensions=args.ext,
    min_idle=args.min_idle if args.min_idle > 0 else None,
    exclude_hidden=args.no_hidden,
    max_depth=args.depth,
    root_path=str(scan_path),   # ← добавить
)
```

### Проверка

```bash
# Создай тестовую структуру:
mkdir -p /tmp/depth_test/level1/level2/level3
echo "root" > /tmp/depth_test/root.txt
echo "l1" > /tmp/depth_test/level1/l1.txt
echo "l2" > /tmp/depth_test/level1/level2/l2.txt
echo "l3" > /tmp/depth_test/level1/level2/level3/l3.txt

python analyzer.py /tmp/depth_test --depth 1 --output /tmp/depth_test.html
# Ожидание: root.txt и l1.txt → 2 файла
# НЕ должно быть: l2.txt, l3.txt

python analyzer.py /tmp/depth_test --depth 2 --output /tmp/depth_test2.html
# Ожидание: root.txt, l1.txt, l2.txt → 3 файла
```

---

## Баг #CR-5 — Двойное вычисление метрик (`analyzer.py`)

### Серьёзность: 🟢 Низкая (логическая ошибка, не влияет на результат)

### Проблема

```python
# analyzer.py — функция apply_filters_and_metrics()
def apply_filters_and_metrics(files, filters):
    for file in files:
        if filters and not all(f(file) for f in filters):
            continue

        # Вычисление метрик (если ещё не вычислены)
        if file.idle_days == 0 and file.uselessness_index == 0:  # ← неверная проверка
            compute_file_metrics(file)

        yield file
```

Условие `idle_days == 0 and uselessness_index == 0` должно означать
«метрики не вычислены». Но оно ложно срабатывает для **реально свежих файлов**:
файл созданный и accessed сегодня имеет `idle_days=0` и `uselessness_index=0`
по формуле, а не потому что метрики не считались.

Кроме того, метрики уже вычисляются в `build_file_info` в `scanner.py`.
Функция `compute_file_metrics` здесь принципиально лишняя —
это мёртвый код пути.

### Исправление

Убрать лишнюю проверку и вызов `compute_file_metrics`:

```python
def apply_filters_and_metrics(
    files: Iterable[FileInfo],
    filters: list,
) -> Generator[FileInfo, None, None]:
    """
    Применяет фильтры к потоку файлов.

    Метрики уже вычислены в scanner.build_file_info() —
    здесь только фильтрация.

    Args:
        files: Генератор FileInfo из сканера.
        filters: Список фильтров.

    Yields:
        FileInfo, прошедшие все фильтры.
    """
    for file in files:
        if filters and not all(f(file) for f in filters):
            continue
        yield file
```

Добавить аннотации типов в сигнатуру — агент оставил `files` и `filters`
без аннотаций, что нарушает требование `mypy --strict`:

```python
from collections.abc import Generator, Iterable
from core.models import FileInfo
from core.filters import FileFilter

def apply_filters_and_metrics(
    files: Iterable[FileInfo],
    filters: list[FileFilter],
) -> Generator[FileInfo, None, None]:
```

Импорт `compute_file_metrics` из `analyzer.py` можно удалить если он
использовался только здесь:

```python
# Проверь imports в analyzer.py — если есть:
from core.metrics import assign_uselessness_levels, compute_file_metrics
# Убери compute_file_metrics:
from core.metrics import assign_uselessness_levels
```

### Проверка

```bash
python analyzer.py . --output /tmp/test_cr5.html --top 5
# Открой отчёт — метрики должны быть корректными для всех файлов
# включая файлы с idle_days=0 (сегодняшние)
```

---

## Порядок применения

```
CR-3 (builder.py)    → 2 минуты, 1 строка
CR-2 (models.py)     → 2 минуты, убрать импорт из цикла
CR-1 (scanner.py)    → 3 минуты, перенести импорт наверх
CR-5 (analyzer.py)   → 5 минут, упростить функцию + аннотации
CR-4 (filters.py)    → 15 минут, самый объёмный — менять сигнатуры
```

CR-4 трогай последним — он меняет сигнатуры функций в трёх файлах
(`filters.py`, `analyzer.py` и тесты в `if __name__ == "__main__"`).