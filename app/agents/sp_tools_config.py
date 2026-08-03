"""
SP_Agent Tools und Pipelines Konfiguration

Dieses Modul enthält alle verfügbaren Smart Planning Tools und Pipelines.
Wird von SP_Agent verwendet für Tool-Ausführung und Pipeline-Orchestrierung.
"""

# Alle verfügbaren Smart Planning Tools
SP_TOOLS = {
    "create_snapshot": {
        "script": "create_snapshot.py",
        "description": "Erstellt einen neuen Snapshot auf dem Smart Planning Server",
        "usage": "Wird verwendet bei: 'Erstelle Snapshot', 'Neuer Snapshot'",
        "output": "Snapshot-ID, Name, Timestamp",
        "dependencies": []
    },
    "download_snapshot": {
        "script": "download_snapshot.py",
        "description": "Lädt einen existierenden Snapshot vom Server herunter (by ID oder Name)",
        "usage": "Wird verwendet bei: 'Hole Snapshot X', 'Lade Snapshot von Server', 'Download Snapshot abc-123'",
        "output": "Lokale Snapshot-Daten, Metadata, snapshot-data.json in Snapshots/{id}/",
        "dependencies": [],
        "requires_identifier": True
    },
    "validate_snapshot": {
        "script": "validate_snapshot.py",
        "description": "Validiert einen Snapshot und zeigt Fehler/Warnungen",
        "usage": "Wird verwendet bei: 'Validiere Snapshot', 'Hat der Snapshot Fehler?'",
        "output": "Validation-Messages (ERROR/WARNING), Status",
        "dependencies": []
    },
    "identify_snapshot": {
        "script": "identify_snapshot.py",
        "description": "Sucht nach spezifischen Werten oder leeren Feldern im Snapshot",
        "usage": "Wird verwendet bei: 'Suche nach ID xyz', 'Finde leere demandId Felder'",
        "output": "Fundstellen mit Kontext, Array-Position, Enriched Context",
        "dependencies": [],
        "modes": {
            "value": "Suche nach konkretem Wert (z.B. 'D830081_005')",
            "empty": "Suche nach leeren Feldern (z.B. --empty demandId)"
        }
    },
    "identify_error_llm": {
        "script": "identify_error_llm.py",
        "description": "LLM analysiert Validierungsfehler und triggert automatisch identify_snapshot",
        "usage": "Wird verwendet bei: 'Analysiere Fehler', erster Schritt der Auto-Korrektur-Pipeline",
        "output": "LLM-Analyse (error_type, search_mode, search_value), last_search_results.json",
        "dependencies": ["validate_snapshot"],
        "creates_iteration": True
    },
    "generate_correction_llm": {
        "script": "generate_correction_llm.py",
        "description": "LLM generiert strukturierte Korrekturvorschläge basierend auf Fehleranalyse",
        "usage": "Wird verwendet bei: Auto-Korrektur-Pipeline nach identify_error_llm",
        "output": "llm_correction_proposal.json mit action, target_path, new_value, reasoning",
        "dependencies": ["identify_error_llm"],
        "uses_iteration": True,
        "recovery_hint": "Falls 'last_search_results.json not found': Führe ZUERST identify_error_llm aus, dann nochmal versuchen"
    },
    "validate_correction_schema_llm": {
        "script": "validate_correction_schema_llm.py",
        "description": "Validiert Korrekturvorschlag gegen Pydantic-Schema (optional, nicht automatisch)",
        "usage": "Wird verwendet bei: Manuelle Schema-Validierung vor apply_correction",
        "output": "Schema-Validierungsstatus, Retry-Versuche bei Fehlern",
        "dependencies": ["generate_correction_llm"],
        "uses_iteration": True,
        "optional": True
    },
    "apply_correction": {
        "script": "apply_correction.py",
        "description": "Wendet LLM-Korrekturvorschlag auf snapshot-data.json an",
        "usage": "Wird verwendet bei: Auto-Korrektur-Pipeline nach generate_correction_llm",
        "output": "Geänderte snapshot-data.json, erweiterte metadata.txt, Backup in iteration-folder",
        "dependencies": ["generate_correction_llm"],
        "uses_iteration": True,
        "modifies_snapshot": True
    },
    "update_snapshot": {
        "script": "update_snapshot.py",
        "description": "Lädt korrigierte Snapshot-Daten auf den Server hoch",
        "usage": "Wird verwendet bei: Nach apply_correction, 'Lade Snapshot hoch'",
        "output": "Server-Response mit isSuccessfullyValidated status, upload-result.json",
        "dependencies": ["apply_correction"]
    },
    "generate_audit_report": {
        "script": "generate_audit_report.py",
        "description": "Generiert professionellen deutschsprachigen Prüfbericht aus metadata.txt",
        "usage": "Wird verwendet bei: 'Erstelle Bericht', 'Generiere Audit-Report'",
        "output": "audit-report.md (Markdown), audit-report-stats.json (Token-Usage)",
        "dependencies": []
    },
    "rename_snapshot": {
        "script": "rename_snapshot.py",
        "description": "Ändert den Namen eines existierenden Snapshots via API",
        "usage": "Wird verwendet bei: 'Ändere Snapshot-Namen', 'Benenne um', 'Setze Namen auf X'",
        "output": "Server-Response mit neuem Namen, RENAME_SUCCESS/RENAME_FAILED",
        "dependencies": [],
        "requires_snapshot_id": True,
        "requires_new_name": True
    }
}

# Vorkonfigurierte Pipelines für komplexe Workflows
SP_PIPELINES = {
    "full_correction": {
        "name": "Vollständige Fehlerkorrektur",
        "steps": [
            "validate_snapshot",
            "identify_error_llm",
            "generate_correction_llm",
            "validate_correction_schema_llm",  # Schema-Validierung vor Anwendung
            "apply_correction",
            "update_snapshot",
            "validate_snapshot"  # Re-validierung
        ],
        "description": "Komplette Pipeline: Validierung → Fehleranalyse → Korrektur-Generierung → Schema-Check → Anwendung → Upload → Re-Validierung"
    },
    "correction_from_validation": {
        "name": "Korrektur bei existierender Validierung",
        "steps": [
            "identify_error_llm",
            "generate_correction_llm",
            "validate_correction_schema_llm",  # Schema-Validierung vor Anwendung
            "apply_correction",
            "update_snapshot",
            "validate_snapshot"  # Re-validierung
        ],
        "description": "Startet bei existierenden Validierungsdaten: Fehleranalyse → Korrektur → Schema-Check → Anwendung → Upload → Re-Validierung"
    },
    "analyze_only": {
        "name": "Nur Analyse (keine Änderungen)",
        "steps": [
            "validate_snapshot",
            "identify_error_llm",
            "generate_correction_llm",
            "validate_correction_schema_llm"  # Schema-Check auch bei Analyse
        ],
        "description": "Analysiert Fehler, generiert und validiert Vorschläge ohne Snapshot zu ändern"
    },
    "apply_and_upload": {
        "name": "Korrektur anwenden und hochladen",
        "steps": [
            "apply_correction",
            "update_snapshot",
            "validate_snapshot"
        ],
        "description": "Wendet existierenden Korrekturvorschlag an und lädt hoch (Schema-Check übersprungen)"
    }
}
