// ========================
// Variables y selects
// ========================
const cryptoSelect = document.getElementById('cryptoSelect');
const resSelect = document.getElementById('resSelect');
const tbody = document.querySelector('#prices-table tbody');
const AUTH_HEADER = { 'Authorization': 'Basic ' + btoa('admin:1234') };

// ========================
// Funciones auxiliares
// ========================
const parseNum = s => {
  if (s == null) return 0;
  if (typeof s === 'number') return s;
  const m = String(s).replace(/[^\d\.-]/g, '');
  return m ? parseFloat(m) : 0;
};

const parsePct = s => {
  if (s == null) return 0;
  if (typeof s === 'number') return s;
  const m = String(s).match(/-?\d+(?:\.\d+)?/);
  return m ? parseFloat(m[0]) : 0;
};

const fmt = (v, min = 2, max = 6) => {
  const n = parseNum(v);
  return Number.isNaN(n) ? '-' : n.toLocaleString(undefined, { minimumFractionDigits: min, maximumFractionDigits: max });
};

// ========================
// Transformación de velas
// ========================
function transformCandleData(candles) {
  return candles.map(c => ({
    x: new Date(c.ts * 1000),
    open: parseFloat(c.open),
    high: parseFloat(c.high),
    low: parseFloat(c.low),
    close: parseFloat(c.close)
  }));
}

// ========================
// Dibujar gráfico con Plotly
// ========================
function drawPlotlyChart(candleData, crypto, resolution) {
  Plotly.purge('chart');

  const trace = {
    x: candleData.map(c => c.x),
    open: candleData.map(c => c.open),
    high: candleData.map(c => c.high),
    low: candleData.map(c => c.low),
    close: candleData.map(c => c.close),
    type: 'candlestick',
    increasing: { line: { color: 'green' } },
    decreasing: { line: { color: 'red' } },
    name: `${crypto} (${resolution})`
  };

  const layout = {
    title: `${crypto} (${resolution})`,
    xaxis: { type: 'date', title: 'Tiempo' },
    yaxis: { autorange: true, title: 'Precio' },
    margin: { t: 30, b: 30 }
  };

  Plotly.newPlot('chart', [trace], layout, { responsive: true });
}

// ========================
// Fetch y dibujar gráfico
// ========================
async function drawChart() {
  const crypto = cryptoSelect.value;
  const resolution = resSelect.value;
  if (!crypto) return;

  try {
    const resp = await fetch(`/static/ohlc_snapshots/${crypto}_${resolution}.json`);
    if (!resp.ok) throw new Error(`Archivo OHLC no encontrado: ${crypto}_${resolution}.json`);

    const data = await resp.json();
    const candleData = transformCandleData(data.candles || []);
    if (!candleData.length) return;

    drawPlotlyChart(candleData, crypto, resolution);
  } catch (err) {
    console.error("Error dibujando gráfico OHLC:", err);
  }
}

// ========================
// Tabla principal
// ========================
async function fetchTable() {
  try {
    const res = await fetch('/api/table', { headers: AUTH_HEADER });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();

    tbody.innerHTML = '';

    data.rows.forEach(r => {
      const pct = parsePct(r.pct_change_24h);
      const vol = parseNum(r.volatility_1h);
      const sigClass = r.signal === 'B' ? 'signal-B' : (r.signal === 'S' ? 'signal-S' : 'signal--');

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><b>${r.crypto ?? '-'}</b></td>
        <td class="num">${fmt(r.actual_price)}</td>
        <td class="num">${fmt(r.highest_1h)}</td>
        <td class="num">${fmt(r.lower_1h)}</td>
        <td class="num">${fmt(r.avg_1h)}</td>
        <td class="num">${fmt(vol)}</td>
        <td class="num" style="font-weight:700; color:${pct>0?'#16a34a':pct<0?'#dc2626':'#6b7280'}">${pct.toFixed(2)}%</td>
        <td class="sig ${sigClass}">${r.signal ?? '-'}</td>
      `;
      tbody.appendChild(tr);
    });

    // Actualizar select de cryptos
    const current = cryptoSelect.value;
    const symbols = data.rows.map(r => r.crypto);
    if (!cryptoSelect.options.length || Array.from(cryptoSelect.options).map(o=>o.value).join(',') !== symbols.join(',')) {
      cryptoSelect.innerHTML = symbols.map(s => `<option value="${s}">${s}</option>`).join('');
      if (symbols.includes(current)) cryptoSelect.value = current;
    }

  } catch (err) {
    console.error('Error fetching table:', err);
  }
}

// ========================
// Intervalos y eventos
// ========================
setInterval(fetchTable, 5000);
setInterval(drawChart, 5000);
cryptoSelect.addEventListener('change', drawChart);
resSelect.addEventListener('change', drawChart);

// ========================
// Primer render
// ========================
fetchTable().then(drawChart);
