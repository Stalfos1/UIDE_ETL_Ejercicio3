# app/ohlc_service.py
from .ohlc_generator import get_ohlc
from .ohlc_persist import persist_ohlc_json
from .collector import get_cryptos_from_env

RESOLUTIONS = ["second", "minute", "hour", "day"]
CRYPTO_SYMBOLS = ["BTC", "ETH", "SOL", "DOGE"]  # O leer desde env

def generate_and_persist_all_ohlc(crypto_symbol=None, resolution=None):
    """
    Genera y persiste OHLC.
    - Si crypto_symbol es None, genera para todas las criptos.
    - Si resolution es None, genera para todas las resoluciones.
    """
    cryptos = [crypto_symbol] if crypto_symbol else get_cryptos_from_env()
    resolutions = [resolution] if resolution else ["second", "minute", "hour", "day"]

    for crypto in cryptos:
        for res in resolutions:
            persist_ohlc_json(crypto, res)