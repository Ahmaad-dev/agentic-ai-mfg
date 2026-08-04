# 🤖 Multi-Agent System für Smart Planning & Manufacturing

Intelligentes Multi-Agent System mit Orchestrator, RAG, Chat und Smart Planning Integration für Produktionsplanung.

## 🚀 Features

### **Multi-Agent Architektur**
- ✅ **Orchestrator**: Intelligentes Routing und Multi-Step Planning
- ✅ **Chat Agent**: Allgemeine Konversation und Erklärungen
- ✅ **RAG Agent**: Dokumentensuche mit Azure AI Search
- ✅ **SP Agent**: Smart Planning Snapshot-Verwaltung (Erstellen, Validieren, Korrigieren)

### **Smart Planning Integration**
- ✅ **Snapshot Management**: Erstellen, Validieren, Umbenennen
- ✅ **Automatische Fehlerkorrektur**: LLM-gestützte Datenkorrektur
- ✅ **Pipeline-Workflows**: full_correction, correction_from_validation, analyze_only
- ✅ **Audit Reports**: Detaillierte Validierungs- und Korrekturberichte

### **Intelligente Features**
- ✅ **Kontextbewusstsein**: 10 Messages Historie mit 1000 Zeichen/Message
- ✅ **Natürliche Interaktion**: Keine unnötigen Rückfragen bei klaren Anfragen
- ✅ **Zentrale Konfiguration**: Alle Limits in `core/agent_config.py`
- ✅ **Robustes Logging**: Vollständige Logs in `logs/`

## 📦 Installation

```bash
cd app
python -m venv .venv
.venv\Scripts\activate
pip install -r deploy/requirements.txt
pip install -r deploy/requirements-azure.txt   # nur für Azure SQL / Blob / ACS nötig
```

## ⚙️ Konfiguration

### 1. Umgebungsvariablen

Alles kommt aus der Umgebung — im Code stehen keine Endpunkte, Schlüssel oder
Ressourcennamen. Lokal liest die Anwendung `app/.env` (nicht versioniert), in Azure setzt
Terraform dieselben Variablen an der Container App.

```env
# --- Azure OpenAI: EIN Satz je Agent. Alle vier sind PFLICHT (must_env), ein fehlender
#     Wert bricht den Start ab, statt später mit einer unklaren Meldung zu scheitern.
AZURE_OPENAI_CHAT_ENDPOINT=https://<ressource>.openai.azure.com
AZURE_OPENAI_CHAT_KEY=...
AZURE_OPENAI_CHAT_API_VERSION=2025-01-01-preview
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4.1

AZURE_OPENAI_RAG_ENDPOINT=https://<ressource>.openai.azure.com
AZURE_OPENAI_RAG_KEY=...
AZURE_OPENAI_RAG_API_VERSION=2025-01-01-preview
AZURE_OPENAI_RAG_DEPLOYMENT=gpt-4.1

AZURE_OPENAI_ORCHESTRATION_ENDPOINT=https://<ressource>.openai.azure.com
AZURE_OPENAI_ORCHESTRATION_KEY=...
AZURE_OPENAI_ORCHESTRATION_API_VERSION=2025-01-01-preview
AZURE_OPENAI_ORCHESTRATION_DEPLOYMENT=gpt-4.1

AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT=text-embedding-3-small

# --- Von den Runtime-Skripten benutzt (laufen als Subprozess, eigener Satz)
AZURE_OPENAI_ENDPOINT=https://<ressource>.openai.azure.com
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_API_VERSION=2025-01-01-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4.1

# --- Azure AI Search
AZURE_SEARCH_ENDPOINT=https://<dienst>.search.windows.net
AZURE_SEARCH_ADMIN_KEY=...
AZURE_SEARCH_INDEX=process-docs-index

# --- Smart Planning (ESAROM). Nur CLIENT_SECRET ist Pflicht; die übrigen drei haben
#     Standardwerte, die auf die TESTUMGEBUNG zeigen — für Produktion setzen!
CLIENT_SECRET=...
SMART_PLANNING_BASE_URI=https://<host>
SMART_PLANNING_CLIENT_ID=apiClient-test
SMART_PLANNING_REALM=Esarom

# --- Datenbank. Fehlt sie, nutzt die Anwendung SQLite unter app/db/pt4.sqlite3.
DATABASE_URL=mssql+pyodbc://...

# --- Sonstiges
AZURE_SPEECH_KEY=...
AZURE_SPEECH_REGION=swedencentral
NOTIFICATION_CHANNEL=acs
ACS_CONNECTION_STRING=...
ACS_SENDER_EMAIL=DoNotReply@<domain>.azurecomm.net
APP_BASE_URL=http://localhost:8000
```

> **Nach jedem `terraform apply`**, der Ressourcen neu anlegt oder Schlüssel rotiert, ist die
> lokale `.env` veraltet. Typisches Symptom: HTTP 401 mit „invalid subscription key or wrong
> API endpoint" — obwohl der Endpunkt stimmt. Dann die Schlüssel aus Azure nachziehen.

