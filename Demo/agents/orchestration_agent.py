"""
OrchestrationAgent - Koordiniert alle Sub-Agenten
"""
import json
import logging
from typing import Dict, List
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class OrchestrationAgent(BaseAgent):
    """Orchestration Agent - Koordiniert alle Sub-Agenten"""
    
    def __init__(
        self,
        aoai_client,
        model_name: str,
        agents: Dict[str, BaseAgent],
        router_temperature: float = 0,
        router_max_tokens: int = 200
    ):
        """
        Args:
            aoai_client: Azure OpenAI Client
            model_name: Deployment-Name des Modells
            agents: Dictionary der verfügbaren Agenten {"chat": ChatAgent, "rag": RAGAgent}
            router_temperature: Temperature für Routing (default: 0 = deterministisch)
            router_max_tokens: Max Tokens für Router-Antwort
        """
        system_prompt = (
            "Du bist der Orchestration Agent eines Multi-Agent-Systems für eine Produktionsumgebung. "
            "Deine Aufgaben:\n"
            "1. Analysiere die User-Anfrage und entscheide, welcher Agent zuständig ist\n"
            "2. Leite die Anfrage an den passenden Agenten weiter\n"
            "3. Bei unklaren Anfragen: Stelle selbst Rückfragen\n"
            "4. Aggregiere und präsentiere die Ergebnisse\n\n"
            "Verfügbare Modi:\n"
            "- Chat Agent: Allgemeine Konversation, Erklärungen, Smalltalk\n"
            "- RAG Agent: Fragen zu internen Dokumenten, Richtlinien, technischen Spezifikationen\n"
            "- Clarify: Unklare Anfragen → Rückfragen stellen\n\n"
            "Entscheide klug und transparent."
        )
        
        super().__init__(
            name="Orchestrator",
            system_prompt=system_prompt,
            temperature=router_temperature
        )
        
        self.aoai_client = aoai_client
        self.model_name = model_name
        self.agents = agents
        self.router_max_tokens = router_max_tokens
    
    def _route_request(self, user_input: str, chat_history: List) -> Dict:
        """Entscheidet, welcher Agent zuständig ist"""
        
        # Kontext-Summary für Router
        context_summary = ""
        if chat_history:
            recent = chat_history[-4:]
            context_summary = "\n\nBISHERIGER KONTEXT:\n"
            for msg in recent:
                role = "User" if msg["role"] == "user" else "Assistant"
                context_summary += f"{role}: {msg['content'][:300]}...\n"
        
        router_prompt = f"""Analysiere die folgende Benutzeranfrage und entscheide, welcher Agent zuständig ist.

{context_summary}

AKTUELLE ANFRAGE: {user_input}

OPTIONEN:
- "chat": Allgemeine Fragen, Smalltalk, Erklärungen (keine Firmendokumente nötig)
- "rag": Fragen zu Firmendokumenten, Richtlinien, technischen Spezifikationen, Prozessen
- "clarify": Anfrage ist unklar, vage oder benötigt mehr Kontext (z.B. "Was?", "Stimmt das?", "Wie meinst du das?")

REGELN:
- Wenn die Anfrage ohne Kontext nicht verstanden werden kann → "clarify"
- Wenn Pronomen ohne Bezug verwendet werden ("das", "es") → prüfe Kontext, sonst "clarify"
- Bei klaren Fragen → "chat" oder "rag"

Antworte NUR mit JSON:
{{
  "agent": "chat" | "rag" | "clarify",
  "reason": "Kurze Begründung",
  "search_query": "Optimierte Query (nur bei rag, sonst null)"
}}"""
        
        try:
            response = self.aoai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "Du bist ein präziser Router. Antworte nur mit JSON."},
                    {"role": "user", "content": router_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.router_max_tokens
            )
            
            output = response.choices[0].message.content.strip()
            
            # JSON bereinigen
            if output.startswith("```json"):
                output = output[7:]
            if output.startswith("```"):
                output = output[3:]
            if output.endswith("```"):
                output = output[:-3]
            
            routing = json.loads(output.strip())
            
            # Validierung
            if "agent" not in routing or routing["agent"] not in ["chat", "rag", "clarify"]:
                raise ValueError(f"Ungültiges Routing: {routing}")
            
            logger.info(f"[{self.name}] Routing: {routing['agent']} - {routing.get('reason', 'N/A')}")
            
            return routing
            
        except Exception as e:
            logger.error(f"[{self.name}] Routing-Fehler: {e}, Fallback zu Chat")
            return {
                "agent": "chat",
                "reason": f"Routing-Fehler, Fallback aktiviert: {str(e)}",
                "search_query": None
            }
    
    def execute(self, user_input: str, context: Dict = None) -> Dict:
        """Orchestriert die Anfrage"""
        logger.info(f"[{self.name}] Orchestriere Anfrage: {user_input[:100]}")
        
        chat_history = context.get("chat_history", []) if context else []
        
        # 1. Routing-Entscheidung
        routing = self._route_request(user_input, chat_history)
        selected_agent_name = routing["agent"]
        
        # 2. Clarify-Route behandeln (Orchestrator selbst stellt Rückfragen)
        if selected_agent_name == "clarify":
            logger.info(f"[{self.name}] Unklare Anfrage erkannt - stelle Rückfragen")
            
            clarify_prompt = (
                f"Die folgende Anfrage ist unklar oder benötigt mehr Kontext:\n\n"
                f"ANFRAGE: {user_input}\n\n"
                f"Stelle 1-2 höfliche, präzise Rückfragen, um die Anfrage zu klären."
            )
            
            messages = [
                {"role": "system", "content": "Du bist ein hilfreicher Assistent, der bei unklaren Anfragen gezielt nachfragt."},
                *chat_history[-4:],
                {"role": "user", "content": clarify_prompt}
            ]
            
            try:
                response = self.aoai_client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.7
                )
                
                clarify_response = response.choices[0].message.content
                
                return {
                    "response": clarify_response,
                    "metadata": {
                        "agent": "clarify",
                        "orchestrator_decision": {
                            "selected_agent": "clarify",
                            "reason": routing.get("reason", "Anfrage benötigt Klärung")
                        }
                    }
                }
            except Exception as e:
                logger.error(f"[{self.name}] Clarify-Fehler: {e}")
                return {
                    "response": "Entschuldigung, ich habe deine Anfrage nicht ganz verstanden. Könntest du das bitte präzisieren?",
                    "metadata": {"agent": "clarify", "error": str(e)}
                }
        
        # 3. Agent ausführen (Chat oder RAG)
        if selected_agent_name not in self.agents:
            logger.error(f"[{self.name}] Unbekannter Agent: {selected_agent_name}")
            return {
                "response": f"Interner Fehler: Agent '{selected_agent_name}' nicht gefunden.",
                "metadata": {"agent": self.name, "error": "unknown_agent"}
            }
        
        selected_agent = self.agents[selected_agent_name]
        
        # Query für RAG optimieren falls vorhanden
        query = routing.get("search_query") or user_input
        
        # 4. Agent ausführen
        result = selected_agent.execute(query, context)
        
        # 5. Metadata erweitern
        result["metadata"]["orchestrator_decision"] = {
            "selected_agent": selected_agent_name,
            "reason": routing.get("reason", "N/A")
        }
        
        logger.info(f"[{self.name}] Anfrage abgeschlossen durch {selected_agent_name} Agent")
        
        return result
