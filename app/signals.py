from decimal import Decimal, InvalidOperation
from typing import List, Tuple, Optional, Union

def ema(values: List[Decimal], period: int) -> List[Decimal]:
    # Cálculo EMA clásico
    if not values:
        return []
    k = Decimal(2) / Decimal(period + 1)
    emas: List[Decimal] = []
    ema_prev: Optional[Decimal] = None
    for v in values:
        if ema_prev is None:
            ema_prev = v
        else:
            ema_prev = (v - ema_prev) * k + ema_prev
        emas.append(ema_prev)
    return emas

def signal_bs(prices: List[Decimal], avg_1h: Optional[Union[Decimal, float, str]]) -> str:
    # Heurística simple: cruce EMA5 vs EMA15 o desvío del promedio 1h
    if len(prices) < 15:
        return "-"

    ema5 = ema(prices, 5)
    ema15 = ema(prices, 15)

    if len(ema5) >= 2 and len(ema15) >= 2:
        if ema5[-2] <= ema15[-2] and ema5[-1] > ema15[-1]:
            return "B"
        if ema5[-2] >= ema15[-2] and ema5[-1] < ema15[-1]:
            return "S"

    # Validación segura de avg_1h
    if avg_1h is not None:
        try:
            avg_1h = Decimal(str(avg_1h))  # convierte float o str a Decimal
            last = prices[-1]
            up = avg_1h * Decimal("1.002")
            down = avg_1h * Decimal("0.998")
            if last > up:
                return "B"
            if last < down:
                return "S"
        except (InvalidOperation, TypeError, ValueError):
            # Si no se puede convertir, ignora la regla de avg_1h
            pass

    return "-"
