# Belegübersicht AP1 bis AP7 und AP-E

## AP1 – Correction Proposal und Confidence

Das reale Pydantic-Schema steht in `demo/smart-planning/runtime/correction_models.py`.

`CorrectionProposal` enthält:

| Feld | Typ | Pflicht/Standard |
|---|---|---|
| `action` | `str` | Pflicht |
| `target_path` | `str` | Pflicht |
| `current_value` | `Optional[str \| int \| float \| bool \| None \| dict \| list]` | `None` |
| `new_value` | gleicher Union-Typ | `None` |
| `reasoning` | `str` | Pflicht |
| `additional_updates` | `Optional[List[AdditionalUpdate]]` | leere Liste |
| `confidence_score` | `Optional[float]` | `None`, validiert auf 0–1 |
| `status` | `Literal["pending_review","approved","rejected","modified","applied"]` | `pending_review` |

`AdditionalUpdate` besteht aus `target_path: str`, `current_value` und `new_value` mit denselben JSON-kompatiblen Union-Typen. Der Wrapper `LLMCorrectionResponse` enthält außerdem `iteration`, `snapshot_id`, `original_error`, `error_analyzed` und `correction_proposal`.

Wichtig: Felder wie `llm_confidence`, `schema_valid`, `value_grounded`, `memory_support` und `formula_version` werden im erzeugten Roh-JSON ergänzt, sind aber nicht als Felder des Pydantic-Modells deklariert.

Die aktuell aktive Formel in `demo/smart-planning/runtime/generate_correction_llm.py` lautet:

\[
confidence = 0{,}5 \cdot llm\_confidence
+ 0{,}3 \cdot value\_grounded
+ 0{,}2 \cdot memory\_support
\]

Aktive Versionsbezeichnung: `v3`. Bei `manual_intervention_required` wird der Score auf `0` gesetzt.

Der Artikel-124211-Vorschlag mit `confidence_score=0,775` entstand mit der früheren Version `v0`: Das Artefakt enthält `llm_confidence=0,95`, `schema_valid=true`, aber noch kein `value_grounded`, `memory_support` oder `formula_version`. Die Rechnung war:

\[
0{,}5 \cdot 0{,}95 + 0{,}3 \cdot 1 + 0{,}2 \cdot 0 = 0{,}775
\]

Die Datenbank kennzeichnet diesen historischen Vorschlag nachträglich als `formula_version=v0`.

## AP2 – Persistenz

Die realen ORM-Tabellen stehen in `demo/db/models.py`:

| Tabelle | Schlüssel und wesentliche Felder |
|---|---|
| `sessions` | PK `id`; `started_at`, `snapshot_id`, `user_ref` |
| `messages` | PK `id`, FK `session_id`; `role`, `agent_name`, `content`, `created_at` |
| `agent_runs` | PK `id`, FK `session_id`; Agent, Tool, Status, Tokenzahlen, Kostenschätzung, Laufzeit |
| `snapshots_meta` | PK `snapshot_id`; Fehler/Warnungen vorher und nachher, `last_validated_at` |
| `proposals` | PK `proposal_id`, FK `snapshot_id`; Fehlertyp, Zielpfad, Alt-/Neuwert, Begründung, Evidenz, Confidence-Komponenten, Formelversion, Status und Guard-Metadaten |
| `reviews` | PK `id`, FK `proposal_id`; `decision`, `final_value`, `comment`, `reviewer_ref`, `decided_at`, `revalidation_result` |
| `email_drafts` | PK `id`, FK `session_id`; Empfänger, Betreff, Text/HTML, Status, Version, Provider-ID und Versandzeit |
| `memory_items` | PK `id`, FK `source_proposal_id`; Fehlertyp, Entity-Pattern, KI-/Menschenwert, Entscheidung, Kommentar und Revalidierungserfolg |

