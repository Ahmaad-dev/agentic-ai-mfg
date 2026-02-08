# Smart Planning API - Snapshot Tools

Dieses Verzeichnis enthält Skripte zum Erstellen und Verwalten von Snapshots über die Smart Planning API.

## Virtual Environment

cd C:\Projektarbeiten\agentic-ai-mfg\demo
.venv\Scripts\Activate.ps1

## Skripte

### 1. Python: `create_snapshot.py`

**Als Skript ausführen:**
```bash
python create_snapshot.py
```
example:
C:\Projektarbeiten\agentic-ai-mfg\demo\smart-planning\runtime

python create_snapshot.py


### 2. Python: `validate_snapshot.py`

**Als Skript ausführen:**
```bash
python validate_snapshot.py
```
example:
C:\Projektarbeiten\agentic-ai-mfg\demo\smart-planning\runtime

python validate_snapshot.py


### 3. Python: `identify_snapshot.py`

Sucht nach spezifischen Werten oder leeren Feldern in den Snapshot-Daten.

**Wichtig:**
- Benötigt eine aktive Snapshot-ID in `runtime-files/current_snapshot.txt`
- Liest Daten aus `Snapshots/{snapshot_id}/snapshot-data.json`
- Speichert Ergebnisse in `last_search_results.json` (Snapshot-Ordner + neueste Iteration)

**Modus 1: Suche nach Wert (VALUE mode)**
```bash
python identify_snapshot.py <search_value>
```

Beispiele:
```bash
# Suche nach Demand-ID
python identify_snapshot.py D830081_005

# Suche nach Article-ID
python identify_snapshot.py 830081
```

**Modus 2: Suche nach leeren Feldern (EMPTY_FIELD mode)**
```bash
python identify_snapshot.py --empty <field_name>
```

Beispiele:
```bash
# Finde leere demandId Felder
python identify_snapshot.py --empty demandId

# Finde leere articleId Felder
python identify_snapshot.py --empty articleId

# Finde leere workerQualifications (Root-Level Array)
python identify_snapshot.py --empty workerQualifications
```

**Spezialfall: Leere Root-Level Arrays (z.B. workerQualifications)**

Bei leeren Root-Level Arrays verwendet das Tool einen 3-stufigen Hierarchie-Ansatz:

1. **Plan A**: Versuche Daten aus Snapshot selbst zu lernen (field_examples, patterns)
2. **Plan B**: Reference Data Fallback (wenn `config.json` → `use_reference_data_fallback: true`)
   - Lädt Daten aus `runtime/identify-tool-files/reference-snapshot.json`
   - Fügt `reference_data_available: true` zu `last_search_results.json` hinzu
   - LLM kann dann `USE_REFERENCE_DATA` vorschlagen
3. **Plan C**: Manual Intervention (wenn Config=false oder keine Reference-Daten)
   - Fügt `manual_intervention_required: true` zu `last_search_results.json` hinzu
   - LLM schlägt `action: "manual_intervention_required"` vor

**Output:**
- Konsolen-Ausgabe mit gefundenen Ergebnissen
- `last_search_results.json` mit:
  - `search_mode`: "value" oder "empty_field"
  - `error_type`: DUPLICATE_ID, SINGLE_MATCH oder EMPTY_FIELD
  - `original_structure`: Array der gefundenen Objekte
  - `results`: Detaillierte Analyse mit Referenzen und Artikel-Kontext
  - **NEU**: `reference_data_available`, `reference_data`, `reference_data_count` (bei Plan B)
  - **NEU**: `manual_intervention_required`, `reason` (bei Plan C)
  - `context`: Gesamt-Statistiken


### 4. Python: `identify_error_llm.py`

Automatisierte Fehleranalyse mit Azure OpenAI LLM.

**Wichtig:**
- Benötigt `.env` Datei mit Azure OpenAI Credentials (siehe Umgebungsvariablen unten)
- Benötigt aktive Snapshot-ID in `runtime-files/current_snapshot.txt`
- Analysiert nur ERROR-Level Messages (ignoriert WARNINGs)
- Erstellt automatisch `iteration-{nummer}` Ordner mit Analyse-Ergebnissen

**Als Skript ausführen:**
```bash
python identify_error_llm.py
```

**Demo-Modus (für Tests ohne echte Validation-Daten):**
```bash
python identify_error_llm.py --demo
```

