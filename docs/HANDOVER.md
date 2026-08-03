# Übergabe — Stand 03.08.2026

Kurzfassung für einen frischen Chat. Ausführliche Begründungen zu jedem Punkt stehen in
`docs/PROJECT_LOG.md` (append-only, chronologisch, Einträge vom 02./03.08.2026).

---

## 1. Das Wichtigste zuerst

**Es ist NICHTS committet.** Zwei Arbeitskopien liegen ungesichert vor:

| Repository | Zustand |
|---|---|
| `C:\Projektarbeiten\agentic-ai-mfg` | 99 Umbenennungen + ~15 geänderte/neue Dateien |
| `C:\Projektarbeiten\Infra\...-terraform` | `infra/terraform.tfvars`, `infra/variables.tf` |

Vorgeschlagene Aufteilung in vier Commits, damit jeder für sich rückrollbar bleibt:
UI-Redesign · neue Funktionen samt DB-Migration · Repository-Umbau · Infrastruktur-Angleichung.

---

## 2. Neue Verzeichnisstruktur (Umbau abgeschlossen und im Container verifiziert)

```
agentic-ai-mfg/
├─ app/     9,2 MB — nur Code (war 615 MB); hieß bis 02.08. `demo/`
│  ├─ core/            agent_config, cost_model, storage_manager, rulebook_loader
│  ├─ deploy/          Dockerfile, entrypoint.sh, gunicorn.conf.py, requirements*
│  ├─ tools/smart-planning/runtime/   per Subprozess aufgerufene Skripte
│  └─ agents/ routes/ db/ memory/ skills/ ui/ eval/ alembic/ index/ mcp_connections/
├─ data/    618 MB — snapshots, logs, archive  [gitignoriert]
└─ docs/    unangetastet
```

**Nachgewiesen:** Image baut und läuft (410 MB), 15/15 Module und 13/13 Runtime-Skripte
importierbar, 12 Lernkarten + Monolith auffindbar, 28 Snapshot-Ordner, alembic auf `head`,
ein Runtime-Skript als echter Subprozess gelaufen, Code-Auszug liest weiterhin Zeile 7777
von 165282 (identisch zum Stand vor dem Umbau).

---

## 3. Offene ENTSCHEIDUNG (blockiert nichts, sollte aber vor dem ersten Azure-Deploy fallen)

**Datenbankspalten sind nicht Unicode-fähig.** Das generierte T-SQL nutzt `VARCHAR`/`TEXT`
statt `NVARCHAR`. Unter der Azure-Standardkollation nur CP1252: deutsche Umlaute sind drin,
ein Pfeil „→", ein Emoji oder Kyrillisch **nicht** — die würden still zu „?".
Betroffen u. a. `messages.content` (freier Nutzertext) und `reviews.comment` (der Prüfnachweis
des Menschen). Vorhandene Daten sind geprüft und sauber.

- **Weg A (empfohlen):** UTF-8-Kollation in Terraform — eine Zeile, Terraform legt die
  (leere) Datenbank neu an.
- **Weg B:** Modelle auf `Unicode`/`UnicodeText` + Migration über ~10 Tabellen.

Beides ist JETZT billig, weil die Azure-Datenbank leer ist. Später ist es eine Datenmigration.

---

## 4. Offene TODOs

### AI Search / Index / Dokumente — vom Nutzer bewusst vertagt
1. `app/index/ingest_docs.py:21` liest `AZURE_OPENAI_KEY`; Terraform liefert `AZURE_OPENAI_API_KEY`.
2. `app/index/ingest_docs.py:26` hat einen fest codierten Windows-Pfad zu den PDFs.
3. `app/index/create_index.py:106` ist nicht idempotent (`create_index` statt `create_or_update_index`).
4. Der Index `process-docs-index` existiert in Azure NICHT — der RAG-Agent läuft dort ins Leere.
5. Der Dokumenten-Storage `saagenticaimfg/basic-ai-informations` wird nicht als Variable
   ans Backend übergeben; Punkt 2 ist erst danach lösbar.
