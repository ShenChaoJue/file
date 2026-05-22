# Development Guide

## Prerequisites

- Python 3.12+
- Node.js 22+
- npm
- Docker CLI for deployment verification

## Backend workflow

```bash
cd backend
python -m pytest -q
```

For iterative local runs:

```bash
uvicorn app.main:app --reload
```

## Frontend workflow

```bash
cd frontend
npm test
npm run build
npm run dev
```

## Suggested change loop

1. Add or update a test.
2. Run the targeted test and confirm the failure or expected red state.
3. Implement the smallest code change.
4. Re-run the targeted test.
5. Run the full backend or frontend suite for the affected area.
6. Commit the change.

## Practical reminders

- Keep file operations inside `FileSystemService`.
- Re-run backend tests after any auth, metadata, or filesystem change.
- Re-run frontend build after TypeScript or component changes.
- If Docker is available, run `docker compose config` and a smoke test before declaring deployment work done.
