import os
import logging
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

load_dotenv()

# ========== KONFIGURATION ==========
# RAG Retrieval Einstellungen
RAG_TOP_K = 10  # Anzahl Suchergebnisse
RAG_MIN_SCORE = 0.5  # Minimaler Relevanz-Score (0.0-1.0)

# Router Einstellungen
ROUTER_TEMPERATURE = 0  # Deterministische Routing-Entscheidungen
ROUTER_MAX_TOKENS = 150  # Max Tokens für Router-Antwort
ROUTER_CONTEXT_MESSAGES = 6  # Anzahl Messages für Router-Kontext (letzte 3 Paare)
ROUTER_CONTEXT_CHAR_LIMIT = 500  # Max Zeichen pro Message im Router-Kontext

# Chat History
MAX_HISTORY_MESSAGES = 10  # Anzahl Messages für Assistent-Kontext (muss gerade sein)
# ===================================

# Logging einrichten
logs_dir = Path(__file__).parent / "logs"
logs_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(
            logs_dir / f'chat_{datetime.now().strftime("%Y%m%d")}.log',
            encoding='utf-8'  # UTF-8 für Emoji-Support
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

def embed(text: str):
    try:
        r = aoai.embeddings.create(
            model=emb_deployment,
            input=text
        )
        return r.data[0].embedding
    except Exception as e:
        logger.error(f"Embedding-Fehler: {e}")
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
        logger.error(f"Suchfehler: {e}")
        return "", [], 0.0, False

def route_with_llm(user_input: str, recent_messages: list, enable_debug_logging: bool = True) -> dict:
    """
    LLM-basierte Intent-Klassifikation zur Entscheidung zwischen RAG, Chat oder Rückfragen.
    
    Returns:
        dict mit Feldern: route, reason, search_query (optional)
        - route: "doc_query" | "general_chat" | "clarify"
        - reason: Begründung für die Routing-Entscheidung
        - search_query: Optimierte Suchanfrage (nur bei doc_query)
    """
    
    router_system_prompt = """Du bist ein Router-System, das eingehende Benutzeranfragen klassifiziert.

Deine Aufgabe: Entscheide, ob die Anfrage:
1. "doc_query" - Interne Dokumente/Wissensbasis benötigt (Richtlinien, technische Specs, Prozesse, etc.)
2. "general_chat" - Allgemeine Konversation/Smalltalk ohne Dokumentenbedarf
3. "clarify" - Anfrage ist unklar und benötigt Rückfragen

REGELN:
- "doc_query": Fragen zu spezifischen Prozessen, Richtlinien, Sicherheitsvorschriften, technischen Details, die in Firmendokumenten stehen könnten
  → WICHTIG: Auch unvollständige Anfragen wie "suche in meinen Unterlagen nach X" oder "prüf in docs" zählen als doc_query!
  → Nutze den Gesprächskontext, um das Thema X zu identifizieren
- "general_chat": Begrüßungen, Danksagungen, allgemeine Wissensfragen (die nicht firmenspezifisch sind), Smalltalk
- "clarify": Vage Formulierungen wie "stimmt das?", "was meinst du?", Anfragen ohne klaren Kontext UND ohne erkennbares Thema im Gesprächsverlauf

KONTEXT-AWARENESS:
- Wenn die aktuelle Anfrage unvollständig ist ("suche nach..."), prüfe den Gesprächskontext für das Thema
- Beispiel: Vorherige Frage war "Was ist Power Automate?" → "suche in Unterlagen nach" bedeutet "suche nach Power Automate"

ANTWORTE NUR MIT DIESEM JSON-FORMAT (kein weiterer Text!):
{
  "route": "doc_query" | "general_chat" | "clarify",
  "reason": "Kurze Begründung für die Entscheidung",
  "search_query": "Optimierte Suchanfrage (nur bei doc_query, sonst null)"
}"""
    
    # Kontext aus letzten Messages für bessere Routing-Entscheidung
    context_summary = ""
    if recent_messages:
        last_messages = recent_messages[-ROUTER_CONTEXT_MESSAGES:]
        context_summary = "\n\nBISHERIGER GESPRÄCHSKONTEXT:\n"
        for msg in last_messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            content = msg["content"][:ROUTER_CONTEXT_CHAR_LIMIT]
            if len(msg["content"]) > ROUTER_CONTEXT_CHAR_LIMIT:
                content += "..."
            context_summary += f"{role}: {content}\n"
    
    router_user_prompt = f"{context_summary}\n\nAKTUELLE BENUTZERANFRAGE:\n{user_input}\n\nKlassifiziere diese Anfrage unter Berücksichtigung des Gesprächskontexts und antworte mit JSON."
    
    try:
        response = aoai.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": router_system_prompt},
                {"role": "user", "content": router_user_prompt}
            ],
            temperature=ROUTER_TEMPERATURE,
            max_tokens=ROUTER_MAX_TOKENS
        )
        
        router_output = response.choices[0].message.content.strip()
        
        # Versuche JSON zu parsen
        # Manchmal gibt LLM ```json...``` zurück, bereinigen
        if router_output.startswith("```json"):
            router_output = router_output[7:]
        if router_output.startswith("```"):
            router_output = router_output[3:]
        if router_output.endswith("```"):
            router_output = router_output[:-3]
        
        router_output = router_output.strip()
        routing_decision = json.loads(router_output)
        
        # Validierung des Schemas
        if "route" not in routing_decision:
            raise ValueError("Fehlendes 'route' Feld in Router-Antwort")
        
        if routing_decision["route"] not in ["doc_query", "general_chat", "clarify"]:
            raise ValueError(f"Ungültiger route-Wert: {routing_decision['route']}")
        
        # Defaults setzen falls Felder fehlen
        if "reason" not in routing_decision:
            routing_decision["reason"] = "Keine Begründung angegeben"
        if "search_query" not in routing_decision:
            routing_decision["search_query"] = None
        
        if enable_debug_logging:
            logger.info(f"Router-Entscheidung: route={routing_decision['route']}, reason={routing_decision['reason']}, search_query={routing_decision.get('search_query')}")
        
        return routing_decision
        
    except json.JSONDecodeError as e:
        logger.error(f"Router JSON-Parsing Fehler: {e}. Raw output: {router_output}")
        # Fallback: Heuristik basierend auf Keywords
        return _fallback_routing(user_input, enable_debug_logging)
    
    except Exception as e:
        logger.error(f"Router Fehler: {e}")
        return _fallback_routing(user_input, enable_debug_logging)


