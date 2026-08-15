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

- ✅ **Human-in-the-Loop Governance**: Korrekturen werden als Vorschlag eingefroren, nichts wird autonom geschrieben (`HUMAN_IN_THE_LOOP` — lokal in `.env`, in Azure über Terraform)
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
app/
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
├── core/                      # (seit 02.08.2026 — waren lose im Wurzelverzeichnis)
│   ├── agent_config.py        # GEÄNDERT: HUMAN_IN_THE_LOOP-Toggle, COST_PER_1K_TOKENS
│   ├── cost_model.py
│   ├── storage_manager.py
│   └── rulebook_loader.py     # AP7: laedt die Lernkarten (lokal ODER aus dem Blob)
├── agents/
│   ├── orchestration_agent.py # GEÄNDERT: HitL-Block + Token-Accumulator (5 LLM-Call-Stellen)
│   ├── chat_agent.py          # GEÄNDERT: response.usage in metadata
│   └── rag_agent.py           # GEÄNDERT: response.usage in metadata
├── tools/smart-planning/      # (seit 02.08.2026 unter tools/)
│   ├── runtime/
│   │   ├── correction_models.py        # GEÄNDERT: confidence_score, status, schema_valid
│   │   └── generate_correction_llm.py  # GEÄNDERT: Confidence-Formel, Proposal-Record, DB-Write, Token-Lesen
│
│  Snapshots liegen seit 02.08.2026 AUSSERHALB der Anwendung: <repo>/data/snapshots/
│  (bzw. im Blob-Container "snapshots"), darin _proposals/ als zentrale JSON-Ablage.
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

Jeder Korrekturvorschlag trägt eine Konfidenz zwischen 0 und 1, zusammengesetzt aus drei
Signalen:

```
Konfidenz = 0.5 · llm_confidence     Selbsteinschätzung des Modells
          + 0.3 · value_grounded     Wert aus den Daten belegbar? (deterministisch, kein LLM)
          + 0.2 · memory_support     Rückhalt aus früheren menschlichen Entscheidungen

danach:  ist memory_support == 1.0, gilt mindestens 0.9
```

Sonderfall: `action == "manual_intervention_required"` → Score zwingend `0.0`.

Die drei Signale stammen aus **drei verschiedenen Quellen** — das ist der Kern der Konstruktion:

| Signal | Quelle |
|---|---|
| `llm_confidence` | das Modell selbst |
| `value_grounded` | der Snapshot (`snapshot-data.json`), deterministisch geprüft |
| `memory_support` | die Tabelle `memory_items` (frühere menschliche Entscheidungen) |

Nur das erste kommt aus dem Modell. Die beiden anderen sind reproduzierbar und dürfen die
Selbsteinschätzung deshalb korrigieren.

> **Diese Darstellung ist bewusst knapp.** Die Zahl ist governance-relevant — welche Frage
> hinter jedem Signal steckt, warum die Selbsteinschätzung nur halb zählt, warum es die
> Untergrenze gibt und wie ein Prüfer die Zahl lesen sollte, steht in
> **[`docs/KONFIDENZ.md`](../docs/04_PT4/KONFIDENZ.md)**, samt durchgerechnetem Beispiel und der
> Entwicklung der Formel von v0 bis v4.

Der Formelstand wird pro Vorschlag in `formula_version` mitgespeichert, damit alte Vorschläge
erkennbar bleiben und nicht stillschweigend mit neuen vermischt werden.

> **Wie die Agenten zusammenarbeiten**, was jeder von ihnen weiss, warum Chat und RAG ihre
> Antwort selbst formulieren, wie sich betreuter und automatischer Betrieb unterscheiden und
> ob das gesammelte Feedback auch ohne Human-in-the-Loop wirkt, steht in
> **[`docs/AGENTEN_ARCHITEKTUR.md`](../docs/04_PT4/AGENTEN_ARCHITEKTUR.md)**.

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

SQLite-Datei `app/db/pt4.sqlite3` wird automatisch angelegt. Kein weiterer Setup nötig.

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

**Kostenrate anpassen** (Standard: `0.005 USD/1K` — Schätzung, als Annahme markiert; im Einsatz ist gpt-4.1):

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


---

## Was sich seit dieser Fassung geändert hat (Stand 04.08.2026)

Dieses Dokument beschreibt den PT4-Stand. Drei Dinge sind seither dazugekommen und stehen
ausführlich in `docs/PROJECT_LOG.md`:

- **AP7 — Lernkarten statt Monolith.** `RULEBOOK_MODE` (`cards` | `monolith`) wählt die
  Quelle. Im Cloud-Betrieb liegen die Karten im Blob-Container `skills` und lassen sich dort
  bearbeiten, **ohne ein neues Image zu bauen**. Abgleich mit dem Repository über
  `python -m tools.sync_skills`.
- **Verzeichnisumbau.** `demo/` heißt `app/`; Querschnittsmodule unter `core/`, Runtime-Skripte
  unter `tools/`, Auslieferung unter `deploy/`, Laufzeitdaten unter `<repo>/data/`.
- **Beide Schalter sind in Azure konfigurierbar.** `HUMAN_IN_THE_LOOP` und `RULEBOOK_MODE`
  stehen im `env`-Block der Container App und sind in Terraform mit einer Wertprüfung
  abgesichert.
