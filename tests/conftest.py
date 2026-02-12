# tests/conftest.py
import os
import sys
import importlib
from pathlib import Path

import pytest
from httpx import AsyncClient, ASGITransport

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture
async def db_session(app) -> AsyncSession:
    # Use the same dependency that the app uses
    agen = get_db()
    session = await agen.__anext__()
    try:
        yield session
    finally:
        await session.close()


@pytest.fixture(scope="session")
def test_db_url(tmp_path_factory):
    db_dir = tmp_path_factory.mktemp("db")
    db_path = db_dir / "test.sqlite"
    return f"sqlite+aiosqlite:////{db_path}"


@pytest.fixture(scope="session")
def app(test_db_url):
    # Ensure app reads test DB url
    os.environ["KORRESPONDENZ_DATABASE_URL"] = test_db_url

    # Import after env var is set
    import app.settings
    import app.database
    import app.main

    # Reload to ensure engine/settings pick up env var
    importlib.reload(app.settings)
    importlib.reload(app.database)
    importlib.reload(app.main)

    return app.main.app


@pytest.fixture(autouse=True)
async def _init_db(app):
    from app.database import init_db
    await init_db()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
