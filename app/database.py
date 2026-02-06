"""
Datenbank-Verbindung und Session-Management
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.settings import get_settings
from app.models.database import Base

from pathlib import Path
from urllib.parse import urlparse

def ensure_sqlite_dir(db_url: str) -> None:
    # Handles sqlite+aiosqlite:////abs/path and sqlite+aiosqlite:///rel/path
    if not db_url.startswith("sqlite"):
        return

    # Strip scheme and keep path part; for sqlite URLs the path is after "///" or "////"
    parsed = urlparse(db_url)
    db_path = parsed.path  # includes leading "/" for absolute paths

    if not db_path:
        return

    p = Path(db_path)
    # If it's a directory-based sqlite (rare), skip; typically it's a file
    if p.suffix:  # looks like a file
        p.parent.mkdir(parents=True, exist_ok=True)


# Engine erstellen
settings = get_settings()
ensure_sqlite_dir(settings.database.url)

engine = create_async_engine(
    settings.database.url,
    echo=settings.server.debug,
    connect_args={"check_same_thread": False},  # Für SQLite
    poolclass=StaticPool
)

# Session Factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_db():
    """Erstellt alle Tabellen"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """Dependency für FastAPI"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