Ein aktueller read-only Datenbankcheck ergab: 84 Sessions, 104 Agent-Läufe, 13 Proposals, 6 Reviews, 6 Memory-Fälle und 3 E-Mail-Entwürfe.

## AP3 – Review-Backend und Apply-Guards

Der Blueprint verwendet den Prefix `/api/review`. Die fünf Kernendpunkte in `demo/routes/review.py` sind:

1. `GET /api/review/proposals`
2. `GET /api/review/proposals/<proposal_id>`
3. `POST /api/review/proposals/<proposal_id>/approve`
4. `POST /api/review/proposals/<proposal_id>/reject`
5. `POST /api/review/proposals/<proposal_id>/modify`

Zusätzlich existieren inzwischen:

- `GET /api/review/proposals/<proposal_id>/context`
- `GET /api/review/proposals/<proposal_id>/memory`

Die Apply-Kette enthält folgende Guards:

- `HUMAN_IN_THE_LOOP`: Verhindert im Orchestrator automatisches Anwenden und lenkt Korrekturpipelines auf `analyze_only`.
- `APPLICABLE_STATUS` plus `review_count`: `_apply_after_review()` akzeptiert nur `approved` oder `modified` mit mindestens einer persistierten Review-Zeile.
- `check_iteration_is_latest()`: Blockiert veraltete Proposal-Iterationen, weil `apply_correction.py` sonst die neueste statt der tatsächlich geprüften Iteration anwenden könnte.
- `check_identity_guard()`: Blockiert das Schreiben, wenn am Zielindex nicht mehr dasselbe Objekt liegt wie bei der Proposal-Erzeugung.
- `prepare_proposal_for_apply()` beziehungsweise `ProposalApplyBlockedError`: Blockiert `manual_intervention_required` und ein Modify bei Actions, die `new_value` nicht konsumieren, beispielsweise `remove_from_array`.

Netz- und Pipelinefehler werden separat als HTTP 502 mit `failed_at`, `error` und `revalidation_result` dokumentiert; die menschliche Entscheidung bleibt dabei committed.

## AP4 – Review Board

AP4 ist in `demo/ui/review.html`, `demo/ui/scripts/review.js` und `demo/ui/css/styles.css` umgesetzt. Das Board zeigt die offenen Proposals, Snapshot-Filter, Deep-Links, Fehlerkontext mit echten Zeilennummern, Alt-/Neuwert-Diff, Zusatz-Updates, Confidence-Begründungen, ähnliche Memory-Fälle und die Aktionen Approve, Modify und Reject. Nach einem Reload wird auch die persistierte menschliche Entscheidung wieder dargestellt.

## AP5 – MCP und E-Mail

Der FastMCP-Server registriert in `demo/mcp_connections/server.py` zwölf Tools:

1. `get_pending_reviews`
2. `get_review_details`
3. `approve_correction`
4. `reject_correction`
5. `modify_correction`
6. `get_snapshot_status`
7. `get_dashboard_metrics`
8. `create_email_draft`
9. `get_email_draft`
10. `revise_email_draft`
11. `send_email_draft`
12. `cancel_email_draft`

Die Review-Entscheidungstools persistieren die Entscheidung, starten aber nicht selbst die Apply-Pipeline.

Der E-Mail-Ablauf besitzt folgende Schritte:

- **Draft:** `create_email_draft` persistiert Version 1 im Status `draft`.
- **Revise:** `revise_email_draft` ersetzt den sichtbaren Inhalt und erhöht die Version; der Status bleibt `draft`.
- **Confirm:** Eine Zustimmung wie „Ja, passt“ versendet noch nichts. `confirmed=True` ist eine technische Voraussetzung des Send-Tools, kein eigener DB-Status.
- **Send:** Erst „Bitte absenden“ ruft `send_email_draft(..., confirmed=True)` auf; danach gilt `status=sent`.
- **Cancel:** Ein Abbruch setzt `status=cancelled`.

