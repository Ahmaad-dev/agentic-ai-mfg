import os
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

load_dotenv()

# Logging einrichten
logs_dir = Path(__file__).parent / "logs"
logs_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / f'chat_{datetime.now().strftime("%Y%m%d")}.log')
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

def embed(text: str):
    try:
        r = aoai.embeddings.create(
            model=emb_deployment,
            input=text
        )
        return r.data[0].embedding
    except Exception as e:
        print(f"Embedding-Fehler: {e}")
        return None

def retrieve_context(query: str, k: int = 4, min_score: float = 0.5):
    """
    Retrieval mit Score-Threshold
    min_score: Minimaler Relevanz-Score (0.0 - 1.0), darunter wird Kontext verworfen
    Returns: (context_text, source_list, max_score, has_relevant_results)
    """
    try:
        qv = embed(query)
        if qv is None:
            return "", [], 0.0, False

        vector_query = VectorizedQuery(
            vector=qv,
            k_nearest_neighbors=k,
            fields="contentVector"
        )

        results = search.search(
            search_text="",
            vector_queries=[vector_query],
            select=["title", "source", "content", "page"]  # page hinzugefügt
        )

        chunks = []
        sources = []
        scores = []
        
        for r in results:
            score = r.get("@search.score", 0.0)
            scores.append(score)
            
            # Nur Ergebnisse über Threshold nehmen
            if score >= min_score:
                title = r.get("title", "")
                source = r.get("source", "")
                content = r.get("content", "")
                page = r.get("page")
                
                chunks.append(f"- {title} ({source}): {content}")
                
                # Quelle mit Seitenzahl speichern
                if source:
                    if page:
                        source_with_page = f"{source} (Seite {page})"
                    else:
                        source_with_page = source
                    sources.append(source_with_page)
        
        max_score = max(scores) if scores else 0.0
        has_relevant_results = len(chunks) > 0
        
        # Wenn kein Ergebnis über Threshold: leerer Kontext
        if not has_relevant_results:
            logger.warning(f"Alle Suchergebnisse unter Threshold {min_score} (Max-Score: {max_score:.3f})")
            return "", [], max_score, False
        
        logger.info(f"Relevanz-Score: {max_score:.3f} ({len(chunks)} Ergebnisse über {min_score})")
        return "\n".join(chunks), sorted(set(sources)), max_score, True
        
    except Exception as e:
        print(f"Suchfehler: {e}")
        return "", [], 0.0, False

def should_use_rag(user_input: str) -> bool:
    """
    Prüft, ob RAG aktiviert werden soll.
    Aktiviert bei Keywords wie: rag, suche, dokument, wissen, richtlinie, etc.
    """
    trigger_words = [
        "rag", "suche", "suchen", "durchsuche", "finde", "dokument", 
        "wissen", "wissensbasis", "quelle", "richtlinie", "guideline",
        "nachschlagen", "recherche", "index", "datenbank"
    ]
    
    user_lower = user_input.lower()
    return any(word in user_lower for word in trigger_words)

messages = []
system_prompt = (
    "Du bist ein intelligenter Assistent für Produktionsumgebungen. "
    "Du hast Zugriff auf eine Wissensbasis mit Richtlinien und Dokumenten. "
    "Antworte natürlich und konversationell. Beachte den gesamten Gesprächsverlauf. "
    "Wenn du Zugriff auf Kontext aus der Wissensbasis hast, nutze ihn intelligent. "
    "Wenn nicht, antworte basierend auf deinem allgemeinen Wissen."
)

MAX_HISTORY_MESSAGES = 10  # Letzte 5 User + 5 Assistant Messages

def get_recent_messages(messages, max_pairs=5):
    """Behält nur die letzten N Nachrichten-Paare"""
    if len(messages) <= max_pairs * 2:
        return messages
    return messages[-(max_pairs * 2):]

print("Chat gestartet! 'exit' zum Beenden.")
print("Tipp: Verwende Begriffe wie 'rag', 'suche' oder 'dokument' für Wissensbank-Zugriff.\n")

while True:
    user_input = input("Du: ")
    if user_input.lower() in ["exit", "quit", "beenden"]:
        print("Chat beendet.")
        break

    # Logging der User-Frage
    logger.info(f"user_question: {user_input}")

    # Schritt 1: Prüfe ob RAG-Intent erkannt wird
    has_rag_intent = should_use_rag(user_input)
    
    # Basis-Messages mit System-Prompt und Historie (nur letzte N Messages)
    recent_messages = get_recent_messages(messages, max_pairs=5)
    base_messages = [
        {"role": "system", "content": system_prompt},
        *recent_messages,
    ]
    
    # Schritt 2: Wenn Intent erkannt → RAG probieren, aber nur nutzen wenn Score gut
    if has_rag_intent:
        logger.info("RAG-Intent erkannt - Wissensbasis wird durchsucht...")
        context, sources, relevance_score, has_relevant_results = retrieve_context(user_input, k=10, min_score=0.5)
        
        # RAG = (Intent erkannt) AND (Score >= Threshold)
        use_rag = has_rag_intent and has_relevant_results
        
        if use_rag:
            # Echtes RAG: Intent + gute Ergebnisse
            logger.info(f"RAG aktiviert - Gefundene Quellen: {sources}")
            user_message_with_context = (
                f"KONTEXT AUS WISSENSBASIS:\n"
                f"{context}\n\n"
                f"---\n\n"
                f"FRAGE: {user_input}"
            )
            messages_to_send = base_messages + [
                {"role": "user", "content": user_message_with_context}
            ]
        else:
            # Intent erkannt, aber Score zu niedrig → Fallback zu normalem Chat
            logger.info(f"RAG-Intent erkannt, aber Score zu niedrig ({relevance_score:.3f}) - Fallback zu Chat-Modus")
            user_message_no_context = (
                f"[HINWEIS: Wissensbasis durchsucht, aber keine ausreichend relevanten Dokumente gefunden (Score: {relevance_score:.2f})]\n\n"
                f"FRAGE: {user_input}\n\n"
                f"Bitte stelle 1-2 präzise Rückfragen, welche spezifischen Informationen benötigt werden."
            )
            messages_to_send = base_messages + [
                {"role": "user", "content": user_message_no_context}
            ]
            sources = []
    else:
        # Kein RAG-Intent: Normaler Chat-Modus
        logger.info("Chat-Modus (kein RAG-Intent erkannt)")
        use_rag = False
        sources = []
        messages_to_send = base_messages + [
            {"role": "user", "content": user_input}
        ]

    completion = aoai.chat.completions.create(
        model=deployment_name,
        messages=messages_to_send
    )

    assistant_message = completion.choices[0].message.content
    
    # Logging der Assistant-Antwort
    logger.info(f"assistant_answer: {assistant_message}")
    
    messages.append({"role": "user", "content": user_input})
    messages.append({"role": "assistant", "content": assistant_message})

    # Ausgabe mit RAG-Indikator
    mode_indicator = "[RAG]" if use_rag else "[Chat]"
    print(f"\n{mode_indicator} Assistent: {assistant_message}\n")
    
    if sources:
        print("Quellen:", ", ".join(sources), "\n")
