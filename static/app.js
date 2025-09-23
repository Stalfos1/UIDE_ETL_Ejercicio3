async function drawChart() {
  if (isDrawing) return;
  isDrawing = true;
  try {
    const crypto = cryptoSelect.value || (cryptoSelect.options[0] && cryptoSelect.options[0].value);
    const resolution = resSelect.value || 'minute';
    if (!crypto) { isDrawing = false; return; }

    const { points } = await fetchSeries(crypto, resolution);
    const n = points.length;

    // KPIs
    pointsCount.textContent = n;
    lastPrice.textContent = n ? fmt(points[n-1].y) : '-';

    const canvas = document.getElementById('chart');

    // Destruir cualquier instancia previa (evita "Canvas is already in use")
    const existing = (typeof Chart?.getChart === 'function')
      ? (Chart.getChart(canvas) || Chart.getChart('chart'))
      : null;
    if (existing) existing.destroy();
    if (priceChart) { try { priceChart.destroy(); } catch(e){} }

    // Si no hay puntos, no intentes dibujar
    if (n === 0) {
      console.warn('drawChart(): no hay puntos para graficar');
      isDrawing = false;
      return;
    }

    // Construir labels como strings para EJE CATEGORY (sin adapter)
    const labels = points.map(p => {
      try { return new Date(p.x).toLocaleString(); } catch(_) { return String(p.x); }
    });
    const ys = points.map(p => p.y);

    // Asegurar altura del contenedor
    const wrap = document.getElementById('chartWrap');
    if (wrap && wrap.clientHeight < 100) { wrap.style.height = '320px'; }

    // Crear gráfico SIEMPRE con eje CATEGORY (sin adapter de fechas)
    priceChart = new Chart(canvas.getContext('2d'), {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: `${crypto} (${resolution})`,
          data: ys,
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
        animation: false,
        scales: {
          x: { type: 'category' },   // 👈 forzado a category
          y: { beginAtZero: false }
        },
        plugins: { legend: { display: true } }
      }
    });

    priceChart.update();
  } catch (err) {
    console.error('Error en drawChart:', err);
  } finally {
    isDrawing = false;
  }
}
