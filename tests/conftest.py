# tests/conftest.py
import os
import importlib
import pytest

@pytest.fixture(scope="session")
def test_db_url(tmp_path_factory):
    db_dir = tmp_path_factory.mktemp("db")
    db_path = db_dir / "test.sqlite"
    return f"sqlite+aiosqlite:////{db_path}"

@pytest.fixture(scope="session")
def app(test_db_url):
    # Must be set before importing modules that create the engine
    os.environ["KORRESPONDENZ_DATABASE_URL"] = test_db_url

    # Reload modules to pick up env var if they were imported elsewhere
    import app.settings
    importlib.reload(app.settings)
    import app.database
    importlib.reload(app.database)
    import app.main
    importlib.reload(app.main)

    return app.main.app
