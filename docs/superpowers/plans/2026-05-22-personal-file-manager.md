# Personal File Manager Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Docker-deployable single-user Linux web file manager with a modern macOS Finder-like UI and a root-directory security sandbox.

**Architecture:** Create a FastAPI backend that owns authentication, SQLite metadata, root-safe filesystem operations, uploads, and search. Create a React/Vite/TypeScript frontend that consumes those APIs and implements Finder-style navigation, icon/list views, multi-selection, context menus, drag-to-move, upload, dialogs, and macOS Sonoma visual styling. Serve the built frontend from the FastAPI app in a single Docker Compose service.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2, SQLite, pytest, httpx/TestClient, React 18, Vite, TypeScript, Vitest, Testing Library, Docker Compose.

---

## Source Spec

Implementation must follow `docs/superpowers/specs/2026-05-22-personal-file-manager-design.md`.

## File Structure

Create this project structure:

```text
.
├── .dockerignore
├── .env.example
├── Dockerfile
├── README.md
├── docker-compose.yml
├── backend
│   ├── pyproject.toml
│   ├── app
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── errors.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── auth.py
│   │   ├── filesystem.py
│   │   ├── metadata.py
│   │   └── routers
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       ├── files.py
│   │       └── metadata.py
│   └── tests
│       ├── conftest.py
│       ├── test_auth.py
│       ├── test_filesystem_security.py
│       ├── test_files_api.py
│       ├── test_metadata_api.py
│       └── test_search.py
└── frontend
    ├── index.html
    ├── package.json
    ├── tsconfig.json
    ├── tsconfig.node.json
    ├── vite.config.ts
    └── src
        ├── main.tsx
        ├── App.tsx
        ├── styles.css
        ├── api.ts
        ├── types.ts
        ├── selection.ts
        ├── selection.test.ts
        └── components
            ├── AppShell.tsx
            ├── Sidebar.tsx
            ├── Toolbar.tsx
            ├── FileArea.tsx
            ├── ContextMenu.tsx
            ├── Dialogs.tsx
            └── UploadPanel.tsx
```

Boundary decisions:

- `backend/app/filesystem.py` is the only module that performs raw path resolution and file mutations.
- API routers use root-relative paths only.
- `backend/app/metadata.py` stores app metadata and trash records, not file contents.
- `frontend/src/selection.ts` owns selection rules so icon and list view stay consistent.
- `frontend/src/api.ts` is the only frontend file that knows raw HTTP endpoint shapes.

---

