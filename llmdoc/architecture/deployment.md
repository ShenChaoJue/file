# Deployment Architecture

Deployment uses a single Docker Compose service.

## Image build

`Dockerfile` has two stages:

1. `frontend-builder` uses Node to install frontend dependencies and run `npm run build`.
2. `runtime` uses Python 3.12 slim, installs backend dependencies, copies backend code, and copies frontend `dist` output to `/app/static`.

The runtime starts:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Runtime layout

- FastAPI serves APIs under `/api/*`.
- FastAPI also serves packaged frontend static assets from `/app/static`.
- Host files are mounted at `/data/files`.
- App metadata is mounted at `/app/data`.

## Compose service

`docker-compose.yml` defines one service named `file-manager`, exposing port `8000` and mounting both managed file and app-data directories.

## Operational note

Change `APP_PASSWORD` and `APP_SECRET_KEY` before real deployment. If the SQLite database already contains a user, changing `APP_PASSWORD` later will not reset the password.
