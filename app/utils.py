from decimal import Decimal, InvalidOperation
from typing import Tuple
import time

def parse_amount(amount_str: str) -> Decimal:
    # Respeta exactamente el string original, pero devuelve Decimal para métricas.
    try:
        return Decimal(amount_str)
    except InvalidOperation:
        # Si el API devolviera algo inesperado, dejamos rastro controlado.
        raise ValueError(f"Invalid price format: {amount_str!r}")

def now_ts() -> int:
    return int(time.time())

def parse_crypto_pair(pair: str) -> Tuple[str, str]:
    # "BTC-USD" -> ("BTC", "USD")
    if "-" not in pair:
        raise ValueError("Crypto pair must be like BTC-USD")
    a, b = pair.split("-", 1)
    return a.upper(), b.upper()
