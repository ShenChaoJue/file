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
