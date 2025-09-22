from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import Optional, List, Tuple
from .db import Price
import time

def last_price_for_crypto(db: Session, crypto: str) -> Optional[Price]:
    stmt = select(Price).where(Price.crypto == crypto).order_by(desc(Price.ts)).limit(1)
    return db.execute(stmt).scalars().first()

def insert_price_if_changed(db: Session, crypto: str, amount_str: str, amount_dec: Decimal, currency: str, ts: int) -> Optional[Price]:
    # Evitar insertar si no cambió el precio vs el último insertado
    last = last_price_for_crypto(db, crypto)
    if last and last.amount_str == amount_str:
        return None
    now = int(time.time())
    p = Price(crypto=crypto, amount_str=amount_str, amount_dec=amount_dec, currency=currency, ts=ts, fetched_at=now)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

def stats_last_hour(db: Session, crypto: str) -> Tuple[Optional[Decimal], Optional[Decimal], Optional[Decimal]]:
    one_hour_ago = int(time.time()) - 3600
    stmt = select(
        func.max(Price.amount_dec),
        func.min(Price.amount_dec),
        func.avg(Price.amount_dec),
    ).where(Price.crypto == crypto, Price.ts >= one_hour_ago)
    result = db.execute(stmt).one_or_none()
    if not result:
        return (None, None, None)
    return result

def fetch_series(db: Session, crypto: str, since_ts: int) -> List[Tuple[int, Decimal, str]]:
    # Devuelve (ts, amount_dec, amount_str)
    stmt = select(Price.ts, Price.amount_dec, Price.amount_str).where(
        Price.crypto == crypto, Price.ts >= since_ts
    ).order_by(Price.ts.asc())
    return [(row[0], row[1], row[2]) for row in db.execute(stmt).all()]
