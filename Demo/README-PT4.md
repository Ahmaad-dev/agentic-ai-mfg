# PT4 — Projektarbeit 4: Enterprise-Governance-Schicht

> Dieses Dokument beschreibt ausschließlich die Erweiterungen aus **Projektarbeit 4**.  
> Die Basis-Dokumentation des Systems (Installation, Agenten, SP-Integration) findest du in [`README.md`](README.md).

---

PT4 verwandelt das System vom autonomen PoC zur enterprise-fähigen Lösung. Alle Änderungen sind **additiv** — das bestehende Chat-/Korrektur-Verhalten bleibt unberührt.

---

## Was PT4 hinzufügt

| Bereich | PT3 (vorher) | PT4 (neu) |
|---|---|---|
| Korrekturen | automatisch geschrieben | Vorschlag erzeugt, **wartet auf Freigabe** |
| Confidence | kein Score | Formel `0.5·llm + 0.3·schema + 0.2·memory` |
| Proposals | nur in `iteration-N/` vergraben | zusätzlich zentral (`_proposals/`) + DB |
| Persistenz | keine DB | SQLAlchemy 2.0 + Alembic, 7 Tabellen |
| Token/Kosten | nicht erfasst | pro Request in `agent_runs` gespeichert |
| HitL-Freigabe | — | AP3/AP4 *(in Arbeit)* |
| Memory | — | AP7 *(geplant)* |

---

## Features (PT4)

- ✅ **Human-in-the-Loop Governance**: Korrekturen werden als Vorschlag eingefroren, nichts wird autonom geschrieben (`HUMAN_IN_THE_LOOP`-Toggle in `agent_config.py`)
- ✅ **Confidence-Score**: Jeder Korrekturvorschlag trägt einen nachvollziehbaren Score (Formel: `0.5·llm_confidence + 0.3·schema_valid + 0.2·memory`)
- ✅ **Proposal-Persistenz**: Vorschläge werden zentral als JSON (`_proposals/`) und in der relationalen DB (`proposals`-Tabelle) abgelegt, jeweils mit stabiler `proposal_id`
- ✅ **Datenbank-Backbone**: SQLAlchemy 2.0 + Alembic-Migrationen; 7 Tabellen
- ✅ **Token/Cost-Tracking**: Prompt- und Completion-Tokens jedes LLM-Calls werden pro Request aggregiert und in `agent_runs` gespeichert (inkl. Kostenschätzung)
- 🔄 **HitL-Backend** *(AP3 — in Arbeit)*: Flask-Blueprint mit approve / reject / modify-Endpoints
- 🔄 **HitL-UI** *(AP4 — in Arbeit)*: Before/After-Diff, Confidence-Anzeige, Freigabe-Buttons
- 🔄 **Memory-System** *(AP7 — geplant)*: Case-Based Reasoning aus historischen Entscheidungen

---

## Neue und geänderte Dateien

```
demo/
├── db/                        # NEU — Datenbank-Layer
│   ├── __init__.py
│   ├── models.py              # SQLAlchemy ORM (7 Tabellen)
│   ├── session.py             # Engine/Session-Factory (SQLite ↔ Azure SQL via DATABASE_URL)
│   ├── repository.py          # CRUD-Funktionen
│   └── pt4.sqlite3            # Lokale DB (gitignored)
├── alembic/                   # NEU — Alembic-Migrationen
│   └── versions/
│       └── 55f1c1b3…_ap2_initial_schema.py
├── alembic.ini                # NEU
├── agent_config.py            # GEÄNDERT: HUMAN_IN_THE_LOOP-Toggle, COST_PER_1K_TOKENS
├── agents/
│   ├── orchestration_agent.py # GEÄNDERT: HitL-Block + Token-Accumulator (5 LLM-Call-Stellen)
│   ├── chat_agent.py          # GEÄNDERT: response.usage in metadata
│   └── rag_agent.py           # GEÄNDERT: response.usage in metadata
├── smart-planning/
│   ├── runtime/
│   │   ├── correction_models.py        # GEÄNDERT: confidence_score, status, schema_valid
│   │   └── generate_correction_llm.py  # GEÄNDERT: Confidence-Formel, Proposal-Record, DB-Write, Token-Lesen
│   └── Snapshots/
│       └── _proposals/        # NEU — zentrale JSON-Ablage aller Vorschläge
└── web_server.py              # GEÄNDERT: DB-Session/Message/AgentRun + Token/Cost pro Request
```

---

## Human-in-the-Loop Toggle

Der Toggle steuert, ob Korrekturen autonom angewendet werden dürfen.

```env
# .env — Standard: true (sicher, PT4-Modus)
HUMAN_IN_THE_LOOP=true

# false = Legacy-Verhalten (PT3, nur für Tests/Baseline)
HUMAN_IN_THE_LOOP=false
```

Bei `true` werden folgende Pfade blockiert (kein automatisches Schreiben in `snapshot-data.json`):

| Pfad | Verhalten bei Toggle=true |
|---|---|
| Pipeline `full_correction` | → umgebogen auf `analyze_only` (nur Vorschlag) |
| Pipeline `correction_from_validation` | → umgebogen auf `analyze_only` |
| Pipeline `apply_and_upload` | → blockiert mit Freigabe-Hinweis |
| Einzel-Tool `apply_correction` | → blockiert mit Freigabe-Hinweis |

