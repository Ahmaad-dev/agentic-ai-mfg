# PT4 — Belege für den Projektbericht

**Stand: 2026-07-14.** Alle Angaben in diesem Dokument sind aus dem laufenden Code und der
realen Datenbank (`demo/db/pt4.sqlite3`) gezogen — nichts ist geschätzt oder aus der Erinnerung
rekonstruiert. Wo eine Zahl **nicht** zitierfähig ist, steht das ausdrücklich dabei.

**Inhalt:** [AP1](#ap1) · [AP2](#ap2) · [AP3](#ap3) · [AP5](#ap5) · [AP6](#ap6) · [AP7](#ap7) ·
[Nachweise & Messungen](#nachweise)

---

<a id="ap1"></a>
## AP1 — Schema, Confidence-Formel, Versionsbezeichnung

### Reales `CorrectionProposal`-Schema

Quelle: `demo/smart-planning/runtime/correction_models.py` (Pydantic v2).

| Feld | Typ | Pflicht |
|---|---|---|
| `action` | `str` | ja |
| `target_path` | `str` | ja |
| `current_value` | `Optional[Union[str, int, float, bool, None, dict, list]]` | nein |
| `new_value` | `Optional[Union[str, int, float, bool, None, dict, list]]` | nein |
| `reasoning` | `str` | ja |
| `additional_updates` | `Optional[List[AdditionalUpdate]]` (default `[]`) | nein |
| `confidence_score` | `Optional[float]`, `@field_validator` erzwingt `[0.0, 1.0]` | nein |
| `status` | `Literal["pending_review","approved","rejected","modified","applied"]`, default `pending_review` | nein |

**`AdditionalUpdate`:** `target_path: str`, `current_value: Union[...]`, `new_value: Union[...]`

**Wrapper `LLMCorrectionResponse`:** `iteration: int`, `snapshot_id: str`,
`original_error: OriginalError`, `error_analyzed: ErrorAnalyzed`,
`correction_proposal: CorrectionProposal`

> **Hinweis für den Bericht:** Die abgeleiteten Confidence-Felder (`value_grounded`,
> `value_grounded_reason`, `memory_support`, `memory_support_reason`, `formula_version`,
> `schema_valid`, `confidence_rationale`) sind **nicht Teil des Pydantic-Modells**. Sie werden
> additiv an das Proposal-Dict gehängt und in der DB-Tabelle `proposals` geführt. Das Modell
> setzt kein `extra="forbid"`, deshalb ist das zulässig und bricht keine Validierung.

### Aktive Confidence-Formel

Code-Konstante: `CONFIDENCE_FORMULA_VERSION = "v3"`
(`demo/smart-planning/runtime/generate_correction_llm.py`)

```
confidence = 0.5 · llm_self_estimate     (Selbsteinschätzung des LLM, 0..1, A–D-Rubrik)
           + 0.3 · value_grounded        (deterministisch, KLASSENABHÄNGIG)
           + 0.2 · memory_support        (deterministisch, abgestuft 0 / 0.5 / 1.0)

Sonderfall: action == "manual_intervention_required"  →  confidence = 0.0
```

**`value_grounded` — klassenabhängig seit AP-E.0:**

| Feldklasse | Geprüfte Frage |
|---|---|
| Identitätsfeld (`demandId`, `articleId`, `workPlanId`) | Ist der Wert im Array **eindeutig** UND folgt er der **ID-Konvention** (Mehrheits-Strukturform, z. B. `D100079_001` → `A999999_999`)? |
| Referenzfeld | Existiert das referenzierte Objekt? |
| Wertfeld | Sitzt derselbe Wert auf demselben Feld eines vergleichbaren Objekts (bzw. ist er Element einer solchen Liste)? |
| `add_to_array` | Dieselben Prüfungen auf das **neue** Objekt (Identität eindeutig+konventionell, Referenzen belegt) |

**`memory_support`:** `0.0` kein Fall · `0.0` negativer Präzedenzfall · `0.5` Präzedenz für die
Fehlerart · `1.0` ein Mensch hat genau diesen Wert bestätigt.

### Formel-Generationen (in der DB unterscheidbar)

| Version | Mittelterm | Effekt |
|---|---|---|
| **v0** | `schema_valid` (**immer 1**) | Score kollabiert auf quasi-konstant ~0.775 |
| **v1** | `value_grounded` real, `memory_support` **fest 0** | Score bei **0.8 gedeckelt** |
| **v2** | `memory_support` abgestuft (AP7.2) | voller Bereich, aber `value_grounded` noch invertiert für IDs |
| **v3** | `value_grounded` **klassenabhängig** (AP-E.0) | aktuell aktiv |

> **v2- und v3-Scores sind NICHT vergleichbar.** Die Gewichte sind identisch, aber die Semantik
> des 0.3-Terms hat sich geändert. Das Dashboard muss eine Generation pinnen
> (`?formula_version=v3`).

### Antwort auf die 124211-Frage: **NEIN — der Wert 0,775 stammt aus einer FRÜHEREN Formel**

Der betreffende Vorschlag ist `ec96832c-1573-4ad4-995a-77d541b258f7__iteration-5`:

```
confidence_score = 0.775
value_grounded   = NULL          ← Feld existierte zu diesem Zeitpunkt noch nicht
memory_support   = NULL          ← ebenso
schema_valid     = 1
formula_version  = v0            ← die ÄLTESTE Generation
error_type       = WORK_ITEM_CONFIGS_COMPLETENESS
status           = applied
created_at       = 2026-07-10 21:55:44
```

**Rechnung:** `0.5 · 0.95 + 0.3 · 1.0 (schema_valid, immer 1) + 0.2 · 0 = 0.775`

Der Mittelterm war **tautologisch** — das Proposal wird unmittelbar nach dem Bau gegen das
Pydantic-Modell validiert, `schema_valid` ist deshalb per Konstruktion immer 1. Deshalb kollabierte
der Score.

> ⚠️ **Dieser Wert darf NICHT als Beleg für die aktuelle Confidence-Mechanik zitiert werden.**

**Vergleich, derselbe Fehlertyp mit der aktuellen Formel** (`1ef11903-…__iteration-4`):

```
confidence_score = 0.75
value_grounded   = 1.0    ("Wert existiert bereits in articles[23].workItemConfigs")
memory_support   = 0.0
formula_version  = v3
```

---

<a id="ap2"></a>
## AP2 — Reale DB-Tabellen mit Schlüsselfeldern

SQLAlchemy 2.0 + Alembic (5 Migrationen). Lokal SQLite, Ziel Azure SQL über `DATABASE_URL`.

| Tabelle | PK | Fremdschlüssel | Zeilen |
|---|---|---|---|
| `sessions` | `id` | — | 84 |
| `messages` | `id` | `session_id → sessions.id` | 94 |
| `agent_runs` | `id` | `session_id → sessions.id` | 104 |
| `snapshots_meta` | `snapshot_id` | — | 15 |
| `proposals` | `proposal_id` | `snapshot_id → snapshots_meta.snapshot_id` | 13 |
| `reviews` | `id` | `proposal_id → proposals.proposal_id` | 6 |
| `memory_items` | `id` | `source_proposal_id → proposals.proposal_id` | 6 |
| `email_drafts` | `id` | `session_id → sessions.id` | 3 |

**Wichtige Spalten:**

- **`proposals`** — `proposal_id` (deterministisch: `{snapshot_id}__iteration-{N}`), `snapshot_id`,
  `error_type`, `target_path`, `affected_entity`, `old_value`, `suggested_value`, `reasoning`,
  `evidence`, `confidence_score`, `schema_valid`, `status`, `correction_kind`,
  `target_entity_type`, `target_entity_id`, `identity_check_supported`, `value_grounded`,
  `value_grounded_reason`, `confidence_rationale`, `memory_support`, `memory_support_reason`,
  `formula_version`, `created_at`
- **`reviews`** — `proposal_id`, `decision`, `final_value`, `comment`, `reviewer_ref`,
  `decided_at`, `revalidation_result`
- **`memory_items`** — `error_type`, `affected_entity_pattern`, `suggested_value`, `final_value`,
  `decision`, `comment`, `revalidation_ok`, `source_proposal_id`
- **`agent_runs`** — `agent_name`, `tool_name`, `status`, `tokens_prompt`, `tokens_completion`,
  `cost_estimate`, `duration_ms`

---

<a id="ap3"></a>
## AP3 — Review-Endpunkte und Guards der Apply-Kette

### Endpunkte (Blueprint-Präfix `/api/review`)

| Methode | Pfad | Zweck |
|---|---|---|
| GET | `/api/review/proposals` | offene Vorschläge |
| GET | `/api/review/proposals/<proposal_id>` | Detail (inkl. Entscheidung, seit 2026-07-12) |
| POST | `/api/review/proposals/<proposal_id>/approve` | KI-Wert unverändert übernehmen + anwenden |
| POST | `/api/review/proposals/<proposal_id>/reject` | verwerfen (wendet **nichts** an) |
| POST | `/api/review/proposals/<proposal_id>/modify` | menschlichen Wert setzen + anwenden |
| GET | `/api/review/proposals/<proposal_id>/context` | AP4.7 — Fehlerstelle im Original mit Zeilennummern |
| GET | `/api/review/proposals/<proposal_id>/memory` | AP7.3 — ähnliche, menschlich entschiedene Altfälle |

### Guards der Apply-Kette

| # | Guard | HTTP | Was er blockiert |
|---|---|---|---|
| 1+2 | **Entscheidungs-Guard** | 409 | Blockiert, wenn der Status nicht `approved`/`modified` ist **oder** keine Review-Zeile existiert — verhindert, dass ohne menschliche Entscheidung angewendet wird. |
| 3 | **Iterations-Guard** (AP3.3a) | 409 | Blockiert, wenn eine **neuere Iteration** existiert als die geprüfte — `apply_correction.py` löst selbst die höchste Iteration auf und würde sonst still eine **andere** Korrektur anwenden als die freigegebene. |
| 4 | **Identitäts-Guard** (AP3.5b) | 409 | Blockiert, wenn das Objekt an der Zielposition **nicht mehr dasselbe** ist — Schutz davor, nach einer Array-Umsortierung das **falsche Objekt** zu korrigieren. |
| 5 | **Action-Guard** | 422 | Blockiert Modify auf `remove_from_array` / `manual_intervention_required`, **bevor** Daten mutiert werden — sonst verpufft der Menschenwert still bzw. `applied=true` wäre gelogen. |
| — | **Idempotenz-Guard** (`_is_still_undecided`) | 409-A | Weist eine **zweite** Entscheidung auf demselben Proposal ab. Review-Zeile und Proposal-Status werden in **einer** Transaktion geschrieben und können nie auseinanderdriften. |

---

<a id="ap5"></a>
## AP5 — MCP-Tools, E-Mail-Workflow, Versanddienst

### Real registrierte MCP-Tools (12)

`FastMCP`-Server, `demo/mcp_connections/server.py` (Zeilen 18–29):

**Review-Tools (7):** `get_pending_reviews` · `get_review_details` · `approve_correction` ·
`reject_correction` · `modify_correction` · `get_snapshot_status` · `get_dashboard_metrics`

**E-Mail-Tools (5):** `create_email_draft` · `get_email_draft` · `revise_email_draft` ·
`send_email_draft` · `cancel_email_draft`

### E-Mail-Workflow — reale Zustände

Zustandsfeld: `email_drafts.status`

```
create_email_draft  →  status = "draft",  version = 1
revise_email_draft  →  status bleibt "draft",  version += 1     ← KEIN eigener Status
send_email_draft(confirmed=True)  →  status = "sent",  provider_message_id gesetzt
cancel_email_draft  →  status = "cancelled"
```

> **Wichtig:** „Revise" ist **kein eigener Zustand**, sondern eine Versionserhöhung bei
> bleibendem `draft`. Real belegt: ein Entwurf steht auf `version = 3`.
> Versand erfolgt **ausschließlich** nach expliziter Bestätigung (`confirmed=True`), im Chat
> durch „Bitte absenden".

**Realer Nachweis — 3 versendete E-Mails mit Provider-Message-ID:**

| Betreff | Version | Gesendet |
|---|---|---|
| „Abendessen und Projekt-Update" | 3 | 2026-07-12 11:53 |
| „Bitte keine Löschung meiner Ressourcen" | 1 | 2026-07-12 19:02 |
| „Meine Begeisterung für die Arbeit" | 1 | 2026-07-13 11:00 |

### Versanddienst

**Azure Communication Services (ACS).**
`EmailClient.from_connection_string(ACS_CONNECTION_STRING)`, Absender aus `ACS_SENDER_EMAIL`.
Ein **SendGrid**-Adapter existiert alternativ; die Auswahl läuft über die Umgebungsvariable
`NOTIFICATION_CHANNEL`. Produktiv genutzt wurde ACS (die drei Message-IDs oben).

---

<a id="ap6"></a>
## AP6 — Kennzahlen und Data-Quality-Flags

Live abgerufen: `GET /api/dashboard/metrics?preset=all`

### KPIs (25, real berechnet)

| KPI | Wert | Berechnungsgrundlage |
|---|---|---|
| `proposals_total` | 13 | Zeilen in `proposals` |
| `proposals_open` | 7 | `status = pending_review` |
| `decisions_total` | 6 | **letzte** Review je Proposal |
| `approve_count` | 2 | `reviews.decision = approve` |
| `modify_count` | 3 | `reviews.decision = modify` |
| `reject_count` | 1 | `reviews.decision = reject` |
| `approval_rate` | 0.3333 | approve ÷ Entscheidungen |
| `modify_rate` | 0.5 | modify ÷ Entscheidungen |
| `reject_rate` | 0.1667 | reject ÷ Entscheidungen |
| **`accepted_unchanged_rate`** | **0.3333** | approve ÷ Entscheidungen — **die AK2-Kennzahl** |
| `avg_confidence` | 0.6912 | Mittel über `proposals.confidence_score` |
| `revalidation_attempts` | 2 | Reviews mit auswertbarem `revalidation_result` |
| `revalidation_success` | 2 | davon `is_valid = true` |
| `revalidation_success_rate` | 1.0 | success ÷ attempts |
| `revalidation_untrusted` | 2 | Läufe **ohne** `errors_before` (False-Green, vor AP3.3d) |
| `handling_time_median_s` | 55.948 | `decided_at − created_at`, Median |
| `handling_time_mean_s` | 74.231 | dito, Mittel |
| `handling_time_n` | 3 | Anzahl gewerteter Reviews |
| `handling_time_excluded_fixtures` | 3 | in derselben Sekunde entschieden → Skript-Fixtures |
| `tokens_prompt` | 1.623.748 | Summe `agent_runs.tokens_prompt` |
| `tokens_completion` | 34.248 | Summe `agent_runs.tokens_completion` |
| `tokens_total` | 1.657.996 | Summe |
| `cost_estimate_usd` | 4.4019 | Preismodell, Input/Output getrennt (AP6.3) |
| `agent_runs` | 104 | Zeilen in `agent_runs` |
| `validations` | 7 | getrackte Validierungsläufe |
| `snapshots_tracked` | 15 | Zeilen in `snapshots_meta` |

### Charts

`calibration` (5 Bins) · `confidence_distribution` (5 Bins) · `error_types` (6) · `timeline` (7)

### Data-Quality-Flags (8, alle real aktiv)

| Flag | Sev. | Berechnungsgrundlage |
|---|---|---|
| `CONFIDENCE_LEGACY_FORMULA` | warning | **6 von 6** Entscheidungen stammen aus Formel **v0** → Score quasi-konstant, Kalibrierungskurve flach **konstruktionsbedingt**, nicht als Messergebnis |
| `ERROR_TYPE_LEGACY_HEURISTIC` | warning | `error_type` aus der widerlegten Zähl-Heuristik (>1 Treffer → `DUPLICATE_ID`) |
| `REVALIDATION_PRE_AP33D` | warning | `revalidation_result` **ohne** `errors_before` → der Validierungsjob wurde nicht getriggert, „0 Fehler" ist falsches Grün |
| `SMALL_SAMPLE` | warning | **n < 10** Entscheidungen → **keine Rate hier ist statistisch belastbar** |
| `HANDLING_TIME_FIXTURES` | info | 3 Reviews in derselben Sekunde entschieden wie erzeugt → Skript-Fixtures, separat ausgewiesen |
| `COST_IS_ESTIMATE` | info | Preise aus Modell, nicht aus der Azure-Abrechnung |
| `TOKENS_INCOMPLETE` | info | nicht jeder Lauf schreibt Token-Zahlen |
| `VALIDATION_COUNT_PARTIAL` | info | nur getrackte Validierungen gezählt |

> **Designprinzip (zitierfähig):** Das Dashboard **verschweigt keine Unsicherheit**. Jede Größe,
> die nicht vertrauenswürdig ist, trägt einen expliziten Flag. Verschwindet ein Flag, weil die
> Daten sauber geworden sind, ist genau das das Signal, dass die Kennzahl belastbar wurde.

---

<a id="ap7"></a>
## AP7 — Retrieval-Logik, `memory_support`, konkretes Beispiel

### Ähnlichkeitskriterium

**Schlüssel: `affected_entity_pattern`** — der Zielpfad mit **wegnormalisiertem Array-Index**:

```
demands[386].articleId   →   demands[].articleId
demands[5].demandId      →   demands[].demandId
```

Der konkrete Index eines Snapshots ist Rauschen; erst die Normalisierung macht einen Altfall
gegen einen neuen Fehler matchbar.

**Ranking:** Pattern-Übereinstimmung ist **Pflicht** (harter Filter). Zusätzlich: gleicher
`error_type` → +1, bestandene Revalidierung (`revalidation_ok = true`) → +1. Sortierung nach
Score, dann nach Aktualität, Rückgabe der Top-k (Default k = 3, im UI k = 5).

**Warum NICHT über `error_type`:** Die Fallbasis mischt Legacy-Labels (`EMPTY_FIELD`, aus der
Zeit vor AP3.6b) mit den maßgeblichen Tags (`UNIQUE_IDS`). Ein `error_type`-Retrieval würde
genau die relevanten Altfälle verfehlen — siehe Beispiel unten.

### Weg vom Altfall in den Confidence-Score

```
1. Fehler erkannt      → Zielpfad steht in last_search_results.results[0].path
2. Retrieval           → entity_pattern(path) → Altfälle aus memory_items
3. Evidenz             → Top-k Fälle gehen als Klartext in den Korrektur-Prompt
                         ("Ein Mensch entschied hier: modify → D100005_001, weil …")
4. Vorschlag entsteht  → new_value
5. memory_support      → deterministisch aus (new_value, gefundene Fälle):
                            1.0  ein Mensch hat GENAU DIESEN Wert bestätigt
                            0.5  Präzedenz für die Fehlerart, kein Wert-Präzedenzfall
                            0.0  kein Fall  ODER  negativer Präzedenzfall
                                 (dieser Wert wurde schon vorgeschlagen und verworfen)
6. confidence          → + 0.2 · memory_support
```

### Konkreter, realer Fall

**Neuer Fehler:** leere `demandId` in Snapshot `e92b3ee2`, Zielpfad `demands[5].demandId`
**Retrieval-Schlüssel:** `demands[].demandId` → **3 Altfälle gefunden**

| Fall | `error_type` | Entscheidung | KI schlug vor | Mensch entschied | Begründung des Menschen |
|---|---|---|---|---|---|
| **#1** | `UNIQUE_IDS` | modify | `D210446_003` | `D210451_001` | — |
| **#5** | **`EMPTY_FIELD`** | modify | `AI_GUESS_999` | `D100005_001` | *„AI guessed wrong."* |
| **#4** | **`EMPTY_FIELD`** | approve | `D100005_001` | `D100005_001` | *„AI value is correct."* |

> **Genau hier zeigt sich die Schlüsselwahl empirisch:** Fall #1 trägt `UNIQUE_IDS`, die Fälle #4
> und #5 tragen `EMPTY_FIELD`. Der Pattern-Schlüssel vereint sie **trotz** unterschiedlicher
> Labels. Ein `error_type`-Retrieval hätte **zwei von drei verfehlt**.

**Wirkung auf den Score:**

```
memory_support = 0.5
  Grund: "3 vergleichbare Fälle vorhanden, aber kein Präzedenzfall für genau diesen Wert."

confidence = 0.745  =  0.5 · llm  +  0.3 · 1.0  +  0.2 · 0.5     [formula v3]
```

**Ohne Gedächtnis wäre der Score 0.645 gewesen — der gefundene Präzedenzfall hebt die Confidence
um 0.1.**

---

<a id="nachweise"></a>
## Nachweise und Messungen

### Screenshots: **KEINE vorhanden**

Im Repository existieren **vier** Bilddateien:

| Datei | Art |
|---|---|
| `docs/azure-ai-foundry-logo.jpg` | Logo |
| `docs/KBC3353 CANCOM_Logo.jpg` | Logo |
| `docs/microsoft-azure-logo.png` | Logo |
| `demo/ui/logo-agentic.png` | Logo |

**Es gibt keinen Screenshot vom Review-Diff und keinen vom Dashboard.** Beide Oberflächen laufen
und sind aufnahmebereit — die Screenshots müssen für den Bericht noch erstellt werden.

### Reale Vorher/Nachher-Messung eines Apply-Laufs

Quelle: `reviews.revalidation_result`

| Proposal | Entscheidung | Wertquelle | **errors_before → errors_after** | Server-Validierungsjob |
|---|---|---|---|---|
| `ec96832c…__iteration-5` | **modify** | `human_modify` | **2 → 0** | `FINISHED`, Job `38246600…` |
| `1e3667d9…__iteration-1` | **modify** | `human_modify` | **1 → 0** | `FINISHED`, Job `89928cab…` |

Beide: `pipeline_success = true`, `is_valid = true`, `errors = 0`, `warnings = 5`.
Beide sind **echte Human-in-the-Loop-Entscheidungen**, bei denen der Mensch den KI-Wert
**überstimmt** hat (`value_source = human_modify`) — und die Korrektur hat den Fehler
nachweislich beseitigt.

> ⚠️ **Zwei weitere Apply-Läufe zeigen `errors_before = NULL`.** Das sind Läufe **vor AP3.3d**, in
> denen der Validierungsjob nicht getriggert wurde und der Server deshalb pauschal „0 Fehler"
> meldete — **falsches Grün**. Das Dashboard markiert sie über `REVALIDATION_PRE_AP33D` und zählt
> sie als `revalidation_untrusted = 2`. **Nicht als Erfolg zitieren.**

### AP-E: approve-unverändert (x von n)

```
approve  (KI-Wert unverändert übernommen):   2 von 6   =  33,3 %
modify   (Mensch hat korrigiert):            3 von 6   =  50,0 %
reject   (verworfen):                        1 von 6   =  16,7 %
```

> ⚠️ **Diese Zahl ist NICHT als AK2-Nachweis verwendbar.** Drei Gründe:
> 1. Der `SMALL_SAMPLE`-Flag ist aktiv (**n = 6 < 10**) — statistisch nicht belastbar.
> 2. **Alle 6** Entscheidungen stammen aus Formel-Generation **v0**.
> 3. **3 von 6** sind Skript-Fixtures (in derselben Sekunde entschieden wie erzeugt).
>
> **AK2 (≥ 80 % akzeptiert ohne Modifikation) ist derzeit NICHT belegt und darf nicht behauptet
> werden.** Der Seeding-Lauf (AP-E.2) mit 10 vorbereiteten Snapshots plus den 7 offenen
> Vorschlägen ergibt **17 Entscheidungen** — erst dann fällt der `SMALL_SAMPLE`-Flag und die Zahl
> wird zitierfähig.

### Weitere Zahlen, die NICHT zitiert werden dürfen

- **Die 85-%-Auto-Fix-Rate aus der Phase-3-Dokumentation.** Sie beruht mit hoher Wahrscheinlichkeit
  auf demselben False-Green-Validierungsbug (`REVALIDATION_PRE_AP33D`). Nicht ungeprüft übernehmen.
- **Der Confidence-Wert 0,775 des 124211-Vorschlags** — Formel-Generation v0, siehe AP1.

---

## Zusammenfassung: Was ist belegt, was nicht

| Aussage | Status |
|---|---|
| HitL-Kette läuft end-to-end (Vorschlag → Review → Apply → Revalidierung) | ✅ **belegt** (2 reale Läufe, `2→0` und `1→0`, mit Server-Job-IDs) |
| Der Mensch kann die KI überstimmen und die Korrektur hält | ✅ **belegt** (beide Läufe sind `human_modify`) |
| Deterministische Guards verhindern falsches Anwenden | ✅ **belegt** (5 Guards, HTTP 409/422) |
| Confidence hat Trennschärfe | ✅ **belegt** an der Testkatalog-Ground-Truth (richtig: 0.74–0.775; falsch: 0.475) |
| Gedächtnis findet Altfälle und hebt die Confidence | ✅ **belegt** (3 Fälle gefunden, `memory_support = 0.5`, +0.1 auf den Score) |
| MCP-Integration mit 12 Tools + realem E-Mail-Versand | ✅ **belegt** (3 Message-IDs) |
| Dashboard mit Live-KPIs und Ehrlichkeits-Flags | ✅ **belegt** (25 KPIs, 8 Flags) |
| **AK2: ≥ 80 % akzeptiert ohne Modifikation** | ❌ **NICHT belegt** (n = 6, `SMALL_SAMPLE`, v0-Formel, 3 Fixtures) |
| **Kalibrierungskurve** | ❌ **NICHT belegt** (flach konstruktionsbedingt, alle Entscheidungen aus v0) |
| Screenshots | ❌ **nicht vorhanden** |