6. Semantic Search bleibt aus, solange Search auf dem Free-SKU läuft (aktuell erfüllt —
   der RAG-Agent nutzt reine Vektorsuche).

### Betrieb
7. `max_replicas = 1` bei mehrminütigen Pipeline-Läufen: ein Lauf blockiert die einzige
   Instanz komplett. `min_replicas` ist bereits auf 1 (Scale-to-Zero aus).
8. `LOCAL_STORAGE_PATH` in der Azure-Konfiguration prüfen — lokal stillgelegt, das Image
   setzt den Wert selbst.
9. `image_tag = "0.2.1"` in `terraform.tfvars` — mit den Änderungen von heute gehört ein
   neuer Tag dazu, sonst zieht die Container App das alte Image ohne ODBC-Treiber.
10. 13 Stellen rufen ESAROM mit `verify=False` auf (TLS-Prüfung aus). Bewusst nicht angefasst.
11. `NOTIFICATION_RECIPIENT_EMAIL` setzt Terraform, der Code liest sie nicht — der
    E-Mail-Agent nimmt den Empfänger aus dem Gespräch.

### UI (aus dem Entwurf, nicht umgesetzt)
12. Sammelentscheidungen im Review Board — **bewusst offen**, steht quer zu „nie ohne
    ausdrückliche menschliche Zustimmung".
13. Benutzermenü mit Avatar — im Entwurf eine Attrappe („Miriam Kessler"), ohne Login-System
    nichts zu bauen.

---

## 5. Fallen, die diese Sitzung Zeit gekostet haben

- **Die CSP blockt Inline-Skripte** (`script-src 'self'` in `web_server.py`). UI-Tests im
  Headless-Browser brauchen eine echte `.js`-Datei; Inline-`<script>` wird stillschweigend
  verworfen.
- **Das Icon-Subset muss bei JEDEM neuen Symbol neu erzeugt werden** (`app/ui/css/fonts.css`
  nennt die enthaltenen 38). Fehlt eins, rendert der Browser den NAMEN als Text; wegen
  `overflow:hidden` sieht man das nicht. Prüfung: `el.scrollWidth > el.clientWidth`.
- **Im Container gibt es kein Repository-Wurzelverzeichnis.** Die Anwendung liegt auf `/app`;
  `Path(__file__).parent.parent` ist dort die Dateisystemwurzel. Deshalb `LOG_DIR` und
  `LOCAL_STORAGE_PATH` — beide setzt das Image.
- **git kannte den Ordner als `Demo/`** (großes D), die Platte als `demo/`. Solche
  Groß-/Kleinschreibungs-Diskrepanzen fallen auf Windows nie auf, auf einer Linux-CI sofort.
- **`&&`-Ketten in Shell-Skripten brechen still ab.** Ein fehlgeschlagenes `mv` hat einmal
  einen ganzen Patch übersprungen, ohne Fehlermeldung. Nach jedem Umbau nachmessen.

---

## 6. Zustand der Umgebung

- Dev-Server läuft auf **Port 8000** (aus `app/`, `./.venv/Scripts/python.exe web_server.py`)
- **Docker Desktop läuft**, Image `agentic-ai-mfg:audit2` liegt vor
- `app/.env`: `LOCAL_STORAGE_PATH` stillgelegt, Deployments auf `gpt-4.1`. **Am 03.08.**
  **mussten OpenAI-, Search- und Speech-Schluessel aus Azure nachgezogen werden** — sie waren
  nach der Terraform-Uebernahme veraltet (401 im Chat). `APP_BASE_URL` hatte ausserdem ein
  doppeltes `http://`. Merke: nach jedem `terraform apply` ist die lokale `.env` verdaechtig.
- Datenbank lokal: SQLite unter `app/db/pt4.sqlite3`, Stand `9b1e40c7d2a3 (head)`

---

## 7. Womit weitermachen

1. **Commits vorbereiten** (vier Stück, siehe oben) — der Stand ist ungesichert.
2. **Weg A oder B** zur Unicode-Frage entscheiden.
3. Danach: Search-/Index-Block (Punkte 1–6) oder erstes echtes Azure-Deploy mit neuem
   `image_tag`.
