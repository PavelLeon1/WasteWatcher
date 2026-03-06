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
  <!-- Chart.js CDN -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <!-- DATA -->
  <script>
    const FILE_DATA = {FILE_DATA_PLACEHOLDER};
    const STATS_DATA = {STATS_DATA_PLACEHOLDER};
  </script>
  <!-- APP LOGIC -->
  <script>
    {JS}
  </script>
</body>
</html>"""


# Для обратной совместимости с builder.py
TEMPLATE: str = build_template()
