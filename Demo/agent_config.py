"""
Agent Configuration
Zentrale Konfiguration für alle Agenten
"""

# ========== AGENT KONFIGURATION ==========

# ZENTRALE CHAT-HISTORIE KONFIGURATION
# Diese Einstellung gilt für ALLE Agenten (Chat, RAG, SP, Orchestrator)
CHAT_HISTORY_CONFIG = {
    "max_history_pairs": 5,          # Anzahl User+Assistant Paare (5 Paare = 10 Messages)
    "max_planning_pairs": 2,         # Anzahl Paare für Orchestrator Planning (2 Paare = 4 Messages)
    "max_message_chars": 1000,       # Maximale Zeichen pro Message für alle LLM-Calls (Token-Kontrolle)
    "max_tokens": 700                # Maximale Output-Tokens für LLM-Antworten (Chat, RAG)
}

# ========== SYSTEM PROMPTS ==========
# Default System Prompt für Chat Agent
# HINWEIS: Minimaler Prompt - Persönlichkeit/Ton kommt vom Orchestrator
DEFAULT_CHAT_SYSTEM_PROMPT = """
Du bist ein Wissensbasis-Assistent für allgemeine Fragen.
Beantworte Fragen sachlich und direkt.

Du hast KEINEN Zugriff auf Firmendokumente oder Wissensdatenbanken.
Bei Fragen zu internen Dokumenten: Verweise auf die Dokumenten-Suche.

WICHTIG: Deine Antworten werden vom Orchestrator interpretiert und aufbereitet.
Generiere NUR die sachliche Kern-Antwort ohne Begrüßungen oder Persönlichkeit.
"""

# Default System Prompt für RAG Agent
# HINWEIS: Namen/Ton kommen vom Orchestrator, hier nur RAG-Logik
DEFAULT_RAG_SYSTEM_PROMPT = """
Du bist ein spezialisierter Wissensbasis-Assistent für Produktionsplanung.
Du hast Zugriff auf interne Dokumente, Richtlinien und technische Spezifikationen.

WICHTIG:
1. Beantworte Fragen NUR basierend auf dem bereitgestellten Kontext aus der Wissensbasis
2. Wenn der Kontext die Frage nicht beantwortet, sage klar: 'Diese Information ist nicht in den vorliegenden Dokumenten enthalten'
3. Gib IMMER die relevanten Quellen an
4. Deine Antworten werden vom Orchestration Agent im Gesprächskontext interpretiert
5. Fokussiere dich auf die faktische Extraktion aus den Dokumenten
6. Der Orchestrator wird deine Antwort für den User aufbereiten
"""

# Default System Prompt für Orchestration Agent (bei Interpretation)
# ZENTRALE STELLE: Hier Persönlichkeit, Namen, Ton konfigurieren!
DEFAULT_ORCHESTRATOR_INTERPRETATION_PROMPT = """
Du bist Juliet, ein hilfreicher KI-Assistent für Smart Planning und Produktionsplanung.
Der User heißt Ahmad. dein name ist Juliet.

WICHTIGE SNAPSHOT-VALIDIERUNGS-REGELN:
1. Ein Snapshot ist "fehlerfrei" NUR wenn ERROR-Count = 0 (Warnings sind erlaubt)
2. Der Server akzeptiert Snapshots mit Warnings als valide (isSuccessfullyValidated: true)
3. Wenn User fragt "gibt es Probleme?" → Berichte sowohl ERRORs als auch WARNINGs transparent
4. Wenn User sagt "korrigiere das" → Frage nach: "Soll ich nur ERRORs beheben oder auch WARNINGs?"
5. Standardmäßig korrigiere NUR ERRORs (bis isSuccessfullyValidated: true)
6. Bei WARNINGs: Erkläre dass sie nicht kritisch sind, aber erwähne sie trotzdem

Deine Hauptaufgabe: Ergebnisse der Sub-Agenten (Chat, RAG, SP_Agent) im Kontext 
der Konversation interpretieren und benutzerfreundlich aufbereiten.

WICHTIGE REGELN FÜR DEINE ANTWORTEN:

1. KEINE TECHNISCHEN PFADE:
   - Gib NIEMALS vollständige Dateipfade aus wie "C:\\Projektarbeiten\\..." oder "C:/Users/..."
   - Erwähne nur Dateinamen oder IDs: "Snapshot abc-123" statt "C:\\...\\abc-123"
   - Bei Dateien: Nur Name ohne Pfad

2. BENUTZERFREUNDLICHKEIT:
   - Schreibe in natürlicher, gesprächiger Sprache
   - Maximal 4-5 Sätze pro Antwort
   - Vermeide JSON, technische Outputs oder rohe Daten

3. KONTEXT NUTZEN:
   - Beziehe dich auf den bisherigen Gesprächsverlauf
   - **WICHTIG: Extrahiere Informationen aus früheren Antworten (z.B. Snapshot-IDs)**
   - Verwende Pronomen wenn klar ("Der Snapshot", nicht "Snapshot abc-123" jedes Mal)
   - Antworte direkt auf die User-Frage
   - Wenn User sagt "den von vorhin" oder "den Snapshot" → Nutze die ID aus der Historie

4. AGENT-SPEZIFISCH:
   - Bei SP_Agent: Fokus auf IDs, Status, nächste Schritte
   - Bei RAG_Agent: Betone Quellen, aber nicht zu technisch
   - Bei Chat_Agent: Natürlich und persönlich

5. FEHLER-HANDLING:
   - Bei Fehlern: Erkläre was schiefging, nicht wie (technisch)
   - Schlage nächste Schritte vor
   - Bleibe konstruktiv und hilfreich
"""

