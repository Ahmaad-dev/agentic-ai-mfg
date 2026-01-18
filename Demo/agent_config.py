"""
Agent Configuration
Zentrale Konfiguration für alle Agenten
"""

# ========== AGENT KONFIGURATION ==========

# Gemeinsame Basis-Einstellungen für alle Agenten
BASE_AGENT_CONFIG = {
    "max_history_pairs": 5,      # Einheitlich: Letzte 10 Messages (5 Paare)
    "max_tokens": 700            # Einheitlich: Maximale Output-Tokens
}

# ========== SYSTEM PROMPTS ==========
# Alle System-Prompts zentral hier definiert

# Default System Prompt für Chat Agent
DEFAULT_CHAT_SYSTEM_PROMPT = """
Du bist ein hilfreicher Chat-Assistent. Deine Name lautet Juliet! Und mein Name ist Ahmad.
Du beantwortest allgemeine Fragen, hilfst bei Erklärungen und führst normale Konversationen.
Du hast KEINEN Zugriff auf interne Firmendokumente oder Wissensdatenbanken.
Antworte natürlich, freundlich und präzise.
"""

# Default System Prompt für RAG Agent
DEFAULT_RAG_SYSTEM_PROMPT = """
Du bist ein spezialisierter Wissensbasis-Assistent für Produktionsumgebungen.
Du hast Zugriff auf interne Dokumente, Richtlinien und technische Spezifikationen.
WICHTIG: Beantworte Fragen NUR basierend auf dem bereitgestellten Kontext aus der Wissensbasis.
Wenn der Kontext die Frage nicht beantwortet, sage klar: 'Diese Information ist nicht in den vorliegenden Dokumenten enthalten.'
Gib IMMER die Quellen deiner Informationen an.
"""

# Chat Agent Einstellungen
CHAT_AGENT_CONFIG = {
    "temperature": 0.7,
    "max_tokens": BASE_AGENT_CONFIG["max_tokens"],
    "max_history_pairs": BASE_AGENT_CONFIG["max_history_pairs"],
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
    "max_tokens": BASE_AGENT_CONFIG["max_tokens"],
    "max_history_pairs": BASE_AGENT_CONFIG["max_history_pairs"],
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
    "router_max_tokens": 200     # Kurze Router-Antworten
}

# Chat History (global)
MAX_HISTORY_MESSAGES = 10  # Maximale Messages im Hauptloop (muss gerade sein)

