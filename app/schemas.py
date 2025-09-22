from pydantic import BaseModel
from typing import List

class TableRow(BaseModel):
    crypto: str
    actual_price: str
    highest_1h: str
    lower_1h: str
    avg_1h: str
    signal: str
    volatility_1h: str      # 🔹 nuevo campo
    pct_change_24h: str     # 🔹 nuevo campo

class TableResponse(BaseModel):
    rows: List[TableRow]

class ArrayPoint(BaseModel):
    ts: int
    price: str

class ArrayResponse(BaseModel):
    crypto: str
    resolution: str
    points: List[ArrayPoint]
