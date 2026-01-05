# 🤖 Agentic AI Manufacturing Assistant

Intelligenter Chat-Assistent mit RAG (Retrieval-Augmented Generation) für Produktionsumgebungen.

## 🚀 Features

- ✅ **Flexibler Chat**: Normaler Modus ohne RAG für allgemeine Fragen
- ✅ **RAG on Demand**: Aktiviert bei Keywords wie "suche", "dokument", "rag"
- ✅ **Chathistorie**: Kontextbewusste Konversationen
- ✅ **Token-Management**: Automatische Begrenzung auf letzte 10 Messages
- ✅ **Fehlerbehandlung**: Robuste Error-Handling
- ✅ **Logging**: Vollständiges Logging in Dateien

## 📦 Installation

```bash
cd demo
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## ⚙️ Konfiguration

1. Kopiere `.env.example` zu `.env`
2. Fülle deine Azure-Credentials ein
3. Optional: Setze `DOCS_DIRECTORY` für eigenen Dokumenten-Pfad

## 🏃 Nutzung

### 1. Index erstellen
```bash
python index/create_index.py
```

### 2. Dokumente indizieren
```bash
# Dummy-Daten (zum Testen)
python index/ingest-dummy.py

# Echte PDFs
python index/ingest_docs.py
```

### 3. Chat starten
```bash
python playground.py
```

## 💡 Beispiel-Nutzung

```
Du: Wie geht's?
💬 [Chat] Assistent: Mir geht es gut, danke! ...

Du: Suche nach Hallentemperatur
🔍 [RAG] Assistent: Laut den Richtlinien sollte ...
📚 Quellen: internal-guideline.pdf
```

## 📊 Trigger-Wörter für RAG

- rag, suche, suchen, durchsuche
- finde, dokument, wissen, wissensbasis
- quelle, richtlinie, guideline
- nachschlagen, recherche, index, datenbank

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
    ├── ingest-dummy.py    # Test-Daten
    └── ingest_docs.py     # PDF-Import
```

## 🎯 Nächste Schritte

- [ ] LLM-basierte RAG-Aktivierung statt Keywords
- [ ] Streaming für Echtzeit-Antworten
- [ ] Multi-Turn RAG mit Conversation Memory
- [ ] Hybrid Search (Vector + Keyword)
- [ ] Web-UI mit Streamlit/Gradio
