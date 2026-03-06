# 🛠️ Исправления — Производительность и архитектура шаблона

---

## Баг #5 — Зависание при «Show All» (100k+ файлов)

### Причина

В `renderTable()` при `perPage === 0` весь массив `filteredData` (100k+ элементов)
превращается в одну гигантскую HTML-строку через `.map().join('')` и затем одним
вызовом `tbody.innerHTML = ...` вставляется в DOM. Браузер пытается отрендерить
100 000 строк одновременно — поток блокируется на 10–30 секунд.

### Решение — заменить «Show All» на чанковый рендер с `requestAnimationFrame`

**Шаг 5.1 — убрать опцию «0 = все» из select, добавить разумный максимум:**

Найди в шаблоне `<select id="per-page-select">` и замени его содержимое:

```html
<select id="per-page-select">
  <option value="25">25 per page</option>
  <option value="50" selected>50 per page</option>
  <option value="100">100 per page</option>
  <option value="250">250 per page</option>
  <option value="500">500 (slow)</option>
</select>
```

> Убери опцию `value="0"` («All») полностью — она источник проблемы.
> 500 строк рендерится мгновенно, а навигация по 2076 страницам удобнее, чем зависший браузер.

**Шаг 5.2 — исправить `renderTable()` убрав ветку `perPage === 0`:**

Найди функцию `renderTable()` и замени её полностью:

```javascript
function renderTable() {
  const tbody = document.getElementById('table-body');
  const perPage = state.perPage;
  const start = (state.currentPage - 1) * perPage;
  const end = start + perPage;
  const pageData = state.filteredData.slice(start, end);

  if (pageData.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:40px;color:var(--color-text-muted)">Файлы не найдены</td></tr>';
    renderPagination();
    return;
  }

  // Строим HTML одной строкой — быстрее серии appendChild
  tbody.innerHTML = pageData.map(file => `
    <tr class="useless-${file.uselessness_level || 'low'}">
      <td>${getLevelIcon(file.uselessness_level)}</td>
      <td class="path-cell" title="${escapeHtml(file.path || '')}">${escapeHtml(truncatePath(file.path || ''))}</td>
      <td>${escapeHtml(file.name || '')}</td>
      <td>${escapeHtml(file.extension || '')}</td>
      <td>${escapeHtml(file.size_human || '0 B')}</td>
      <td>${file.idle_days ?? 0}</td>
      <td>${(file.uselessness_index || 0).toLocaleString(undefined, {maximumFractionDigits: 0})}</td>
      <td>${escapeHtml(file.uselessness_human || '0.00 MB·days')}</td>
    </tr>
  `).join('');

  renderPagination();
}
```

**Шаг 5.3 — исправить `renderPagination()` убрав ветки `perPage === 0`:**

Найди все вхождения `state.perPage === 0` в `renderPagination()` и `goToPage()` — удали эти условия, оставив только обычную логику пагинации.

Конкретно заменить:
```javascript
// БЫЛО:
const totalPages = state.perPage === 0 ? 1 : Math.ceil(totalItems / state.perPage);
const start = state.perPage === 0 ? 1 : (state.currentPage - 1) * state.perPage + 1;
const end = state.perPage === 0 ? totalItems : Math.min(...);

// СТАЛО:
const totalPages = Math.ceil(totalItems / state.perPage);
const start = (state.currentPage - 1) * state.perPage + 1;
const end = Math.min(state.currentPage * state.perPage, totalItems);
```

**Шаг 5.4 — добавить индикатор загрузки при смене страницы (UX):**

Перед `tbody.innerHTML = ...` добавь мгновенный визуальный отклик:

```javascript
// В начало renderTable(), перед map():
tbody.style.opacity = '0.4';
requestAnimationFrame(() => {
  tbody.innerHTML = pageData.map(...).join('');
  tbody.style.opacity = '1';
  renderPagination();
});
// Убери вызов renderPagination() в конце — он теперь внутри rAF
```

**Шаг 5.5 — защита от слишком большого perPage через URL/прямой ввод:**

В обработчике смены `per-page-select` добавь guard:

