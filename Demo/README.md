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

### 2. Agent Configuration
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

### Chat starten
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

```
demo/
├── playground.py          # Haupt-Chat-Interface
├── requirements.txt       # Dependencies
├── .env                   # Config (nicht in Git)
└── index/
    ├── create_index.py    # Index-Erstellung
    main.py                    # Haupt-Interface mit Multi-Agent System
├── agent_config.py            # Zentrale Agent-Konfiguration
├── requirements.txt           # Python Dependencies
├── .env                       # Environment Variables (nicht in Git)
├── agents/                    # Agent-Implementierungen
│   ├── orchestration_agent.py # Routing & Planning
│   ├── chat_agent.py          # Allgemeine Konversation
│   ├── rag_agent.py           # Dokumentensuche
│   ├── sp_agent.py            # Smart Planning Integration
│   ├── base_agent.py          # Basis-Klasse
│   └── sp_tools_config.py     # SP Tools & Pipelines
├── smart-planning/            # Smart Planning Runtime
│   ├── runtime/               # Python Scripts für SP-Tools
│   └── Snapshots/             # Snapshot-Daten
├── index/                     # RAG Index Management
│   ├── create_index.py        # Index-Erstellung
│   └── ingest_docs.py         # Dokumenten-Import
└── logs/                      # Log-Dateien
```

## 🔧 Architektur

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