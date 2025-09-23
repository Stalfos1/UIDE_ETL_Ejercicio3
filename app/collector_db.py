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

