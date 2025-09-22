# app/collector_db.py
import sqlite3
import os
from decimal import Decimal
from .utils import parse_amount, now_ts, parse_crypto_pair
from datetime import datetime, timedelta

# Ruta de la DB SQLite (una carpeta arriba de app/)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "crypto.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

# Guardar precio en la DB
def insert_price(crypto_symbol: str, price_usd: Decimal, signal: str = '-', change_24h: float = None):
    conn = get_connection()
    cur = conn.cursor()

    # Obtener crypto_id
    cur.execute("SELECT id FROM cryptocurrency WHERE symbol = ?", (crypto_symbol,))
    result = cur.fetchone()
    if not result:
        print(f"[WARN] Crypto {crypto_symbol} no encontrada en la tabla cryptocurrency")
        conn.close()
        return
    crypto_id = result[0]

    # Insertar precio
    cur.execute("""
        INSERT INTO crypto_prices (crypto_id, price_usd, signal, change_24h)
        VALUES (?, ?, ?, ?)
    """, (crypto_id, float(price_usd), signal, change_24h))
    conn.commit()
    conn.close()
    print(f"[INFO] Insertado: {crypto_symbol}={price_usd}$ signal={signal} change_24h={change_24h}")

# Insertar criptomonedas iniciales
def insert_cryptos_initial():
    cryptos = [
        ("Bitcoin", "BTC"),
        ("Ethereum", "ETH"),
        ("Solana", "SOL"),
        ("Dogecoin", "DOGE")
    ]
    conn = get_connection()
    cur = conn.cursor()
    for name, symbol in cryptos:
        cur.execute("INSERT OR IGNORE INTO cryptocurrency (name, symbol) VALUES (?, ?)", (name, symbol))
    conn.commit()
    conn.close()
    print("[INFO] Criptomonedas iniciales insertadas")


def fetch_ohlc(crypto: str, resolution: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    now = datetime.utcnow()
    if resolution == "second":
        delta = timedelta(minutes=5)  # últimos 5 minutos
        group_by = 1
    elif resolution == "minute":
        delta = timedelta(hours=1)
        group_by = 60
    elif resolution == "hour":
        delta = timedelta(days=1)
        group_by = 3600
    elif resolution == "day":
        delta = timedelta(days=30)
        group_by = 86400

    ts_from = int((now - delta).timestamp())
    c.execute(
        """
        SELECT timestamp, price_usd
        FROM crypto_prices
        WHERE crypto_id = (SELECT id FROM cryptocurrency WHERE symbol = ?)
          AND timestamp >= ?
        ORDER BY timestamp ASC
        """,
        (crypto, ts_from)
    )
    rows = c.fetchall()
    conn.close()

    # Convertir a OHLC por intervalo de seconds = group_by
    candles = []
    bucket = []
    last_ts = None
    for ts, price in rows:
        ts_bucket = ts // group_by * group_by
        if last_ts is None:
            last_ts = ts_bucket
        if ts_bucket != last_ts:
            if bucket:
                candles.append({
                    "ts": last_ts,
                    "open": bucket[0],
                    "high": max(bucket),
                    "low": min(bucket),
                    "close": bucket[-1]
                })
            bucket = []
            last_ts = ts_bucket
        bucket.append(price)
    if bucket:
        candles.append({
            "ts": last_ts,
            "open": bucket[0],
            "high": max(bucket),
            "low": min(bucket),
            "close": bucket[-1]
        })

    return candles