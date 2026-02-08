"""
BaseAgent - Basis-Klasse für alle Agenten
"""
from typing import Dict, Optional
from agent_config import CHAT_HISTORY_CONFIG


class BaseAgent:
    """Basis-Klasse für alle Agenten"""
    
    def __init__(
        self,
        name: str,
        system_prompt: str,
        description: Optional[str] = None,
        routing_description: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        max_history_pairs: Optional[int] = None
    ):
        """
        Args:
            name: Name des Agenten
            system_prompt: System-Prompt für den Agenten
            description: Kurze Beschreibung des Agenten (für Logging/Docs)
            routing_description: Optimierte Beschreibung für Orchestrator-Routing (falls None: nutzt description)
            temperature: LLM Temperature (0.0-1.0)
            max_tokens: Maximale Output-Tokens (None = default)
            max_history_pairs: Anzahl Message-Paare im Kontext (None = alle)
        """
        self.name = name
        self.system_prompt = system_prompt
        self.description = description or f"{name} Agent"
        self.routing_description = routing_description or self.description
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_history_pairs = max_history_pairs
    
    def execute(self, user_input: str, context: Dict = None) -> Dict:
        """
        Führt den Agenten aus
        
        Args:
            user_input: Benutzereingabe
            context: Kontext-Dictionary mit chat_history, etc.
        
        Returns:
            {"response": str, "metadata": dict}
        """
        raise NotImplementedError(f"Agent {self.name} muss execute() implementieren")
    
    def _get_chat_history(self, context: Dict) -> list:
        """Extrahiert Chat-History mit Limit (Messages + Zeichen pro Message)"""
        if not context:
            return []
        
        history = context.get("chat_history", [])
        
        # 1. Limitiere Anzahl Messages
        if self.max_history_pairs is not None:
            max_messages = self.max_history_pairs * 2
            if len(history) > max_messages:
                history = history[-max_messages:]
        
        # 2. Limitiere Zeichen pro Message (nutzt zentrale Config)
        max_chars = CHAT_HISTORY_CONFIG.get("max_message_chars", 1000)
        truncated_history = []
        for msg in history:
            truncated_msg = msg.copy()
            if len(truncated_msg.get("content", "")) > max_chars:
                truncated_msg["content"] = truncated_msg["content"][:max_chars]
            truncated_history.append(truncated_msg)
        
        return truncated_history