---

## Confidence-Score

Jeder erzeugte Korrekturvorschlag trägt drei Felder:

```json
"correction_proposal": {
  "llm_confidence": 0.95,      // LLM-Selbsteinschätzung (0.0–1.0)
  "schema_valid": true,        // Pydantic-Validierung bestanden
  "confidence_score": 0.775    // berechnetes Komposit
}
```

**Formel** (in `generate_correction_llm.py`, Funktion `compute_confidence_score`):

```
confidence = 0.5 · llm_confidence
           + 0.3 · schema_valid     (1.0 wenn gültig, 0.0 sonst)
           + 0.2 · memory_support   (AP7; derzeit 0.0)
```

**Sonderfall:** `action == "manual_intervention_required"` → Score wird zwingend auf `0.0` gesetzt.

---

## Datenbankschema

| Tabelle | Inhalt |
|---|---|
| `sessions` | Eine Chat-Session pro Nutzer-Interaktion |
| `messages` | Jede User- und Assistenten-Nachricht mit `role`, `agent_name`, `content` |
| `agent_runs` | Ein Eintrag pro Agent-Ausführung: `tokens_prompt`, `tokens_completion`, `cost_estimate`, `duration_ms` |
| `snapshots_meta` | Snapshot-Metadaten: Fehler/Warnungen vor und nach Korrektur |
| `proposals` | Korrekturvorschläge: `confidence_score`, `schema_valid`, `status`, `target_path`, `suggested_value` |
| `reviews` | Menschliche Freigabe-Entscheidungen: `decision`, `final_value`, `comment` *(befüllt in AP3)* |
| `memory_items` | Case-Based-Reasoning-Speicher *(befüllt in AP7)* |

Alle 7 Tabellen werden per **Alembic** verwaltet. Migration einmalig ausführen:

```bash
cd demo
python -m alembic upgrade head
```

---

## Datenbank-Konfiguration (SQLite ↔ Azure SQL)

Der Backend-Wechsel erfolgt ausschließlich über eine Umgebungsvariable — kein Code ändert sich.

### Lokal (Standard, keine Konfiguration nötig)

SQLite-Datei `demo/db/pt4.sqlite3` wird automatisch angelegt. Kein weiterer Setup nötig.

### Azure SQL (Produktion)

**1. Connection String ermitteln:**  
Azure Portal → SQL-Datenbank → *Verbindungszeichenfolgen* → ODBC-Treiber kopieren.

**2. `.env` erweitern:**

```env
# PT4 Datenbank — leer = lokale SQLite (Standard)
DATABASE_URL=mssql+pyodbc://<user>:<pw>@<server>.database.windows.net:1433/<db>?driver=ODBC+Driver+18+for+SQL+Server
```

**3. Migration einmalig auf Azure SQL ausführen:**

```bash
cd demo
python -m alembic upgrade head
```

**4. `web_server.py` neu starten** — fertig.

> 💡 **Secrets in Produktion:** Für Container Apps / Azure App Service die `DATABASE_URL` als App Setting (nie im Image) oder aus Key Vault injizieren. Das SDK (`azure-keyvault-secrets`) ist bereits in `requirements-azure.txt` enthalten.

### Key Vault (Enterprise)

```python
# In initialize_system() einmalig aufrufen:
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

client = SecretClient(
    vault_url="https://<vault>.vault.azure.net",
    credential=DefaultAzureCredential()
)
os.environ["DATABASE_URL"] = client.get_secret("database-url").value
```

---

## Token- und Kosten-Tracking

Jeder Chat-Request schreibt einen `agent_runs`-Eintrag mit:
- `tokens_prompt` / `tokens_completion`: aus `response.usage` der jeweiligen Azure OpenAI-Calls aggregiert
- `cost_estimate`: `(tokens_total / 1000) × COST_PER_1K_TOKENS`

**Kostenrate anpassen** (Standard: `0.005 USD/1K` — gpt-4o-Schätzung, als Annahme markiert):

```env
COST_PER_1K_TOKENS=0.005
```

> ⚙️ Verfeinerung pro Modell folgt in AP6 (Dashboard).

Subprocess-Tokens (z. B. aus `generate_correction_llm.py`) werden aus der bereits gespeicherten `llm_correction_call.json` gelesen — **die Runtime-Tools selbst wurden nicht verändert**.

---

## Aktueller Stand (Milestones)

| Milestone | AP | Status |
|---|---|---|
| M1 — Correction Proposal Layer | AP1 | ✅ abgeschlossen |
| M2 — Persistence Layer | AP2 + AP2.5 | ✅ abgeschlossen |
| M3 — HitL Backend | AP3 | 🔄 in Arbeit |
| M4 — HitL Frontend | AP4 | ⬜ offen |
| M5 — MCP Integration | AP5 | ⬜ offen |
| M6 — Dashboard | AP6 | ⬜ offen |
| M7 — Memory System | AP7 | ⬜ offen |
| M8 — Evaluation & Demo | AP-E | ⬜ offen |
