"""
CSS-стили HTML-отчёта.

Этот файл содержит только CSS-стили.
Редактируй этот файл при изменении стилей отчёта.
"""

CSS: str = """
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
"""