**Workflow:**
1. Lädt Validation-Daten aus `snapshot-validation.json`
2. LLM analysiert erste ERROR-Message
3. LLM entscheidet automatisch zwischen:
   - **VALUE mode**: Bei konkreten IDs (z.B. "Duplicate IDs: D830081_005")
   - **EMPTY_FIELD mode**: Bei leeren Feldern (z.B. "Demand IDs must not be empty")
4. Erstellt `iteration-{nummer}` Ordner mit:
   - `llm_identify_response.json` - LLM-Antwort
   - `llm_identify_call.json` - Kompletter Request/Response + Token-Verbrauch
   - `last_search_results.json` - Detaillierte Suchergebnisse (falls investigate)
5. Triggert automatisch `identify_snapshot.py` mit korrektem Modus

**Output-Beispiel:**
```
📊 Found 2 ERROR message(s)
🤖 LLM Analysis:
   Search Mode: empty_field
   Search Value: demandId
   Error Type: Demand IDs must not be empty
   Should Investigate: True

📁 Created iteration folder: iteration-5
🔧 Triggering identify tool in EMPTY FIELD mode for: demandId
```


### 5. Python: `generate_correction_llm.py`

Generiert strukturierte Korrekturvorschläge mit Azure OpenAI LLM.

**Wichtig:**
- Benötigt `.env` Datei mit Azure OpenAI Credentials
- Benötigt aktive Snapshot-ID in `runtime-files/current_snapshot.txt`
- Verwendet `llm-validation-fix-rules.md` als **Single Point of Truth** für Behebungsregeln
- Nutzt bestehenden Iteration-Ordner (erstellt KEINEN neuen)

**Als Skript ausführen:**
```bash
python generate_correction_llm.py
```

**Workflow:**
1. Lädt Snapshot-ID aus `current_snapshot.txt`
2. Findet höchsten Iteration-Ordner mit `llm_identify_response.json`
3. Lädt 3 Inputs:
   - `llm-validation-fix-rules.md` - Behebungsregeln (fachliche Logik)
   - `llm_identify_response.json` - Original-Error + Analyse
   - `last_search_results.json` - Fundstellen + enriched_context
4. LLM-Call mit strukturiertem Prompt
5. Speichert in bestehenden `iteration-{nummer}` Ordner:
   - `llm_correction_proposal.json` - Strukturierter Korrekturvorschlag
   - `llm_correction_call.json` - Kompletter Request/Response + Token-Verbrauch

**Output-Format (llm_correction_proposal.json):**
```json
{
  "iteration": 6,
  "snapshot_id": "...",
  "original_error": {...},
  "error_analyzed": {...},
  "correction_proposal": {
    "action": "update_field",
    "target_path": "demands[3].demandId",
    "current_value": "",
    "new_value": "DSPE_EM_002",
    "reasoning": "Pattern detected: DSPE_{articleId}_{sequence}...",
    "additional_updates": []
  }
}
```

**Unterstützte Actions:**
- `update_field`: Ändert einen Feldwert (Standard)
- `add_to_array`: Fügt ein Element zu einem Array hinzu
- `remove_from_array`: Entfernt ein Element aus einem Array
- **NEU**: `manual_intervention_required`: Keine automatische Korrektur möglich (z.B. bei Config=false)

**Spezialfall: Reference Data Fallback**

Wenn `last_search_results.json` `reference_data_available: true` enthält, kann das LLM vorschlagen:
```json
{
  "action": "update_field",
  "new_value": "USE_REFERENCE_DATA"
}
```
Das bedeutet: Verwende Daten aus `runtime/identify-tool-files/reference-snapshot.json`

**Output-Beispiel:**
```
Snapshot ID: 8909716f-ed63-4602-96d1-7dbb1b122241
Using existing iteration: 6

Loading inputs...
- Fix rules loaded (2906 chars)
- Error analysis loaded (iteration 6)
- Search results loaded (1 results)

Generating correction proposal with LLM...

Proposal generated:
- Action: update_field
- Target: demands[3].demandId
- New Value: DSPE_EM_002
- Additional Updates: 0

Token Usage:
- Prompt: 2678
- Completion: 102
- Total: 2780
```


### 6. Python: `validate_correction_schema_llm.py`

