"""
Audit Report Generator for Smart Planning Snapshots
Generates a professional audit report based on metadata.txt
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from openai import AzureOpenAI

# UTF-8 Encoding für Windows-Terminal
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables (aus demo-Verzeichnis)
# Lade .env aus dem demo-Verzeichnis (2 Ebenen höher)
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def load_snapshot_id():
    """Load current snapshot ID from runtime-files/current_snapshot.txt"""
    runtime_files_dir = Path(__file__).parent / "runtime-files"
    current_snapshot_file = runtime_files_dir / "current_snapshot.txt"
    
    if not current_snapshot_file.exists():
        print(f"Error: {current_snapshot_file} not found")
        sys.exit(1)
    
    with open(current_snapshot_file, 'r') as f:
        content = f.read().strip()
        if "snapshot_id = " in content:
            return content.split("snapshot_id = ")[1].strip()
        else:
            print(f"Error: Invalid format in {current_snapshot_file}")
            sys.exit(1)


def load_metadata(snapshot_id):
    """Load metadata.txt from snapshot folder"""
    snapshot_dir = Path(__file__).parent.parent / "Snapshots" / snapshot_id
    metadata_file = snapshot_dir / "metadata.txt"
    
    if not metadata_file.exists():
        print(f"Error: {metadata_file} not found")
        sys.exit(1)
    
    with open(metadata_file, 'r', encoding='utf-8') as f:
        return f.read()


def load_upload_results(snapshot_id):
    """Load upload-result.json from snapshot folder (optional)"""
    snapshot_dir = Path(__file__).parent.parent / "Snapshots" / snapshot_id
    upload_results_file = snapshot_dir / "upload-result.json"
    
    if not upload_results_file.exists():
        return None
    
    with open(upload_results_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_audit_report_with_llm(metadata_content, upload_results, snapshot_id):
    """Generate professional audit report using Azure OpenAI"""
    
    client = AzureOpenAI(
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY")
    )
    
    # Format upload results for prompt
    upload_results_text = ""
    if upload_results:
        upload_results_text = f"""

**UPLOAD RESULTS (upload-result.json):**
```json
{json.dumps(upload_results, indent=2)}
```
"""
    
    prompt = f"""Du bist ein professioneller technischer Auditor. Erstelle einen umfassenden Prüfbericht basierend auf den Metadaten eines Smart Planning Snapshots.

**STRUKTUR DER METADATEN:**
Die metadata.txt Datei enthält strukturierte Informationen über den Snapshot und alle Korrektur-Iterationen. Sie verwendet Markdown-Überschriften und JSON-Blöcke:

**Hauptsektionen (typische Reihenfolge):**
1. **# SNAPSHOT INFORMATIONS**: JSON-Block mit Snapshot-Metadaten
   - id, name, comment, isSuccessfullyValidated, dataModifiedAt, dataModifiedBy, etc.

2. **## INITIAL VALIDATION (First Run)**: Erste Validierung nach Snapshot-Erstellung
   - Timestamp, total messages, summary (X ERROR, Y WARNING), status
   - Detaillierte Validierungsmeldungen als Array mit level + message für jedes Problem

3. **## UPLOAD Iteration N**: Server-Upload-Ergebnisse (kann mehrfach vorkommen)
   - Uploaded at timestamp
   - Server validated: True/False
   - Modified at (server), Modified by
   - Status-Nachricht: "SNAPSHOT IS VALID" oder "SNAPSHOT HAS ERRORS"
   - Kann von "### LLM Correction Applied (Iteration N)" Untersektion gefolgt werden

4. **## VALIDATION Iteration N**: Zusätzliche Validierungsläufe (ohne Upload)
   - Gleiche Struktur wie INITIAL VALIDATION
   - Wird für lokale Validierung ohne Server-Upload verwendet

5. **### LLM Correction Applied (Iteration N)**: Details zu automatischen Korrekturen (Untersektion unter UPLOAD)
   - **Original Error**: level (ERROR/WARNING) + message
   - **Error Analysis**: error_type (EMPTY_FIELD/DUPLICATE_ID/SINGLE_MATCH), search_mode, search_value, results_count
   - **Correction Applied**: action, target_path, old/new value, reasoning
   - **Special Warnings** (bedingt):
     * "⚠⚠⚠ MANUAL INTERVENTION REQUIRED" - Keine automatische Korrektur angewendet (action: manual_intervention_required)
     * "IMPORTANT: Reference Data Fallback Used" - Daten aus Referenz-Snapshot kopiert (new_value: USE_REFERENCE_DATA)
   - **Additional Updates**: Liste sekundärer Korrekturen (normalerweise leeres Array)
   - **Original llm_correction_proposal**: Vollständiger JSON-Vorschlag der LLM

