from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def test_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    files_root = tmp_path / "files"
    app_data = tmp_path / "app-data"
    files_root.mkdir()
    app_data.mkdir()
    monkeypatch.setenv("APP_USERNAME", "admin")
    monkeypatch.setenv("APP_PASSWORD", "secret123")
    monkeypatch.setenv("APP_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("FILES_ROOT", str(files_root))
    monkeypatch.setenv("APP_DATA_DIR", str(app_data))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{app_data / 'test.db'}")

    from app.config import get_settings
    import app.db as db_module

    get_settings.cache_clear()
    db_module.engine = db_module.make_engine()
    db_module.SessionLocal.configure(bind=db_module.engine)
    return files_root


@pytest.fixture()
def client(test_env: Path) -> Generator[TestClient, None, None]:
    from app.main import create_app

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