Validiert LLM-generierte Korrekturvorschläge gegen Pydantic-Schema mit automatischer LLM-Korrektur.

**Wichtig:**
- Eigenständiges Tool (wird NICHT automatisch von apply_correction.py aufgerufen)
- Benötigt aktive Snapshot-ID in `runtime-files/current_snapshot.txt`
- Benötigt `llm_correction_proposal.json` im höchsten Iteration-Ordner
- Verwendet Pydantic-Models aus `correction_models.py` für Schema-Validierung
- Max. 5 Retry-Versuche mit LLM bei Schema-Fehlern

**Als Skript ausführen:**
```bash
python validate_correction_schema_llm.py
```

**Workflow:**
1. Findet höchsten Iteration-Ordner mit `llm_correction_proposal.json`
2. Lädt Korrekturvorschlag aus `llm_correction_proposal.json`
3. Validiert gegen Pydantic-Schema (LLMCorrectionResponse)
4. Bei Validierungsfehler:
   - LLM erhält ValidationError + Original-Inputs + JSON-Schema
   - Max. 5 Retry-Versuche
   - Bei Erfolg: Überschreibt `llm_correction_proposal.json` mit korrigierter Version
5. Speichert alle Versuche im Iteration-Ordner:
   - `retry_0.json` - Originaler Vorschlag (vor Validation)
   - `retry_1.json` bis `retry_5.json` - LLM-Korrekturversuche

**Exit Codes:**
- `0` = Schema valid (entweder direkt oder nach erfolgreicher LLM-Korrektur)
- `1` = Schema invalid (auch nach 5 Retries)

**Output-Beispiel (Success):**
```
=== Schema Validation ===

Snapshot ID: 736a4e03-652f-4f74-b8ca-4da803d30173
Using iteration: 1

Loading correction proposal...
Validating schema...
✓ OK Schema validation passed

=== Done ===
```

**Output-Beispiel (Mit Retry):**
```
=== Schema Validation ===

Snapshot ID: 736a4e03-652f-4f74-b8ca-4da803d30173
Using iteration: 1

Loading correction proposal...
Validating schema...
⚠ Schema validation failed

Starting LLM retry process (max 5 attempts)...

Retry 1/5: Calling LLM to fix schema...
✓ LLM generated corrected proposal
Validating corrected proposal...
✓ OK Schema validation passed

File updated: llm_correction_proposal.json

=== Done ===
```


### 7. Python: `apply_correction.py`

Wendet LLM-generierte Korrekturvorschläge auf snapshot-data.json an.

**Wichtig:**
- Eigenständiges Tool (Schema-Validierung muss vorher separat durchgeführt werden)
- Benötigt aktive Snapshot-ID in `runtime-files/current_snapshot.txt`
- Benötigt **validiertes** `llm_correction_proposal.json` im höchsten Iteration-Ordner
- Erstellt **Backup** von snapshot-data.json und snapshot-validation.json im Iteration-Ordner
- Ändert snapshot-data.json im **Haupt-Snapshot-Ordner** (nicht in Iteration)
- Dokumentiert komplette LLM-Analyse in metadata.txt

**Als Skript ausführen:**
```bash
python apply_correction.py
```

**Workflow:**
1. Findet höchsten Iteration-Ordner mit `llm_correction_proposal.json`
2. **Schema-Check**: Validiert Vorschlag gegen Pydantic-Schema
   - Bei INVALID: Klare Fehlermeldung + Exit 1
   - Empfehlung: `python validate_correction_schema_llm.py` ausführen
3. **Backup**: Kopiert snapshot-data.json + snapshot-validation.json → iteration-{nummer}/
4. Lädt Korrekturvorschlag aus `llm_correction_proposal.json`
5. Parst target_path (z.B. `demands[3].demandId`)
6. Wendet Korrektur an:
   - **Standard**: Hauptkorrektur (target_path + new_value)
   - **USE_REFERENCE_DATA**: Lädt Daten aus `runtime/identify-tool-files/reference-snapshot.json`
   - **manual_intervention_required**: Keine Änderung an snapshot-data.json
   - Additional_updates (falls vorhanden, z.B. für Referenz-Updates)