Der tatsächlich verwendete Versanddienst ist Azure Communication Services Email. SendGrid ist als alternative Providerimplementierung vorhanden. Automatische Proposal-E-Mails sind deaktiviert; Versand erfolgt ausschließlich nach Aufforderung im Chat.

## AP6 – Dashboard

Der Dashboard-Endpunkt ist `GET /api/dashboard/metrics` in `demo/routes/dashboard.py`.

### Berechnete Kennzahlen

| Kennzahl | Berechnungsgrundlage |
|---|---|
| `validations` | `agent_runs` mit `tool_name="validate_snapshot"` |
| `snapshots_tracked` | Anzahl `snapshots_meta` |
| `proposals_total` | im Zeitraum erzeugte Proposals |
| `proposals_open` | aktueller Bestand mit `pending_review`, nicht zeitgefiltert |
| `decisions_total` | Approve + Reject + Modify |
| `approve_count`, `reject_count`, `modify_count` | Reviews nach Entscheidung |
| `approval_rate`, `reject_rate`, `modify_rate` | jeweilige Entscheidung durch alle Entscheidungen |
| `accepted_unchanged_rate` | ausschließlich Approve durch alle Entscheidungen |
| `avg_confidence` | Mittelwert vorhandener Confidence-Scores |
| `revalidation_attempts` | vertrauenswürdige Apply-/Revalidierungsversuche |
| `revalidation_success` | Pipeline erfolgreich und `errors_after < errors_before` |
| `revalidation_success_rate` | Erfolge durch vertrauenswürdige Versuche |
| `revalidation_untrusted` | alte Versuche ohne `errors_before` |
| `handling_time_median_s`, `handling_time_mean_s` | `decided_at - created_at`, ohne schnelle Fixtures |
| `handling_time_n` | einbezogene Bearbeitungszeiten |
| `handling_time_excluded_fixtures` | Entscheidungen unter 60 Sekunden |
| `tokens_prompt`, `tokens_completion`, `tokens_total` | Summe der gespeicherten Tokenwerte |
| `cost_estimate_usd` | Neubewertung der Tokens mit aktuellem Input-/Output-Preismodell |
| `agent_runs` | Anzahl Agent-Läufe im Zeitraum |

Zusätzlich berechnet das Dashboard eine Entscheidungszeitreihe, Fehlerartenverteilung, Confidence-Verteilung und Kalibrierung nach fünf Confidence-Bändern.

### Data-Quality-Flags

- `RANGE_EXCLUDES_DATA`: Datensätze liegen außerhalb des Zeitfilters.
- `RANGE_INPUT_IGNORED`: Ungültige Filterwerte wurden ersetzt.
- `GRANULARITY_COARSENED`: Zu viele Zeit-Buckets wurden automatisch vergröbert.
- `CONFIDENCE_LEGACY_FORMULA`: Entscheidungen verwenden die alte v0-/unbekannte Confidence-Formel.
- `CONFIDENCE_MIXED_FORMULA_VERSIONS`: Nicht vergleichbare Formelgenerationen wurden gemeinsam ausgewählt.
- `ERROR_TYPE_LEGACY_HEURISTIC`: Alte Fehlertypen stammen aus der Trefferzählung statt aus Validator-Tags.
- `REVALIDATION_PRE_AP33D`: Revalidierung stammt aus der Zeit vor dem echten Server-Validation-Trigger.
- `HANDLING_TIME_FIXTURES`: Unplausibel schnelle Testentscheidungen wurden erkannt.
- `COST_IS_ESTIMATE`: Kosten sind eine Listenpreisschätzung, keine Azure-Rechnung.
- `TOKENS_INCOMPLETE`: Agent-Läufe ohne Tokenwerte machen Summen zur Untergrenze.
- `VALIDATION_COUNT_PARTIAL`: Serverseitige Validierungsjobs fehlen in `agent_runs`.
- `SMALL_SAMPLE`: Weniger als zehn Entscheidungen erlauben keine belastbare Statistik.

