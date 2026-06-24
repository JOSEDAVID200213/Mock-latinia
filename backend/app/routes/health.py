"""
Health check y status del sistema.
"""
from fastapi import APIRouter

from app.config import (
    ALLOWED_EXTENSIONS,
    GEMINI_MODEL,
    MAX_FILE_SIZE_MB,
    STORAGE_BACKEND,
)

router = APIRouter(tags=["system"])


@router.get("/")
async def root():
    """Ruta raíz — confirma que el servicio está activo."""
    return {"status": "ok", "service": "Meeting Summary AI", "version": "1.0.0"}


@router.get("/health")
async def health_check():
    """Verifica que el sistema está operativo."""
    return {
        "status": "healthy",
        "service": "Meeting Summary AI",
        "version": "1.0.0",
    }


@router.get("/status")
async def system_status():
    """Retorna configuración y estado actual del sistema."""
    return {
        "status": "operational",
        "config": {
            "model": GEMINI_MODEL,
            "storage_backend": STORAGE_BACKEND,
            "max_file_size_mb": MAX_FILE_SIZE_MB,
            "supported_formats": sorted(ALLOWED_EXTENSIONS),
        },
    }