def _fallback_routing(user_input: str, enable_debug_logging: bool = True) -> dict:
    """
    Fallback-Routing bei Router-Fehler oder JSON-Parsing-Problem.
    Nutzt einfache Keyword-Heuristik.
    """
    user_lower = user_input.lower()
    
    # Dokument-Keywords
    doc_keywords = [
        "dokument", "richtlinie", "guideline", "vorschrift", "prozess",
        "temperatur", "sicherheit", "wartung", "anleitung", "handbuch",
        "standard", "spezifikation", "regel", "vorgabe"
    ]
    
    # Smalltalk-Keywords
    chat_keywords = ["hallo", "hi", "hey", "danke", "dankeschön", "tschüss", "bis", "servus"]
    
    # Clarify-Keywords
    clarify_keywords = ["was meinst du", "wie?", "hä?", "verstehe nicht", "stimmt das"]
    
    if any(word in user_lower for word in clarify_keywords):
        route = "clarify"
        reason = "Fallback: Unklare Anfrage erkannt (Keyword-Heuristik)"
    elif any(word in user_lower for word in chat_keywords):
        route = "general_chat"
        reason = "Fallback: Smalltalk erkannt (Keyword-Heuristik)"
    elif any(word in user_lower for word in doc_keywords):
        route = "doc_query"
        reason = "Fallback: Dokument-Keywords erkannt (Keyword-Heuristik)"
    else:
        # Default: Bei Unklarheit → clarify, um sicher zu gehen
        route = "clarify"
        reason = "Fallback: Keine eindeutige Kategorie, Rückfrage empfohlen"
    
    if enable_debug_logging:
        logger.warning(f"Fallback-Routing aktiviert: route={route}, reason={reason}")
    
    return {
        "route": route,
        "reason": reason,
        "search_query": user_input if route == "doc_query" else None
    }