### Task 1: Backend Foundation, Configuration, Database, And Error Shape

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/db.py`
- Create: `backend/app/errors.py`
- Create: `backend/app/models.py`
- Create: `backend/app/schemas.py`
- Create: `backend/app/main.py`
- Create: `backend/tests/conftest.py`

- [ ] **Step 1: Write failing backend smoke tests**

Create `backend/tests/conftest.py`:

```python
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
```

Create `backend/tests/test_auth.py`:

```python
def test_health_endpoint_returns_ok(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_structured_not_found_error(client):
    response = client.get("/api/missing")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
```

- [ ] **Step 2: Run tests and verify they fail because the app does not exist**

Run:

```bash
cd backend
python -m pytest tests/test_auth.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app'` or missing FastAPI project files.

- [ ] **Step 3: Create backend package and dependencies**

Create `backend/pyproject.toml`:

```toml
[project]
name = "personal-file-manager-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.111.0",
  "uvicorn[standard]>=0.30.0",
  "sqlalchemy>=2.0.30",
  "pydantic-settings>=2.3.0",
  "python-multipart>=0.0.9",
  "passlib[bcrypt]>=1.7.4",
  "itsdangerous>=2.2.0"
]

[project.optional-dependencies]
test = [
  "pytest>=8.2.0",
  "httpx>=0.27.0"
]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

Create `backend/app/__init__.py`:

```python
"""Personal file manager backend."""
```

Create `backend/app/config.py`:

```python
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_username: str = Field(default="admin", alias="APP_USERNAME")
    app_password: str = Field(default="change-me", alias="APP_PASSWORD")
    app_secret_key: str = Field(default="dev-secret-change-me", alias="APP_SECRET_KEY")
    files_root: Path = Field(default=Path("/data/files"), alias="FILES_ROOT")
    app_data_dir: Path = Field(default=Path("/app/data"), alias="APP_DATA_DIR")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    upload_max_bytes: int = Field(default=512 * 1024 * 1024, alias="UPLOAD_MAX_BYTES")
    search_max_depth: int = Field(default=8, alias="SEARCH_MAX_DEPTH")
    search_max_entries: int = Field(default=5000, alias="SEARCH_MAX_ENTRIES")
    search_max_results: int = Field(default=200, alias="SEARCH_MAX_RESULTS")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return f"sqlite:///{self.app_data_dir / 'app.db'}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Create `backend/app/errors.py`:

```python
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def error_body(code: str, message: str) -> dict[str, dict[str, str]]:
    return {"error": {"code": code, "message": message}}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=error_body(exc.code, exc.message))

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "not_found" if exc.status_code == 404 else "http_error"
        return JSONResponse(status_code=exc.status_code, content=error_body(code, str(exc.detail)))

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content=error_body("validation_error", str(exc)))
```

Create `backend/app/db.py`:

```python
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def make_engine():
    settings = get_settings()
    connect_args = {"check_same_thread": False} if settings.resolved_database_url.startswith("sqlite") else {}
    return create_engine(settings.resolved_database_url, connect_args=connect_args)


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
```

Create `backend/app/models.py`:

```python
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("path", name="uq_favorites_path"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class RecentPath(Base):
    __tablename__ = "recent_paths"
    __table_args__ = (UniqueConstraint("path", name="uq_recent_path"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    last_accessed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Preference(Base):
    __tablename__ = "preferences"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    source_path: Mapped[str | None] = mapped_column(Text)
    target_path: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class TrashRecord(Base):
    __tablename__ = "trash_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    original_path: Mapped[str] = mapped_column(Text, nullable=False)
    trash_path: Mapped[str] = mapped_column(Text, nullable=False)
    original_name: Mapped[str] = mapped_column(Text, nullable=False)
    deleted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
```

Create `backend/app/schemas.py`:

```python
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    username: str


class FileEntry(BaseModel):
    name: str
    path: str
    kind: Literal["file", "directory", "symlink", "other"]
    size: int | None
    modified_at: datetime | None
    can_download: bool


class DirectoryResponse(BaseModel):
    path: str
    entries: list[FileEntry]


class PathRequest(BaseModel):
    path: str = "/"


class RenameRequest(BaseModel):
    path: str
    new_name: str


class MoveCopyRequest(BaseModel):
    sources: list[str] = Field(min_length=1)
    target_dir: str


class SearchResponse(BaseModel):
    query: str
    base_path: str
    entries: list[FileEntry]
    truncated: bool


class FavoriteRequest(BaseModel):
    path: str


class PreferenceRequest(BaseModel):
    key: str
    value: str
```

Create `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.db import init_db
from app.errors import register_error_handlers
from app.schemas import HealthResponse


def create_app() -> FastAPI:
    settings = get_settings()
    settings.files_root.mkdir(parents=True, exist_ok=True)
    settings.app_data_dir.mkdir(parents=True, exist_ok=True)
    init_db()

    app = FastAPI(title="Personal File Manager")
    register_error_handlers(app)

    @app.get("/api/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    static_dir = settings.app_data_dir / "static"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    return app


app = create_app()
```

- [ ] **Step 4: Run tests and verify they pass**

Run:

```bash
cd backend
python -m pytest tests/test_auth.py -v
```

Expected: PASS for both tests.

- [ ] **Step 5: Commit**

```bash
git add backend
git commit -m "feat: add backend foundation"
```

---

### Task 2: Authentication And Single-User Bootstrap

**Files:**
- Create: `backend/app/auth.py`
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/routers/auth.py`
- Modify: `backend/app/main.py`
- Modify: `backend/tests/test_auth.py`

- [ ] **Step 1: Extend failing auth API tests**

Append to `backend/tests/test_auth.py`:

```python
def test_first_start_creates_user_from_environment(client):
    from app.db import SessionLocal
    from app.models import User

    with SessionLocal() as db:
        users = db.query(User).all()
    assert len(users) == 1
    assert users[0].username == "admin"
    assert users[0].password_hash != "secret123"


def test_login_sets_http_only_session_cookie(client):
    response = client.post("/api/auth/login", json={"username": "admin", "password": "secret123"})
    assert response.status_code == 200
    assert response.json() == {"username": "admin"}
    assert "session" in response.cookies


def test_me_requires_login(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_me_returns_user_after_login(client):
    client.post("/api/auth/login", json={"username": "admin", "password": "secret123"})
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json() == {"username": "admin"}


def test_login_rejects_wrong_password(client):
    response = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"
```

- [ ] **Step 2: Run tests and verify they fail for missing auth routes**

Run:

```bash
cd backend
python -m pytest tests/test_auth.py -v
```

Expected: FAIL on `/api/auth/login` and `/api/auth/me` returning 404.

- [ ] **Step 3: Implement auth helpers**

Create `backend/app/auth.py`:

```python
from typing import Annotated

from fastapi import Depends, Request, Response
from itsdangerous import BadSignature, URLSafeSerializer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.errors import AppError
from app.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SESSION_COOKIE = "session"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def serializer() -> URLSafeSerializer:
    return URLSafeSerializer(get_settings().app_secret_key, salt="session")


def bootstrap_user(db: Session) -> None:
    if db.query(User).first() is not None:
        return
    settings = get_settings()
    user = User(username=settings.app_username, password_hash=hash_password(settings.app_password))
    db.add(user)
    db.commit()


def issue_session(response: Response, user: User) -> None:
    token = serializer().dumps({"user_id": user.id})
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )


def clear_session(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")


def current_user(request: Request, db: Annotated[Session, Depends(get_db)]) -> User:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise AppError("unauthenticated", "Login required", 401)
    try:
        payload = serializer().loads(token)
    except BadSignature as exc:
        raise AppError("unauthenticated", "Invalid session", 401) from exc
    user = db.get(User, payload.get("user_id"))
    if user is None:
        raise AppError("unauthenticated", "Invalid session", 401)
    return user
```

Create `backend/app/routers/__init__.py`:

```python
"""API routers."""
```

Create `backend/app/routers/auth.py`:

```python
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.auth import clear_session, current_user, issue_session, verify_password
from app.db import get_db
from app.errors import AppError
from app.models import User
from app.schemas import LoginRequest, LoginResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, response: Response, db: Annotated[Session, Depends(get_db)]) -> LoginResponse:
    user = db.query(User).filter(User.username == payload.username).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise AppError("invalid_credentials", "Invalid username or password", 401)
    issue_session(response, user)
    return LoginResponse(username=user.username)


@router.post("/logout")
def logout(response: Response) -> dict[str, str]:
    clear_session(response)
    return {"status": "ok"}


@router.get("/me", response_model=LoginResponse)
def me(user: Annotated[User, Depends(current_user)]) -> LoginResponse:
    return LoginResponse(username=user.username)
```

Modify `backend/app/main.py` so it imports and bootstraps auth:

```python
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

    @app.get("/api/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    static_dir = settings.app_data_dir / "static"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    return app


app = create_app()
```

- [ ] **Step 4: Run auth tests and verify they pass**

Run:

```bash
cd backend
python -m pytest tests/test_auth.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/auth.py backend/app/routers backend/app/main.py backend/tests/test_auth.py
git commit -m "feat: add single user authentication"
```

---

### Task 3: Root-Safe Filesystem Service

**Files:**
- Create: `backend/app/filesystem.py`
- Create: `backend/tests/test_filesystem_security.py`

- [ ] **Step 1: Write failing filesystem security tests**

Create `backend/tests/test_filesystem_security.py`:

```python
from pathlib import Path

import pytest

from app.errors import AppError
from app.filesystem import FileSystemService


def test_resolves_root_relative_path(test_env: Path):
    service = FileSystemService(root=test_env, app_data_dir=test_env.parent / "app-data")
    assert service.resolve("/") == test_env.resolve()
    assert service.resolve("/nested").parent == test_env.resolve()


def test_blocks_parent_traversal(test_env: Path):
    service = FileSystemService(root=test_env, app_data_dir=test_env.parent / "app-data")
    with pytest.raises(AppError) as exc:
        service.resolve("/../secret")
    assert exc.value.code == "path_outside_root"


def test_blocks_absolute_path_outside_root(test_env: Path):
    service = FileSystemService(root=test_env, app_data_dir=test_env.parent / "app-data")
    with pytest.raises(AppError) as exc:
        service.resolve("/etc/passwd")
    assert exc.value.code == "path_not_found"


def test_blocks_symlink_escape(test_env: Path, tmp_path: Path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("secret", encoding="utf-8")
    link = test_env / "link"
    link.symlink_to(outside, target_is_directory=True)
    service = FileSystemService(root=test_env, app_data_dir=test_env.parent / "app-data")
    with pytest.raises(AppError) as exc:
        service.resolve("/link/secret.txt")
    assert exc.value.code == "path_outside_root"


def test_rejects_invalid_new_name(test_env: Path):
    service = FileSystemService(root=test_env, app_data_dir=test_env.parent / "app-data")
    with pytest.raises(AppError) as exc:
        service.validate_name("../bad")
    assert exc.value.code == "invalid_name"
```

- [ ] **Step 2: Run tests and verify they fail because service is missing**

Run:

```bash
cd backend
python -m pytest tests/test_filesystem_security.py -v
```

Expected: FAIL with import error for `app.filesystem`.

- [ ] **Step 3: Implement root-safe filesystem service skeleton**

Create `backend/app/filesystem.py`:

```python
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.errors import AppError
from app.schemas import FileEntry


@dataclass(frozen=True)
class TrashMove:
    original_path: str
    trash_path: str
    original_name: str


class FileSystemService:
    def __init__(self, root: Path, app_data_dir: Path) -> None:
        self.root = root.resolve()
        self.app_data_dir = app_data_dir.resolve()
        self.trash_dir = self.app_data_dir / "trash"
        self.trash_dir.mkdir(parents=True, exist_ok=True)

    def to_relative(self, absolute: Path) -> str:
        rel = absolute.resolve().relative_to(self.root)
        return "/" + rel.as_posix() if rel.as_posix() != "." else "/"

    def resolve(self, user_path: str, *, must_exist: bool = True) -> Path:
        if not user_path.startswith("/"):
            user_path = "/" + user_path
        raw = user_path.lstrip("/")
        candidate = (self.root / raw).resolve(strict=False)
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise AppError("path_outside_root", "Path is outside the managed root", 403) from exc
        if must_exist and not candidate.exists():
            raise AppError("path_not_found", "Path does not exist", 404)
        if must_exist:
            real = candidate.resolve()
            try:
                real.relative_to(self.root)
            except ValueError as exc:
                raise AppError("path_outside_root", "Path is outside the managed root", 403) from exc
        return candidate

    def validate_name(self, name: str) -> str:
        clean = name.strip()
        if not clean or clean in {".", ".."} or "/" in clean or "\\" in clean:
            raise AppError("invalid_name", "Invalid file name", 400)
        return clean

    def entry_for(self, path: Path) -> FileEntry:
        stat = path.lstat()
        if path.is_symlink():
            kind = "symlink"
        elif path.is_dir():
            kind = "directory"
        elif path.is_file():
            kind = "file"
        else:
            kind = "other"
        return FileEntry(
            name=path.name,
            path=self.to_relative(path),
            kind=kind,
            size=None if kind == "directory" else stat.st_size,
            modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            can_download=kind == "file",
        )

    def list_dir(self, user_path: str) -> list[FileEntry]:
        directory = self.resolve(user_path)
        if not directory.is_dir():
            raise AppError("not_directory", "Path is not a directory", 400)
        return sorted((self.entry_for(child) for child in directory.iterdir()), key=lambda item: (item.kind != "directory", item.name.lower()))

    def create_folder(self, parent_path: str, name: str) -> FileEntry:
        parent = self.resolve(parent_path)
        if not parent.is_dir():
            raise AppError("not_directory", "Parent is not a directory", 400)
        target = parent / self.validate_name(name)
        self.resolve(self.to_relative(target), must_exist=False)
        if target.exists():
            raise AppError("target_exists", "Target already exists", 409)
        target.mkdir()
        return self.entry_for(target)

    def rename(self, user_path: str, new_name: str) -> FileEntry:
        source = self.resolve(user_path)
        target = source.parent / self.validate_name(new_name)
        self.resolve(self.to_relative(target), must_exist=False)
        if target.exists():
            raise AppError("target_exists", "Target already exists", 409)
        source.rename(target)
        return self.entry_for(target)

    def move_many(self, sources: list[str], target_dir: str) -> list[FileEntry]:
        target = self.resolve(target_dir)
        if not target.is_dir():
            raise AppError("not_directory", "Target is not a directory", 400)
        moved: list[FileEntry] = []
        for source_path in sources:
            source = self.resolve(source_path)
            destination = target / source.name
            self.resolve(self.to_relative(destination), must_exist=False)
            if destination.exists():
                raise AppError("target_exists", "Target already exists", 409)
            source.rename(destination)
            moved.append(self.entry_for(destination))
        return moved

    def copy_many(self, sources: list[str], target_dir: str) -> list[FileEntry]:
        target = self.resolve(target_dir)
        if not target.is_dir():
            raise AppError("not_directory", "Target is not a directory", 400)
        copied: list[FileEntry] = []
        for source_path in sources:
            source = self.resolve(source_path)
            destination = target / source.name
            self.resolve(self.to_relative(destination), must_exist=False)
            if destination.exists():
                raise AppError("target_exists", "Target already exists", 409)
            if source.is_dir():
                shutil.copytree(source, destination, symlinks=True)
            else:
                shutil.copy2(source, destination)
            copied.append(self.entry_for(destination))
        return copied

    def delete_to_trash(self, user_path: str) -> TrashMove:
        source = self.resolve(user_path)
        original_path = self.to_relative(source)
        trash_name = f"{uuid.uuid4().hex}-{source.name}"
        destination = self.trash_dir / trash_name
        shutil.move(str(source), destination)
        return TrashMove(original_path=original_path, trash_path=str(destination), original_name=source.name)
```

- [ ] **Step 4: Run filesystem security tests and verify they pass**

Run:

```bash
cd backend
python -m pytest tests/test_filesystem_security.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/filesystem.py backend/tests/test_filesystem_security.py
git commit -m "feat: add root safe filesystem service"
```

---

### Task 4: File API, Upload, Download, Operations, And Search

**Files:**
- Create: `backend/app/routers/files.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_files_api.py`
- Create: `backend/tests/test_search.py`

- [ ] **Step 1: Write failing file API tests**

Create `backend/tests/test_files_api.py`:

```python
from pathlib import Path


def login(client):
    client.post("/api/auth/login", json={"username": "admin", "password": "secret123"})


def test_files_require_auth(client):
    response = client.get("/api/files", params={"path": "/"})
    assert response.status_code == 401


def test_list_root_returns_entries(client, test_env: Path):
    (test_env / "Documents").mkdir()
    (test_env / "notes.txt").write_text("hello", encoding="utf-8")
    login(client)
    response = client.get("/api/files", params={"path": "/"})
    assert response.status_code == 200
    names = [entry["name"] for entry in response.json()["entries"]]
    assert names == ["Documents", "notes.txt"]


def test_create_rename_move_copy_delete_flow(client, test_env: Path):
    login(client)
    assert client.post("/api/files/folders", json={"path": "/Projects"}).status_code == 200
    (test_env / "a.txt").write_text("a", encoding="utf-8")
    rename = client.post("/api/files/rename", json={"path": "/a.txt", "new_name": "b.txt"})
    assert rename.status_code == 200
    move = client.post("/api/files/move", json={"sources": ["/b.txt"], "target_dir": "/Projects"})
    assert move.status_code == 200
    copy = client.post("/api/files/copy", json={"sources": ["/Projects/b.txt"], "target_dir": "/"})
    assert copy.status_code == 200
    delete = client.delete("/api/files", params={"path": "/b.txt"})
    assert delete.status_code == 200
    assert not (test_env / "b.txt").exists()


def test_upload_conflict_returns_409(client, test_env: Path):
    (test_env / "same.txt").write_text("old", encoding="utf-8")
    login(client)
    response = client.post(
        "/api/files/upload",
        data={"path": "/"},
        files={"file": ("same.txt", b"new", "text/plain")},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "target_exists"


def test_download_file(client, test_env: Path):
    (test_env / "download.txt").write_text("content", encoding="utf-8")
    login(client)
    response = client.get("/api/files/download", params={"path": "/download.txt"})
    assert response.status_code == 200
    assert response.content == b"content"
```

Create `backend/tests/test_search.py`:

```python
from pathlib import Path


def login(client):
    client.post("/api/auth/login", json={"username": "admin", "password": "secret123"})


def test_search_from_current_directory_by_name(client, test_env: Path):
    (test_env / "photos").mkdir()
    (test_env / "photos" / "cat.jpg").write_bytes(b"cat")
    (test_env / "notes.txt").write_text("cat inside content does not count", encoding="utf-8")
    login(client)
    response = client.get("/api/files/search", params={"path": "/photos", "q": "cat"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["base_path"] == "/photos"
    assert [entry["path"] for entry in payload["entries"]] == ["/photos/cat.jpg"]
```

- [ ] **Step 2: Run tests and verify they fail for missing file routes**

Run:

```bash
cd backend
python -m pytest tests/test_files_api.py tests/test_search.py -v
```

Expected: FAIL with 404 for `/api/files` routes.

- [ ] **Step 3: Implement file router**

Create `backend/app/routers/files.py`:

```python
import shutil
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth import current_user
from app.config import get_settings
from app.db import get_db
from app.errors import AppError
from app.filesystem import FileSystemService
from app.models import OperationLog, TrashRecord, User
from app.schemas import DirectoryResponse, FileEntry, MoveCopyRequest, RenameRequest, SearchResponse

router = APIRouter(prefix="/api/files", tags=["files"])


def fs() -> FileSystemService:
    settings = get_settings()
    return FileSystemService(settings.files_root, settings.app_data_dir)


def log_operation(db: Session, action: str, source: str | None = None, target: str | None = None) -> None:
    db.add(OperationLog(action=action, source_path=source, target_path=target))
    db.commit()


@router.get("", response_model=DirectoryResponse)
def list_files(
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
    path: str = Query(default="/"),
) -> DirectoryResponse:
    entries = fs().list_dir(path)
    log_operation(db, "list", path)
    return DirectoryResponse(path=path, entries=entries)


@router.post("/folders", response_model=FileEntry)
def create_folder(
    payload: dict[str, str],
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FileEntry:
    raw_path = payload.get("path", "")
    parent, name = raw_path.rsplit("/", 1) if "/" in raw_path.strip("/") else ("/", raw_path.strip("/"))
    if not name:
        raise AppError("invalid_name", "Folder name is required", 400)
    entry = fs().create_folder(parent or "/", name)
    log_operation(db, "create_folder", entry.path)
    return entry


@router.post("/rename", response_model=FileEntry)
def rename(
    payload: RenameRequest,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FileEntry:
    entry = fs().rename(payload.path, payload.new_name)
    log_operation(db, "rename", payload.path, entry.path)
    return entry


@router.post("/move", response_model=list[FileEntry])
def move(
    payload: MoveCopyRequest,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[FileEntry]:
    entries = fs().move_many(payload.sources, payload.target_dir)
    log_operation(db, "move", ",".join(payload.sources), payload.target_dir)
    return entries


@router.post("/copy", response_model=list[FileEntry])
def copy(
    payload: MoveCopyRequest,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[FileEntry]:
    entries = fs().copy_many(payload.sources, payload.target_dir)
    log_operation(db, "copy", ",".join(payload.sources), payload.target_dir)
    return entries


@router.delete("")
def delete_file(
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
    path: str = Query(),
) -> dict[str, str]:
    trash_move = fs().delete_to_trash(path)
    db.add(TrashRecord(original_path=trash_move.original_path, trash_path=trash_move.trash_path, original_name=trash_move.original_name))
    db.add(OperationLog(action="delete", source_path=trash_move.original_path, target_path=trash_move.trash_path))
    db.commit()
    return {"status": "ok"}


@router.post("/upload", response_model=FileEntry)
async def upload(
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
    path: str = Form(default="/"),
    file: UploadFile = File(),
) -> FileEntry:
    service = fs()
    directory = service.resolve(path)
    if not directory.is_dir():
        raise AppError("not_directory", "Upload target is not a directory", 400)
    name = service.validate_name(file.filename or "upload.bin")
    target = directory / name
    service.resolve(service.to_relative(target), must_exist=False)
    if target.exists():
        raise AppError("target_exists", "Target already exists", 409)
    with target.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    entry = service.entry_for(target)
    log_operation(db, "upload", None, entry.path)
    return entry


@router.get("/download")
def download(
    user: Annotated[User, Depends(current_user)],
    path: str = Query(),
) -> FileResponse:
    target = fs().resolve(path)
    if not target.is_file():
        raise AppError("not_file", "Path is not a downloadable file", 400)
    return FileResponse(target, filename=target.name)


@router.get("/search", response_model=SearchResponse)
def search(
    user: Annotated[User, Depends(current_user)],
    path: str = Query(default="/"),
    q: str = Query(min_length=1),
) -> SearchResponse:
    settings = get_settings()
    service = fs()
    base = service.resolve(path)
    if not base.is_dir():
        raise AppError("not_directory", "Search base is not a directory", 400)
    results: list[FileEntry] = []
    visited = 0
    truncated = False
    needle = q.lower()
    stack: list[tuple[Path, int]] = [(base, 0)]
    while stack:
        current, depth = stack.pop()
        if depth > settings.search_max_depth:
            truncated = True
            continue
        for child in current.iterdir():
            visited += 1
            if visited > settings.search_max_entries:
                truncated = True
                stack.clear()
                break
            if needle in child.name.lower():
                results.append(service.entry_for(child))
                if len(results) >= settings.search_max_results:
                    truncated = True
                    stack.clear()
                    break
            if child.is_dir() and not child.is_symlink():
                stack.append((child, depth + 1))
    return SearchResponse(query=q, base_path=path, entries=results, truncated=truncated)
```

Modify `backend/app/main.py` to include the file router:

```python
from app.routers.files import router as files_router
```

and after `app.include_router(auth_router)` add:

```python
    app.include_router(files_router)
```

- [ ] **Step 4: Run file API and search tests**

Run:

```bash
cd backend
python -m pytest tests/test_files_api.py tests/test_search.py -v
```

Expected: PASS.

- [ ] **Step 5: Run all backend tests**

Run:

```bash
cd backend
python -m pytest -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/files.py backend/app/main.py backend/tests/test_files_api.py backend/tests/test_search.py
git commit -m "feat: add file operations api"
```

---

### Task 5: Metadata API For Favorites, Recent Paths, Preferences, And Logs

**Files:**
- Create: `backend/app/metadata.py`
- Create: `backend/app/routers/metadata.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_metadata_api.py`

- [ ] **Step 1: Write failing metadata API tests**

Create `backend/tests/test_metadata_api.py`:

```python
def login(client):
    client.post("/api/auth/login", json={"username": "admin", "password": "secret123"})


def test_favorites_crud(client):
    login(client)
    add = client.post("/api/metadata/favorites", json={"path": "/Photos"})
    assert add.status_code == 200
    assert client.get("/api/metadata/favorites").json() == [{"path": "/Photos"}]
    delete = client.delete("/api/metadata/favorites", params={"path": "/Photos"})
    assert delete.status_code == 200
    assert client.get("/api/metadata/favorites").json() == []


def test_preferences_round_trip(client):
    login(client)
    response = client.put("/api/metadata/preferences", json={"key": "viewMode", "value": "icon"})
    assert response.status_code == 200
    prefs = client.get("/api/metadata/preferences").json()
    assert prefs == {"viewMode": "icon"}


def test_recent_paths_returns_latest_first(client):
    login(client)
    client.post("/api/metadata/recent", json={"path": "/A"})
    client.post("/api/metadata/recent", json={"path": "/B"})
    assert client.get("/api/metadata/recent").json() == [{"path": "/B"}, {"path": "/A"}]
```

- [ ] **Step 2: Run tests and verify they fail for missing metadata routes**

Run:

```bash
cd backend
python -m pytest tests/test_metadata_api.py -v
```

Expected: FAIL with 404 responses.

- [ ] **Step 3: Implement metadata service and router**

Create `backend/app/metadata.py`:

```python
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Favorite, Preference, RecentPath


def normalize_path(path: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    return path


def add_favorite(db: Session, path: str) -> None:
    path = normalize_path(path)
    if db.query(Favorite).filter(Favorite.path == path).first() is None:
        db.add(Favorite(path=path))
        db.commit()


def remove_favorite(db: Session, path: str) -> None:
    path = normalize_path(path)
    favorite = db.query(Favorite).filter(Favorite.path == path).first()
    if favorite is not None:
        db.delete(favorite)
        db.commit()


def list_favorites(db: Session) -> list[str]:
    return [row.path for row in db.query(Favorite).order_by(Favorite.created_at.asc()).all()]


def touch_recent(db: Session, path: str) -> None:
    path = normalize_path(path)
    recent = db.query(RecentPath).filter(RecentPath.path == path).first()
    if recent is None:
        db.add(RecentPath(path=path, last_accessed_at=datetime.utcnow()))
    else:
        recent.last_accessed_at = datetime.utcnow()
    db.commit()


def list_recent(db: Session) -> list[str]:
    rows = db.query(RecentPath).order_by(RecentPath.last_accessed_at.desc()).limit(20).all()
    return [row.path for row in rows]


def set_preference(db: Session, key: str, value: str) -> None:
    pref = db.get(Preference, key)
    if pref is None:
        db.add(Preference(key=key, value=value))
    else:
        pref.value = value
    db.commit()


def get_preferences(db: Session) -> dict[str, str]:
    return {row.key: row.value for row in db.query(Preference).order_by(Preference.key.asc()).all()}
```

Create `backend/app/routers/metadata.py`:

```python
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import current_user
from app.db import get_db
from app.metadata import add_favorite, get_preferences, list_favorites, list_recent, remove_favorite, set_preference, touch_recent
from app.models import User
from app.schemas import FavoriteRequest, PreferenceRequest

router = APIRouter(prefix="/api/metadata", tags=["metadata"])


def path_list(paths: list[str]) -> list[dict[str, str]]:
    return [{"path": path} for path in paths]


@router.get("/favorites")
def favorites(user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> list[dict[str, str]]:
    return path_list(list_favorites(db))


@router.post("/favorites")
def create_favorite(payload: FavoriteRequest, user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    add_favorite(db, payload.path)
    return {"status": "ok"}


@router.delete("/favorites")
def delete_favorite(path: str, user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    remove_favorite(db, path)
    return {"status": "ok"}


@router.get("/recent")
def recent(user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> list[dict[str, str]]:
    return path_list(list_recent(db))


@router.post("/recent")
def create_recent(payload: FavoriteRequest, user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    touch_recent(db, payload.path)
    return {"status": "ok"}


@router.get("/preferences")
def preferences(user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    return get_preferences(db)


@router.put("/preferences")
def update_preference(payload: PreferenceRequest, user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    set_preference(db, payload.key, payload.value)
    return {"status": "ok"}
```

Modify `backend/app/main.py` to import and include metadata router:

```python
from app.routers.metadata import router as metadata_router
```

and after file router include:

```python
    app.include_router(metadata_router)
```

- [ ] **Step 4: Run metadata tests and all backend tests**

Run:

```bash
cd backend
python -m pytest tests/test_metadata_api.py -v
python -m pytest -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/metadata.py backend/app/routers/metadata.py backend/app/main.py backend/tests/test_metadata_api.py
git commit -m "feat: add metadata api"
```

---

### Task 6: Frontend Foundation, API Client, And Selection Model

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/types.ts`
- Create: `frontend/src/api.ts`
- Create: `frontend/src/selection.ts`
- Create: `frontend/src/selection.test.ts`
- Create: `frontend/src/App.tsx`

- [ ] **Step 1: Write failing selection model tests**

Create `frontend/src/selection.test.ts`:

```ts
import { describe, expect, it } from 'vitest';
import { toggleSelection, rangeSelection } from './selection';

describe('selection model', () => {
  it('toggles a path on and off', () => {
    expect(toggleSelection([], '/a.txt')).toEqual(['/a.txt']);
    expect(toggleSelection(['/a.txt'], '/a.txt')).toEqual([]);
  });

  it('selects an inclusive range between anchor and target', () => {
    const entries = ['/a.txt', '/b.txt', '/c.txt', '/d.txt'];
    expect(rangeSelection(entries, '/b.txt', '/d.txt')).toEqual(['/b.txt', '/c.txt', '/d.txt']);
  });

  it('falls back to target when anchor is missing', () => {
    expect(rangeSelection(['/a.txt'], '/missing', '/a.txt')).toEqual(['/a.txt']);
  });
});
```

- [ ] **Step 2: Add frontend package files and run failing test**

Create `frontend/package.json`:

```json
{
  "name": "personal-file-manager-frontend",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite --host 0.0.0.0",
    "build": "tsc && vite build",
    "test": "vitest run"
  },
  "dependencies": {
    "@vitejs/plugin-react": "latest",
    "vite": "latest",
    "typescript": "latest",
    "react": "latest",
    "react-dom": "latest",
    "lucide-react": "latest"
  },
  "devDependencies": {
    "vitest": "latest",
    "@testing-library/react": "latest",
    "@testing-library/jest-dom": "latest",
    "jsdom": "latest"
  }
}
```

Create `frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["DOM", "DOM.Iterable", "ES2020"],
    "allowJs": false,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "ESNext",
    "moduleResolution": "Node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

Create `frontend/tsconfig.node.json`:

```json
{
  "compilerOptions": {
    "composite": true,
    "module": "ESNext",
    "moduleResolution": "Node",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

Create `frontend/vite.config.ts`:

```ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: { environment: 'jsdom' },
  server: { proxy: { '/api': 'http://localhost:8000' } }
});
```

Run:

```bash
cd frontend
npm install
npm test -- selection.test.ts
```

Expected: FAIL because `src/selection.ts` does not exist.

- [ ] **Step 3: Implement selection model and frontend foundation**

Create `frontend/src/selection.ts`:

```ts
export function toggleSelection(selected: string[], path: string): string[] {
  return selected.includes(path) ? selected.filter((item) => item !== path) : [...selected, path];
}

export function rangeSelection(allPaths: string[], anchor: string | null, target: string): string[] {
  const targetIndex = allPaths.indexOf(target);
  const anchorIndex = anchor ? allPaths.indexOf(anchor) : -1;
  if (targetIndex === -1) return [];
  if (anchorIndex === -1) return [target];
  const start = Math.min(anchorIndex, targetIndex);
  const end = Math.max(anchorIndex, targetIndex);
  return allPaths.slice(start, end + 1);
}
```

Create `frontend/src/types.ts`:

```ts
export type FileKind = 'file' | 'directory' | 'symlink' | 'other';

export interface FileEntry {
  name: string;
  path: string;
  kind: FileKind;
  size: number | null;
  modified_at: string | null;
  can_download: boolean;
}

export interface DirectoryResponse {
  path: string;
  entries: FileEntry[];
}

export interface UserResponse {
  username: string;
}

export type ViewMode = 'icon' | 'list';
```

Create `frontend/src/api.ts`:

```ts
import type { DirectoryResponse, FileEntry, UserResponse } from './types';

async function request<T>(input: RequestInfo, init?: RequestInit): Promise<T> {
  const response = await fetch(input, { credentials: 'include', ...init });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ error: { message: response.statusText } }));
    throw new Error(body.error?.message ?? response.statusText);
  }
  return response.json() as Promise<T>;
}

export const api = {
  me: () => request<UserResponse>('/api/auth/me'),
  login: (username: string, password: string) =>
    request<UserResponse>('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    }),
  list: (path: string) => request<DirectoryResponse>(`/api/files?path=${encodeURIComponent(path)}`),
  createFolder: (path: string) =>
    request<FileEntry>('/api/files/folders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path })
    }),
  rename: (path: string, newName: string) =>
    request<FileEntry>('/api/files/rename', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path, new_name: newName })
    }),
  move: (sources: string[], targetDir: string) =>
    request<FileEntry[]>('/api/files/move', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sources, target_dir: targetDir })
    }),
  copy: (sources: string[], targetDir: string) =>
    request<FileEntry[]>('/api/files/copy', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sources, target_dir: targetDir })
    }),
  delete: (path: string) => request<{ status: string }>(`/api/files?path=${encodeURIComponent(path)}`, { method: 'DELETE' }),
  search: (path: string, q: string) => request<{ entries: FileEntry[] }>(`/api/files/search?path=${encodeURIComponent(path)}&q=${encodeURIComponent(q)}`),
  upload: (path: string, file: File) => {
    const form = new FormData();
    form.append('path', path);
    form.append('file', file);
    return request<FileEntry>('/api/files/upload', { method: 'POST', body: form });
  },
  favorites: () => request<Array<{ path: string }>>('/api/metadata/favorites'),
  recent: () => request<Array<{ path: string }>>('/api/metadata/recent'),
  touchRecent: (path: string) =>
    request<{ status: string }>('/api/metadata/recent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path })
    }),
  preferences: () => request<Record<string, string>>('/api/metadata/preferences'),
  setPreference: (key: string, value: string) =>
    request<{ status: string }>('/api/metadata/preferences', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key, value })
    })
};
```

Create `frontend/index.html`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Personal File Manager</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

Create `frontend/src/main.tsx`:

```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

Create `frontend/src/App.tsx`:

```tsx
export default function App() {
  return <div className="app-loading">Personal File Manager</div>;
}
```

Create empty placeholder `frontend/src/styles.css`:

```css
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", sans-serif;
}
```

- [ ] **Step 4: Run frontend tests and build**

Run:

```bash
cd frontend
npm test -- selection.test.ts
npm run build
```

Expected: PASS and build succeeds.

- [ ] **Step 5: Commit**

```bash
git add frontend
git commit -m "feat: add frontend foundation"
```

---

### Task 7: Finder UI Components And Interactions

**Files:**
- Create: `frontend/src/components/AppShell.tsx`
- Create: `frontend/src/components/Sidebar.tsx`
- Create: `frontend/src/components/Toolbar.tsx`
- Create: `frontend/src/components/FileArea.tsx`
- Create: `frontend/src/components/ContextMenu.tsx`
- Create: `frontend/src/components/Dialogs.tsx`
- Create: `frontend/src/components/UploadPanel.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Create AppShell component**

Create `frontend/src/components/AppShell.tsx`:

```tsx
import type { ReactNode } from 'react';

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <main className="desktop">
      <section className="finder-window">
        <div className="traffic-lights" aria-hidden="true">
          <span className="red" />
          <span className="yellow" />
          <span className="green" />
        </div>
        {children}
      </section>
    </main>
  );
}
```

- [ ] **Step 2: Create Sidebar component**

Create `frontend/src/components/Sidebar.tsx`:

```tsx
import { Clock, Folder, HardDrive, Star } from 'lucide-react';

interface SidebarProps {
  favorites: string[];
  recent: string[];
  currentPath: string;
  onNavigate: (path: string) => void;
}

export function Sidebar({ favorites, recent, currentPath, onNavigate }: SidebarProps) {
  const item = (path: string, label: string, icon: JSX.Element) => (
    <button className={currentPath === path ? 'sidebar-item active' : 'sidebar-item'} onClick={() => onNavigate(path)}>
      {icon}<span>{label}</span>
    </button>
  );

  return (
    <aside className="sidebar">
      <h3>Locations</h3>
      {item('/', 'Files', <HardDrive size={16} />)}
      <h3>Favorites</h3>
      {favorites.length === 0 ? <p className="muted">No favorites</p> : favorites.map((path) => item(path, path.split('/').pop() || '/', <Star size={16} />))}
      <h3>Recent</h3>
      {recent.length === 0 ? <p className="muted">No recent paths</p> : recent.map((path) => item(path, path.split('/').pop() || '/', <Clock size={16} />))}
      <div className="sidebar-footer"><Folder size={15} /> Single-user mode</div>
    </aside>
  );
}
```

- [ ] **Step 3: Create Toolbar component**

Create `frontend/src/components/Toolbar.tsx`:

```tsx
import { ChevronLeft, ChevronRight, FolderPlus, Grid2X2, List, Search, Upload } from 'lucide-react';
import type { ViewMode } from '../types';

interface ToolbarProps {
  path: string;
  viewMode: ViewMode;
  query: string;
  canBack: boolean;
  canForward: boolean;
  onBack: () => void;
  onForward: () => void;
  onQuery: (value: string) => void;
  onNewFolder: () => void;
  onUploadClick: () => void;
  onViewMode: (mode: ViewMode) => void;
}

export function Toolbar(props: ToolbarProps) {
  return (
    <header className="toolbar">
      <div className="nav-buttons">
        <button disabled={!props.canBack} onClick={props.onBack}><ChevronLeft size={18} /></button>
        <button disabled={!props.canForward} onClick={props.onForward}><ChevronRight size={18} /></button>
      </div>
      <div className="path-pill">{props.path}</div>
      <label className="search-box"><Search size={16} /><input value={props.query} onChange={(event) => props.onQuery(event.target.value)} placeholder="Search current folder" /></label>
      <button onClick={props.onNewFolder}><FolderPlus size={17} /> New Folder</button>
      <button onClick={props.onUploadClick}><Upload size={17} /> Upload</button>
      <div className="segmented">
        <button className={props.viewMode === 'icon' ? 'active' : ''} onClick={() => props.onViewMode('icon')}><Grid2X2 size={16} /></button>
        <button className={props.viewMode === 'list' ? 'active' : ''} onClick={() => props.onViewMode('list')}><List size={16} /></button>
      </div>
    </header>
  );
}
```

- [ ] **Step 4: Create FileArea component with multi-select and drag-to-move**

Create `frontend/src/components/FileArea.tsx`:

```tsx
import type { MouseEvent } from 'react';
import { File, Folder, Link } from 'lucide-react';
import type { FileEntry, ViewMode } from '../types';

interface FileAreaProps {
  entries: FileEntry[];
  selected: string[];
  viewMode: ViewMode;
  onOpen: (entry: FileEntry) => void;
  onSelect: (entry: FileEntry, event: MouseEvent<HTMLButtonElement>) => void;
  onContext: (entry: FileEntry, x: number, y: number) => void;
  onMove: (sources: string[], targetDir: string) => void;
}

function iconFor(entry: FileEntry) {
  if (entry.kind === 'directory') return <Folder size={38} />;
  if (entry.kind === 'symlink') return <Link size={34} />;
  return <File size={34} />;
}

export function FileArea({ entries, selected, viewMode, onOpen, onSelect, onContext, onMove }: FileAreaProps) {
  const paths = selected;
  const item = (entry: FileEntry) => (
    <button
      key={entry.path}
      className={selected.includes(entry.path) ? 'file-item selected' : 'file-item'}
      draggable
      onDragStart={(event) => event.dataTransfer.setData('text/plain', JSON.stringify(selected.includes(entry.path) ? paths : [entry.path]))}
      onDragOver={(event) => { if (entry.kind === 'directory') event.preventDefault(); }}
      onDrop={(event) => {
        event.preventDefault();
        const sources = JSON.parse(event.dataTransfer.getData('text/plain')) as string[];
        if (entry.kind === 'directory') onMove(sources, entry.path);
      }}
      onClick={(event) => onSelect(entry, event)}
      onDoubleClick={() => onOpen(entry)}
      onContextMenu={(event) => { event.preventDefault(); onContext(entry, event.clientX, event.clientY); }}
    >
      <span className="file-icon">{iconFor(entry)}</span>
      <span className="file-name">{entry.name}</span>
      {viewMode === 'list' && <span className="file-meta">{entry.kind}</span>}
    </button>
  );
  return <section className={viewMode === 'icon' ? 'file-area icon-view' : 'file-area list-view'}>{entries.map(item)}</section>;
}
```

- [ ] **Step 5: Create ContextMenu, Dialogs, and UploadPanel components**

Create `frontend/src/components/ContextMenu.tsx`:

```tsx
interface ContextMenuProps {
  x: number;
  y: number;
  visible: boolean;
  selectionCount: number;
  onClose: () => void;
  onOpen: () => void;
  onDownload: () => void;
  onRename: () => void;
  onCopy: () => void;
  onDelete: () => void;
  onDetails: () => void;
}

export function ContextMenu(props: ContextMenuProps) {
  if (!props.visible) return null;
  const action = (label: string, fn: () => void) => <button onClick={() => { fn(); props.onClose(); }}>{label}</button>;
  return (
    <div className="context-menu" style={{ left: props.x, top: props.y }}>
      {action('Open / Download', props.onOpen)}
      {action('Download', props.onDownload)}
      {props.selectionCount === 1 && action('Rename', props.onRename)}
      {action('Copy to Current Folder', props.onCopy)}
      {action('Delete', props.onDelete)}
      {props.selectionCount === 1 && action('Show Details', props.onDetails)}
    </div>
  );
}
```

Create `frontend/src/components/Dialogs.tsx`:

```tsx
import type { FileEntry } from '../types';

interface DialogsProps {
  renameValue: string;
  setRenameValue: (value: string) => void;
  renaming: boolean;
  details: FileEntry | null;
  confirmDelete: boolean;
  onRenameConfirm: () => void;
  onDeleteConfirm: () => void;
  onClose: () => void;
}

export function Dialogs(props: DialogsProps) {
  return (
    <>
      {props.renaming && (
        <div className="modal"><div className="sheet"><h2>Rename</h2><input autoFocus value={props.renameValue} onChange={(event) => props.setRenameValue(event.target.value)} /><button onClick={props.onRenameConfirm}>Rename</button><button onClick={props.onClose}>Cancel</button></div></div>
      )}
      {props.confirmDelete && (
        <div className="modal"><div className="sheet"><h2>Move to Trash?</h2><p>This moves selected items to the app-managed trash.</p><button className="danger" onClick={props.onDeleteConfirm}>Delete</button><button onClick={props.onClose}>Cancel</button></div></div>
      )}
      {props.details && (
        <div className="modal"><div className="sheet"><h2>{props.details.name}</h2><p>Path: {props.details.path}</p><p>Type: {props.details.kind}</p><p>Size: {props.details.size ?? '—'}</p><p>Modified: {props.details.modified_at ?? '—'}</p><button onClick={props.onClose}>Close</button></div></div>
      )}
    </>
  );
}
```

Create `frontend/src/components/UploadPanel.tsx`:

```tsx
interface UploadPanelProps {
  visible: boolean;
  onUpload: (file: File) => void;
  onClose: () => void;
}

export function UploadPanel({ visible, onUpload, onClose }: UploadPanelProps) {
  if (!visible) return null;
  return (
    <div className="modal"><div className="sheet"><h2>Upload</h2><input type="file" onChange={(event) => { const file = event.target.files?.[0]; if (file) onUpload(file); }} /><button onClick={onClose}>Close</button></div></div>
  );
}
```

- [ ] **Step 6: Wire App state and interactions**

Replace `frontend/src/App.tsx` with:

```tsx
import { useEffect, useMemo, useState } from 'react';
import { api } from './api';
import { rangeSelection, toggleSelection } from './selection';
import type { FileEntry, ViewMode } from './types';
import { AppShell } from './components/AppShell';
import { Sidebar } from './components/Sidebar';
import { Toolbar } from './components/Toolbar';
import { FileArea } from './components/FileArea';
import { ContextMenu } from './components/ContextMenu';
import { Dialogs } from './components/Dialogs';
import { UploadPanel } from './components/UploadPanel';

export default function App() {
  const [user, setUser] = useState<string | null>(null);
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const [path, setPath] = useState('/');
  const [entries, setEntries] = useState<FileEntry[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [anchor, setAnchor] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('icon');
  const [history, setHistory] = useState<string[]>(['/']);
  const [historyIndex, setHistoryIndex] = useState(0);
  const [query, setQuery] = useState('');
  const [favorites, setFavorites] = useState<string[]>([]);
  const [recent, setRecent] = useState<string[]>([]);
  const [menu, setMenu] = useState({ visible: false, x: 0, y: 0 });
  const [renaming, setRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState('');
  const [details, setDetails] = useState<FileEntry | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [error, setError] = useState('');

  const selectedEntries = useMemo(() => entries.filter((entry) => selected.includes(entry.path)), [entries, selected]);

  async function load(nextPath = path) {
    const data = query ? await api.search(nextPath, query) : await api.list(nextPath);
    setEntries(data.entries);
    await api.touchRecent(nextPath).catch(() => undefined);
    setRecent((await api.recent().catch(() => [])).map((item) => item.path));
  }

  async function navigate(nextPath: string) {
    setPath(nextPath);
    setSelected([]);
    setAnchor(null);
    const nextHistory = history.slice(0, historyIndex + 1).concat(nextPath);
    setHistory(nextHistory);
    setHistoryIndex(nextHistory.length - 1);
    await load(nextPath);
  }

  useEffect(() => { api.me().then((me) => setUser(me.username)).catch(() => undefined); }, []);
  useEffect(() => { if (user) { load('/'); api.favorites().then((items) => setFavorites(items.map((item) => item.path))).catch(() => undefined); } }, [user]);
  useEffect(() => { if (user) load(path).catch((exc) => setError(String(exc.message ?? exc))); }, [query]);

  if (!user) {
    return <main className="login-screen"><form onSubmit={async (event) => { event.preventDefault(); try { const me = await api.login(username, password); setUser(me.username); } catch (exc) { setError(String((exc as Error).message)); } }}><h1>Personal File Manager</h1><input value={username} onChange={(event) => setUsername(event.target.value)} /><input type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Password" /><button>Login</button>{error && <p className="error">{error}</p>}</form></main>;
  }

  const current = selectedEntries[0];
  return (
    <AppShell>
      <Sidebar favorites={favorites} recent={recent} currentPath={path} onNavigate={navigate} />
      <section className="main-pane" onClick={() => setMenu({ ...menu, visible: false })}>
        <Toolbar path={path} viewMode={viewMode} query={query} canBack={historyIndex > 0} canForward={historyIndex < history.length - 1} onBack={() => { const i = historyIndex - 1; setHistoryIndex(i); navigate(history[i]); }} onForward={() => { const i = historyIndex + 1; setHistoryIndex(i); navigate(history[i]); }} onQuery={setQuery} onNewFolder={async () => { const name = prompt('Folder name'); if (name) { await api.createFolder(`${path === '/' ? '' : path}/${name}`); await load(); } }} onUploadClick={() => setUploadOpen(true)} onViewMode={(mode) => { setViewMode(mode); api.setPreference('viewMode', mode).catch(() => undefined); }} />
        {error && <p className="banner">{error}</p>}
        <FileArea entries={entries} selected={selected} viewMode={viewMode} onOpen={(entry) => { if (entry.kind === 'directory') navigate(entry.path); else window.location.href = `/api/files/download?path=${encodeURIComponent(entry.path)}`; }} onSelect={(entry, event) => { const all = entries.map((item) => item.path); if (event.shiftKey) setSelected(rangeSelection(all, anchor, entry.path)); else if (event.metaKey || event.ctrlKey) setSelected(toggleSelection(selected, entry.path)); else setSelected([entry.path]); setAnchor(entry.path); }} onContext={(entry, x, y) => { if (!selected.includes(entry.path)) setSelected([entry.path]); setMenu({ visible: true, x, y }); }} onMove={async (sources, targetDir) => { await api.move(sources, targetDir); await load(); }} />
        <ContextMenu visible={menu.visible} x={menu.x} y={menu.y} selectionCount={selected.length} onClose={() => setMenu({ ...menu, visible: false })} onOpen={() => current && (current.kind === 'directory' ? navigate(current.path) : window.location.href = `/api/files/download?path=${encodeURIComponent(current.path)}`)} onDownload={() => current && (window.location.href = `/api/files/download?path=${encodeURIComponent(current.path)}`)} onRename={() => { setRenameValue(current?.name ?? ''); setRenaming(true); }} onCopy={async () => { await api.copy(selected, path); await load(); }} onDelete={() => setConfirmDelete(true)} onDetails={() => setDetails(current ?? null)} />
        <Dialogs renameValue={renameValue} setRenameValue={setRenameValue} renaming={renaming} details={details} confirmDelete={confirmDelete} onRenameConfirm={async () => { if (current) await api.rename(current.path, renameValue); setRenaming(false); await load(); }} onDeleteConfirm={async () => { for (const item of selected) await api.delete(item); setConfirmDelete(false); setSelected([]); await load(); }} onClose={() => { setRenaming(false); setDetails(null); setConfirmDelete(false); }} />
        <UploadPanel visible={uploadOpen} onUpload={async (file) => { await api.upload(path, file); setUploadOpen(false); await load(); }} onClose={() => setUploadOpen(false)} />
      </section>
    </AppShell>
  );
}
```

- [ ] **Step 7: Apply macOS Sonoma styling**

Replace `frontend/src/styles.css` with:

```css
* { box-sizing: border-box; }
body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", sans-serif; background: #0f172a; color: #172033; }
button, input { font: inherit; }
button { border: 0; border-radius: 10px; background: rgba(255,255,255,.5); padding: 8px 10px; cursor: pointer; color: #182033; display: inline-flex; gap: 6px; align-items: center; }
button:disabled { opacity: .35; cursor: default; }
.login-screen, .desktop { min-height: 100vh; display: grid; place-items: center; background: radial-gradient(circle at 20% 10%, #f8b6d2, transparent 30%), radial-gradient(circle at 80% 20%, #a7c7ff, transparent 30%), linear-gradient(135deg, #f8fafc, #c7d2fe 50%, #fbcfe8); }
.login-screen form { width: 360px; padding: 28px; border-radius: 28px; background: rgba(255,255,255,.72); backdrop-filter: blur(28px); box-shadow: 0 30px 80px rgba(15,23,42,.25); display: grid; gap: 14px; }
.login-screen input, .sheet input, .search-box input { border: 0; border-radius: 12px; padding: 10px 12px; background: rgba(255,255,255,.7); outline: none; }
.finder-window { width: min(1180px, 94vw); height: min(760px, 90vh); position: relative; display: grid; grid-template-columns: 240px 1fr; overflow: hidden; border-radius: 26px; background: rgba(255,255,255,.55); backdrop-filter: blur(32px) saturate(1.3); box-shadow: 0 40px 110px rgba(15,23,42,.32); border: 1px solid rgba(255,255,255,.6); }
.traffic-lights { position: absolute; top: 18px; left: 18px; display: flex; gap: 8px; z-index: 3; }
.traffic-lights span { width: 12px; height: 12px; border-radius: 999px; display: block; }
.red { background: #ff5f57; } .yellow { background: #febc2e; } .green { background: #28c840; }
.sidebar { padding: 56px 14px 16px; background: rgba(239,246,255,.48); border-right: 1px solid rgba(255,255,255,.55); backdrop-filter: blur(22px); }
.sidebar h3 { margin: 16px 8px 8px; font-size: 12px; color: rgba(23,32,51,.55); text-transform: uppercase; letter-spacing: .05em; }
.sidebar-item { width: 100%; justify-content: flex-start; background: transparent; margin-bottom: 4px; }
.sidebar-item.active { background: rgba(255,255,255,.75); box-shadow: inset 0 0 0 1px rgba(255,255,255,.7); }
.sidebar-footer, .muted { color: rgba(23,32,51,.55); font-size: 13px; padding: 8px; display: flex; gap: 8px; align-items: center; }
.main-pane { display: grid; grid-template-rows: auto auto 1fr; min-width: 0; }
.toolbar { height: 62px; padding: 12px 14px; display: flex; align-items: center; gap: 10px; border-bottom: 1px solid rgba(255,255,255,.55); background: rgba(255,255,255,.28); }
.nav-buttons, .segmented { display: flex; gap: 4px; padding: 4px; border-radius: 13px; background: rgba(255,255,255,.35); }
.segmented .active { background: white; }
.path-pill { min-width: 130px; max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; padding: 9px 12px; border-radius: 14px; background: rgba(255,255,255,.5); }
.search-box { flex: 1; min-width: 180px; display: flex; align-items: center; gap: 8px; padding: 0 10px; border-radius: 14px; background: rgba(255,255,255,.55); }
.search-box input { flex: 1; background: transparent; }
.file-area { padding: 18px; overflow: auto; align-content: start; }
.icon-view { display: grid; grid-template-columns: repeat(auto-fill, minmax(104px, 1fr)); gap: 14px; }
.list-view { display: grid; gap: 6px; }
.file-item { text-align: center; background: transparent; border-radius: 14px; padding: 12px 8px; color: #172033; min-width: 0; }
.list-view .file-item { display: grid; grid-template-columns: 34px 1fr 120px; text-align: left; align-items: center; }
.file-item.selected { background: rgba(0,122,255,.18); box-shadow: inset 0 0 0 1px rgba(0,122,255,.35); }
.file-icon { color: #3178c6; display: grid; place-items: center; }
.file-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.file-meta { color: rgba(23,32,51,.55); font-size: 13px; }
.context-menu { position: fixed; z-index: 10; width: 190px; padding: 7px; border-radius: 14px; background: rgba(255,255,255,.86); backdrop-filter: blur(20px); box-shadow: 0 20px 55px rgba(15,23,42,.25); display: grid; gap: 3px; }
.context-menu button { justify-content: flex-start; background: transparent; }
.context-menu button:hover { background: rgba(0,122,255,.12); }
.modal { position: fixed; inset: 0; background: rgba(15,23,42,.22); display: grid; place-items: center; z-index: 20; }
.sheet { width: 360px; padding: 22px; display: grid; gap: 12px; border-radius: 22px; background: rgba(255,255,255,.88); backdrop-filter: blur(24px); box-shadow: 0 25px 80px rgba(15,23,42,.28); }
.danger { background: #ff453a; color: white; }
.banner, .error { color: #b42318; padding: 8px 16px; }
```

- [ ] **Step 8: Run frontend build**

Run:

```bash
cd frontend
npm run build
```

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add frontend/src
git commit -m "feat: add finder style frontend"
```

---

### Task 8: Docker Compose Deployment And Documentation

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `.dockerignore`
- Create or modify: `README.md`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Modify backend static serving target**

In `backend/app/main.py`, set static dir to support Docker image frontend output. Replace:

```python
    static_dir = settings.app_data_dir / "static"
```

with:

```python
    static_dir = settings.app_data_dir / "static"
    packaged_static_dir = settings.app_data_dir.parent / "static"
    if not static_dir.exists() and packaged_static_dir.exists():
        static_dir = packaged_static_dir
```

- [ ] **Step 2: Create Dockerfile**

Create `Dockerfile`:

```dockerfile
FROM node:22-bookworm AS frontend-builder
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    FILES_ROOT=/data/files \
    APP_DATA_DIR=/app/data
RUN pip install --no-cache-dir \
    "fastapi>=0.111.0" \
    "uvicorn[standard]>=0.30.0" \
    "sqlalchemy>=2.0.30" \
    "pydantic-settings>=2.3.0" \
    "python-multipart>=0.0.9" \
    "passlib[bcrypt]>=1.7.4" \
    "itsdangerous>=2.2.0"
COPY backend/app /app/app
COPY --from=frontend-builder /frontend/dist /app/static
RUN mkdir -p /data/files /app/data
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 3: Create compose and env files**

Create `docker-compose.yml`:

```yaml
services:
  file-manager:
    build: .
    ports:
      - "8000:8000"
    environment:
      APP_USERNAME: ${APP_USERNAME:-admin}
      APP_PASSWORD: ${APP_PASSWORD:-change-me-now}
      APP_SECRET_KEY: ${APP_SECRET_KEY:-replace-with-a-long-random-secret}
      FILES_ROOT: /data/files
      APP_DATA_DIR: /app/data
    volumes:
      - ${HOST_FILES_DIR:-./data/files}:/data/files
      - ${HOST_APP_DATA_DIR:-./data/app}:/app/data
    restart: unless-stopped
```

Create `.env.example`:

```env
APP_USERNAME=admin
APP_PASSWORD=change-me-now
APP_SECRET_KEY=replace-with-a-long-random-secret
HOST_FILES_DIR=./data/files
HOST_APP_DATA_DIR=./data/app
```

Create `.dockerignore`:

```text
.git
node_modules
frontend/node_modules
frontend/dist
backend/.pytest_cache
backend/**/__pycache__
data
.env
```

- [ ] **Step 4: Create README deployment instructions**

Create `README.md`:

```markdown
# Personal File Manager

A single-user web file manager for Linux with a modern macOS Finder-like interface.

## Quick Start

```bash
cp .env.example .env
mkdir -p data/files data/app
docker compose up --build
```

Open <http://localhost:8000> and log in with `APP_USERNAME` and `APP_PASSWORD` from `.env`.

## Storage

- Managed files are mounted at `/data/files` in the container.
- SQLite metadata and app-managed trash are stored under `/app/data`.
- The app only accepts root-relative paths and blocks traversal or symlink escapes outside `/data/files`.

## First User

On first startup, the app creates one user from `APP_USERNAME` and `APP_PASSWORD`. If the SQLite database already contains a user, later environment changes do not overwrite the stored password hash.

## Development

Backend:

```bash
cd backend
python -m pytest -v
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
npm test
```
```

- [ ] **Step 5: Run local verification**

Run:

```bash
cd backend
python -m pytest -v
cd ../frontend
npm test
npm run build
cd ..
docker compose config
docker compose build
```

Expected: pytest PASS, Vitest PASS, frontend build PASS, compose config valid, Docker image builds successfully.

- [ ] **Step 6: Commit**

```bash
git add Dockerfile docker-compose.yml .env.example .dockerignore README.md backend/app/main.py
git commit -m "feat: add docker deployment"
```

---

### Task 9: Final Integration Verification And Spec Coverage Check

**Files:**
- Modify only if verification reveals a defect in files from previous tasks.

- [ ] **Step 1: Run complete backend test suite**

Run:

```bash
cd backend
python -m pytest -v
```

Expected: PASS.

- [ ] **Step 2: Run complete frontend test and build suite**

Run:

```bash
cd frontend
npm test
npm run build
```

Expected: PASS.

- [ ] **Step 3: Run Docker deployment smoke test**

Run:

```bash
cd ..
mkdir -p data/files data/app
echo "hello" > data/files/hello.txt
docker compose up --build -d
curl -s http://localhost:8000/api/health
docker compose down
```

Expected: `curl` prints `{"status":"ok"}` and compose shuts down cleanly.

- [ ] **Step 4: Manual browser acceptance check**

Run:

```bash
docker compose up --build
```

Open `http://localhost:8000` and verify:

- Login works with `.env` credentials.
- Root directory lists mounted files.
- New folder works.
- Upload works.
- Rename works.
- Copy works.
- Drag a file onto a folder to move it.
- Delete moves item away from managed root listing.
- Search finds names from the current directory downward.
- Icon/list view toggle works.
- Right-click menu appears and actions work.
- Details dialog shows path, type, size, and modified time only.

- [ ] **Step 5: Commit final fixes if any**

If no defects were found, do not create an empty commit. If fixes were needed:

```bash
git add <changed-files>
git commit -m "fix: complete file manager integration"
```

## Self-Review Notes

Spec coverage:

- Single-user login and env bootstrap: Task 2.
- Linux root directory management and sandboxing: Tasks 3 and 4.
- Docker Compose deployment: Task 8.
- macOS Sonoma Finder-like UI: Task 7.
- Icon/list views, toolbar, sidebar, context menu, multi-select, drag move: Tasks 6 and 7.
- Upload, download, rename, delete-to-trash, move, copy, create folder: Tasks 3 and 4.
- Favorites, recent paths, view preferences, operation logs: Task 5 and Task 7 preference wiring.
- Current-directory filename search: Task 4.
- Structured errors and tests: Tasks 1, 3, 4, and 5.

Placeholder scan: no deferred placeholders are intended; every task names exact files, commands, and expected results.

Type consistency: backend schemas use snake_case for API fields and frontend API client maps TypeScript calls to those field names; file paths are root-relative strings everywhere.
