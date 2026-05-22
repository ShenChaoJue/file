# Verification

Use these commands before claiming that a change works.

## Backend

```bash
cd backend
python -m pytest -q
```

Expected current baseline: 21 tests pass. Warnings about `datetime.utcnow()` may appear; they are known warnings, not current failures.

## Frontend

```bash
cd frontend
npm test
npm run build
```

Expected current baseline: selection tests pass and Vite production build succeeds.

## Docker

If Docker is available:

```bash
mkdir -p data/files data/app
echo "hello" > data/files/hello.txt
docker compose up --build -d
curl -s http://localhost:8000/api/health
docker compose down
```

Expected health response:

```json
{"status":"ok"}
```

## Known environment limitation

In the original implementation environment, `docker` was not installed, so Docker build/runtime was not verified there. Do not claim Docker runtime success unless you have run the Docker commands in an environment with Docker available.
