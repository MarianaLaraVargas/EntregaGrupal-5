from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# IMPORT CORRECTO (usa el paquete 'backend')
from backend.routes import inventory, pipeline

app = FastAPI(
    title="Gym Inventory API",
    description="API + Frontend para el inventario del gimnasio",
    version="1.0.0",
)

# Registrar routers
app.include_router(inventory.router)
app.include_router(pipeline.router)

# Servir el frontend (frontend/index.html) en la raíz "/"
frontend_dir = Path(__file__).resolve().parents[1] / "frontend"
app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
