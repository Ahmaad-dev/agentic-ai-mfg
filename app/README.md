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
- ✅ **Zentrale Konfiguration**: Alle Limits in `agent_config.py`
- ✅ **Robustes Logging**: Vollständige Logs in `logs/`

## 📦 Installation

```bash
cd demo
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## ⚙️ Konfiguration

### 1. Environment Variables
Erstelle `.env` im demo-Verzeichnis:
```env
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o
AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT=text-embedding-ada-002

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_API_KEY=your-key
AZURE_SEARCH_INDEX=your-index

# Smart Planning API (optional)
SP_API_BASE_URL=https://your-sp-api.com
SP_CLIENT_ID=your-client-id
SP_CLIENT_SECRET=your-secret
```

### 2. Storage-Konfiguration (Lokal vs. Cloud)

Das System unterstützt zwei Storage-Modi, die über die `.env` Datei gesteuert werden:

**Lokal (Standard für Entwicklung):**
```env
STORAGE_MODE=LOCAL
LOCAL_STORAGE_PATH=./smart-planning/Snapshots
```

**Azure Blob Storage (für Cloud-Deployment):**
```env
STORAGE_MODE=AZURE
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net
AZURE_STORAGE_CONTAINER=snapshots
```

> ⚠️ **Wichtig für Nutzer:** Du musst nichts an deinem Workflow ändern. `web_server.py` starten und chatten funktioniert genauso wie bisher. Der `StorageManager` in `storage_manager.py` entscheidet automatisch anhand von `STORAGE_MODE`, ob lokal oder in die Cloud gespeichert wird.

#### Wechsel zu Azure Blob Storage (Schritt für Schritt)

1. **Connection String im Azure Portal holen:**  
   Azure Portal → Storage Account → *Security + Networking* → *Access keys* → `Connection string` kopieren

2. **`.env` aktualisieren:**
   ```env
   STORAGE_MODE=AZURE
   AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net
   AZURE_STORAGE_CONTAINER=snapshots
   ```

3. **Container im Storage Account anlegen** (einmalig):  
   Azure Portal → Storage Account → *Containers* → `+ Container` → Name: `snapshots`  
   *(oder den Namen aus `AZURE_STORAGE_CONTAINER` verwenden)*

4. **`web_server.py` neu starten** – fertig.  
   Alle neuen Snapshots landen ab jetzt automatisch im Blob Storage.

> 💡 **Lokale Snapshots migrieren:** Bestehende Snapshot-Ordner aus `smart-planning/Snapshots/` können manuell über den Azure Storage Explorer in den Container hochgeladen werden. Die Ordnerstruktur (`{snapshot-id}/iteration-1/...`) bleibt dabei identisch.

### 3. Agent Configuration
Zentrale Einstellungen in `agent_config.py`:
```python
CHAT_HISTORY_CONFIG = {
    "max_history_pairs": 5,      # 10 Messages gesamt
    "max_planning_pairs": 2,     # 4 Messages für Planning
    "max_message_chars": 1000,   # Token-Kontrolle
    "max_tokens": 700            # LLM Output
}
```

## 🏃 Nutzung

### Web-Interface starten (empfohlen)
```bash
cd demo
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
  SP_Agent (sp_agent.py)
        │  ruft per subprocess auf
        ▼
  Runtime-Scripts (create_snapshot.py, validate_snapshot.py, ...)
        │  nutzen
        ▼
  StorageManager (storage_manager.py)
        │
        ├── STORAGE_MODE=LOCAL  →  ./smart-planning/Snapshots/  (Dateisystem)
        └── STORAGE_MODE=AZURE  →  Azure Blob Storage Container
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