import os, asyncio, secrets
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from dotenv import load_dotenv
from typing import List

from .db import init_db, SessionLocal
from .collector import extraction_loop, setup_event_chain, get_cryptos_from_env
from .aggregator import table_row, arrays, ohlc   # 🔹 ahora importamos ohlc
from .schemas import TableResponse, TableRow, ArrayResponse, ArrayPoint

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

# 🔹 Evento de inicio
@app.on_event("startup")
async def startup_event():
    init_db()
    setup_event_chain()
    asyncio.create_task(extraction_loop())

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

# 🔹 Nuevo endpoint: OHLC
@app.get("/api/ohlc/{resolution}/{crypto}")
async def get_ohlc(resolution: str, crypto: str, user: str = Depends(get_current_user)):
    with SessionLocal() as db:
        data = ohlc(db, crypto.upper(), resolution.lower())
        return {"crypto": crypto.upper(), "resolution": resolution.lower(), "candles": data}