messages = []
system_prompt = (
    "Du bist ein intelligenter Assistent für Produktionsumgebungen. "
    "Du hast Zugriff auf eine Wissensbasis mit Richtlinien und Dokumenten. "
    "Antworte natürlich und konversationell. Beachte den gesamten Gesprächsverlauf. "
    "Wenn du Zugriff auf Kontext aus der Wissensbasis hast, nutze ihn intelligent. "
    "Wenn nicht, antworte basierend auf deinem allgemeinen Wissen."
)

def get_recent_messages(messages, max_pairs=None):
    """Behält nur die letzten N Nachrichten-Paare"""
    if max_pairs is None:
        max_pairs = MAX_HISTORY_MESSAGES // 2  # Konvertiere Messages zu Paaren
    if len(messages) <= max_pairs * 2:
        return messages
    return messages[-(max_pairs * 2):]

print("Chat gestartet! 'exit' zum Beenden.\n")

while True:
    user_input = input("Du: ")
    if user_input.lower() in ["exit", "quit", "beenden"]:
        print("Chat beendet.")
        break

    # Logging der User-Frage
    logger.info(f"user_question: {user_input}")

    # Basis-Messages mit System-Prompt und Historie (nur letzte N Messages)
    recent_messages = get_recent_messages(messages)  # Nutzt MAX_HISTORY_MESSAGES
    base_messages = [
        {"role": "system", "content": system_prompt},
        *recent_messages,
    ]
    
    # Schritt 1: LLM-Router entscheidet über Intent
    routing = route_with_llm(user_input, recent_messages, enable_debug_logging=True)
    route = routing["route"]
    reason = routing["reason"]
    search_query = routing.get("search_query", user_input)
    
    logger.info(f"Router: route={route}, reason={reason}")
    
    # Schritt 2: Route-basierte Verarbeitung
    use_rag = False
    sources = []
    
    if route == "doc_query":
        # Dokumenten-Anfrage: RAG durchführen
        logger.info(f"Dokumenten-Query erkannt - Starte Retrieval mit Query: '{search_query}'")
        context, sources, relevance_score, has_relevant_results = retrieve_context(
            search_query, k=RAG_TOP_K, min_score=RAG_MIN_SCORE
        )
        
        logger.info(f"Retrieval-Ergebnis: max_score={relevance_score:.3f}, hits_above_threshold={len(sources)}")
        
        if has_relevant_results:
            # RAG: Gute Treffer gefunden
            use_rag = True
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
            # Retrieval lieferte keine guten Ergebnisse → Rückfragen
            logger.info(f"Retrieval-Score zu niedrig ({relevance_score:.3f}) - Wechsel zu Rückfragen")
            user_message_no_context = (
                f"[HINWEIS: Wissensbasis durchsucht, aber keine ausreichend relevanten Dokumente gefunden (Max-Score: {relevance_score:.2f})]\n\n"
                f"FRAGE: {user_input}\n\n"
                f"Bitte stelle 1-2 präzise Rückfragen, um die benötigten Informationen zu ermitteln."
            )
            messages_to_send = base_messages + [
                {"role": "user", "content": user_message_no_context}
            ]
    
    elif route == "clarify":
        # Unklare Anfrage: LLM soll Rückfragen stellen
        logger.info("Unklare Anfrage - Assistent wird Rückfragen stellen")
        user_message_clarify = (
            f"[HINWEIS: Anfrage ist unklar oder benötigt mehr Kontext]\n\n"
            f"ANFRAGE: {user_input}\n\n"
            f"Stelle höflich 1-2 präzise Rückfragen, um die Anfrage zu klären."
        )
        messages_to_send = base_messages + [
            {"role": "user", "content": user_message_clarify}
        ]
    
    else:  # route == "general_chat"
        # Normaler Chat-Modus: Keine RAG-Suche nötig
        logger.info("Chat-Modus - Keine Dokumentensuche erforderlich")
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

    # Ausgabe mit detailliertem Mode-Indikator
    if use_rag:
        mode_indicator = "[RAG]"
    elif route == "clarify":
        mode_indicator = "[Rückfrage]"
    else:
        mode_indicator = "[Chat]"
    
    print(f"\n{mode_indicator} Assistent: {assistant_message}\n")
    
    if sources:
        print("Quellen:", ", ".join(sources), "\n")
