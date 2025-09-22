import asyncio
import httpx
import os
from typing import Callable, Dict, List, Any
from .utils import parse_amount, now_ts, parse_crypto_pair
from .db import SessionLocal
from .crud import insert_price_if_changed

COINBASE_BASE = "https://api.coinbase.com/v2/prices"

class EventBus:
    def __init__(self) -> None:
        self._listeners: Dict[str, List[Callable[[Any], Any]]] = {}

    def on(self, event: str, handler: Callable[[Any], Any]) -> None:
        self._listeners.setdefault(event, []).append(handler)

    async def emit(self, event: str, data: Any) -> None:
        for handler in self._listeners.get(event, []):
            res = handler(data)
            if asyncio.iscoroutine(res):
                await res

event_bus = EventBus()

def get_cryptos_from_env() -> List[str]:
    raw = os.getenv("CRYPTOS", "BTC-USD,ETH-USD,SOL-USD,DOGE-USD")
    return [s.strip().upper() for s in raw.split(",") if s.strip()]

async def fetch_price(client: httpx.AsyncClient, pair: str) -> Dict[str, Any]:
    # Coinbase endpoint: /v2/prices/{crypto}/spot  donde {crypto} es el par (BTC-USD)
    url = f"{COINBASE_BASE}/{pair}/spot"
    r = await client.get(url, timeout=10.0)
    r.raise_for_status()
    data = r.json()
    amount_str = data["data"]["amount"]   # string exacto
    base = data["data"]["base"]           # ej. BTC
    currency = data["data"]["currency"]   # ej. USD
    ts = now_ts()
    return {"pair": pair, "amount_str": amount_str, "base": base, "currency": currency, "ts": ts}

async def extraction_loop():
    cryptos = get_cryptos_from_env()
    interval = float(os.getenv("FETCH_INTERVAL_SECONDS", "1"))
    async with httpx.AsyncClient() as client:
        while True:
            try:
                results = await asyncio.gather(*[fetch_price(client, c) for c in cryptos], return_exceptions=True)
                for res in results:
                    if isinstance(res, Exception):
                        continue
                    await event_bus.emit("price_raw", res)
            except Exception:
                # evitar caídas; en producción usar logging
                pass
            await asyncio.sleep(interval)

# Handlers (observer)

def transform_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Validaciones mínimas + casting Decimal
    pair = payload["pair"]
    amount_str = payload["amount_str"]
    base, currency = parse_crypto_pair(pair)
    if currency != payload["currency"].upper():
        # nos quedamos con el currency del par (consistencia)
        payload["currency"] = currency
    payload["amount_dec"] = parse_amount(amount_str)
    return payload

def load_handler(payload: Dict[str, Any]) -> None:
    # Inserta incrementalmente si cambió el precio
    with SessionLocal() as db:
        insert_price_if_changed(
            db,
            crypto=payload["pair"],
            amount_str=payload["amount_str"],
            amount_dec=payload["amount_dec"],
            currency=payload["currency"],
            ts=payload["ts"],
        )

# Al registrar los handlers, encadenamos: price_raw -> transform_handler -> load_handler
# price_raw llama a transform y luego a load, de forma secuencial.
async def chain_handler(payload: Dict[str, Any]) -> None:
    transformed = transform_handler(payload)
    load_handler(transformed)

def setup_event_chain() -> None:
    event_bus.on("price_raw", chain_handler)
