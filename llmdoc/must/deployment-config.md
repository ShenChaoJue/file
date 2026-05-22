# Deployment Configuration

Deployment is Docker Compose with one service: `file-manager`.

## Required environment variables

- `APP_USERNAME` — initial single-user username. Default in compose: `admin`.
- `APP_PASSWORD` — initial single-user password. Change before real deployment.
- `APP_SECRET_KEY` — signing key for session cookies. Use a long random value.
- `HOST_FILES_DIR` — host directory mounted as `/data/files`.
- `HOST_APP_DATA_DIR` — host directory mounted as `/app/data`.

## Container paths

- `/data/files` — managed file root.
- `/app/data` — SQLite DB, app metadata, and app-managed trash.
- `/app/static` — packaged frontend build output.

## Persistence rule

Both managed files and app data must be persisted. If `/app/data` is deleted, SQLite metadata and the initial user record are lost, and first-user bootstrap will run again.

## Deployment files

- `Dockerfile` builds frontend assets then creates a Python runtime image.
- `docker-compose.yml` mounts file and app-data volumes.
- `.env.example` documents the expected variables.
