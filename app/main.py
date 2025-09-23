import os, asyncio, secrets
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from dotenv import load_dotenv
from typing import List

from .db import init_db, SessionLocal
from .collector import extraction_loop, setup_event_chain, get_cryptos_from_env
from .collector_db import insert_cryptos_initial
from .aggregator import table_row, arrays, ohlc
from .schemas import TableResponse, TableRow, ArrayResponse, ArrayPoint
from .ohlc_service import generate_and_persist_all_ohlc  # 🔹 nuevo import

# 🔹 Cargar variables de entorno
load_dotenv()

# 🔹 Crear la aplicación FastAPI
app = FastAPI(title="Crypto Signals ETL")

# 🔹 Autenticación básica
security = HTTPBasic()

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, os.getenv("APP_USER", "admin"))
    correct_password = secrets.compare_digest(credentials.password, os.getenv("APP_PASS", "1234"))
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# 🔹 Servir frontend estático
app.mount("/static", StaticFiles(directory="static"), name="static")

# 🔹 Task periódico para actualizar OHLC
async def periodic_ohlc_update(cryptos, resolutions, interval_sec=600):
    while True:
        for crypto in cryptos:
            for res in resolutions:
                generate_and_persist_all_ohlc(crypto, res)
        await asyncio.sleep(interval_sec)

# 🔹 Evento de inicio
@app.on_event("startup")
async def startup_event():
    init_db()
    insert_cryptos_initial()
    setup_event_chain()

    # 🔹 Lanzar extracción en background
    asyncio.create_task(extraction_loop())

    # 🔹 Generar y persistir OHLC al iniciar
    cryptos = get_cryptos_from_env()
    resolutions = ["second", "minute", "hour", "day"]
    for crypto in cryptos:
        for res in resolutions:
            generate_and_persist_all_ohlc(crypto, res)

    # 🔹 Lanzar un task periódico para actualizar OHLC cada X segundos
    asyncio.create_task(periodic_ohlc_update(cryptos, resolutions, interval_sec=600))  # cada 10 min

# 🔹 Página principal (UI)
@app.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse("static/index.html")

# 🔹 API protegida con autenticación
@app.get("/api/table", response_model=TableResponse)
async def get_table(user: str = Depends(get_current_user)):
    cryptos = get_cryptos_from_env()
    with SessionLocal() as db:
        rows: List[TableRow] = [TableRow(**table_row(db, c)) for c in cryptos]
        return TableResponse(rows=rows)

@app.get("/api/arrays/{resolution}/{crypto}", response_model=ArrayResponse)
async def get_arrays(resolution: str, crypto: str, user: str = Depends(get_current_user)):
    resolution = resolution.lower()
    if resolution not in {"second", "minute", "hour", "day"}:
        raise HTTPException(400, "Invalid resolution")
    with SessionLocal() as db:
        pts = [ArrayPoint(**p) for p in arrays(db, crypto.upper(), resolution)]
        return ArrayResponse(crypto=crypto.upper(), resolution=resolution, points=pts)
