from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from decimal import Decimal
from sqlalchemy import func, select
import time, statistics

from .crud import stats_last_hour, fetch_series
from .signals import signal_bs
from .db import Price, engine

# 🔹 Volatilidad de la última hora (compatible con SQLite y otros motores)
def volatility_last_hour(db: Session, crypto: str) -> Optional[Decimal]:
    one_hour_ago = int(time.time()) - 3600

    if engine.dialect.name == "sqlite":
        # Calcular en Python
        stmt = select(Price.amount_dec).where(
            Price.crypto == crypto, Price.ts >= one_hour_ago
        )
        rows = [row[0] for row in db.execute(stmt).all()]
        if not rows:
            return None
        return Decimal(str(statistics.pstdev(rows)))
    else:
        # Usar stddev nativo en motores que lo soportan
        stmt = select(func.stddev(Price.amount_dec)).where(
            Price.crypto == crypto, Price.ts >= one_hour_ago
        )
        return db.execute(stmt).scalar()

# 🔹 % cambio en 24h (cálculo en Python para compatibilidad con SQLite)
def pct_change_24h(db: Session, crypto: str) -> Optional[float]:
    now = int(time.time())
    day_ago = now - 86400
    stmt = select(Price.amount_dec).where(
        Price.crypto == crypto, Price.ts >= day_ago
    ).order_by(Price.ts.asc())
    rows = [row[0] for row in db.execute(stmt).all()]
    if len(rows) < 2:
        return None
    first, last = rows[0], rows[-1]
    return float((last - first) / first * 100)

# 🔹 Fila de la tabla
def table_row(db: Session, crypto: str) -> Dict[str, Any]:
    # Métricas de 1h
    high, low, avg = stats_last_hour(db, crypto)
    since = int(time.time()) - 3600
    series = fetch_series(db, crypto, since)

    prices = [row[1] for row in series]
    amount_str = series[-1][2] if series else "-"
    sig = signal_bs(prices, avg)

    # Extras
    vol = volatility_last_hour(db, crypto)
    pct24 = pct_change_24h(db, crypto)

    return {
        "crypto": crypto,
        "actual_price": amount_str,
        "highest_1h": str(high) if high is not None else "-",
        "lower_1h": str(low) if low is not None else "-",
        "avg_1h": str(avg) if avg is not None else "-",
        "signal": sig,
        "volatility_1h": str(vol) if vol else "-",
        "pct_change_24h": f"{pct24:.2f}%" if pct24 else "-"
    }

# 🔹 Arrays (series de tiempo promediadas)
def arrays(db: Session, crypto: str, resolution: str) -> List[Dict[str, Any]]:
    now = int(time.time())
    if resolution == "second":
        since = now - 60
    elif resolution == "minute":
        since = now - 3600
    elif resolution == "hour":
        since = now - 24 * 3600
    elif resolution == "day":
        since = now - 30 * 24 * 3600
    else:
        raise ValueError("resolution must be one of: second, minute, hour, day")

    series = fetch_series(db, crypto, since)  # (ts, amount_dec, amount_str)

    buckets: List[Dict[str, Any]] = []

    def push_bucket(ts_key: int, values: List[Decimal]):
        if not values:
            return
        avg = sum(values) / Decimal(len(values))
        buckets.append({"ts": ts_key, "price": str(avg)})

    if resolution == "second":
        for ts, _, amount_str in series:
            buckets.append({"ts": ts, "price": amount_str})
        return buckets

    # Caso agregado
    size = {"minute": 60, "hour": 3600, "day": 86400}[resolution]
    curr_key = None
    acc: List[Decimal] = []
    for ts, amount_dec, _ in series:
        key = (ts // size) * size
        if curr_key is None:
            curr_key = key
        if key != curr_key:
            push_bucket(curr_key, acc)
            curr_key = key
            acc = [amount_dec]
        else:
            acc.append(amount_dec)
    push_bucket(curr_key, acc)
    return buckets

# 🔹 OHLC (velas) para minute/hour/day
def ohlc(db: Session, crypto: str, resolution: str) -> List[Dict[str, Any]]:
    now = int(time.time())
    if resolution == "minute":
        since, size = now - 3600, 60
    elif resolution == "hour":
        since, size = now - 86400, 3600
    elif resolution == "day":
        since, size = now - 30 * 86400, 86400
    else:
        raise ValueError("OHLC supported only for minute/hour/day")

    series = fetch_series(db, crypto, since)
    buckets = {}
    for ts, amount_dec, _ in series:
        key = (ts // size) * size
        if key not in buckets:
            buckets[key] = {
                "open": amount_dec,
                "high": amount_dec,
                "low": amount_dec,
                "close": amount_dec
            }
        else:
            b = buckets[key]
            b["high"] = max(b["high"], amount_dec)
            b["low"] = min(b["low"], amount_dec)
            b["close"] = amount_dec
    return [{"ts": k, **v} for k, v in sorted(buckets.items())]