### 2. Storage: lokal gegen Blob

`STORAGE_MODE` entscheidet, wohin **zwei verschiedene Dinge** gehen — Snapshot-Daten und
Lernkarten. Das ist der Punkt, den man leicht übersieht:

| | `STORAGE_MODE=LOCAL` | `STORAGE_MODE=AZURE` |
|---|---|---|
| Snapshots | `data/snapshots/` (Standard, dateirelativ) | Blob-Container aus `AZURE_STORAGE_CONTAINER` |
| Lernkarten | `app/skills/` | Blob-Container aus `AZURE_SKILLS_CONTAINER` |

```env
# lokal
STORAGE_MODE=LOCAL

# Cloud
STORAGE_MODE=AZURE
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
AZURE_STORAGE_CONTAINER=snapshots
AZURE_SKILLS_CONTAINER=skills
RULEBOOK_SKILLS_PREFIX=            # leer: Karten liegen in der Container-Wurzel
```

**Im Azure-Modus liest der Regelwerk-Lader die Lernkarten NICHT aus dem Container-Image**,
sondern aus dem Blob Storage. Der Ordner `app/skills/` ist dort unbeteiligt. Fehlen die
Karten im Blob, stirbt die Korrektur-Pipeline mit
`FileNotFoundError: _core.md not found` — Chat, Review Board und Dashboard laufen weiter.

Zwei getrennte Container sind Absicht: Lernkarten sind Konfiguration, keine Daten. Lägen sie
im Snapshot-Container, würde ein Aufräumen dort das Regelwerk mitlöschen.

### 3. Lernkarten pflegen — ohne Deployment

Der eigentliche Gewinn des Blob-Ansatzes: eine Karte im Azure-Portal zu bearbeiten ändert das
Verhalten **sofort**, ohne neues Image und ohne Zugriff auf dieses Repository.

Für den Abgleich mit dem Repository:

```bash
python -m tools.sync_skills status              # nur anzeigen
python -m tools.sync_skills push                # fehlende Karten hochladen
python -m tools.sync_skills pull                # Portal-Änderungen zurückholen
```

`push` lädt **nur fehlende** Karten hoch. Abweichende werden gemeldet und übersprungen — sonst
würde ein Routine-Abgleich genau die Portal-Korrekturen zerstören, für die der Mechanismus
gebaut ist. Überschreiben erfordert `--overwrite`.

### 4. Verhaltensschalter

| Variable | Standard | Bedeutung |
|---|---|---|
| `HUMAN_IN_THE_LOOP` | `true` | **Sicherheitsschalter.** `false` = Korrekturen werden ohne menschliche Freigabe angewendet. |
| `RULEBOOK_MODE` | `cards` | `cards` = Lernkarten, `monolith` = die eine große Regeldatei |

Lokal über `.env`, in Azure über Terraform (`variables.tf`) — dort mit Validierung, ein
ungültiger Wert bricht im `terraform plan` ab.

### 5. Agent-Konfiguration

Zentrale Einstellungen in `core/agent_config.py`:

```python
CHAT_HISTORY_CONFIG = {
    "max_history_pairs": 5,      # 10 Nachrichten gesamt
    "max_planning_pairs": 2,     # 4 Nachrichten für die Planung
    "max_message_chars": 1000,   # Token-Kontrolle
    "max_tokens": 700            # LLM-Ausgabe
}
```

## 🏃 Nutzung

