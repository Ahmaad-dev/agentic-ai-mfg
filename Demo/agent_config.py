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
    "temperature": 0.7,          # Kreativ für natürliche Konversation
    "max_tokens": BASE_AGENT_CONFIG["max_tokens"],
    "max_history_pairs": BASE_AGENT_CONFIG["max_history_pairs"],
    "system_prompt": DEFAULT_CHAT_SYSTEM_PROMPT  # Nutzt Default aus agent_config.py
}

# RAG Agent Einstellungen
RAG_AGENT_CONFIG = {
    "temperature": 0.3,          # Faktentreu für Dokumenten-basierte Antworten
    "max_tokens": BASE_AGENT_CONFIG["max_tokens"],
    "max_history_pairs": BASE_AGENT_CONFIG["max_history_pairs"],
    "top_k": 8,                  # 8 Retrieval-Ergebnisse
    "min_score": 0.5,            # Minimaler Relevanz-Score
    "system_prompt": DEFAULT_RAG_SYSTEM_PROMPT  # Nutzt Default aus agent_config.py
}

# Orchestrator Einstellungen
ORCHESTRATOR_CONFIG = {
    "router_temperature": 0,     # Deterministisches Routing
    "router_max_tokens": 200     # Kurze Router-Antworten
}

# Chat History (global)
MAX_HISTORY_MESSAGES = 10  # Maximale Messages im Hauptloop (muss gerade sein)

