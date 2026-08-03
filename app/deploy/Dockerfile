# Multi-stage build für optimale Image-Größe
FROM python:3.11-slim AS builder

# Build-Abhängigkeiten
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Requirements installieren (system-weit, kein --user)
# Der Build-Kontext bleibt app/ — nur die Dateien liegen jetzt in deploy/.
COPY deploy/requirements.txt deploy/requirements-azure.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-azure.txt

# Production Stage
FROM python:3.11-slim

WORKDIR /app

# Runtime-Abhängigkeiten inkl. Microsoft ODBC Driver 18 für SQL Server.
# OHNE den Treiber ist `pyodbc` zwar installiert, aber jede Verbindung zu Azure SQL
# scheitert erst beim ersten Request — der Container startet also scheinbar erfolgreich
# und faellt danach bei jeder Anfrage um. `unixodbc` ist der Treibermanager, den pyodbc
# zur Laufzeit braucht. ACCEPT_EULA ist fuer msodbcsql18 zwingend.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    ca-certificates \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
       | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" \
       > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 unixodbc \
    && rm -rf /var/lib/apt/lists/*

# Python packages von builder kopieren (system-weit in /usr/local)
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Application code kopieren
COPY . .

# Non-root user erstellen. Das Ausfuehrbar-Bit des Entrypoints wird hier gesetzt: der
# Build-Kontext kommt von Windows, das kein POSIX-Ausfuehrungsrecht kennt.
RUN chmod +x /app/deploy/entrypoint.sh && \
    useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Laufzeitpfade. Die Anwendung legt Logs und Snapshots normalerweise NEBEN dem Code ab
# (<repo>/data/...). Im Image gibt es kein Repository-Wurzelverzeichnis — dort liegt die
# Anwendung auf /app, und der Pfad daneben waere die Dateisystemwurzel, in die appuser
# nicht schreiben darf. Beide Ziele werden deshalb hier ausdruecklich gesetzt.
ENV LOG_DIR=/app/logs \
    LOCAL_STORAGE_PATH=/mnt/snapshots

RUN mkdir -p /app/logs && chown -R appuser:appuser /app/logs
RUN mkdir -p /mnt/snapshots && chown -R appuser:appuser /mnt/snapshots

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Expose port
EXPOSE 8000

# Migration vor dem Start (siehe deploy/entrypoint.sh), danach gunicorn.
ENTRYPOINT ["/app/deploy/entrypoint.sh"]
CMD ["gunicorn", "--config", "deploy/gunicorn.conf.py", "web_server:app"]
