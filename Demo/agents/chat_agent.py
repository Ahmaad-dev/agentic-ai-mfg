"""
ChatAgent - Allgemeine Konversation ohne Wissensbasis
"""
import json
import logging
from typing import Dict, Optional
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ChatAgent(BaseAgent):
    """Chat Agent - Allgemeine Konversation ohne Wissensbasis"""
    
    def __init__(
        self,
        aoai_client,
        model_name: str,
        system_prompt: Optional[str] = None,
        description: Optional[str] = None,
        routing_description: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 500,
        max_history_pairs: int = 5
    ):
        """
        Args:
            aoai_client: Azure OpenAI Client
            model_name: Deployment-Name des Modells
            system_prompt: Custom System-Prompt (None = default)
            description: Kurze Beschreibung (für Logging)
            routing_description: Routing-optimierte Beschreibung (für Orchestrator)
            temperature: LLM Temperature (default: 0.7 für Kreativität)
            max_tokens: Max Output-Tokens (default: 500)
            max_history_pairs: Anzahl Message-Paare (default: 5 = 10 Messages)
        """
        super().__init__(
            name="Chat",
            system_prompt=system_prompt,
            description=description,
            routing_description=routing_description,
            temperature=temperature,
            max_tokens=max_tokens,
            max_history_pairs=max_history_pairs
        )
        
        self.aoai_client = aoai_client
        self.model_name = model_name
    
    def execute(self, user_input: str, context: Dict = None) -> Dict:
        """Führt Chat-Konversation durch"""
        logger.info(f"[{self.name} Agent] Verarbeite Anfrage: {user_input[:100]}")
        
        chat_history = self._get_chat_history(context)
        
        # Prüfe ob Snapshot-Metadaten verfügbar sind
        snapshot_context = ""
        if context and "last_snapshot_metadata" in context:
            import json
            metadata = context["last_snapshot_metadata"]
            snapshot_context = f"\n\nVERFÜGBARE SNAPSHOT-INFORMATIONEN (nutze diese um User-Fragen zu beantworten):\n{json.dumps(metadata, indent=2, ensure_ascii=False)}"
            logger.info(f"[{self.name} Agent] Snapshot-Metadaten verfügbar für Kontext")
        
        messages = [
            {"role": "system", "content": self.system_prompt + snapshot_context},
            *chat_history,
            {"role": "user", "content": user_input}
        ]
        
        try:
            # LLM-Call Parameter vorbereiten
            call_params = {
                "model": self.model_name,
                "messages": messages,
                "temperature": self.temperature
            }
            
            if self.max_tokens is not None:
                call_params["max_tokens"] = self.max_tokens
            
            response = self.aoai_client.chat.completions.create(**call_params)
            
            answer = response.choices[0].message.content
            
            logger.info(
                f"[{self.name} Agent] Antwort generiert "
                f"({len(answer)} Zeichen, Temp={self.temperature}, "
                f"History={len(chat_history)} msgs)"
            )
            
            return {
                "response": answer,  # Rohe LLM-Response
                "metadata": {
                    "agent": self.name,
                    "sources": [],
                    "confidence": "high",
                    "raw_result": True,  # Signal für Orchestrator
                    "config": {
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens,
                        "history_pairs": self.max_history_pairs
                    }
                }
            }
        except Exception as e:
            logger.error(f"[{self.name} Agent] Fehler: {e}")
            return {
                "response": f"Es tut mir leid, es gab einen Fehler bei der Verarbeitung: {str(e)}",
                "metadata": {"agent": self.name, "error": str(e)}
            }