**Muster-Erkennung:**
- UPLOAD-Sektionen können LLM Correction Untersektionen enthalten (wenn Korrekturen vor Upload durchgeführt wurden)
- VALIDATION-Sektionen enthalten NIE LLM Correction Untersektionen (sie validieren nur)
- Mehrere UPLOAD + VALIDATION Zyklen zeigen iterativen Korrekturprozess
- "additional_updates" Array listet sekundäre Korrekturen neben Hauptkorrektur
- Leeres "additional_updates": [] bedeutet nur Hauptkorrektur wurde angewendet

**SNAPSHOT METADATA (metadata.txt):**
```
{metadata_content}
```{upload_results_text}

**BERICHT-ANFORDERUNGEN:**

Erstelle einen professionellen Prüfbericht im Markdown-Format mit folgender Struktur:

# Snapshot Prüfbericht

## Zusammenfassung
- Kurze Übersicht über den Snapshot und seinen aktuellen Status
- Gesamtzahl der angewendeten Korrekturen
- Finaler Validierungsstatus
- Wichtigste Erkenntnisse (falls Probleme bestehen bleiben)

## Snapshot-Übersicht
- Snapshot ID: {snapshot_id}
- Name: [aus Metadaten extrahieren]
- Erstellt: [Timestamp extrahieren]
- Geändert von: [aus Metadaten extrahieren]
- Anzahl Iterationen: [aus Metadaten zählen]

## Validierungsverlauf

### Initiale Validierung
- Datum: [extrahieren]
- Status: [extrahieren]
- Fehler: [zählen und auflisten]
- Warnungen: [zählen und auflisten]

### Finale Validierung
- Datum: [extrahieren]
- Status: [extrahieren]
- Fehler: [zählen und auflisten]
- Warnungen: [zählen und auflisten]

### Validierungsfortschritt
[Erstelle eine Übersichtstabelle mit dem Fortschritt von initial bis final]

## Angewendete Korrekturen

[Für jede Iteration in den Metadaten eine detaillierte Sektion erstellen:]

### Iteration [N]: [Fehlertyp]

**Ursprünglicher Fehler:**
- Level: ERROR/WARNING
- Nachricht: [Fehlermeldung extrahieren]

**Ursachenanalyse:**
- Fehlertyp: [EMPTY_FIELD, DUPLICATE_ID, etc.]
- Betroffener Pfad: [target_path]
- Suchergebnisse: [Anzahl]

**Korrektur-Details:**
- Durchgeführte Aktion: [update_field, USE_REFERENCE_DATA, manual_intervention_required, etc.]
- Zielpfad: `[path]`
- Alter Wert: `[value]`
- Neuer Wert: `[value]`
- Begründung: [LLM-Begründung extrahieren]

**Besondere Hinweise:**
[Falls USE_REFERENCE_DATA verwendet wurde:]
⚠️ **Referenzdaten-Fallback verwendet**
- Quelle: Referenz-Snapshot
- Importierte Daten: [Details]
- Manuelle Verifikation: EMPFOHLEN

[Falls manual_intervention_required:]
⚠️⚠️⚠️ **MANUELLE INTERVENTION ERFORDERLICH**
- Status: Keine automatische Korrektur angewendet
- Grund: [extrahieren]
- Erforderliche Aktion: Manuelle Überprüfung und Korrektur

**Zusätzliche Updates:**
[additional_updates auflisten falls vorhanden]

---

## Verwendung von Referenzdaten

[Falls Iteration Referenzdaten verwendet hat:]
- Iterationen mit Referenzdaten: [Anzahl]
- Betroffene Felder: [Liste]
- Verifikationsstatus: [MANUELLE ÜBERPRÜFUNG AUSSTEHEND / VERIFIZIERT]

[Falls keine Referenzdaten verwendet:]
Es wurden keine Referenzdaten-Fallbacks für diesen Snapshot verwendet.

## Manuelle Interventionen

[Falls manuelle Interventionen erforderlich waren:]
- Anzahl manueller Interventionsanfragen: [Anzahl]
- Felder die manuelle Überprüfung benötigen: [Liste]
- Status: [AUSSTEHEND / GELÖST]

[Falls keine:]
Es waren keine manuellen Interventionen erforderlich.

## Zeitverlauf

