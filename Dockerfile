FROM node:22-bookworm AS frontend-builder
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
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
    "python-multipart>=0.0.9" \
    "itsdangerous>=2.2.0"
COPY backend/app /app/app
COPY --from=frontend-builder /frontend/dist /app/static
RUN mkdir -p /data/files /app/data
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
