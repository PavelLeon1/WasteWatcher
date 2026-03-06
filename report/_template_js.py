"""
JavaScript-логика HTML-отчёта.

Этот файл содержит только JavaScript-код.
Редактируй этот файл при изменении логики таблицы, пагинации, сортировки и т.д.
"""

JS: str = """
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
        .slice(0, 10);

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
"""
