import os
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

load_dotenv()

# ========== KONFIGURATION ==========
# RAG Retrieval Einstellungen
RAG_TOP_K = 10
RAG_MIN_SCORE = 0.5

# Router Einstellungen
ROUTER_TEMPERATURE = 0
ROUTER_MAX_TOKENS = 200

# Chat History
MAX_HISTORY_MESSAGES = 10
# ===================================

# Logging einrichten
logs_dir = Path(__file__).parent / "logs"
logs_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(
            logs_dir / f'multiagent_{datetime.now().strftime("%Y%m%d")}.log',
            encoding='utf-8'
        )
    ]
)
logger = logging.getLogger(__name__)

def must_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing env var: {name}")
    return v

aoai = AzureOpenAI(
    azure_endpoint=must_env("AZURE_OPENAI_ENDPOINT"),
    api_key=must_env("AZURE_OPENAI_KEY"),
    api_version=must_env("AZURE_OPENAI_API_VERSION")
)

deployment_name = must_env("AZURE_OPENAI_DEPLOYMENT")
emb_deployment = must_env("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT")

search = SearchClient(
    endpoint=must_env("AZURE_SEARCH_ENDPOINT"),
    index_name=must_env("AZURE_SEARCH_INDEX"),
    credential=AzureKeyCredential(must_env("AZURE_SEARCH_ADMIN_KEY"))
)


# ========== AGENT CLASSES ==========

class BaseAgent:
    """Basis-Klasse für alle Agenten"""
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
    
    def execute(self, user_input: str, context: Dict = None) -> Dict:
        """
        Führt den Agenten aus
        Returns: {"response": str, "metadata": dict}
        """
        raise NotImplementedError


class ChatAgent(BaseAgent):
    """Chat Agent - Allgemeine Konversation ohne Wissensbasis"""
    
    def __init__(self):
        system_prompt = (
            "Du bist ein hilfreicher Chat-Assistent. "
            "Du beantwortest allgemeine Fragen, hilfst bei Erklärungen und führst normale Konversationen. "
            "Du hast KEINEN Zugriff auf interne Firmendokumente oder Wissensdatenbanken. "
            "Antworte natürlich, freundlich und präzise."
        )
        super().__init__("Chat", system_prompt)
    
    def execute(self, user_input: str, context: Dict = None) -> Dict:
        """Führt Chat-Konversation durch"""
        logger.info(f"[{self.name} Agent] Verarbeite Anfrage: {user_input[:100]}")
        
        chat_history = context.get("chat_history", []) if context else []
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            *chat_history,
            {"role": "user", "content": user_input}
        ]
        
        try:
            response = aoai.chat.completions.create(
                model=deployment_name,
                messages=messages,
                temperature=0.7
            )
            
            answer = response.choices[0].message.content
            
            logger.info(f"[{self.name} Agent] Antwort generiert ({len(answer)} Zeichen)")
            
            return {
                "response": answer,
                "metadata": {
                    "agent": self.name,
                    "sources": [],
                    "confidence": "high"
                }
            }
        except Exception as e:
            logger.error(f"[{self.name} Agent] Fehler: {e}")
            return {
                "response": f"Es tut mir leid, es gab einen Fehler bei der Verarbeitung: {str(e)}",
                "metadata": {"agent": self.name, "error": str(e)}
            }


