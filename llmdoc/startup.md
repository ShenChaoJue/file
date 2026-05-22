# Startup

Read this first when working on the Personal File Manager project.

## What this project is

A single-user Linux web file manager with a modern macOS Finder-like UI. It manages a real host directory mounted into the app and stores metadata in SQLite.

## First docs to read

1. `llmdoc/must/security-boundaries.md` for filesystem and auth safety rules.
2. `llmdoc/must/verification.md` before claiming anything works.
3. `llmdoc/overview/project-overview.md` for scope and non-goals.
4. Relevant architecture doc:
   - Backend/API work: `llmdoc/architecture/backend.md`
   - Frontend/UI work: `llmdoc/architecture/frontend.md`
   - Docker/deploy work: `llmdoc/architecture/deployment.md`

## Code map

- Backend: `backend/app/`
- Backend tests: `backend/tests/`
- Frontend: `frontend/src/`
- Docker deployment: `Dockerfile`, `docker-compose.yml`, `.env.example`

## Important constraints

- Never bypass `FileSystemService` for path resolution or file mutation.
- Treat all user-provided paths as root-relative paths under `FILES_ROOT`.
- Do not add multi-user, sharing, file content indexing, chunked uploads, or preview/transcoding unless the spec changes.
- The app-managed trash lives under `APP_DATA_DIR/trash`, not inside the managed file root.

## Current verification status

Last known local verification:

- `cd backend && python -m pytest -q` → 21 passed.
- `cd frontend && npm test` → 3 passed.
- `cd frontend && npm run build` → succeeded.
- Docker was not verified in this environment because Docker CLI was unavailable.
