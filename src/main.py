import logging
from datetime import datetime

from fastapi import FastAPI

from src.core.db import init_db
from src.routers import auth, selections

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="SpinBot API")

app.include_router(auth.router)
app.include_router(selections.router)


@app.on_event("startup")
def startup() -> None:
    init_db()

@app.get("/api/status")
def get_status():
    return {
        "status": "online",
        "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