[Chronologische Timeline erstellen:]
- **[Datum/Zeit]** - Snapshot erstellt
- **[Datum/Zeit]** - Initiale Validierung (X Fehler, Y Warnungen)
- **[Datum/Zeit]** - Iteration 1: [Kurzbeschreibung]
- **[Datum/Zeit]** - Upload zum Server
- **[Datum/Zeit]** - Iteration 2: [Kurzbeschreibung]
- **[Datum/Zeit]** - Finaler Upload
- **[Datum/Zeit]** - Finale Validierung (X Fehler, Y Warnungen)

## Fazit

### Zusammenfassung der Änderungen
- Behobene Fehler gesamt: [Anzahl]
- Adressierte Warnungen gesamt: [Anzahl]
- Erfolgsrate: [Prozentsatz]

### Finaler Status
[VALIDE ✓ / HAT FEHLER ✗]

### Empfehlungen
[Basierend auf den Metadaten 2-3 umsetzbare Empfehlungen geben:]
1. [Empfehlung 1]
2. [Empfehlung 2]
3. [Empfehlung 3]

---

**Bericht erstellt:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Snapshot ID:** {snapshot_id}  
**Berichtstyp:** Automatisch generierter LLM-Prüfbericht

---

**WICHTIGE ANWEISUNGEN:**
1. Extrahiere ALLE Informationen aus den bereitgestellten Metadaten
2. Sei präzise mit Daten, Zeitstempeln und Werten
3. Verwende Tabellen wo sinnvoll für bessere Lesbarkeit
4. Hebe kritische Probleme mit korrekter Formatierung hervor (⚠️, ✓, ✗)
5. Wahre durchgehend professionellen Ton
6. Beziehe ALLE Iterationen aus den Metadaten ein
7. Berechne Statistiken korrekt (Fehleranzahl, Erfolgsraten)
8. Erfinde KEINE Informationen - verwende nur was in den Metadaten steht
9. Formatiere Code/Pfade mit Backticks
10. Verwende Markdown-Formatierung für Überschriften, Listen, Hervorhebungen

Erstelle jetzt den vollständigen Prüfbericht."""

    print("Generating audit report with LLM...")
    
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        messages=[
            {"role": "system", "content": "Du bist ein professioneller technischer Auditor, spezialisiert auf Datenqualität und Compliance-Berichterstattung. Antworte immer auf Deutsch."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=4000
    )
    
    report_content = response.choices[0].message.content
    
    # Extract token usage
    token_usage = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens
    }
    
    return report_content, token_usage


def save_audit_report(snapshot_id, report_content, token_usage):
    """Save audit report to snapshot folder"""
    snapshot_dir = Path(__file__).parent.parent / "Snapshots" / snapshot_id
    
    # Save as Markdown
    report_file = snapshot_dir / "audit-report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"✓ Audit report saved to: {report_file}")
    
    # Save token usage stats
    stats_file = snapshot_dir / "audit-report-stats.json"
    stats = {
        "generated_at": datetime.now().isoformat(),
        "snapshot_id": snapshot_id,
        "token_usage": token_usage,
        "report_file": str(report_file)
    }
    
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    
    print(f"✓ Report statistics saved to: {stats_file}")
    
    return report_file


def main():
    """Main function"""
    print("=" * 70)
    print("AUDIT REPORT GENERATOR")
    print("=" * 70)
    print()
    
    # Load snapshot ID
    snapshot_id = load_snapshot_id()
    print(f"Snapshot ID: {snapshot_id}")
    print()
    
    # Load metadata
    print("Loading metadata...")
    metadata_content = load_metadata(snapshot_id)
    print(f"✓ Metadata loaded ({len(metadata_content)} characters)")
    
    # Load upload results (optional)
    upload_results = load_upload_results(snapshot_id)
    if upload_results:
        print(f"✓ Upload results loaded")
    else:
        print("  (No upload-result.json found - skipping)")
    print()
    
    # Generate report with LLM
    report_content, token_usage = generate_audit_report_with_llm(metadata_content, upload_results, snapshot_id)
    print()
    print(f"✓ Report generated")
    print(f"  Token usage:")
    print(f"    - Prompt: {token_usage['prompt_tokens']}")
    print(f"    - Completion: {token_usage['completion_tokens']}")
    print(f"    - Total: {token_usage['total_tokens']}")
    print()
    
    # Save report
    report_file = save_audit_report(snapshot_id, report_content, token_usage)
    print()
    
    print("=" * 70)
    print("✓ AUDIT REPORT GENERATION COMPLETE")
    print("=" * 70)
    print()
    print(f"Report: {report_file}")
    print()


if __name__ == "__main__":
    main()
