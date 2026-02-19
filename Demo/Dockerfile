# Multi-stage build für optimale Image-Größe
FROM python:3.11-slim AS builder

# Build-Abhängigkeiten
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Requirements installieren (system-weit, kein --user)
COPY requirements.txt requirements-azure.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-azure.txt

# Production Stage
FROM python:3.11-slim

WORKDIR /app

# Runtime-Abhängigkeiten
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python packages von builder kopieren (system-weit in /usr/local)
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Application code kopieren
COPY . .

# Non-root user erstellen
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Logs directory erstellen
RUN mkdir -p /app/logs && chown -R appuser:appuser /app/logs

# Snapshots mount point
RUN mkdir -p /mnt/snapshots && chown -R appuser:appuser /mnt/snapshots

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Expose port
EXPOSE 8000

# Gunicorn als Production Server
CMD ["gunicorn", "--config", "gunicorn.conf.py", "web_server:app"]
