# =============================================================================
# Feuerwehr Anwesenheits-App - Dockerfile
# =============================================================================
# Multi-Stage Build für optimierte Image-Größe
# =============================================================================

# Stage 1: Frontend bauen
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Package-Dateien kopieren
COPY frontend/package*.json ./

# Dependencies installieren
RUN npm ci

# Frontend-Quellcode kopieren
COPY frontend/ ./

# Frontend bauen
RUN npm run build

# Stage 2: Backend vorbereiten
FROM python:3.11-slim AS backend

WORKDIR /app

# System-Dependencies installieren
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python-Dependencies installieren
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Backend-Code kopieren
COPY backend/ ./

# Frontend-Build aus Stage 1 kopieren
COPY --from=frontend-builder /app/frontend/../backend/static ./static

# Daten-Verzeichnis erstellen
RUN mkdir -p /app/data

# Non-root User erstellen
RUN useradd -r -s /bin/false appuser && \
    chown -R appuser:appuser /app

USER appuser

# Environment-Variablen
ENV HOST=0.0.0.0 \
    PORT=8000 \
    DATABASE_PATH=/app/data/feuerwehr_anwesenheit.db \
    CREATE_DEMO_DATA=true \
    FEUERWACHE_NAME="Freiwillige Feuerwehr Musterstadt" \
    AUTO_TIMEOUT_HOURS=3 \
    SESSION_CHECK_INTERVAL=60 \
    PYTHONUNBUFFERED=1

# Port freigeben
EXPOSE 8000

# Health Check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

# Anwendung starten
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
