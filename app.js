const data = window.DASHBOARD_DATA || { tables: {}, figures: [] };
const tabsRoot = document.getElementById('tabs');
const tablesRoot = document.getElementById('tables-root');
const graphPanel = document.getElementById('panel-graficas');
const subtitle = document.getElementById('subtitle');
const updatedAtEl = document.getElementById('updated-at');
const unidadesRegistroEl = document.getElementById('value-unidades-registro');
const unidadesRegistroDetailEl = document.getElementById('value-unidades-registro-detail');
const estadosRegistroEl = document.getElementById('value-estados-registro');
const estadosRegistroDetailEl = document.getElementById('value-estados-registro-detail');
const unidadesCompletasEl = document.getElementById('value-unidades-completas');
const unidadesCompletasDetailEl = document.getElementById('value-unidades-completas-detail');

const updateStorePrefix = `dashboard-update:${window.location.pathname}`;

function parseValidDate(value) {
  if (!value) return null;
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function getDataSignature() {
  try {
    return JSON.stringify({
      tables: data.tables || {},
      figures: data.figures || [],
    });
  } catch {
    return '';
  }
}

function readStoredUpdateInfo() {
  try {
    return {
      signature: localStorage.getItem(`${updateStorePrefix}:signature`),
      updatedAt: localStorage.getItem(`${updateStorePrefix}:updatedAt`),
    };
  } catch {
    return { signature: null, updatedAt: null };
  }
}

function writeStoredUpdateInfo(signature, updatedAt) {
  try {
    localStorage.setItem(`${updateStorePrefix}:signature`, signature);
    localStorage.setItem(`${updateStorePrefix}:updatedAt`, updatedAt.toISOString());
  } catch {
    // Ignorar si el navegador bloquea localStorage.
  }
}

function resolveDataUpdatedAt() {
  const signature = getDataSignature();
  const fromData = parseValidDate(
    data.updated_at || data.updatedAt || data.last_updated || data.lastUpdated
  );

  if (fromData) {
    writeStoredUpdateInfo(signature, fromData);
    return fromData;
  }

  const stored = readStoredUpdateInfo();
  if (stored.signature === signature) {
    const storedDate = parseValidDate(stored.updatedAt);
    if (storedDate) return storedDate;
  }

  const now = new Date();
  writeStoredUpdateInfo(signature, now);
  return now;
}

if (data.title) document.title = data.title;
if (subtitle) {
  const nTables = Object.keys(data.tables || {}).length;
  const nCharts = (data.figures || []).length;
  subtitle.textContent = `Visualizacion general con ${nCharts} grafica(s) y ${nTables} tabla(s).`;
}

if (updatedAtEl) {
  const updatedAt = resolveDataUpdatedAt();
  const fechaHora = updatedAt.toLocaleString('es-MX', {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
  updatedAtEl.textContent = `Actualizado: ${fechaHora}`;
}

function formatNumber(value) {
  return new Intl.NumberFormat('es-MX').format(value || 0);
}

function calculateSummaryMetrics() {
  const avanceRows = data.tables?.tabla_avance?.rows || [];
  const entidadesRows = data.tables?.tabla_entidades?.rows || [];

  const totalEstados = avanceRows.length;
  const estadosConRegistro = avanceRows.reduce((sum, row) => {
    return Number(row.unidades_respondieron || 0) > 0 ? sum + 1 : sum;
  }, 0);
  const totalUnidades = avanceRows.reduce((sum, row) => sum + Number(row.total_unidades || 0), 0);
  const unidadesConRegistro = avanceRows.reduce((sum, row) => sum + Number(row.unidades_respondieron || 0), 0);
  const unidadesCompletas = entidadesRows.reduce((sum, row) => {
    return Number(row.porcentaje || 0) >= 100 ? sum + Number(row.unidades || 0) : sum;
  }, 0);

  return {
    totalEstados,
    estadosConRegistro,
    totalUnidades,
    unidadesConRegistro,
    unidadesCompletas,
  };
}

function renderSummaryMetrics() {
  const metrics = calculateSummaryMetrics();
  const porcentajeCompletas = metrics.unidadesConRegistro
    ? (metrics.unidadesCompletas / metrics.unidadesConRegistro) * 100
    : 0;

  if (unidadesRegistroEl) {
    unidadesRegistroEl.textContent = formatNumber(metrics.unidadesConRegistro);
  }
  if (unidadesRegistroDetailEl) {
    unidadesRegistroDetailEl.textContent = `de ${formatNumber(metrics.totalUnidades)} unidades totales`;
  }
  if (estadosRegistroEl) {
    estadosRegistroEl.textContent = formatNumber(metrics.estadosConRegistro);
  }
  if (estadosRegistroDetailEl) {
    estadosRegistroDetailEl.textContent = `de ${formatNumber(metrics.totalEstados)} estados totales`;
  }
  if (unidadesCompletasEl) {
    unidadesCompletasEl.textContent = formatNumber(metrics.unidadesCompletas);
  }
  if (unidadesCompletasDetailEl) {
    unidadesCompletasDetailEl.textContent = `${porcentajeCompletas.toFixed(1)}% de las unidades con registro`;
  }
}

function activatePanel(panelId, button) {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  const panel = document.getElementById(panelId);
  if (panel) panel.classList.add('active');
  if (button) button.classList.add('active');

  if (panelId === 'panel-graficas') {
    setTimeout(() => {
      document.querySelectorAll('.chart').forEach(el => Plotly.Plots.resize(el));
    }, 120);
  }
}

function createTab(label, panelId, isActive = false) {
  const btn = document.createElement('button');
  btn.className = 'tab-btn';
  btn.type = 'button';
  btn.textContent = label;
  btn.addEventListener('click', () => activatePanel(panelId, btn));
  tabsRoot.appendChild(btn);
  if (isActive) btn.classList.add('active');
}

function getRenderableFigures() {
  const seen = new Set();
  return (data.figures || []).filter(item => {
    const figure = item.figure || {};
    const signature = JSON.stringify({
      data: figure.data || [],
      layout: figure.layout || {},
    });
    if (seen.has(signature)) return false;
    seen.add(signature);
    return true;
  });
}

function renderGraphs() {
  graphPanel.className = 'panel active';
  const wrap = document.createElement('div');
  wrap.className = 'grid';
  graphPanel.appendChild(wrap);

  const figures = getRenderableFigures();

  if (subtitle) {
    const nTables = Object.keys(data.tables || {}).length;
    subtitle.textContent = `Visualizacion general con ${figures.length} grafica(s) y ${nTables} tabla(s).`;
  }

  figures.forEach((item, i) => {
    const card = document.createElement('article');
    card.className = 'chart-card';
    const chartId = `chart-${i}`;
    const el = document.createElement('div');
    el.id = chartId;
    el.className = 'chart';
    card.appendChild(el);
    wrap.appendChild(card);

    const figure = item.figure || {};
    const finalLayout = {
      ...(figure.layout || {}),
      autosize: true,
    };

    if (typeof figure?.layout?.height === 'number') {
      el.style.height = `${figure.layout.height}px`;
      card.style.minHeight = `${Math.max(figure.layout.height + 20, 180)}px`;
    }

    Plotly.react(chartId, figure.data || [], finalLayout, {
      responsive: true,
      displayModeBar: true,
      displaylogo: false,
    });
  });

  if (!figures.length) {
    graphPanel.innerHTML = '<p>No hay graficas disponibles.</p>';
  }
}

function renderTablePanel(name, tableData) {
  const panelId = `panel-${name}`;
  const section = document.createElement('section');
  section.id = panelId;
  section.className = 'panel';

  const toolbar = document.createElement('div');
  toolbar.className = 'table-toolbar';
  if (tableData.excel) {
    const link = document.createElement('a');
    link.className = 'btn-excel';
    link.href = tableData.excel;
    link.download = tableData.excel;
    link.textContent = 'Descargar Excel';
    toolbar.appendChild(link);
  }
  section.appendChild(toolbar);

  const wrap = document.createElement('div');
  wrap.className = 'table-wrap';

  const table = document.createElement('table');
  const thead = document.createElement('thead');
  const trh = document.createElement('tr');
  (tableData.columns || []).forEach(col => {
    const th = document.createElement('th');
    th.textContent = col;
    trh.appendChild(th);
  });
  thead.appendChild(trh);
  table.appendChild(thead);

  const tbody = document.createElement('tbody');
  (tableData.rows || []).forEach(row => {
    const tr = document.createElement('tr');
    (tableData.columns || []).forEach(col => {
      const td = document.createElement('td');
      const value = row[col];
      td.textContent = value == null ? '' : String(value);
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);

  wrap.appendChild(table);
  section.appendChild(wrap);
  tablesRoot.appendChild(section);

  return panelId;
}

createTab('Principal - Graficas', 'panel-graficas', true);
renderSummaryMetrics();
renderGraphs();

Object.entries(data.tables || {}).forEach(([name, tableData]) => {
  const panelId = renderTablePanel(name, tableData);
  createTab(name.replace('tabla_', 'Tabla ').replace(/_/g, ' '), panelId, false);
});

window.addEventListener('resize', () => {
  document.querySelectorAll('.chart').forEach(el => Plotly.Plots.resize(el));
});
