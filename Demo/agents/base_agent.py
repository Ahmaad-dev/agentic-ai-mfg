"""
BaseAgent - Basis-Klasse für alle Agenten
"""
from typing import Dict, Optional


class BaseAgent:
    """Basis-Klasse für alle Agenten"""
    
    def __init__(
        self,
        name: str,
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        max_history_pairs: Optional[int] = None
    ):
        """
        Args:
            name: Name des Agenten
            system_prompt: System-Prompt für den Agenten
            temperature: LLM Temperature (0.0-1.0)
            max_tokens: Maximale Output-Tokens (None = default)
            max_history_pairs: Anzahl Message-Paare im Kontext (None = alle)
        """
        self.name = name
        self.system_prompt = system_prompt
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
        """Extrahiert Chat-History mit Limit"""
        if not context:
            return []
        
        history = context.get("chat_history", [])
        
        if self.max_history_pairs is None:
            return history
        
        max_messages = self.max_history_pairs * 2
        if len(history) <= max_messages:
            return history
        
        return history[-max_messages:]
