"""
HTML/CSS/JS шаблон отчёта.

Полный автономный шаблон для генерации интерактивного отчёта.
"""

from core.constants import (
    CHART_BAR_CATEGORIES_LIMIT,
    TREEMAP_CATEGORIES_LIMIT,
    VERSION,
)

# Плейсхолдеры для подстановки данных
FILE_DATA_PLACEHOLDER = "$FILE_DATA_JSON"
STATS_DATA_PLACEHOLDER = "$STATS_DATA_JSON"


TEMPLATE: str = """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Disk Space Analyzer Report</title>
  <style>
    /* =============================================================================
       CSS VARIABLES
       ============================================================================= */
    :root {
      --color-primary: #3b82f6;
      --color-primary-dark: #2563eb;
      --color-success: #22c55e;
      --color-warning: #f59e0b;
      --color-danger: #ef4444;
      --color-bg: #f8fafc;
      --color-surface: #ffffff;
      --color-text: #1e293b;
      --color-text-muted: #64748b;
      --color-border: #e2e8f0;
      --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
      --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
      --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
      --radius: 8px;
      --font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    /* Dark mode */
    @media (prefers-color-scheme: dark) {
      :root {
        --color-bg: #0f172a;
        --color-surface: #1e293b;
        --color-text: #f1f5f9;
        --color-text-muted: #94a3b8;
        --color-border: #334155;
        --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.3);
        --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.4);
        --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.5);
      }
    }

    /* =============================================================================
       BASE STYLES
       ============================================================================= */
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    html {
      overflow-x: hidden;
    }

    body {
      font-family: var(--font-family);
      background-color: var(--color-bg);
      color: var(--color-text);
      line-height: 1.6;
      padding: 20px;
      overflow-x: hidden;
    }

    .container {
      max-width: 100%;
      margin: 0 auto;
      padding: 0 24px;
      box-sizing: border-box;
    }

    h1, h2, h3 {
      margin-bottom: 0.5em;
      color: var(--color-text);
    }

    h1 {
      font-size: 1.75rem;
      font-weight: 700;
    }

    h2 {
      font-size: 1.25rem;
      font-weight: 600;
    }

    /* =============================================================================
       HEADER
       ============================================================================= */
    .header {
      background: var(--color-surface);
      padding: 20px;
      border-radius: var(--radius);
      box-shadow: var(--shadow-sm);
      margin-bottom: 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 15px;
    }

    .header-info {
      display: flex;
      flex-direction: column;
      gap: 5px;
    }

    .header-meta {
      font-size: 0.875rem;
      color: var(--color-text-muted);
    }

    /* =============================================================================
       DASHBOARD CARDS
       ============================================================================= */
    .dashboard {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 15px;
      margin-bottom: 20px;
    }

    .card {
      background: var(--color-surface);
      padding: 20px;
      border-radius: var(--radius);
      box-shadow: var(--shadow-sm);
      transition: transform 0.2s, box-shadow 0.2s;
    }

    .card:hover {
      transform: translateY(-2px);
      box-shadow: var(--shadow-md);
    }

    .card-label {
      font-size: 0.875rem;
      color: var(--color-text-muted);
      margin-bottom: 8px;
    }

    .card-value {
      font-size: 1.5rem;
      font-weight: 700;
      color: var(--color-text);
    }

    .card-value.success { color: var(--color-success); }
    .card-value.warning { color: var(--color-warning); }
    .card-value.danger { color: var(--color-danger); }

    /* =============================================================================
       CHARTS ROW
       ============================================================================= */
    .charts-row {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
      gap: 15px;
      margin-bottom: 20px;
      overflow-x: auto;
    }

    .chart-container {
      background: var(--color-surface);
      padding: 20px;
      border-radius: var(--radius);
      box-shadow: var(--shadow-sm);
      height: 350px;
      position: relative;
      display: flex;
      flex-direction: column;
      overflow-y: auto;
    }

    .chart-title {
      font-size: 1rem;
      font-weight: 600;
      margin-bottom: 15px;
      color: var(--color-text);
      flex-shrink: 0;
    }

    .chart-canvas-wrapper {
      flex: 1;
      position: relative;
      min-height: 0;
    }

    /* =============================================================================
       TABLE CONTROLS
       ============================================================================= */
    .controls {
      background: var(--color-surface);
      padding: 15px 20px;
      border-radius: var(--radius);
      box-shadow: var(--shadow-sm);
      margin-bottom: 15px;
      display: flex;
      flex-wrap: wrap;
      gap: 15px;
      align-items: center;
      justify-content: space-between;
    }

    .search-box {
      display: flex;
      align-items: center;
      gap: 10px;
      flex: 1;
      min-width: 250px;
    }

    .search-box input {
      flex: 1;
      padding: 10px 15px;
      border: 1px solid var(--color-border);
      border-radius: var(--radius);
      background: var(--color-bg);
      color: var(--color-text);
      font-size: 0.875rem;
    }

    .search-box input:focus {
      outline: none;
      border-color: var(--color-primary);
    }

    .controls-right {
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
    }

    .btn {
      padding: 10px 20px;
      border: none;
      border-radius: var(--radius);
      cursor: pointer;
      font-size: 0.875rem;
      font-weight: 500;
      transition: background-color 0.2s;
    }

    .btn-primary {
      background: var(--color-primary);
      color: white;
    }

    .btn-primary:hover {
      background: var(--color-primary-dark);
    }

    .btn-secondary {
      background: var(--color-bg);
      color: var(--color-text);
      border: 1px solid var(--color-border);
    }

    .btn-secondary:hover {
      background: var(--color-border);
    }

    .pagination-select {
      padding: 10px 15px;
      border: 1px solid var(--color-border);
      border-radius: var(--radius);
      background: var(--color-bg);
      color: var(--color-text);
      font-size: 0.875rem;
      cursor: pointer;
    }

    /* =============================================================================
       TABLE
       ============================================================================= */
    .table-container {
      background: var(--color-surface);
      border-radius: var(--radius);
      box-shadow: var(--shadow-sm);
      overflow: hidden;
      margin-bottom: 20px;
    }

    .table-wrapper {
      overflow-x: hidden;
      max-height: 70vh;
      overflow-y: auto;
      width: 100%;
    }

    table {
      width: 100%;
      table-layout: fixed;
      border-collapse: collapse;
      font-size: 0.875rem;
    }

    thead {
      position: sticky;
      top: 0;
      background: var(--color-surface);
      z-index: 10;
      box-shadow: 0 2px 4px var(--color-bg);
    }

    th {
      padding: 15px 12px;
      text-align: left;
      font-weight: 600;
      color: var(--color-text);
      border-bottom: 2px solid var(--color-border);
      cursor: pointer;
      user-select: none;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    th:hover {
      background: var(--color-bg);
    }

    th .sort-icon {
      margin-left: 5px;
      opacity: 0.5;
    }

    th.sorted .sort-icon {
      opacity: 1;
    }

    td {
      padding: 12px 15px;
      border-bottom: 1px solid var(--color-border);
      color: var(--color-text);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      max-width: 0;
    }

    tbody tr {
      transition: background-color 0.2s;
    }

    tbody tr:hover {
      background: var(--color-bg) !important;
    }

    /* Color coding by uselessness level */
    .useless-low {
      background-color: rgba(34, 197, 94, 0.1);
    }

    .useless-medium {
      background-color: rgba(245, 158, 11, 0.15);
    }

    .useless-high {
      background-color: rgba(239, 68, 68, 0.15);
    }

    /* Path truncation */
    .path-cell {
      max-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    /* =============================================================================
       CUSTOM SCROLLBARS
       ============================================================================= */
    /* Webkit browsers: Chrome, Edge, Safari */
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

    /* =============================================================================
       PAGINATION
       ============================================================================= */
    .pagination {
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 10px;
      padding: 15px;
      background: var(--color-surface);
      border-top: 1px solid var(--color-border);
      flex-wrap: wrap;
    }

    .pagination-info {
      font-size: 0.875rem;
      color: var(--color-text-muted);
    }

    .pagination-btn {
      padding: 8px 16px;
      border: 1px solid var(--color-border);
      border-radius: var(--radius);
      background: var(--color-bg);
      color: var(--color-text);
      cursor: pointer;
      font-size: 0.875rem;
      transition: background-color 0.2s;
    }

    .pagination-btn:hover:not(:disabled) {
      background: var(--color-border);
    }

    .pagination-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .pagination-btn.active {
      background: var(--color-primary);
      color: white;
      border-color: var(--color-primary);
    }

    /* =============================================================================
       FOOTER
       ============================================================================= */
    .footer {
      text-align: center;
      padding: 20px;
      color: var(--color-text-muted);
      font-size: 0.875rem;
    }

    /* =============================================================================
       RESPONSIVE
       ============================================================================= */
    @media (max-width: 768px) {
      body {
        padding: 10px;
      }

      .container {
        padding: 0 10px;
      }

      .header {
        flex-direction: column;
        align-items: flex-start;
      }

      .charts-row {
        grid-template-columns: 1fr;
      }

      .chart-container {
        height: 300px;
      }

      .controls {
        flex-direction: column;
        align-items: stretch;
      }

      .search-box {
        min-width: 100%;
      }

      .controls-right {
        justify-content: stretch;
      }

      .btn {
        flex: 1;
        text-align: center;
      }

      .table-wrapper {
        max-height: 50vh;
      }
    }

    /* =============================================================================
       TOP FILES LIST
       ============================================================================= */
    .top-files-list {
      list-style: none;
      font-size: 0.875rem;
    }

    .top-files-list li {
      padding: 8px 0;
      border-bottom: 1px solid var(--color-border);
      display: flex;
      justify-content: space-between;
      gap: 10px;
      background: rgba(255, 255, 255, 0.03);
      border-radius: 4px;
      margin-bottom: 4px;
    }

    .top-files-list li:nth-child(odd) {
      background: rgba(255, 255, 255, 0.05);
    }

    .top-files-list li:last-child {
      border-bottom: none;
      margin-bottom: 0;
    }

    .top-file-name {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      flex: 1;
    }

    .top-file-size {
      font-weight: 600;
      color: var(--color-primary);
      white-space: nowrap;
    }
  </style>
</head>
<body>
  <div class="container">
    <!-- HEADER -->
    <header class="header">
      <div class="header-info">
        <h1>📊 Disk Space Analyzer Report</h1>
        <div class="header-meta">
          <div>Path: <strong id="scan-path">—</strong></div>
          <div>Generated: <strong id="report-date">—</strong></div>
        </div>
      </div>
    </header>

    <!-- DASHBOARD -->
    <section class="dashboard">
      <div class="card">
        <div class="card-label">📁 Total Files</div>
        <div class="card-value" id="stat-total-files">0</div>
      </div>
      <div class="card">
        <div class="card-label">💾 Total Size</div>
        <div class="card-value success" id="stat-total-size">0 B</div>
      </div>
      <div class="card">
        <div class="card-label">⏱️ Scan Duration</div>
        <div class="card-value" id="stat-duration">0.00s</div>
      </div>
      <div class="card">
        <div class="card-label">⚠️ Skipped Files</div>
        <div class="card-value warning" id="stat-skipped">0</div>
      </div>
      <div class="card">
        <div class="card-label">📈 Avg Uselessness</div>
        <div class="card-value" id="stat-avg-useless">0 MB·days</div>
      </div>
    </section>

    <!-- TOP FILES + CHARTS -->
    <section class="charts-row">
      <div class="chart-container">
        <h3 class="chart-title">🏆 Top 10 Useless Files</h3>
        <ul class="top-files-list" id="top-files-list"></ul>
      </div>
      <div class="chart-container">
        <h3 class="chart-title">📊 Files by Extension</h3>
        <div class="chart-canvas-wrapper">
          <canvas id="ext-chart"></canvas>
        </div>
      </div>
    </section>

    <!-- CONTROLS -->
    <section class="controls">
      <div class="search-box">
        <input type="text" id="search-input" placeholder="🔍 Search files..." aria-label="Search files">
      </div>
      <div class="controls-right">
        <select class="pagination-select" id="per-page-select" aria-label="Items per page">
          <option value="25">25 per page</option>
          <option value="50" selected>50 per page</option>
          <option value="100">100 per page</option>
          <option value="250">250 per page</option>
          <option value="500">500 (slow)</option>
        </select>
        <button class="btn btn-secondary" id="export-csv-btn" title="Export to CSV">
          📥 Export CSV
        </button>
      </div>
    </section>

    <!-- TABLE -->
    <section class="table-container">
      <div class="table-wrapper">
        <table id="files-table">
          <colgroup>
            <col style="width: 5%">
            <col style="width: 30%">
            <col style="width: 15%">
            <col style="width: 6%">
            <col style="width: 10%">
            <col style="width: 7%">
            <col style="width: 12%">
            <col style="width: 15%">
          </colgroup>
          <thead>
            <tr>
              <th data-sort="uselessness_level">Level<span class="sort-icon">↕</span></th>
              <th data-sort="path">Path<span class="sort-icon">↕</span></th>
              <th data-sort="name">Name<span class="sort-icon">↕</span></th>
              <th data-sort="extension">Ext<span class="sort-icon">↕</span></th>
              <th data-sort="size_human">Size<span class="sort-icon">↕</span></th>
              <th data-sort="idle_days">Idle Days<span class="sort-icon">↕</span></th>
              <th data-sort="uselessness_index">Uselessness<span class="sort-icon">↕</span></th>
              <th data-sort="uselessness_human">Uselessness (human)<span class="sort-icon">↕</span></th>
            </tr>
          </thead>
          <tbody id="table-body">
            <!-- Rows will be inserted here -->
          </tbody>
        </table>
      </div>
      <div class="pagination" id="pagination">
        <!-- Pagination controls will be inserted here -->
      </div>
    </section>

    <!-- FOOTER -->
    <footer class="footer">
      <p>Generated by Disk Space Analyzer v<span id="app-version">""" + VERSION + """</span></p>
      <p>Report generated at <span id="footer-date">—</span></p>
    </footer>
  </div>

  <!-- Chart.js CDN -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>

  <!-- DATA -->
  <script>
    const FILE_DATA = """ + FILE_DATA_PLACEHOLDER + """;
    const STATS_DATA = """ + STATS_DATA_PLACEHOLDER + """;
  </script>

  <!-- APP LOGIC -->
  <script>
    /* =============================================================================
       STATE
       ============================================================================= */
    const state = {
      data: FILE_DATA || [],
      filteredData: [],
      currentPage: 1,
      perPage: 50,
      sortColumn: 'uselessness_index',
      sortDirection: 'desc',
      searchQuery: ''
    };

    /* =============================================================================
       UTILITY FUNCTIONS
       ============================================================================= */
    function formatDate(isoString) {
      if (!isoString) return '—';
      const date = new Date(isoString);
      return date.toLocaleString('ru-RU', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    }

    function truncatePath(path, maxLength = 80) {
      if (path.length <= maxLength) return path;
      return '...' + path.slice(-(maxLength - 3));
    }

    function escapeHtml(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }

    /* =============================================================================
       SORTING
       ============================================================================= */
    function sortData(column) {
      if (state.sortColumn === column) {
        state.sortDirection = state.sortDirection === 'asc' ? 'desc' : 'asc';
      } else {
        state.sortColumn = column;
        state.sortDirection = 'desc';
      }

      state.filteredData.sort((a, b) => {
        let aVal = a[column];
        let bVal = b[column];

        // Handle null/undefined
        if (aVal === null || aVal === undefined) aVal = '';
        if (bVal === null || bVal === undefined) bVal = '';

        // Numeric comparison
        if (typeof aVal === 'number' && typeof bVal === 'number') {
          return state.sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
        }

        // String comparison
        aVal = String(aVal).toLowerCase();
        bVal = String(bVal).toLowerCase();
        if (state.sortDirection === 'asc') {
          return aVal.localeCompare(bVal);
        } else {
          return bVal.localeCompare(aVal);
        }
      });

      updateSortIndicators();
      renderTable();
    }

    function updateSortIndicators() {
      document.querySelectorAll('th[data-sort]').forEach(th => {
        th.classList.remove('sorted');
        const icon = th.querySelector('.sort-icon');
        if (icon) icon.textContent = '↕';
      });

      const activeTh = document.querySelector(`th[data-sort="${state.sortColumn}"]`);
      if (activeTh) {
        activeTh.classList.add('sorted');
        const icon = activeTh.querySelector('.sort-icon');
        if (icon) icon.textContent = state.sortDirection === 'asc' ? '↑' : '↓';
      }
    }

    /* =============================================================================
       FILTERING
       ============================================================================= */
    function filterData() {
      const query = state.searchQuery.toLowerCase().trim();

      if (!query) {
        state.filteredData = [...state.data];
      } else {
        state.filteredData = state.data.filter(file => {
          return (
            file.path?.toLowerCase().includes(query) ||
            file.name?.toLowerCase().includes(query) ||
            file.extension?.toLowerCase().includes(query) ||
            file.size_human?.toLowerCase().includes(query) ||
            file.uselessness_human?.toLowerCase().includes(query)
          );
        });
      }

      // Re-apply sorting
      sortData(state.sortColumn);
    }

    /* =============================================================================
       TABLE RENDERING
       ============================================================================= */
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

      // Индикатор загрузки
      tbody.style.opacity = '0.4';

      requestAnimationFrame(() => {
        tbody.innerHTML = pageData.map(file => `
          <tr class="useless-${file.uselessness_level || 'low'}">
            <td>${getLevelIcon(file.uselessness_level)}</td>
            <td class="path-cell" title="${escapeHtml(file.path || '')}">${escapeHtml(truncatePath(file.path || ''))}</td>
            <td>${escapeHtml(file.name || '')}</td>
            <td>${escapeHtml(file.extension || '')}</td>
            <td>${escapeHtml(file.size_human || '0 B')}</td>
            <td>${file.idle_days ?? 0}</td>
            <td>${(file.uselessness_index || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
            <td>${escapeHtml(file.uselessness_human || '0.00 MB·days')}</td>
          </tr>
        `).join('');

        tbody.style.opacity = '1';
        renderPagination();
      });
    }

    function getLevelIcon(level) {
      switch (level) {
        case 'low': return '🟢';
        case 'medium': return '🟡';
        case 'high': return '🔴';
        default: return '⚪';
      }
    }

    /* =============================================================================
       PAGINATION
       ============================================================================= */
    function renderPagination() {
      const pagination = document.getElementById('pagination');
      const totalItems = state.filteredData.length;
      const totalPages = Math.ceil(totalItems / state.perPage);

      if (totalPages <= 1) {
        pagination.innerHTML = `<span class="pagination-info">${totalItems} files total</span>`;
        return;
      }

      const start = (state.currentPage - 1) * state.perPage + 1;
      const end = Math.min(state.currentPage * state.perPage, totalItems);

      let html = `<span class="pagination-info">Showing ${start.toLocaleString()}–${end.toLocaleString()} of ${totalItems.toLocaleString()} files</span>`;

      // Previous button
      html += `<button class="pagination-btn" ${state.currentPage === 1 ? 'disabled' : ''} onclick="goToPage(${state.currentPage - 1})">← Prev</button>`;

      // Page numbers
      const pageNumbers = getPageNumbers(state.currentPage, totalPages);
      pageNumbers.forEach(page => {
        if (page === '...') {
          html += '<span class="pagination-btn" style="cursor:default;">...</span>';
        } else {
          html += `<button class="pagination-btn ${page === state.currentPage ? 'active' : ''}" onclick="goToPage(${page})">${page}</button>`;
        }
      });

      // Next button
      html += `<button class="pagination-btn" ${state.currentPage === totalPages ? 'disabled' : ''} onclick="goToPage(${state.currentPage + 1})">Next →</button>`;

      pagination.innerHTML = html;
    }

    function getPageNumbers(current, total) {
      if (total <= 7) {
        return Array.from({ length: total }, (_, i) => i + 1);
      }

      const pages = [];
      if (current <= 4) {
        pages.push(1, 2, 3, 4, 5, '...', total);
      } else if (current >= total - 3) {
        pages.push(1, '...', total - 4, total - 3, total - 2, total - 1, total);
      } else {
        pages.push(1, '...', current - 1, current, current + 1, '...', total);
      }
      return pages;
    }

    function goToPage(page) {
      const totalPages = Math.ceil(state.filteredData.length / state.perPage);
      if (page < 1 || page > totalPages) return;
      state.currentPage = page;
      renderTable();
    }

    /* =============================================================================
       DASHBOARD
       ============================================================================= */
    function renderDashboard() {
      if (!STATS_DATA) return;

      document.getElementById('stat-total-files').textContent = (STATS_DATA.total_files || 0).toLocaleString();
      document.getElementById('stat-total-size').textContent = STATS_DATA.total_size_human || '0 B';
      document.getElementById('stat-duration').textContent = `${(STATS_DATA.scan_duration_sec || 0).toFixed(2)}s`;
      document.getElementById('stat-skipped').textContent = (STATS_DATA.skipped_files || 0).toLocaleString();
      document.getElementById('stat-avg-useless').textContent = `${(STATS_DATA.avg_uselessness || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;

      // Scan path and date
      const scanPath = document.getElementById('scan-path');
      if (STATS_DATA.scan_path) {
        scanPath.textContent = STATS_DATA.scan_path;
      } else if (state.data.length > 0) {
        // Extract common path prefix
        const firstPath = state.data[0]?.path || '';
        scanPath.textContent = firstPath.split(/[\\\\/]/).slice(0, 3).join('/') || 'Unknown';
      }

      const reportDate = new Date().toLocaleString('ru-RU');
      document.getElementById('report-date').textContent = reportDate;
      document.getElementById('footer-date').textContent = reportDate;
    }

    /* =============================================================================
       TOP FILES LIST
       ============================================================================= */
    function renderTopFiles() {
      const list = document.getElementById('top-files-list');
      const topFiles = (STATS_DATA?.top_useless || []).slice(0, 10);

      if (topFiles.length === 0) {
        list.innerHTML = '<li style="text-align:center;color:var(--color-text-muted);">No data available</li>';
        return;
      }

      list.innerHTML = topFiles.map((file, index) => `
        <li>
          <span class="top-file-name" title="${escapeHtml(file.path || '')}">
            <strong>#${index + 1}</strong> ${escapeHtml(file.name || 'Unknown')}
          </span>
          <span class="top-file-size">${escapeHtml(file.uselessness_human || '')}</span>
        </li>
      `).join('');
    }

    /* =============================================================================
       CHARTS
       ============================================================================= */
    let extChart = null;

    function renderCharts() {
      renderExtChart();
    }

    function renderExtChart() {
      const canvas = document.getElementById('ext-chart');
      if (!canvas) return;

      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      const extDist = STATS_DATA?.ext_distribution || {};
      const entries = Object.entries(extDist)
        .sort((a, b) => b[1] - a[1])
        .slice(0, """ + str(CHART_BAR_CATEGORIES_LIMIT) + """);

      if (entries.length === 0) {
        return;
      }

      const labels = entries.map(([ext]) => ext || '(no extension)');
      const data = entries.map(([, count]) => count);

      // Generate colors
      const colors = labels.map((_, i) => {
        const hue = (i * 137.508) % 360; // Golden angle
        return `hsl(${hue}, 70%, 50%)`;
      });

      // Destroy existing chart to prevent memory leaks and re-rendering issues
      if (extChart) {
        extChart.destroy();
      }

      extChart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            label: 'Files',
            data: data,
            backgroundColor: colors,
            borderColor: colors.map(c => c.replace('50%', '40%')),
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          aspectRatio: 2,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (ctx) => `${ctx.label}: ${ctx.parsed.y} files`
              }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              ticks: { precision: 0 }
            },
            x: {
              ticks: {
                autoSkip: true,
                maxRotation: 45,
                minRotation: 45
              }
            }
          }
        }
      });
    }

    /* =============================================================================
       CSV EXPORT
       ============================================================================= */
    function exportCSV() {
      const headers = [
        'Path', 'Name', 'Extension', 'Size (human)',
        'Idle Days', 'Uselessness Index', 'Uselessness (human)',
        'Level', 'Last Access', 'Modified', 'Created'
      ];

      const rows = state.filteredData.map(file => [
        `"${(file.path || '').replace(/"/g, '""')}"`,
        `"${(file.name || '').replace(/"/g, '""')}"`,
        `"${(file.extension || '').replace(/"/g, '""')}"`,
        `"${file.size_human || ''}"`,
        file.idle_days ?? 0,
        file.uselessness_index || 0,
        `"${file.uselessness_human || ''}"`,
        file.uselessness_level || 'low',
        file.atime || '',
        file.mtime || '',
        file.ctime || ''
      ]);

      const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\\n');
      downloadFile(csv, 'disk_analyzer_export.csv', 'text/csv');
    }

    function downloadFile(content, filename, mimeType) {
      const blob = new Blob([content], { type: mimeType });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }

    /* =============================================================================
       EVENT LISTENERS
       ============================================================================= */
    function initEventListeners() {
      // Search
      const searchInput = document.getElementById('search-input');
      searchInput.addEventListener('input', (e) => {
        state.searchQuery = e.target.value;
        state.currentPage = 1;
        filterData();
      });

      // Per page select
      const perPageSelect = document.getElementById('per-page-select');
      perPageSelect.addEventListener('change', (e) => {
        const val = parseInt(e.target.value, 10);
        state.perPage = Math.min(val, 500);  // Максимум 500 строк
        state.currentPage = 1;
        renderTable();
      });

      // Export CSV
      document.getElementById('export-csv-btn').addEventListener('click', exportCSV);

      // Table header sorting
      document.querySelectorAll('th[data-sort]').forEach(th => {
        th.addEventListener('click', () => {
          sortData(th.dataset.sort);
        });
      });
    }

    /* =============================================================================
       INITIALIZATION
       ============================================================================= */
    function init() {
      // Initial sort by uselessness_index DESC
      state.filteredData = [...state.data];
      sortData('uselessness_index');

      // Render UI
      renderDashboard();
      renderTopFiles();
      renderCharts();
      renderTable();

      // Event listeners
      initEventListeners();

      console.log('Disk Analyzer Report initialized');
      console.log(`Loaded ${state.data.length} files`);
    }

    // Start app when DOM is ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
    } else {
      init();
    }
  </script>
</body>
</html>"""
