# app/ohlc_updater.py
import time
from app.ohlc_persist import persist_ohlc_json

# Lista de criptos y resoluciones que quieres mantener actualizadas
CRYPTOS = ["BTC", "ETH", "SOL", "DOGE"]
RESOLUTIONS = ["minute", "hour", "day"]  # 'second' lo dejamos para tiempo real desde API

# Intervalo en segundos para regenerar los JSONs
UPDATE_INTERVAL = 10  # cada 10 segundos

def main():
    print("[INFO] Iniciando generador de JSON OHLC...")
    while True:
        for crypto in CRYPTOS:
            for res in RESOLUTIONS:
                try:
                    persist_ohlc_json(crypto, res)
                except Exception as e:
                    print(f"[ERROR] Falló al generar JSON {crypto} {res}: {e}")
        time.sleep(UPDATE_INTERVAL)

if __name__ == "__main__":
    main()
