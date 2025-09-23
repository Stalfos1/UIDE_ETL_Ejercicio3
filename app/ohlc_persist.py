# app/ohlc_persist.py
import json
import os
import time
from .ohlc_generator import get_ohlc

JSON_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "ohlc_snapshots")
os.makedirs(JSON_DIR, exist_ok=True)

RESOLUTION_MINUTES = {
    "second": 1,
    "minute": 5,
    "hour": 60,
    "day": 1440
}

# 🔹 Cuánto historial guardar según resolución
WINDOW_SECONDS = {
    "second": 5* 60,        # 5 minutos
    "minute": 30 * 60,       # 30 minutos
    "hour": 24 * 60 * 60,    # 24 horas
    "day": 5 * 24 * 60 * 60  # 5 días
}

def persist_ohlc_json(crypto_symbol: str, resolution: str):
    interval_minutes = RESOLUTION_MINUTES.get(resolution, 5)
    ohlc_data = get_ohlc(
        crypto_symbol,
        interval_minutes=interval_minutes,
        resolution=resolution
    )

    now = int(time.time())
    cutoff = now - WINDOW_SECONDS.get(resolution, 30 * 60)

    candles = []
    for row in ohlc_data:
        ts = int(row['x'].timestamp()) if hasattr(row['x'], 'timestamp') else int(row['x'])
        if ts < cutoff:
            continue  # 🔹 descartamos velas fuera de rango
        o, h, l, c = map(float, row['y'])
        candles.append({"ts": ts, "open": o, "high": h, "low": l, "close": c})

    filename = f"{crypto_symbol}_{resolution}.json"
    filepath = os.path.join(JSON_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump({"candles": candles}, f, ensure_ascii=False, indent=2)

    print(f"[INFO] JSON OHLC guardado en: {filepath} ({len(candles)} velas)")
    return filepath
