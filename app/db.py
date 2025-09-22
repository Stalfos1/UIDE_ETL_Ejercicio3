from sqlalchemy import create_engine, Integer, String, Numeric, BigInteger, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase, mapped_column, Mapped
from sqlalchemy.engine import Engine
from decimal import Decimal
import os

# URL de la base de datos (si no se define en el entorno, usa SQLite por defecto)
DB_URL = os.getenv("DB_URL", "sqlite:///./crypto_prices.sqlite")

engine: Engine = create_engine(DB_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

class Base(DeclarativeBase):
    pass

class Price(Base):
    __tablename__ = "prices"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    crypto: Mapped[str] = mapped_column(String(32), index=True)       # ej: BTC-USD
    amount_str: Mapped[str] = mapped_column(String(64))               # precio exacto string
    amount_dec: Mapped[Decimal] = mapped_column(Numeric(36, 18))      # precio como Decimal
    currency: Mapped[str] = mapped_column(String(8), index=True)      # USD (desde el par)
    ts: Mapped[int] = mapped_column(BigInteger, index=True)           # época (segundos)
    fetched_at: Mapped[int] = mapped_column(BigInteger, index=True)   # época (segundos)

def init_db() -> None:
    """Crea las tablas y aplica PRAGMAs solo si es SQLite."""
    Base.metadata.create_all(bind=engine)
    if engine.dialect.name == "sqlite":
        with engine.begin() as conn:
            conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
            conn.exec_driver_sql("PRAGMA synchronous=NORMAL;")
            conn.exec_driver_sql("PRAGMA foreign_keys=ON;")

def test_connection() -> None:
    """Prueba de conexión y muestra el dialecto. Ayuda a diagnosticar errores DBAPI."""
    try:
        with engine.begin() as conn:
            conn.execute(text("SELECT 1"))
        print(f"✅ Conexión OK | Dialecto: {engine.dialect.name}")
    except Exception as e:
        print(f"❌ Error de conexión: {type(e).__name__}: {e}")
        if hasattr(e, "orig"):
            print(f"🔎 Driver original: {repr(e.orig)}")
        raise
