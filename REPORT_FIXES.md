# 🛠️ Исправления HTML-отчёта — Disk Space Analyzer

Все исправления касаются только отчёта. Backend (scanner, filters, metrics) трогать не нужно.
Исправляй по порядку, после каждого пункта проверяй в браузере.

---

## Баг #1 — Total Size показывает «0 B»

### Симптом
Карточка дашборда `Total Size` отображает `0 B`, хотя файлы найдены и их размеры в таблице корректны.

### Причина
Поле `total_size_bytes` в `ScanStats` не накапливается в процессе сканирования, либо накапливается, но не передаётся в `stats_data` при сериализации в JSON для шаблона.

### Что проверить и исправить

**1. В `core/scanner.py`** — убедись что внутри генератора `scan_directory` после создания `FileInfo` есть накопление:
```python
stats.total_size_bytes += file_info.size_bytes
stats.total_files += 1
yield file_info
```

**2. В `analyzer.py`** — после материализации списка `files = list(filtered)` пересчитай stats явно, так как генератор мог завершиться раньше накопления:
```python
stats.total_size_bytes = sum(f.size_bytes for f in files)
stats.total_files = len(files)
stats.total_size_human = human_readable_size(stats.total_size_bytes)
```

**3. В `report/builder.py`** — в методе `_prepare_data()` убедись что `total_size_human` берётся из `stats`, а не вычисляется заново из нуля:
```python
# НЕВЕРНО:
"total_size": "0 B"

# ВЕРНО:
"total_size": self.stats.total_size_human
```

**4. В `report/template.py`** — в JS убедись что карточка читает правильное поле:
```javascript
// Должно быть именно это поле из STATS_DATA:
document.getElementById('total-size').textContent = STATS_DATA.total_size_human;
// или STATS_DATA.total_size — в зависимости от того как названо поле в to_dict()
```

### Проверка
Запусти анализ любой папки с файлами, открой отчёт — карточка `Total Size` должна показывать суммарный размер, совпадающий с суммой колонки `Size` в таблице.

---

## Баг #2 — Вертикальные скроллбары выбиваются из стилистики

### Симптом
Нативные скроллбары браузера (серые/белые) отображаются в тёмном интерфейсе и визуально конфликтуют со стилем.

### Исправление — добавить в CSS блок кастомных скроллбаров

Добавь в `<style>` шаблона следующие правила (работает в Chrome, Edge, Safari; Firefox — отдельно):

```css
/* Webkit-браузеры: Chrome, Edge, Safari */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 3px;
  transition: background 0.2s;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.30);
}

::-webkit-scrollbar-corner {
  background: transparent;
}

/* Firefox */
* {
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.15) transparent;
}
```

### Проверка
Скроллбары должны стать тонкими (6px), полупрозрачными, в тёмной гамме. Прокрутка работает как прежде.

---

## Баг #3 — Top 10 Useless Files: пункты после #8 теряют фон

### Симптом
Строки #9 и #10 в блоке «Top 10» отображаются без белого/светлого фона — фон пропадает или становится прозрачным.

### Причина
CSS-правило для строк списка использует селектор с ограничением, например `:nth-child(-n+8)`, или контейнер имеет фиксированную высоту без `overflow: visible`, обрезающую нижние элементы. Либо JS рендерит только первые 8 элементов.

### Что проверить и исправить

**В CSS** — найди стиль строки Top 10 (скорее всего `.top-file-item` или `.useless-item`) и проверь нет ли:
```css
/* УДАЛИ или исправь если найдёшь что-то подобное: */
.top-file-item:nth-child(-n+8) { background: ...; }

/* ДОЛЖНО БЫТЬ без ограничения: */
.top-file-item { background: rgba(255, 255, 255, 0.05); }
```

**Высота контейнера** — найди родительский контейнер списка Top 10 и убедись что нет `max-height` или `height` обрезающего содержимое:
```css
/* НЕВЕРНО: */
.top-list { max-height: 320px; overflow: hidden; }

/* ВЕРНО: */
.top-list { overflow: visible; }
```

**В JS** — найди место где рендерится Top 10 и убедись что итерация идёт до 10, а не до 8:
```javascript
// НЕВЕРНО:
const topFiles = STATS_DATA.top_useless.slice(0, 8);

// ВЕРНО:
const topFiles = STATS_DATA.top_useless.slice(0, 10);
```

### Проверка
Все 10 строк должны иметь одинаковый фон и отступы без визуальных различий между #8 и #9.

---

## Баг #4 — Горизонтальный скролл в таблице файлов

### Симптом
Таблица шире видимой области, внизу появляется горизонтальная полоса прокрутки. Колонка `Uselessness (human)` и последние столбцы уходят за край.

### Исправление — три шага

**Шаг 4.1 — убрать горизонтальный скролл у контейнера таблицы:**
```css
/* Найди обёртку таблицы и замени: */

/* НЕВЕРНО: */
.table-wrapper {
  overflow-x: auto;
}

/* ВЕРНО: */
.table-wrapper {
  overflow-x: hidden;
  width: 100%;
}
```

**Шаг 4.2 — сделать таблицу адаптивной по ширине:**
```css
table {
  width: 100%;
  table-layout: fixed;   /* ключевое свойство — делит ширину поровну */
  border-collapse: collapse;
}
```

**Шаг 4.3 — задать явные пропорции колонок через `colgroup`**

Добавь в HTML-шаблон перед `<thead>` блок `<colgroup>` с процентной шириной каждой колонки. Итого должно быть 100%:

```html
<colgroup>
  <col style="width: 4%">   <!-- Level (цветная точка) -->
  <col style="width: 24%">  <!-- Path -->
  <col style="width: 18%">  <!-- Name -->
  <col style="width: 5%">   <!-- Ext -->
  <col style="width: 10%">  <!-- Size (bytes) -->
  <col style="width: 9%">   <!-- Size (human) -->
  <col style="width: 8%">   <!-- Idle Days -->
  <col style="width: 12%">  <!-- Uselessness -->
  <col style="width: 10%">  <!-- Uselessness (human) -->
</colgroup>
```

**Шаг 4.4 — обрезать длинные пути через CSS, а не JS:**
```css
td {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;  /* длинный путь → "...конец/пути" */
  max-width: 0;             /* работает только при table-layout: fixed */
}
```

**Шаг 4.5 — адаптировать ширину всей страницы под таблицу:**
```css
/* Контейнер страницы должен занимать всю ширину viewport: */
.container, main, .report-body {
  max-width: 100%;
  padding: 0 24px;
  box-sizing: border-box;
}
```

### Проверка
- Горизонтального скролла нет ни на странице, ни внутри таблицы
- Все колонки видны одновременно
- Длинные пути обрезаются с `...` (при наведении браузер показывает полный путь через `title`-атрибут — добавь его при рендере строк в JS: `td.title = fullPath`)
- На узких экранах (1280px) таблица не вылезает за края

---

## Порядок применения исправлений

```
Баг #1 (Total Size = 0)          → правка Python backend + шаблон
Баг #4 (горизонтальный скролл)   → правка CSS + colgroup в шаблоне
Баг #2 (вертикальные скроллбары) → добавить CSS блок
Баг #3 (Top 10 фон)              → правка CSS + проверить JS slice
```

После всех правок запусти финальный тест:
```bash
python analyzer.py D:\Games --output test_fixed.html
```
Открой `test_fixed.html` и пройди чеклист:
- [ ] Total Size показывает реальный размер
- [ ] Горизонтального скролла нет
- [ ] Скроллбары тонкие и тёмные
- [ ] Все 10 строк Top 10 имеют одинаковый фон
