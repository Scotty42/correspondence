from app.settings import DatabaseSettings, Settings

def test_database_settings_accepts_url_dict():
    db = DatabaseSettings.model_validate({"url": "sqlite+aiosqlite:////tmp/test.sqlite"})
    assert db.url.startswith("sqlite+aiosqlite:///")


def test_settings_from_yaml_accepts_database_block(tmp_path, monkeypatch):
    # Remove CI override if present
    monkeypatch.delenv("KORRESPONDENZ_DATABASE_URL", raising=False)

    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "database:\n"
        "  url: sqlite+aiosqlite:////tmp/test.sqlite\n"
        "server:\n"
        "  debug: false\n"
    )
    
    monkeypatch.delenv("KORRESPONDENZ_DATABASE_URL", raising=False)
    s = Settings.from_yaml(str(cfg))
    assert s.database.url == "sqlite+aiosqlite:////tmp/test.sqlite"
