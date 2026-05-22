import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_username: str
    app_password: str
    app_secret_key: str
    files_root: Path
    app_data_dir: Path
    database_url: str | None
    upload_max_bytes: int
    search_max_depth: int
    search_max_entries: int
    search_max_results: int

    @property
    def resolved_database_url(self) -> str:
        return self.database_url or f"sqlite:///{self.app_data_dir / 'app.db'}"


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    return default if raw is None else int(raw)


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_username=os.getenv("APP_USERNAME", "admin"),
        app_password=os.getenv("APP_PASSWORD", "change-me"),
        app_secret_key=os.getenv("APP_SECRET_KEY", "dev-secret-change-me"),
        files_root=Path(os.getenv("FILES_ROOT", "/data/files")),
        app_data_dir=Path(os.getenv("APP_DATA_DIR", "/app/data")),
        database_url=os.getenv("DATABASE_URL"),
        upload_max_bytes=_int_env("UPLOAD_MAX_BYTES", 512 * 1024 * 1024),
        search_max_depth=_int_env("SEARCH_MAX_DEPTH", 8),
        search_max_entries=_int_env("SEARCH_MAX_ENTRIES", 5000),
        search_max_results=_int_env("SEARCH_MAX_RESULTS", 200),
    )
