# app/database.py
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.settings import get_settings
from app.models.database import Base


def ensure_sqlite_dir(db_url: str) -> None:
    """
    Create parent dir for sqlite file DBs.

    Accepts:
      - sqlite+aiosqlite:////absolute/path.db
      - sqlite+aiosqlite:///relative/path.db  (relative to cwd)
    Ignores:
      - non-sqlite URLs
      - sqlite memory DBs
    """
    if not db_url.startswith("sqlite"):
        return

    parsed = urlparse(db_url)
    # memory DB variants (sqlite+aiosqlite:///:memory: etc.)
    if parsed.path in ("", "/:memory:") or ":memory:" in parsed.path:
        return

    # parsed.path includes leading "/" (may be multiple for absolute paths)
    p = Path(parsed.path)
    # If it is an absolute linux path, urlparse gives "/absolute/.."
    # If it's "////tmp/x.db" -> parsed.path is "////tmp/x.db" which Path handles as "/tmp/x.db"
    p = Path(str(p))  # normalize

    # only mkdir if a parent exists
    p.parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_engine():
    settings = get_settings()
    ensure_sqlite_dir(settings.database.url)

    return create_async_engine(
        settings.database.url,
        echo=settings.server.debug,
        connect_args={"check_same_thread": False} if settings.database.url.startswith("sqlite") else {},
        poolclass=StaticPool if settings.database.url.startswith("sqlite") else None,
    )


@lru_cache
def get_sessionmaker():
    return async_sessionmaker(bind=get_engine(), class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async_session = get_sessionmaker()
    async with async_session() as session:
        yield session


async def init_db():
    """Erstellt alle Tabellen"""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
