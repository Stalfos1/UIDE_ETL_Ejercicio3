let chart;
const tbody = document.querySelector('#prices-table tbody');
const cryptoSelect = document.getElementById('cryptoSelect');
const resSelect = document.getElementById('resSelect');

// 🔹 Función para traer la tabla
async function fetchTable() {
  const res = await fetch('/api/table', {
    headers: {
      'Authorization': 'Basic ' + btoa('admin:1234') // ⚠️ Usuario y clave de .env (APP_USER, APP_PASS)
    }
  });
  const data = await res.json();
  tbody.innerHTML = '';
  data.rows.forEach(r => {
    const tr = document.createElement('tr');
    const sigClass = r.signal === 'B' ? 'signal-B' : (r.signal === 'S' ? 'signal-S' : 'signal--');
    tr.innerHTML = `
      <td>${r.crypto}</td>
      <td>${r.actual_price}</td>
      <td>${r.highest_1h}</td>
      <td>${r.lower_1h}</td>
      <td>${r.avg_1h}</td>
      <td class="${sigClass}">${r.signal}</td>
      <td>${r.volatility_1h}</td>
      <td>${r.pct_change_24h}</td>
    `;
    tbody.appendChild(tr);
  });

  // llenar el selector de criptos con el primer fetch
  if (cryptoSelect.options.length === 0) {
    data.rows.forEach(r => {
      const opt = document.createElement('option');
      opt.value = r.crypto;
      opt.textContent = r.crypto;
      cryptoSelect.appendChild(opt);
    });
    drawChart(); // primer render
  }
}

// 🔹 Serie simple (para resolución "second")
async function fetchSeries() {
  const c = cryptoSelect.value;
  const res = await fetch(`/api/arrays/${resSelect.value}/${c}`, {
    headers: {
      'Authorization': 'Basic ' + btoa('admin:1234')
    }
  });
  const data = await res.json();
  const labels = data.points.map(p => new Date(p.ts * 1000).toLocaleTimeString());
  const prices = data.points.map(p => parseFloat(p.price));
  return { labels, prices, crypto: data.crypto, resolution: data.resolution };
}

// 🔹 Gráfico (línea u OHLC según resolución)
async function drawChart() {
  const c = cryptoSelect.value;
  const res = resSelect.value;
  const ctx = document.getElementById('chart');

  if (res === "second") {
    // Línea normal
    const { labels, prices, crypto, resolution } = await fetchSeries();
    if (chart) chart.destroy();
    chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: `${crypto} (${resolution})`,
          data: prices,
          tension: 0.2
        }]
      },
      options: {
        responsive: true,
        scales: {
          x: { display: true },
          y: { display: true }
        }
      }
    });
  } else {
    // Velas OHLC
    const resp = await fetch(`/api/ohlc/${res}/${c}`, {
      headers: {
        'Authorization': 'Basic ' + btoa('admin:1234')
      }
    });
    const data = await resp.json();

    if (chart) chart.destroy();
    chart = new Chart(ctx, {
      type: 'candlestick',
      data: {
        datasets: [{
          label: `${data.crypto} (${data.resolution})`,
          data: data.candles.map(candle => ({
            x: new Date(candle.ts * 1000),
            o: parseFloat(candle.open),
            h: parseFloat(candle.high),
            l: parseFloat(candle.low),
            c: parseFloat(candle.close)
          }))
        }]
      },
      options: {
        responsive: true,
        scales: {
          x: {
            ticks: { source: 'auto' }
          },
          y: { display: true }
        }
      }
    });
  }
}

// 🔹 Intervalos de refresco
setInterval(fetchTable, 5000);  // refresca tabla cada 5s
setInterval(drawChart, 10000);  // refresca gráfico cada 10s

// 🔹 Primer render
fetchTable();
