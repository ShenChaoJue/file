# Backend Architecture

The backend lives under `backend/app` and is served by FastAPI.

## Startup flow

`app/main.py` performs startup work:

1. Read environment settings from `app/config.py`.
2. Create `FILES_ROOT` and `APP_DATA_DIR` if missing.
3. Initialize SQLite tables.
4. Bootstrap the first user if the users table is empty.
5. Register error handlers and routers.
6. Mount packaged frontend static assets if available.

## Modules

- `config.py` — environment-driven settings.
- `db.py` — SQLAlchemy engine, base class, session factory, table initialization.
- `models.py` — SQLite tables for users, favorites, recent paths, preferences, operation logs, trash records.
- `errors.py` — structured error envelope and FastAPI exception handlers.
- `auth.py` — PBKDF2 password hashing, user bootstrap, signed session cookie helpers, current-user dependency.
- `filesystem.py` — canonical path resolution and all root-safe file operations.
- `metadata.py` — metadata helpers for favorites, recent paths, and preferences.
- `routers/auth.py` — login/logout/me endpoints.
- `routers/files.py` — directory listing, upload/download, file mutations, and search.
- `routers/metadata.py` — favorites, recent paths, and preferences endpoints.

## Data model

SQLite stores metadata only. Files remain on the host filesystem under `FILES_ROOT`.

## Error model

Errors use this shape:

```json
{"error":{"code":"path_not_found","message":"Path does not exist"}}
```

Prefer stable error codes because the frontend presents user-facing messages from API failures.