7. Speichert korrigierte snapshot-data.json im Haupt-Snapshot-Ordner (außer bei manual_intervention)
8. **Metadata-Dokumentation**: Erweitert metadata.txt mit:
   - Original Error (level + message)
   - Error Analysis (error_type, search_mode, search_value, results_count)
   - Correction Applied (action, target_path, old/new value, reasoning)
   - **NEU**: Reference Data Warning (bei `USE_REFERENCE_DATA`)
   - **NEU**: Manual Intervention Warning (bei `manual_intervention_required`)
   - Additional Updates (Liste aller zusätzlichen Änderungen)
   - Original LLM Proposal (kompletter JSON in Code-Block)

**Path-Format:**
- Pattern: `arrayName[index].fieldName`
- Beispiel: `demands[3].demandId` → Ändert demands[3].demandId

**Exit Codes:**
- `0` = Success - Korrektur erfolgreich angewendet
- `1` = Failure - Schema invalid oder Fehler beim Anwenden

**Output-Beispiel:**
```
=== Correction Applier ===

Snapshot ID: 8909716f-ed63-4602-96d1-7dbb1b122241
Using iteration: 6

Backing up files to iteration-6...
  ✓ Backed up: snapshot-data.json
  ✓ Backed up: snapshot-validation.json

Loading correction proposal...
  Action: update_field
  Target: demands[3].demandId
  Reasoning: Pattern detected: DSPE_{articleId}_{sequence}...

Loading snapshot data...

Applying main correction:
  Path: demands[3].demandId
  New Value: DSPE_EM_002
  Old Value: 
  ✓ Applied

Saving corrected snapshot data...
✓ Saved to: ..\Snapshots\...\snapshot-data.json

Appending to metadata.txt...
✓ Metadata updated

=== Done ===

Next step: Run update_snapshot.py to upload corrections to server
```

**Error-Beispiel (Invalid Schema):**
```
=== Correction Applier ===

ERROR: INVALID JSON SCHEMA DETECTED

The correction proposal in llm_correction_proposal.json does not match the required schema.

Validation Error:
1 validation error for LLMCorrectionResponse
iteration
  Field required [type=missing, input_value={...}, input_type=dict]

PLEASE RUN THIS TOOL FIRST:
  python validate_correction_schema_llm.py

This will validate the schema and automatically fix it with LLM if needed.
```


### 8. Python: `update_snapshot.py`

Lädt korrigierte Snapshot-Daten auf den Smart Planning API Server hoch.

**Wichtig:**
- Benötigt aktive Snapshot-ID in `runtime-files/current_snapshot.txt`
- Benötigt korrigierte `snapshot-data.json` im Snapshot-Ordner
- Benötigt `metadata.txt` im Snapshot-Ordner (für Name/Comment)
- Verwendet PUT /snapshots/{snapshotId} API-Endpoint

**Als Skript ausführen:**
```bash
python update_snapshot.py
```

**Workflow:**
1. Lädt Snapshot-ID aus `current_snapshot.txt`
2. Lädt korrigierte snapshot-data.json aus `Snapshots/{uuid}/snapshot-data.json`
3. Lädt Snapshot-Metadata (name, comment) aus `metadata.txt`
4. Konvertiert snapshot-data zu JSON-String für `dataJson` Feld
5. PUT Request zu `/snapshots/{snapshotId}` mit SnapshotUpdateRequest:
   - `name`: Snapshot-Name
   - `comment`: Snapshot-Kommentar (optional)
   - `dataJson`: Komplette Snapshot-Daten als JSON-String
6. Speichert Upload-Ergebnis in `upload-result.json`

**Exit Codes:**
- `0` = Success - Snapshot erfolgreich auf Server aktualisiert
- `1` = Failure - Fehler beim Upload (HTTP-Error, File not found, etc.)