class RAGAgent(BaseAgent):
    """RAG Agent - Wissensbasis-gestützte Antworten"""
    
    def __init__(self):
        system_prompt = (
            "Du bist ein spezialisierter Wissensbasis-Assistent für Produktionsumgebungen. "
            "Du hast Zugriff auf interne Dokumente, Richtlinien und technische Spezifikationen. "
            "WICHTIG: Beantworte Fragen NUR basierend auf dem bereitgestellten Kontext aus der Wissensbasis. "
            "Wenn der Kontext die Frage nicht beantwortet, sage klar: 'Diese Information ist nicht in den vorliegenden Dokumenten enthalten.' "
            "Gib IMMER die Quellen deiner Informationen an."
        )
        super().__init__("RAG", system_prompt)
    
    def _embed(self, text: str):
        """Erstellt Embedding für Text"""
        try:
            r = aoai.embeddings.create(model=emb_deployment, input=text)
            return r.data[0].embedding
        except Exception as e:
            logger.error(f"[{self.name} Agent] Embedding-Fehler: {e}")
            return None
    
    def _retrieve_context(self, query: str) -> Tuple[str, List[str], float, bool]:
        """Sucht relevante Dokumente"""
        try:
            qv = self._embed(query)
            if qv is None:
                return "", [], 0.0, False

            vector_query = VectorizedQuery(
                vector=qv,
                k_nearest_neighbors=RAG_TOP_K,
                fields="contentVector"
            )

            results = search.search(
                search_text="",
                vector_queries=[vector_query],
                select=["title", "source", "content", "page"]
            )

            chunks = []
            sources = []
            scores = []
            
            for r in results:
                score = r.get("@search.score", 0.0)
                scores.append(score)
                
                if score >= RAG_MIN_SCORE:
                    title = r.get("title", "")
                    source = r.get("source", "")
                    content = r.get("content", "")
                    page = r.get("page")
                    
                    chunks.append(f"- {title} ({source}): {content}")
                    
                    if source:
                        source_ref = f"{source} (Seite {page})" if page else source
                        sources.append(source_ref)
            
            max_score = max(scores) if scores else 0.0
            has_relevant_results = len(chunks) > 0
            
            if not has_relevant_results:
                logger.warning(f"[{self.name} Agent] Keine Ergebnisse über Threshold {RAG_MIN_SCORE} (Max-Score: {max_score:.3f})")
            else:
                logger.info(f"[{self.name} Agent] Relevanz-Score: {max_score:.3f} ({len(chunks)} Ergebnisse)")
            
            return "\n".join(chunks), sorted(set(sources)), max_score, has_relevant_results
            
        except Exception as e:
            logger.error(f"[{self.name} Agent] Suchfehler: {e}")
            return "", [], 0.0, False
    
    def execute(self, user_input: str, context: Dict = None) -> Dict:
        """Führt RAG-basierte Antwort durch"""
        logger.info(f"[{self.name} Agent] Verarbeite Anfrage: {user_input[:100]}")
        
        # Retrieval durchführen
        doc_context, sources, relevance_score, has_relevant = self._retrieve_context(user_input)
        
        if not has_relevant:
            logger.info(f"[{self.name} Agent] Keine relevanten Dokumente gefunden (Score: {relevance_score:.3f})")
            return {
                "response": (
                    "Ich konnte in den vorliegenden Dokumenten keine ausreichend relevanten Informationen zu deiner Frage finden. "
                    "Könntest du die Frage präzisieren oder anders formulieren?"
                ),
                "metadata": {
                    "agent": self.name,
                    "sources": [],
                    "relevance_score": relevance_score,
                    "retrieval_success": False
                }
            }
        
        # Antwort mit Kontext generieren
        chat_history = context.get("chat_history", []) if context else []
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            *chat_history[-4:],  # Nur letzte 2 Paare für RAG
            {
                "role": "user",
                "content": (
                    f"KONTEXT AUS WISSENSBASIS:\n{doc_context}\n\n"
                    f"---\n\n"
                    f"FRAGE: {user_input}\n\n"
                    f"Beantworte die Frage basierend auf dem Kontext. Zitiere die relevanten Quellen."
                )
            }
        ]
        
        try:
            response = aoai.chat.completions.create(
                model=deployment_name,
                messages=messages,
                temperature=0.3  # Niedrigere Temperature für faktentreue
            )
            
            answer = response.choices[0].message.content
            
            logger.info(f"[{self.name} Agent] Antwort generiert mit {len(sources)} Quellen")
            
            return {
                "response": answer,
                "metadata": {
                    "agent": self.name,
                    "sources": sources,
                    "relevance_score": relevance_score,
                    "retrieval_success": True
                }
            }
        except Exception as e:
            logger.error(f"[{self.name} Agent] Fehler: {e}")
            return {
                "response": f"Es gab einen Fehler bei der Verarbeitung: {str(e)}",
                "metadata": {"agent": self.name, "error": str(e)}
            }


