"""
Korrespondenz-System: FastAPI Application
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.settings import get_settings
from app.database import init_db
from app.api import contacts, documents, ai, health


# Logging konfigurieren
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.server.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/Shutdown Events"""
    # Startup
    logger.info("Initialisiere Datenbank...")
    await init_db()
    logger.info("Korrespondenz-System gestartet")
    
    yield
    
    # Shutdown
    logger.info("Korrespondenz-System beendet")


# FastAPI App
app = FastAPI(
    title="Korrespondenz-System",
    description="Self-hosted System für Geschäftskorrespondenz",
    version="0.1.0",
    lifespan=lifespan,
    redirect_slashes=False
)

# CORS (für Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In Produktion einschränken
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(contacts.router, prefix="/api/contacts", tags=["Kontakte"])
app.include_router(documents.router, prefix="/api/documents", tags=["Dokumente"])
app.include_router(ai.router, prefix="/api/ai", tags=["KI"])

# Statische Dateien (generierte PDFs)
documents_path = Path(settings.typst.output_dir)
try:
    documents_path.mkdir(parents=True, exist_ok=True)
except OSError as e:
    logger.warning("Could not create documents directory %s: %s", documents_path, e)

if documents_path.exists():
    app.mount("/files", StaticFiles(directory=str(documents_path)), name="files")
else:
    logger.warning("Static files not mounted because %s does not exist", documents_path)


@app.get("/")
async def root():
    return {
        "name": "Korrespondenz-System",
        "version": "0.1.0",
        "docs": "/docs"
    }