```javascript
perPageSelect.addEventListener('change', (e) => {
  const val = parseInt(e.target.value, 10);
  state.perPage = Math.min(val, 500); // Максимум 500 строк
  state.currentPage = 1;
  renderTable();
});
```

### Проверка
Открой отчёт с 100k+ файлами. Выбери `500 per page` — рендер должен занять < 100мс.
Кнопки пагинации навигируют по страницам без зависания.

---

## Задача #6 — Разбить `template.py` на модули (защита от повреждений агентом)

### Проблема

`template.py` содержит 1000+ строк смешанного Python/HTML/CSS/JS.
Когда агент редактирует один блок CSS — он рискует задеть соседний JS.
При частичной перезаписи файла через `str_replace` агент иногда теряет контекст
и «склеивает» строки неправильно, ломая всю Python-строку шаблона.

### Решение — разбить на 4 независимых файла

**Новая структура:**

```
report/
├── __init__.py
├── builder.py          ← не трогать, он не меняется
├── template.py         ← станет тонким: только сборка из частей (30 строк)
├── _template_css.py    ← весь CSS (~300 строк)
├── _template_js.py     ← весь JavaScript (~400 строк)
└── _template_html.py   ← HTML-скелет (~150 строк)
```

Нижнее подчёркивание в именах `_template_*.py` сигнализирует агенту:
«это внутренние части, не импортировать напрямую».

---

### Шаг 6.1 — Создать `report/_template_css.py`

Вырезать из `TEMPLATE` весь блок между `<style>` и `</style>` (не включая теги)
и поместить в новый файл:

```python
"""CSS-стили HTML-отчёта."""

CSS: str = """
    /* CSS VARIABLES */
    :root { ... }

    /* BASE STYLES */
    * { ... }

    /* ... весь CSS ... */

    /* CUSTOM SCROLLBARS */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 3px; }
    * { scrollbar-width: thin; scrollbar-color: rgba(255,255,255,0.15) transparent; }
"""
```

---

### Шаг 6.2 — Создать `report/_template_js.py`

Вырезать из `TEMPLATE` всё содержимое между `<script>` и `</script>`
(кроме строк с плейсхолдерами `FILE_DATA_JSON` / `STATS_DATA_JSON`) и поместить:

```python
"""JavaScript-логика HTML-отчёта."""

# Плейсхолдеры остаются в шаблоне — JS-файл содержит только функции
JS: str = """
    const state = {
      allData: [],
      filteredData: [],
      currentPage: 1,
      perPage: 50,
      sortColumn: 'uselessness_index',
      sortDirection: 'desc',
    };

    function renderTable() { ... }
    function renderPagination() { ... }
    function sortBy(column) { ... }
    function filterTable(query) { ... }
    function exportCSV() { ... }
    // ... весь JS ...
"""
```

---

### Шаг 6.3 — Создать `report/_template_html.py`

HTML-скелет страницы (теги, блоки разметки, без CSS и JS):

```python
"""HTML-структура отчёта."""

HTML_BODY: str = """
  <div class="header">
    <div class="header-info">
      <h1>🗂 Disk Space Analyzer Report</h1>
      <p class="header-meta">Path: <strong id="scan-path"></strong></p>
      <p class="header-meta">Generated: <strong id="generated-at"></strong></p>
    </div>
  </div>

  <div class="dashboard" id="dashboard"></div>

  <div class="charts-row">
    <div class="chart-card">
      <h2>По расширениям</h2>
      <canvas id="ext-chart"></canvas>
    </div>
    <div class="chart-card">
      <h2>Топ 10 бесполезных файлов</h2>
      <div id="top-useless-list"></div>
    </div>
  </div>

  <div class="table-section">
    <div class="table-controls">
      <input type="text" id="search-input" placeholder="Search files..." oninput="filterTable(this.value)">
      <select id="per-page-select">
        <option value="25">25 per page</option>
        <option value="50" selected>50 per page</option>
        <option value="100">100 per page</option>
        <option value="250">250 per page</option>
        <option value="500">500 (slow)</option>
      </select>
      <button onclick="exportCSV()">⬇ Export CSV</button>
    </div>
    <div class="table-wrapper">
      <table>
        <colgroup>
          <col style="width:4%">
          <col style="width:24%">
          <col style="width:18%">
          <col style="width:5%">
          <col style="width:9%">
          <col style="width:7%">
          <col style="width:13%">
          <col style="width:10%">
        </colgroup>
        <thead> ... </thead>
        <tbody id="table-body"></tbody>
      </table>
    </div>
    <div id="pagination"></div>
  </div>

  <footer>Generated by Disk Space Analyzer v{version}</footer>
"""
```

