from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.auth import bootstrap_user
from app.config import get_settings
from app.db import SessionLocal, init_db
from app.errors import register_error_handlers
from app.routers.auth import router as auth_router
from app.schemas import HealthResponse


def create_app() -> FastAPI:
    settings = get_settings()
    settings.files_root.mkdir(parents=True, exist_ok=True)
    settings.app_data_dir.mkdir(parents=True, exist_ok=True)
    init_db()
    with SessionLocal() as db:
        bootstrap_user(db)

    app = FastAPI(title="Personal File Manager")
    register_error_handlers(app)
    app.include_router(auth_router)

    try:
        from app.routers.files import router as files_router

        app.include_router(files_router)
    except ImportError:
        pass

    try:
        from app.routers.metadata import router as metadata_router

        app.include_router(metadata_router)
    except ImportError:
        pass

    @app.get("/api/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    static_dir = settings.app_data_dir / "static"
    packaged_static_dir = settings.app_data_dir.parent / "static"
    if not static_dir.exists() and packaged_static_dir.exists():
        static_dir = packaged_static_dir
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    return app


app = create_app()