# Chat Agent Einstellungen
CHAT_AGENT_CONFIG = {
    "temperature": 0.7,
    "max_tokens": CHAT_HISTORY_CONFIG["max_tokens"],
    "max_history_pairs": CHAT_HISTORY_CONFIG["max_history_pairs"],
    "system_prompt": DEFAULT_CHAT_SYSTEM_PROMPT,
    "description": "General conversation agent",
    "routing_description": """Use for general questions, greetings, explanations, and conversations that do NOT require company documents.

Use when:
- General greetings (like "Hallo", "Wie geht's?")
- General knowledge questions (like "Was ist KI?", "Erkläre mir...")
- Explanations of general concepts
- Small talk and casual conversation

Do NOT use when:
- User asks about company policies, procedures, or documentation
- Questions about internal processes or technical specifications
- User needs specific information from company documents"""
}

# RAG Agent Einstellungen
RAG_AGENT_CONFIG = {
    "temperature": 0.3,          # Faktentreu für Dokumenten-basierte Antworten
    "max_tokens": CHAT_HISTORY_CONFIG["max_tokens"],
    "max_history_pairs": CHAT_HISTORY_CONFIG["max_history_pairs"],
    "top_k": 8,                  # 8 Retrieval-Ergebnisse
    "min_score": 0.5,            # Minimaler Relevanz-Score
    "system_prompt": DEFAULT_RAG_SYSTEM_PROMPT,
    "description": "Document search and retrieval agent",
    "routing_description": """Use for questions about INTERNAL company documents, policies, procedures, and technical specifications.

Use when:
- User asks about company policies or guidelines ("Was steht in Richtlinie X?", "Wie lautet die Policy für Y?")
- Questions about internal processes ("Wie läuft der Prozess für Z?", "Zeige mir das SOP für...")
- Technical specifications or documentation ("Was sind die technischen Anforderungen?", "Welche Spezifikationen...?")
- User explicitly mentions documents, policies, procedures, or guidelines

Do NOT use when:
- General questions that don't require specific company documentation
- Greetings or small talk
- General knowledge questions
"""
}

# Orchestrator Einstellungen
ORCHESTRATOR_CONFIG = {
    "router_temperature": 0,     # Deterministisches Routing
    "router_max_tokens": 200,    # Kurze Router-Antworten
    "interpretation_system_prompt": DEFAULT_ORCHESTRATOR_INTERPRETATION_PROMPT  # System Prompt für Interpretation
}

# SP Agent Einstellungen
SP_AGENT_CONFIG = {
    "description": "Smart Planning Agent - Snapshot-Verwaltung und automatische Fehlerkorrektur",
    "routing_description": """Smart Planning Agent - Snapshot-Verwaltung, Validierung und automatische Fehlerkorrektur.

Zuständig für alle Smart Planning Anfragen:
- Snapshots erstellen, validieren, korrigieren, umbenennen
- Fehleranalyse und automatische Korrekturen (LLM-gestützt)
- Audit-Reports generieren
- Pipeline-Workflows (full_correction, correction_from_validation, analyze_only)

Trigger-Keywords: 'Snapshot', 'validieren', 'korrigieren', 'Fehler', 'Bericht', 'erstellen', 'analysieren'

Verfügbare Tools:
- create_snapshot, validate_snapshot, identify_snapshot
- identify_error_llm, generate_correction_llm, apply_correction
- update_snapshot, generate_audit_report, rename_snapshot

Verfügbare Pipelines:
- full_correction: Kompletter Workflow (Validierung → Korrektur → Upload)
- correction_from_validation: Korrektur bei existierenden Validierungsdaten
- analyze_only: Nur Analyse ohne Änderungen"""
}

# ========== GLOBALE EINSTELLUNGEN ==========
# Wird von main.py verwendet

# Maximale Messages im Hauptloop - automatisch synchronisiert mit CHAT_HISTORY_CONFIG
MAX_HISTORY_MESSAGES = CHAT_HISTORY_CONFIG["max_history_pairs"] * 2  # 5 Paare = 10 Messages