class OrchestrationAgent(BaseAgent):
    """Orchestration Agent - Koordiniert alle Sub-Agenten"""
    
    def __init__(self, agents: Dict[str, BaseAgent]):
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
        super().__init__("Orchestrator", system_prompt)
        self.agents = agents
    
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
            response = aoai.chat.completions.create(
                model=deployment_name,
                messages=[
                    {"role": "system", "content": "Du bist ein präziser Router. Antworte nur mit JSON."},
                    {"role": "user", "content": router_prompt}
                ],
                temperature=ROUTER_TEMPERATURE,
                max_tokens=ROUTER_MAX_TOKENS
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
                response = aoai.chat.completions.create(
                    model=deployment_name,
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
        
        # 4. Metadata erweitern
        result["metadata"]["orchestrator_decision"] = {
            "selected_agent": selected_agent_name,
            "reason": routing.get("reason", "N/A")
        }
        
        logger.info(f"[{self.name}] Anfrage abgeschlossen durch {selected_agent_name} Agent")
        
        return result


# ========== HAUPTPROGRAMM ==========

def get_recent_messages(messages: List, max_pairs: int = 5) -> List:
    """Behält nur die letzten N Nachrichten-Paare"""
    max_messages = max_pairs * 2
    if len(messages) <= max_messages:
        return messages
    return messages[-max_messages:]


def main():
    """Hauptprogramm"""
    
    # Agenten initialisieren
    chat_agent = ChatAgent()
    rag_agent = RAGAgent()
    
    agents = {
        "chat": chat_agent,
        "rag": rag_agent
    }
    
    orchestrator = OrchestrationAgent(agents)
    
    # Chat-Loop
    messages = []
    
    print("=" * 60)
    print("  Multi-Agent System gestartet!")
    print("=" * 60)
    print(f"  Orchestrator: {orchestrator.name}")
    print(f"  Verfügbare Agenten: {', '.join(agents.keys())}")
    print("=" * 60)
    print("  Eingabe 'exit' zum Beenden\n")
    
    while True:
        user_input = input("Du: ")
        if user_input.lower() in ["exit", "quit", "beenden"]:
            print("Chat beendet.")
            break
        
        logger.info(f"User: {user_input}")
        
        # Kontext vorbereiten
        recent_history = get_recent_messages(messages, max_pairs=5)
        context = {"chat_history": recent_history}
        
        # Orchestrator ausführen
        result = orchestrator.execute(user_input, context)
        
        # Antwort extrahieren
        response = result["response"]
        metadata = result["metadata"]
        
        # Historie aktualisieren
        messages.append({"role": "user", "content": user_input})
        messages.append({"role": "assistant", "content": response})
        
        # Ausgabe formatieren
        agent_name = metadata.get("orchestrator_decision", {}).get("selected_agent", "unknown")
        
        if agent_name == "clarify":
            agent_label = "Rückfrage"
        else:
            agent_label = agent_name.upper()
        
        print(f"\n[{agent_label}] Assistent: {response}\n")
        
        # Quellen ausgeben falls vorhanden
        if metadata.get("sources"):
            print("📚 Quellen:", ", ".join(metadata["sources"]), "\n")
        
        # Debug-Info (optional)
        if metadata.get("orchestrator_decision"):
            reason = metadata["orchestrator_decision"].get("reason", "N/A")
            logger.info(f"Routing-Begründung: {reason}")


if __name__ == "__main__":
    main()
