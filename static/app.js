let chart;
const tbody = document.querySelector('#prices-table tbody');
const cryptoSelect = document.getElementById('cryptoSelect');
const resSelect = document.getElementById('resSelect');
const AUTH_HEADER = { 'Authorization': 'Basic ' + btoa('admin:1234') };


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
  const crypto = cryptoSelect.value;
  const resolution = resSelect.value;
  const res = await fetch(`/api/arrays/${resolution}/${crypto}`, { headers: AUTH_HEADER });
  const data = await res.json();

  const labels = data.points.map(p => new Date(p.ts * 1000).toLocaleTimeString());
  const prices = data.points.map(p => parseFloat(p.price));

  return { labels, prices, crypto: data.crypto, resolution: data.resolution };
}



function resetChartCanvas() {
  const parent = document.getElementById('chart').parentNode;
  const oldCanvas = document.getElementById('chart');
  oldCanvas.remove();
  const newCanvas = document.createElement('canvas');
  newCanvas.id = 'chart';
  newCanvas.style.maxWidth = '100%';
  newCanvas.style.height = '320px';
  parent.appendChild(newCanvas);
  return newCanvas.getContext('2d');
}





// 🔹 Gráfico (línea u OHLC según resolución)
async function drawChart() {
  const crypto = cryptoSelect.value;
  const resolution = resSelect.value;

  try {
    const ctx = resetChartCanvas();  // reinicia el canvas cada vez
    if (resolution === "second") {
      // Línea simple
      const { labels, prices } = await fetchSeries();
      chart = new Chart(ctx, {
        type: 'line',
        data: { 
          labels, 
          datasets: [{ label: `${crypto} (${resolution})`, data: prices, tension: 0.2 }] 
        },
        options: { 
          responsive: true, 
          scales: { x: { display: true }, y: { display: true } } 
        }
      });
    } else {
      // OHLC / candlestick
      const resp = await fetch(`/api/ohlc/${resolution}/${crypto}`, { headers: AUTH_HEADER });
      const data = await resp.json();

      chart = new Chart(ctx, {
        type: 'candlestick',
        data: {
          datasets: [{
            label: `${data.crypto} (${data.resolution})`,
            data: data.candles.map(c => ({
              x: new Date(c.ts * 1000), 
              o: parseFloat(c.open), 
              h: parseFloat(c.high), 
              l: parseFloat(c.low), 
              c: parseFloat(c.close)
            }))
          }]
        },
        options: {
          responsive: true,
          scales: {
            x: {
              type: 'time',          // requiere Luxon o Moment
              time: { unit: resolution === "minute" ? 'minute' : resolution },
              adapters: { date: { locale: 'en' } },
              ticks: { source: 'auto' }
            },
            y: { display: true }
          }
        }
      });
    }
  } catch (err) {
    console.error("Error drawing chart:", err);
  }
}

// 🔹 Intervalos de refresco
setInterval(fetchTable, 5000);  // refresca tabla cada 5s
setInterval(drawChart, 10000);  // refresca gráfico cada 10s

// 🔹 Actualizar gráfico al cambiar cripto o resolución
cryptoSelect.addEventListener('change', drawChart);
resSelect.addEventListener('change', drawChart);

// 🔹 Primer render
fetchTable();
