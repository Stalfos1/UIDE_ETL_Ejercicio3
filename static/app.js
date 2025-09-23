// ==== Config ===
const AUTH_HEADER = { 'Authorization': 'Basic ' + btoa('admin:1234') }; // Ajusta a tu .env

// ==== Elementos UI ====
let priceChart, volChart, gainersChart, signalsChart;
const tbody = document.querySelector('#prices-table tbody');
const cryptoSelect = document.getElementById('cryptoSelect');
const resSelect = document.getElementById('resSelect');
const pointsCount = document.getElementById('pointsCount');
const lastPrice = document.getElementById('lastPrice');

// ==== Utiles ====
const fmt = (v, min=2, max=6) => {
  const n = parseNum(v);
  if (Number.isNaN(n)) return '-';
  return n.toLocaleString(undefined, { minimumFractionDigits: min, maximumFractionDigits: max });
};
const parsePct = (s) => {
  if (s == null) return 0;
  if (typeof s === 'number') return s;
  const m = String(s).match(/-?\d+(?:\.\d+)?/);
  return m ? parseFloat(m[0]) : 0;
};
const parseNum = (s) => {
  if (s == null) return 0;
  if (typeof s === 'number') return s;
  const m = String(s).replace(/[^\d\.-]/g, '');
  return m ? parseFloat(m) : 0;
};

// ==== Tabla principal ====
async function fetchTable() {
  try {
    const res = await fetch('/api/table', { headers: AUTH_HEADER });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();

    // Render filas
    tbody.innerHTML = '';
    data.rows.forEach(r => {
      const tr = document.createElement('tr');
      const pct = parsePct(r.pct_change_24h);
      const vol = parseNum(r.volatility_1h);

      tr.innerHTML = `
        <td><b>${r.crypto ?? '-'}</b></td>
        <td class="num">${fmt(r.actual_price)}</td>
        <td class="num">${fmt(r.highest_1h)}</td>
        <td class="num">${fmt(r.lower_1h)}</td>
        <td class="num">${fmt(r.avg_1h)}</td>
        <td class="num">${fmt(vol)}</td>
        <td class="num" style="font-weight:700; color:${pct>0?'#16a34a':pct<0?'#dc2626':'#6b7280'}">${pct.toFixed(2)}%</td>
        <td class="sig signal-${r.signal ?? '-'}">${r.signal ?? '-'}</td>`;
      tbody.appendChild(tr);
    });

    // Rellenar select de cryptos (primera vez o si cambia el conjunto)
    const current = cryptoSelect.value;
    const symbols = data.rows.map(r => r.crypto);
    if (cryptoSelect.options.length === 0 || Array.from(cryptoSelect.options).map(o=>o.value).join(',') !== symbols.join(',')) {
      cryptoSelect.innerHTML = symbols.map(s => `<option value="${s}">${s}</option>`).join('');
      if (symbols.includes(current)) cryptoSelect.value = current;
    }

    // Cargar paneles de análisis
    buildAnalysis(data.rows);

    // Si no hay gráfico cargado aún, dibuja
    if (!priceChart) drawChart();
  } catch (err) {
    console.error('Error en fetchTable:', err);
  }
}

// ==== Gráfico de línea (arrays/{res}/{crypto}) ====
async function fetchSeries(crypto, resolution) {
  const res = await fetch(`/api/arrays/${resolution}/${crypto}`, { headers: AUTH_HEADER });
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  const labels = data.points.map(p => new Date(p.ts * 1000));
  const prices = data.points.map(p => parseFloat(p.price));
  return { labels, prices, crypto: data.crypto, resolution: data.resolution };
}

async function drawChart() {
  try {
    const crypto = cryptoSelect.value || (cryptoSelect.options[0] && cryptoSelect.options[0].value);
    const resolution = resSelect.value || 'minute';
    if (!crypto) return;

    const { labels, prices } = await fetchSeries(crypto, resolution);

    // KPIs
    pointsCount.textContent = labels.length;
    lastPrice.textContent = prices.length ? fmt(prices[prices.length-1]) : '-';

    // (re)crear canvas
    const canvas = document.getElementById('chart');
    if (priceChart) { priceChart.destroy(); }

    priceChart = new Chart(canvas.getContext('2d'), {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: `${crypto} (${resolution})`,
          data: prices,
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.2,
          fill: false,
          borderColor: '#3b82f6'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { type: 'time', time: { unit: resolution === 'day' ? 'day' : resolution === 'hour' ? 'hour' : 'minute' } },
          y: { beginAtZero: false }
        },
        plugins: { legend: { display: true } }
      }
    });
  } catch (err) {
    console.error('Error en drawChart:', err);
  }
}

// ==== Panel: Análisis ====
function buildAnalysis(rows) {
  // 1) Volatilidad top 5
  const vol = rows
    .map(r => ({ crypto: r.crypto, v: parseNum(r.volatility_1h) }))
    .sort((a,b)=>b.v-a.v)
    .slice(0,5);
  const volLabels = vol.map(x=>x.crypto);
  const volData = vol.map(x=>x.v);

  const vc = document.getElementById('volatilityChart').getContext('2d');
  if (volChart) volChart.destroy();
  volChart = new Chart(vc, {
    type: 'bar',
    data: { labels: volLabels, datasets: [{ label: 'Volatilidad 1H', data: volData }] },
    options: {
      responsive:true,
      scales: { y: { beginAtZero: true } },
      plugins: { legend: { display: false } }
    }
  });

  // 2) Ganadores top 5 por % 24H
  const winners = rows
    .map(r => ({ crypto: r.crypto, p: parsePct(r.pct_change_24h) }))
    .sort((a,b)=>b.p-a.p)
    .slice(0,5);
  const gLabels = winners.map(x=>x.crypto);
  const gData = winners.map(x=>x.p);

  const gc = document.getElementById('gainersChart').getContext('2d');
  if (gainersChart) gainersChart.destroy();
  gainersChart = new Chart(gc, {
    type: 'bar',
    data: { labels: gLabels, datasets: [{ label: '% 24H', data: gData }] },
    options: {
      responsive:true,
      scales: { y: { beginAtZero: true } },
      plugins: { legend: { display: false } }
    }
  });

  // 3) Distribución de señales
  const counts = rows.reduce((acc, r) => { acc[r.signal || '-'] = (acc[r.signal || '-']||0)+1; return acc; }, {});
  const sLabels = Object.keys(counts);
  const sData = Object.values(counts);

  const sc = document.getElementById('signalsChart').getContext('2d');
  if (signalsChart) signalsChart.destroy();
  signalsChart = new Chart(sc, {
    type: 'doughnut',
    data: { labels: sLabels, datasets: [{ data: sData }] },
    options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
  });
}

// ==== Eventos / timers ====
setInterval(fetchTable, 5000);  // tabla + paneles
setInterval(drawChart, 10000);  // gráfico serie
cryptoSelect.addEventListener('change', drawChart);
resSelect.addEventListener('change', drawChart);

// Primer render
fetchTable();

window.addEventListener('resize', () => { if (priceChart) priceChart.resize(); });
