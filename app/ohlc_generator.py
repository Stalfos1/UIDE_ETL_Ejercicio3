from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import time
from datetime import datetime, timedelta

# --------------------------------------------------
# CONFIGURACIÓN
# --------------------------------------------------
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "crypto.db")
DB_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DB_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# --------------------------------------------------
# FUNCIONES
# --------------------------------------------------
def get_ohlc(symbol: str, interval_minutes: int = 5, resolution: str = "minute"):
    """
    Genera OHLC a partir de crypto_prices agrupando por intervalos en minutos.
    Recorta la ventana según la resolución:
    - 'second': últimos 5 minutos
    - 'minute': últimos 30 minutos
    - 'hour': últimas 24 horas
    - 'day': todos los datos disponibles
    """
    session = SessionLocal()
    try:
        # Limpiar símbolo: eliminar sufijo -USD
        symbol_clean = symbol.split("-")[0]

        # Determinar ventana temporal
        now = datetime.now()
        if resolution == "second":
            since = now - timedelta(minutes=5)
        elif resolution == "minute":
            since = now - timedelta(minutes=60)
        elif resolution == "hour":
            since = now - timedelta(hours=24)
        elif resolution == "day":# day
            since = now - timedelta(days=5)

        since_str = since.strftime("%Y-%m-%d %H:%M:%S")

        # Traer precios filtrando por ventana
        rows = session.execute(
            text("""
                SELECT cp.timestamp, cp.price_usd
                FROM crypto_prices cp
                JOIN cryptocurrency c ON cp.crypto_id = c.id
                WHERE c.symbol = :symbol
                  AND cp.timestamp >= :since
                ORDER BY cp.timestamp ASC
            """),
            {"symbol": symbol_clean, "since": since_str}
        ).all()

        if not rows:
            return []

        # Convertir timestamps a UNIX
        prices = [(int(time.mktime(time.strptime(ts, '%Y-%m-%d %H:%M:%S'))), price) for ts, price in rows]

        # Agrupar por intervalos
        interval_sec = interval_minutes * 60
        ohlc = []
        bucket = []
        current_start = prices[0][0] // interval_sec * interval_sec

        for ts, price in prices:
            if ts >= current_start + interval_sec:
                if bucket:
                    o = bucket[0]
                    h = max(bucket)
                    l = min(bucket)
                    c = bucket[-1]
                    ohlc.append({"x": current_start, "y": [o, h, l, c]})
                current_start = ts // interval_sec * interval_sec
                bucket = []
            bucket.append(price)

        # Último bucket
        if bucket:
            o = bucket[0]
            h = max(bucket)
            l = min(bucket)
            c = bucket[-1]
            ohlc.append({"x": current_start, "y": [o, h, l, c]})

        return ohlc

    finally:
        session.close()

# --------------------------------------------------
# EJEMPLO DE USO
# --------------------------------------------------
if __name__ == "__main__":
    crypto_symbol = "BTC-USD"
    # Ejemplo: velas de segundos
    candles = get_ohlc(crypto_symbol, interval_minutes=1, resolution="second")
    for c in candles[:10]:
        print(c)
