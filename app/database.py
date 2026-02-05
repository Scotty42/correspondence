"""
Datenbank-Verbindung und Session-Management
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.settings import get_settings
from app.models.database import Base


# Engine erstellen
settings = get_settings()
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