**Output-Beispiel:**
```
======================================================================
UPDATE SNAPSHOT - Upload Corrected Data to Server
======================================================================

Snapshot ID: 736a4e03-652f-4f74-b8ca-4da803d30173

→ Loading corrected snapshot data from:
  C:\...\Snapshots\736a4e03-652f-4f74-b8ca-4da803d30173\snapshot-data.json
  ✓ Data loaded (1,618,742 characters)

→ Loading snapshot metadata from:
  C:\...\Snapshots\736a4e03-652f-4f74-b8ca-4da803d30173\metadata.txt
  ✓ Name: SP-Agent: Snapshot vom 2026-02-03 21:52:34
  ✓ Comment: (none)
✓ Authentication successful

→ Uploading snapshot data to server...
  Snapshot ID: 736a4e03-652f-4f74-b8ca-4da803d30173
  Name: SP-Agent: Snapshot vom 2026-02-03 21:52:34
  Data size: 1,618,742 characters

======================================================================
✓ SUCCESS - Snapshot updated on server!
======================================================================

Server response:
{
  "name": "SP-Agent: Snapshot vom 2026-02-03 21:52:34",
  "comment": null,
  "id": "736a4e03-652f-4f74-b8ca-4da803d30173",
  "dataModifiedAt": "2026-02-03T21:19:20.097247338Z",
  "dataModifiedBy": "service-account-apiclient-test",
  "isSuccessfullyValidated": false
}

→ Upload result saved to: C:\...\upload-result.json

→ Next step: Run validate_snapshot.py to verify corrections
```


## Konfiguration & Reference Data

### Config-Datei: `identify-tool-files/config.json`

Steuert das Verhalten der automatischen Fehlerkorrektur bei leeren Arrays.

**Pfad:** `runtime/identify-tool-files/config.json`

**Struktur:**
```json
{
  "use_reference_data_fallback": true,
  "description": "Controls whether reference snapshot data can be used as automatic fallback when no other solution exists"
}
```

**Parameter:**
- `use_reference_data_fallback` (boolean):
  - `true`: Reference-Daten dürfen automatisch verwendet werden (Plan B)
  - `false`: Nur manuelle Intervention erlaubt (Plan C)

**Verwendung:**
- Geladen von `identify_snapshot.py` bei `--empty` Modus
- Bestimmt ob `reference_data_available` oder `manual_intervention_required` in `last_search_results.json` gesetzt wird
- LLM nutzt diese Info zur Entscheidung zwischen automatischer Korrektur und manueller Review


### Reference Snapshot: `identify-tool-files/reference-snapshot.json`

Enthält valide Snapshot-Daten als Fallback-Quelle für leere Arrays.

**Pfad:** `runtime/identify-tool-files/reference-snapshot.json`

**Zweck:**
- Bereitstellung von vollständigen, validierten Daten für leere Root-Level Arrays
- Wird nur verwendet wenn `config.json` → `use_reference_data_fallback: true`
- Typische Use Cases:
  - `workerQualifications`: 93 Worker mit Qualifikationen
  - Andere strukturelle Arrays die nicht snapshot-spezifisch sind

**Erstellung:**
Kopiere einen validen Snapshot als Referenz:
```bash
# Beispiel: Snapshot da6d77c3-8eb9-413c-8c19-1c4241aeb594 als Referenz
cp Snapshots/da6d77c3-8eb9-413c-8c19-1c4241aeb594/original-data/snapshot-data.json \
   runtime/identify-tool-files/reference-snapshot.json
```

**Workflow mit Reference Data:**
1. `identify_snapshot.py --empty workerQualifications`
   - Erkennt leeres Array
   - Lädt Config (use_reference_data_fallback: true)
   - Lädt Reference Snapshot
   - Findet `workerQualifications` mit 93 Einträgen
   - Schreibt `reference_data_available: true` + Sample in `last_search_results.json`

2. `generate_correction_llm.py`
   - Liest `reference_data_available: true`
   - LLM schlägt vor: `"new_value": "USE_REFERENCE_DATA"`

3. `apply_correction.py`
   - Erkennt `USE_REFERENCE_DATA`
   - Lädt 93 Einträge aus `reference-snapshot.json`
   - Kopiert sie nach `snapshot-data.json`
   - Dokumentiert in `metadata.txt` mit Warnung zur manuellen Verifikation


## Umgebungsvariablen

Die `.env` Datei muss folgende Variablen enthalten:

```env
# Smart Planning API
CLIENT_SECRET=<your_client_secret>

# Azure OpenAI (für identify_error_llm.py)
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=<your-deployment-name>
AZURE_OPENAI_API_VERSION=2025-01-01-preview
AZURE_OPENAI_API_KEY=<your-api-key>
```




## Hinweise

- SSL-Zertifikatsvalidierung ist in der Test-Umgebung deaktiviert
- Der Crawler benötigt ca. 5-15 Sekunden zur Verarbeitung