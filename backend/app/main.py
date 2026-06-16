"""
Meeting Summary AI — Backend
Punto de entrada principal de la aplicación FastAPI.
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.routes import health, meetings

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

# Crear aplicación
app = FastAPI(
    title="Meeting Summary AI",
    description="Sistema inteligente de estandarización de resúmenes de reuniones con IA",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(health.router)
app.include_router(meetings.router)


@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Meeting Summary AI iniciado")
    logger.info(f"📄 Docs disponibles en: http://localhost:8000/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