Aktueller `preset=all`-Nachweis: HTTP 200, 13 Proposals, 7 offene Reviews, 6 Entscheidungen, 2 Approve, 3 Modify, 1 Reject, 1.657.996 Tokens und geschätzte Kosten von 4,4019 USD.

## AP7 – Retrieval und Memory-Support

Die Retrieval-Logik steht in `demo/memory/retrieval.py`. Der konkrete Arrayindex wird aus dem Zielpfad entfernt, beispielsweise:

```text
demands[999].demandId → demands[].demandId
```

Nur Fälle mit identischem `affected_entity_pattern` werden berücksichtigt. Ein übereinstimmender `error_type` verbessert lediglich das Ranking; er ist kein zwingendes Match-Kriterium. Ein Fall mit erfolgreicher Revalidierung wird ebenfalls höher gereiht. Danach wird nach Score und Aktualität sortiert; standardmäßig werden maximal drei Fälle geliefert.

`memory_support` wird deterministisch berechnet:

- kein ähnlicher Fall → `0,0`
- gleicher Wert wurde früher verworfen oder wegmodifiziert → `0,0`
- ähnliche Fälle, aber kein Wertpräzedenzfall → `0,5`
- ein Mensch bestätigte exakt denselben finalen Wert → `1,0`

Über den Faktor `0,2` verändert das den Confidence-Score um `0`, `0,1` oder `0,2`.

Konkreter read-only Nachweis: Für `demands[999].demandId` mit `error_type=UNIQUE_IDS` wurden die Fälle `#1`, `#5` und `#4` wiedergefunden, obwohl #4/#5 noch das Legacy-Label `EMPTY_FIELD` tragen. Für den vorgeschlagenen Wert `D100005_001` ergab Fall #5 – menschliches Modify auf exakt diesen Wert – `memory_support=1,0`. Für einen unbekannten Wert ergaben dieselben drei Fälle `memory_support=0,5`.

## Nachweise, Screenshots und AP-E

Im Repository befinden sich derzeit keine gespeicherten Review- oder Dashboard-Screenshots. Gefunden wurden nur Logo-/Gestaltungsdateien:

- `demo/ui/logo-agentic.png`
- `docs/azure-ai-foundry-logo.jpg`
- `docs/KBC3353 CANCOM_Logo.jpg`
- `docs/microsoft-azure-logo.png`

Im bisherigen Chat sind vorhanden:

- ein Screenshot der real zugestellten ACS-E-Mail mit funktionierendem Review-Link;
- ein Review-Board-Screenshot für Snapshot `1ef11903-…` mit Fehlerkontext und Vorher/Nachher-Diff für `articles[312].workItemConfigs`;
- zwei UI-Referenzbilder für Plus-Menü und E-Mail-Auswahl.

Ein Dashboard-Screenshot wurde weder im Repository noch in den bisherigen Anhängen gefunden und muss für die Dokumentation noch aufgenommen werden.

Realer Apply-Nachweis für `ec96832c-…__iteration-5`:

```text
errors_before: 2
errors_after:  0
pipeline_success: true
value_source: human_modify
validation_trigger.status: FINISHED
```

AP-E ist noch nicht als vollständige Acceptance-Messung abgeschlossen. In der aktuellen Datenbank liegen 2 von 6 Entscheidungen als „approve – unverändert angenommen“ vor, also 33,33 %. Alle sechs Entscheidungen gehören jedoch zur historischen Formelversion v0; die sieben v3-Proposals sind noch offen. Daher sind **2 von 6 kein finaler AP-E-Wert**. Bereits vorhanden ist eine vorläufige A/B-Messung über drei Snapshots: 81.962 → 68.920 Prompt-Tokens, entsprechend −16 %, bei identischen Vorschlägen; die vollständige Seeding-, Acceptance- und Kalibrierungsmessung bleibt offen.