---

### Шаг 6.4 — Переписать `report/template.py` (станет тонким сборщиком)

```python
"""
Сборщик HTML-шаблона из отдельных модулей.

Каждый компонент живёт в своём файле:
- _template_css.py  — стили
- _template_js.py   — логика
- _template_html.py — разметка

Редактируй нужный компонент, не трогая остальные.
"""

from report._template_css import CSS
from report._template_js import JS
from report._template_html import HTML_BODY
from core.constants import VERSION

FILE_DATA_PLACEHOLDER = "$FILE_DATA_JSON"
STATS_DATA_PLACEHOLDER = "$STATS_DATA_JSON"


def build_template() -> str:
    """
    Собирает финальный HTML-шаблон из компонентов.

    Returns:
        Строка с полным HTML-шаблоном и плейсхолдерами для данных.
    """
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Disk Space Analyzer Report</title>
  <style>{CSS}</style>
</head>
<body>
  <div class="container">
    {HTML_BODY.format(version=VERSION)}
  </div>
  <script>
    const FILE_DATA = {FILE_DATA_PLACEHOLDER};
    const STATS_DATA = {STATS_DATA_PLACEHOLDER};
    {JS}
  </script>
</body>
</html>"""


# Для обратной совместимости с builder.py
TEMPLATE: str = build_template()
```

---

### Шаг 6.5 — Обновить `report/builder.py`

`builder.py` использует `TEMPLATE` из `template.py` — он останется совместимым
без изменений. Но если хочешь явность — замени импорт:

```python
# Было:
from report.template import TEMPLATE, FILE_DATA_PLACEHOLDER, STATS_DATA_PLACEHOLDER

# Стало (опционально, только для явности):
from report.template import TEMPLATE, FILE_DATA_PLACEHOLDER, STATS_DATA_PLACEHOLDER
# ← импорт тот же, builder.py менять не нужно
```

---

### Промпт для Qwen при выполнении этой задачи

Отправь агенту следующее сообщение:

```
Прочитай REPORT_FIXES.md раздел «Задача #6».

Выполняй строго по шагам 6.1 → 6.2 → 6.3 → 6.4:

1. Прочитай report/template.py полностью
2. Создай report/_template_css.py — вырежи CSS-блок
3. Создай report/_template_js.py — вырежи JS-блок
4. Создай report/_template_html.py — вырежи HTML body
5. Перепиши report/template.py как тонкий сборщик (см. Шаг 6.4)
6. Запусти: python analyzer.py . --output test_split.html --top 10
7. Убедись что test_split.html открывается и таблица работает

НЕ редактируй builder.py — он останется совместимым автоматически.
После каждого созданного файла сообщай сколько строк в нём.
```

---

### Итог после рефакторинга

| Файл | Строк | Что редактировать |
|---|---|---|
| `template.py` | ~30 | Никогда (только сборка) |
| `_template_css.py` | ~300 | При правке стилей |
| `_template_js.py` | ~400 | При правке логики таблицы |
| `_template_html.py` | ~150 | При правке разметки |

Агент теперь работает только с нужным файлом и не рискует задеть соседний код.

---

## Порядок выполнения

```
Сначала: Баг #5 (Show All → убрать опцию, исправить renderTable)
Затем:   Задача #6 (разбить template.py на модули)
```

Баг #5 — это 10 минут правки JS.
Задача #6 — рефакторинг на 20–30 минут, но после него работа с шаблоном станет
значительно надёжнее.
