#!/bin/sh
# Startpunkt des Containers.
#
# Warum hier und nicht im Deploy-Workflow: Terraform legt eine LEERE Datenbank an. Ohne
# einen Migrationslauf hat die Anwendung beim ersten Start keine Tabellen — sie wuerde
# starten und bei jedem Request scheitern. `alembic upgrade head` ist idempotent: steht die
# Datenbank bereits auf dem neuesten Stand, ist es ein SELECT auf `alembic_version` und
# sonst nichts. Das ist auch bei Scale-to-Zero-Kaltstarts guenstig genug.
#
# Sicher ist das, weil die Container App auf max_replicas = 1 steht — zwei gleichzeitige
# Migrationslaeufe kann es also nicht geben. Sollte das je hochgesetzt werden, gehoert der
# Migrationslauf in einen eigenen Container Apps Job und SKIP_MIGRATIONS=1 hierher.
set -e

if [ "${SKIP_MIGRATIONS}" = "1" ]; then
    echo "[entrypoint] SKIP_MIGRATIONS=1 — Migration uebersprungen"
else
    echo "[entrypoint] alembic upgrade head"
    # Bewusst KEIN `set +e`: schlaegt die Migration fehl, darf der Container nicht
    # starten. Eine Anwendung, die auf einem halb migrierten Schema laeuft, richtet mehr
    # Schaden an als eine, die sichtbar nicht hochkommt.
    alembic upgrade head
fi

echo "[entrypoint] starte gunicorn"
exec "$@"
