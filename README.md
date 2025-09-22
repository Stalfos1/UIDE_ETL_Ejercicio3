# Crypto Signals ETL (FastAPI + SQLite + Vanilla JS)

Plataforma de señales de trading con ETL **incremental** usando la API pública de Coinbase
(`https://api.coinbase.com/v2/prices/{CRYPTO}/spot`). Implementa:
- **Extracción** cada segundo por *par* (ej. `BTC-USD`, `ETH-USD`, etc.).
- **Transformación** (validación de formato, precisión `Decimal`, estandarización de campos).
- **Carga incremental** (solo inserta si **cambia** el precio).
- **Sincronología incremental**: extracción → transformación → carga se encadenan mediante un *EventBus* (observer/observable).
- **Agregaciones** para arrays por **segundo**, **minuto**, **hora** y **día**.
- **Señales** de compra/venta (heurística EMA 5 vs EMA 15) y métricas de 1h (*Highest 1H*, *Lower 1H*, *AVG 1H*).
- **Frontend web** simple (tabla + gráfico) que consulta la API.

> Columnas solicitadas en la tabla: **Crypto | Actual Pric. | Higest 1H | Lower 1H | AVG Price | Signal (B|S)**

---

## 1) Requisitos

- Python 3.10+
- Pip

## 2) Instalación

```bash
git clone YOUR_REPO_URL crypto-signals-etl
cd crypto-signals-etl
python -m venv .venv
source .venv/bin/activate  # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 3) Variables y configuración

Edite `.env` para definir los símbolos a monitorear (por defecto: `BTC-USD,ETH-USD,SOL-USD,DOGE-USD`)
y el **intervalo** de extracción en segundos.

```
# .env
CRYPTOS=BTC-USD,ETH-USD,SOL-USD,DOGE-USD
FETCH_INTERVAL_SECONDS=1
CURRENCY=USD
```

## 4) Ejecutar en local

```bash
uvicorn app.main:app --reload
```
Abra: http://127.0.0.1:8000

- Frontend web: `/` (tabla + gráfico)
- Tabla de métricas: `/api/table`
- Arrays: `/api/arrays/{resolution}/{crypto}` donde `resolution ∈ {second, minute, hour, day}`

Ejemplos:
```
GET /api/arrays/second/BTC-USD
GET /api/arrays/minute/ETH-USD
GET /api/arrays/hour/SOL-USD
GET /api/arrays/day/DOGE-USD
```

## 5) Estructura del proyecto

```
crypto-signals-etl/
├─ app/
│  ├─ main.py            # FastAPI, rutas, inicio de tareas
│  ├─ db.py              # SQLAlchemy + SQLite
│  ├─ models.py          # ORM
│  ├─ crud.py            # Inserciones/consultas
│  ├─ collector.py       # Extracción + EventBus (observer)
│  ├─ aggregator.py      # Agregaciones y arrays
│  ├─ signals.py         # Señales (EMA5 vs EMA15)
│  ├─ utils.py           # Utilidades (Decimal, tiempos, etc.)
│  └─ schemas.py         # Pydantic (payloads API)
├─ static/
│  ├─ index.html         # UI: tabla + línea temporal (Chart.js)
│  └─ app.js
├─ requirements.txt
├─ .env.sample
├─ .gitignore
└─ README.md
```

## 6) Despliegue rápido (Render / Railway / Fly)

- Crear un servicio web con `uvicorn app.main:app` en el Start Command.
- Añadir variables de entorno de `.env` en el panel del proveedor.

## 7) GitHub (pasos básicos)

```bash
git init
git add .
git commit -m "feat: crypto ETL incremental + web UI"
git branch -M main
git remote add origin YOUR_REPO_URL
git push -u origin main
```

## 8) Notas de la práctica

- **Formato de precio**: se respeta exactamente el string recibido por la API (también se guarda en Decimal para métricas).
- **Consistencia**: cada fila guarda el par (`crypto`, ej. `BTC-USD`) para no mezclar cotizaciones entre monedas.
- **Incremental**: solo insertamos cuando el precio **cambia**, evitando duplicados por segundo.
- **Sincronología**: extracción→transformación→carga se encadenan por eventos (observer).

## 9) Señal B|S (heurística simple)
- Calculamos EMA(5s) y EMA(15s) en la última hora.
- **B (BUY)** si EMA5 cruza por **encima** de EMA15 o si `price > avg_1h * 1.002` (umbrales de ejemplo).
- **S (SELL)** si EMA5 cruza por **debajo** de EMA15 o si `price < avg_1h * 0.998`.
- En caso contrario: `"-"`.

> Ajuste los umbrales en `signals.py` según su criterio de trading.

---

## 10) Licencia y descargo
Este proyecto es educativo. No constituye asesoría financiera.
