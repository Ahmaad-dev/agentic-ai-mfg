"""
Multi-Agent System für Produktionsumgebungen
Modulare Architektur mit Chat Agent, RAG Agent und Orchestrator
"""
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

# Agent-Imports
from agents import ChatAgent, RAGAgent, OrchestrationAgent
from agent_config import (
    CHAT_AGENT_CONFIG,
    RAG_AGENT_CONFIG,
    ORCHESTRATOR_CONFIG,
    MAX_HISTORY_MESSAGES
)

load_dotenv()

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
    """Hilfsfunktion: Lade Environment Variable oder raise Error"""
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing env var: {name}")
    return v


def get_recent_messages(messages: List, max_pairs: int = 5) -> List:
    """Behält nur die letzten N Nachrichten-Paare"""
    max_messages = max_pairs * 2
    if len(messages) <= max_messages:
        return messages
    return messages[-max_messages:]


def initialize_clients():
    """Initialisiert Azure OpenAI und Search Clients"""
    # Chat Agent Client
    aoai_chat = AzureOpenAI(
        azure_endpoint=must_env("AZURE_OPENAI_CHAT_ENDPOINT"),
        api_key=must_env("AZURE_OPENAI_CHAT_KEY"),
        api_version=must_env("AZURE_OPENAI_CHAT_API_VERSION")
    )
    
    # RAG Agent Client
    aoai_rag = AzureOpenAI(
        azure_endpoint=must_env("AZURE_OPENAI_RAG_ENDPOINT"),
        api_key=must_env("AZURE_OPENAI_RAG_KEY"),
        api_version=must_env("AZURE_OPENAI_RAG_API_VERSION")
    )
    
    # Orchestration Agent Client
    aoai_orchestration = AzureOpenAI(
        azure_endpoint=must_env("AZURE_OPENAI_ORCHESTRATION_ENDPOINT"),
        api_key=must_env("AZURE_OPENAI_ORCHESTRATION_KEY"),
        api_version=must_env("AZURE_OPENAI_ORCHESTRATION_API_VERSION")
    )

    # Search Client (shared)
    search = SearchClient(
        endpoint=must_env("AZURE_SEARCH_ENDPOINT"),
        index_name=must_env("AZURE_SEARCH_INDEX"),
        credential=AzureKeyCredential(must_env("AZURE_SEARCH_ADMIN_KEY"))
    )
    
    return aoai_chat, aoai_rag, aoai_orchestration, search


def initialize_agents(aoai_chat, aoai_rag, aoai_orchestration, search):
    """Initialisiert alle Agenten mit Konfiguration"""
    # Deployment-Namen direkt aus ENV laden
    chat_model = must_env("AZURE_OPENAI_CHAT_DEPLOYMENT")
    rag_model = must_env("AZURE_OPENAI_RAG_DEPLOYMENT")
    orchestrator_model = must_env("AZURE_OPENAI_ORCHESTRATION_DEPLOYMENT")
    embeddings_deployment = must_env("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT")
    
    # Chat Agent initialisieren (mit eigenem Client)
    chat_agent = ChatAgent(
        aoai_client=aoai_chat,
        model_name=chat_model,
        **CHAT_AGENT_CONFIG  # Unpacks alle Config-Parameter
    )
    logger.info(f"Chat Agent initialisiert: Model={chat_model}, Temp={chat_agent.temperature}, MaxTokens={chat_agent.max_tokens}, HistoryPairs={chat_agent.max_history_pairs}")
    
    # RAG Agent initialisieren (mit eigenem Client)
    rag_agent = RAGAgent(
        aoai_client=aoai_rag,
        model_name=rag_model,
        emb_model_name=embeddings_deployment,
        search_client=search,
        **RAG_AGENT_CONFIG  # Unpacks alle Config-Parameter
    )
    logger.info(f"RAG Agent initialisiert: Model={rag_model}, Embeddings={embeddings_deployment}, Temp={rag_agent.temperature}, MaxTokens={rag_agent.max_tokens}, TopK={rag_agent.top_k}, MinScore={rag_agent.min_score}")
    
    # Orchestrator initialisieren (mit eigenem Client)
    agents = {
        "chat": chat_agent,
        "rag": rag_agent
    }
    
    orchestrator = OrchestrationAgent(
        aoai_client=aoai_orchestration,
        model_name=orchestrator_model,
        agents=agents,
        **ORCHESTRATOR_CONFIG
    )
    logger.info(f"Orchestrator initialisiert: Model={orchestrator_model}")
    
    return orchestrator, agents


def main():
    """Hauptprogramm"""
    
    print("=" * 60)
    print("  Multi-Agent System gestartet!")
    print("=" * 60)
    
    # Clients initialisieren (3 separate OpenAI Clients)
    aoai_chat, aoai_rag, aoai_orchestration, search = initialize_clients()
    
    # Agenten initialisieren
    orchestrator, agents = initialize_agents(aoai_chat, aoai_rag, aoai_orchestration, search)
    
    print(f"  Orchestrator: {orchestrator.name}")
    print(f"  Verfügbare Agenten: {', '.join(agents.keys())}")
    print("=" * 60)
    print("\n  Agent-Konfiguration:")
    print(f"  [CHAT]  Temp={CHAT_AGENT_CONFIG['temperature']}, MaxTokens={CHAT_AGENT_CONFIG['max_tokens']}, History={CHAT_AGENT_CONFIG['max_history_pairs']} Paare")
    print(f"  [RAG]   Temp={RAG_AGENT_CONFIG['temperature']}, MaxTokens={RAG_AGENT_CONFIG['max_tokens']}, TopK={RAG_AGENT_CONFIG['top_k']}, Score>={RAG_AGENT_CONFIG['min_score']}")
    print("=" * 60)
    print("  Eingabe 'exit' zum Beenden\n")
    
    # Chat-Loop
    messages = []
    
    while True:
        user_input = input("Du: ")
        if user_input.lower() in ["exit", "quit", "beenden"]:
            print("Chat beendet.")
            break
        
        logger.info(f"User: {user_input}")
        
        # Kontext vorbereiten
        recent_history = get_recent_messages(messages, max_pairs=MAX_HISTORY_MESSAGES // 2)
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
        
        # Debug-Info loggen
        if metadata.get("orchestrator_decision"):
            reason = metadata["orchestrator_decision"].get("reason", "N/A")
            logger.info(f"Routing-Begründung: {reason}")
        
        if metadata.get("config"):
            logger.debug(f"Agent-Config verwendet: {metadata['config']}")


if __name__ == "__main__":
    main()
