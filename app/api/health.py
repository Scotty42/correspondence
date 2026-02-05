"""
Health-Check Endpoints
"""
from fastapi import APIRouter

from app.services.ollama_client import OllamaClient
from app.services.paperless_client import PaperlessClient
from app.settings import get_settings


router = APIRouter()


@router.get("/health")
async def health_check():
    """Basis Health-Check"""
    return {"status": "ok"}


@router.get("/health/services")
async def services_status():
    """Status aller externen Services"""
    settings = get_settings()
    
    ollama = OllamaClient()
    paperless = PaperlessClient()
    
    return {
        "ollama": {
            "configured": settings.ollama.enabled,
            "url": settings.ollama.url,
            "model": settings.ollama.model,
            "available": await ollama.is_available()
        },
        "paperless": {
            "configured": settings.paperless.enabled,
            "url": settings.paperless.url,
            "available": await paperless.is_available()
        }
    }