### Web-Interface starten (empfohlen)
```bash
cd app
python web_server.py
```
Dann Browser öffnen: [http://localhost:8000](http://localhost:8000)

Das ist alles. Du chattest direkt mit dem Agenten – egal ob lokal oder in der Cloud deployed.

### Chat via Terminal starten (alternativ)
```bash
python main.py
```

### Beispiel-Interaktionen

**Smart Planning:**
```
Du: Erstelle einen Snapshot
Assistent: Snapshot "SP-Agent: Snapshot vom 2026-02-08" wurde erstellt (ID: abc-123)

Du: Validiere den Snapshot
Assistent: ✅ Snapshot ist valide - 0 Fehler, 4 Warnungen

Du: Korrigiere die Fehler
Assistent: Fehler wurden automatisch korrigiert. Snapshot ist jetzt valide.
```

**Dokumentensuche:**
```
Du: Suche in Dokumenten nach Temperaturrichtlinien
Assistent: Laut den Richtlinien sollte die Hallentemperatur...
📚 Quellen: production-guidelines.pdf
```

**Allgemeine Fragen:**
```
Du: Erkläre mir was ein Snapshot ist
Assistent: Ein Snapshot ist eine Momentaufnahme der Produktionsplanung...
```

## 🔧 Troubleshooting

- **Logs**: Siehe `chat_YYYYMMDD.log`
- **Fehler bei Embedding**: Prüfe AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT
- **Keine Suchergebnisse**: Prüfe ob Index befüllt ist

## 📁 Projektstruktur

> **Umbenannt am 02.08.2026:** Der Anwendungsordner hieß bis dahin `demo/`. Er heißt jetzt
> `app/`, weil es sich um keine Demo mehr handelt. Ältere Einträge in `docs/PROJECT_LOG.md`
> nennen bewusst weiterhin die alten Pfade — es ist ein datiertes Protokoll.

```
agentic-ai-mfg/
├── app/                       # Die gesamte Anwendung
│   ├── web_server.py          # Web-Interface (Flask) → Startpunkt für Chat im Browser
│   ├── main.py                # Terminal-Interface mit Multi-Agent System
│   ├── core/                  # Querschnittsmodule
│   │   ├── agent_config.py    #   Zentrale Agent-Konfiguration
│   │   ├── cost_model.py      #   Token-/Kostenschätzung
│   │   ├── storage_manager.py #   Storage-Abstraktion: LOCAL ↔ Azure Blob Storage
│   │   └── rulebook_loader.py #   Lädt die Lernkarten aus skills/ (CLI: python -m core.rulebook_loader)
│   ├── agents/                # Agent-Implementierungen
│   │   ├── orchestration_agent.py # Routing & Planning
│   │   ├── chat_agent.py      #   Allgemeine Konversation
│   │   ├── rag_agent.py       #   Dokumentensuche
│   │   ├── sp_agent.py        #   Smart Planning (ruft die Runtime-Skripte per Subprozess auf)
│   │   ├── email_agent.py     #   E-Mail entwerfen und senden
│   │   ├── base_agent.py      #   Basis-Klasse
│   │   └── sp_tools_config.py #   SP-Tools & Pipelines
│   ├── routes/                # Flask-Blueprints (Review, Dashboard, Validierung, Apply)
│   ├── db/                    # SQLAlchemy-Modelle und Repository
│   ├── memory/                # Gedächtnis: Fälle schreiben (long_term) und finden (retrieval)
│   ├── skills/                # Lernkarten — Domänenwissen als Markdown, ohne Code
│   ├── mcp_connections/       # MCP-Anbindungen
│   ├── index/                 # RAG-Index-Verwaltung
│   ├── ui/                    # Oberfläche (Chat, Review Board, Management Dashboard)
│   ├── eval/                  # Testläufe zur Auswertung (AP-E)
│   ├── alembic/ + alembic.ini # Datenbank-Migrationen (müssen zusammen bleiben)
│   ├── deploy/                # Dockerfile, gunicorn.conf.py, requirements*.txt
│   ├── .dockerignore          # MUSS hier liegen: Docker sucht sie im Build-Kontext (= app/)
│   └── tools/smart-planning/
│       └── runtime/           # Python-Skripte der SP-Tools (per Subprozess aufgerufen)
│                              # Bleiben BEWUSST unter app/: der Docker-Build kopiert nur
│                              # diesen Kontext — außerhalb wären sie nicht im Image.
├── data/                      # LAUFZEITDATEN, gitignoriert — kein Code
│   ├── snapshots/             # Snapshot-Daten (bei STORAGE_MODE=AZURE im Blob Storage)
│   ├── logs/
│   └── archive/
└── docs/                      # Projektdokumentation, Protokoll, Belege
```

**Weiterführend:** [`README-PT4.md`](README-PT4.md) beschreibt die Governance-Schicht —
Human-in-the-Loop, Konfidenz-Score, Datenbankschema und die zugehörigen Schalter.

## 🔧 Architektur

### Storage-Abstraktion (LOCAL ↔ AZURE)

```
web_server.py / main.py
        │
        ▼
  SP_Agent (agents/sp_agent.py)
        │  ruft per subprocess auf
        ▼
  Runtime-Skripte (tools/smart-planning/runtime/*.py)
        │  nutzen
        ▼
  StorageManager (core/storage_manager.py)
        │
        ├── STORAGE_MODE=LOCAL  →  ../data/snapshots/          (Dateisystem)
        └── STORAGE_MODE=AZURE  →  Blob-Container "snapshots"

  Regelwerk-Lader (core/rulebook_loader.py) nutzt DENSELBEN StorageManager:
        ├── STORAGE_MODE=LOCAL  →  app/skills/*.md
        └── STORAGE_MODE=AZURE  →  Blob-Container "skills"  (im Portal editierbar)
```

Für dich als Nutzer bedeutet das: Du startest immer `web_server.py` und chattest.
Die Storage-Konfiguration in `.env` entscheidet automatisch, wo die Daten landen.

### Orchestrator-Pattern
1. **User Input** → Orchestrator analysiert Anfrage
2. **Planning** → Erstellt Single/Multi-Step Plan
3. **Routing** → Wählt passende Agenten (Chat, RAG, SP)
4. **Execution** → Führt Plan aus (sequenziell/parallel)
5. **Interpretation** → LLM bereitet Ergebnis benutzerfreundlich auf

### Agent-Typen
- **Chat**: Keine externen Tools, nutzt LLM-Wissen
- **RAG**: Azure AI Search für Dokumentensuche
- **SP**: Ruft Python-Tools via subprocess auf (create, validate, correct)