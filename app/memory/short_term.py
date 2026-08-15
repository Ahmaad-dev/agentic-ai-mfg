"""
Short-term (working) memory — session context (PT4 / AP7.4).

**No new capability.** This is the consolidation of logic that has existed and worked since AP2;
it simply had no name and no owner. Behaviour is unchanged — same sliding window, same DB
reload, same defensive swallowing of DB errors.

What short-term memory IS here (and where it used to live):
  - the running conversation of ONE session   (web_server.chat_sessions)
  - reloaded from the DB when the in-memory cache is cold — server restart, or the user
    switches back into an old chat (AP4.6; web_server.get_session_history)
  - truncated to a sliding window before every LLM call, so a long chat cannot drown the
    context (web_server/main.get_recent_messages — which existed TWICE, byte-identical)
  - the chat-session-id -> DB-session-id mapping (web_server._get_db_session_id)

What it is NOT: the human review decisions. Those are NOT in the conversation — they are made
in the Review Board. `orchestration_agent._get_review_decisions()` bridges that gap by reading
them from the DB, and it stays exactly where it is: it is not a workaround for missing memory,
it is the fix for the bug where the chat answered "what was the solution?" with the AI's
proposal even after a human had overruled it.

Long-term (episodic) memory is the sibling module `long_term` / `retrieval`.
"""
import logging
from typing import List, Optional

from db import repository as db_repo

logger = logging.getLogger(__name__)

#: chat-session-id (str) -> list of {"role", "content"}. The in-memory cache, NOT the source
#: of truth — the DB is (see get_history).
_sessions: dict = {}

#: chat-session-id (str) -> DB session id (int)
_db_session_ids: dict = {}

#: Sitzungs-id -> Snapshot-ID, um die es in DIESER Unterhaltung geht ("Fokus-Snapshot").
#:
#: Bis 15.08.2026 hielt der Orchestrator stattdessen EIN Attribut `last_snapshot_metadata`
#: fuer den gesamten Prozess. Da er ein Modul-Global ist, teilten sich ALLE Sitzungen diesen
#: Wert: wer einen Snapshot lud, schob ihn jeder anderen laufenden Unterhaltung in den
#: Systemprompt — in der Cloud auch anderen Nutzern. Der Fokus haengt deshalb jetzt an der
#: Sitzung.
#:
#: Gespeichert wird NUR die ID, nie die Metadaten. Die alte Zwischenspeicherung wurde
#: ausserdem ausschliesslich beim Herunterladen/Anlegen gesetzt und danach nie wieder — nach
#: einer angewendeten Korrektur beschrieb sie einen ueberholten Zustand und behauptete ihn
#: als aktuellen. Eine ID veraltet nicht; der Zustand dazu wird bei jeder Frage neu gelesen.
_focus_snapshots: dict = {}


def set_focus_snapshot(session_id, snapshot_id: Optional[str]) -> None:
    """Merkt, um welchen Snapshot es in dieser Sitzung geht. `None` loescht den Fokus."""
    key = str(session_id)
    if snapshot_id:
        _focus_snapshots[key] = snapshot_id
    else:
        _focus_snapshots.pop(key, None)


def get_focus_snapshot(session_id) -> Optional[str]:
    """Der Snapshot dieser Sitzung — oder None, wenn in dieser Sitzung noch keiner genannt wurde."""
    return _focus_snapshots.get(str(session_id))


def get_db_session_id(chat_session_id, snapshot_id: Optional[str] = None):
    """
    Resolve the web chat-session id to a DB session id. Never breaks chat.

    AP4.6: the frontend now sends the DB session id itself (an integer as string), so a chat
    survives a page reload and a server restart. A numeric id that exists in the DB is used
    as-is. Anything else keeps the old lazy-create behaviour (backwards compatible with
    'default' and the old 'session_<timestamp>' ids).
    """
    if chat_session_id in _db_session_ids:
        return _db_session_ids[chat_session_id]

    # Numeric id -> an existing DB session (the AP4.6 case).
    try:
        numeric = int(str(chat_session_id))
    except (TypeError, ValueError):
        numeric = None
    if numeric is not None:
        try:
            if db_repo.session_exists(numeric):
                _db_session_ids[chat_session_id] = numeric
                return numeric
        except Exception as e:
            logger.warning(f"DB: could not look up session {numeric}: {e}")

    try:
        db_id = db_repo.create_session(snapshot_id=snapshot_id, user_ref=str(chat_session_id))
        _db_session_ids[chat_session_id] = db_id
        return db_id
    except Exception as e:
        logger.warning(f"DB: could not create session for {chat_session_id}: {e}")
        return None


def get_history(session_id: str) -> List[dict]:
    """
    The full conversation of one session.

    AP4.6: the in-memory cache is not the source of truth. If the session is unknown there
    (server restart, or the user switches back into an old chat), the history is reloaded from
    the DB — otherwise the agent answers with no context at all although the conversation was
    persisted long ago. DB errors never break the chat.
    """
    if session_id not in _sessions:
        history = []
        db_sid = get_db_session_id(session_id)
        if db_sid is not None:
            try:
                history = [
                    {"role": m["role"], "content": m["content"],
                     "agent_name": m.get("agent_name")}
                    for m in db_repo.get_messages_as_dicts(db_sid)
                ]
                if history:
                    logger.info(f"Session {session_id}: {len(history)} Nachrichten aus der DB geladen")
            except Exception as e:
                logger.warning(f"DB: could not load history for session {session_id}: {e}")
        _sessions[session_id] = history
    return _sessions[session_id]


#: agent_name aus der Datenbank -> was im Verlauf davorsteht.
#:
#: Der Sinn ist EINE Unterscheidung: stammt ein Satz aus einem Werkzeug (gemessen) oder aus
#: einer freien Formulierung (behauptet)? Alles andere waere Zierde. Unbekannte oder fehlende
#: Namen bekommen bewusst KEIN Etikett — lieber gar keine Herkunft als eine erfundene.
_HERKUNFT = {
    "sp": "Werkzeug-Ergebnis",
    "SP_Agent": "Werkzeug-Ergebnis",
    "rag": "Wissensbasis",
    "RAG": "Wissensbasis",
    "chat": "Gespräch",
    "Chat": "Gespräch",
    "email": "E-Mail-Entwurf",
}


def label_for(agent_name: Optional[str]) -> Optional[str]:
    """Das Herkunfts-Etikett zu einem Agentennamen, oder None wenn unbekannt."""
    return _HERKUNFT.get(agent_name) if agent_name else None


def as_llm_messages(history: List[dict]) -> List[dict]:
    """Verlauf in die Form bringen, die ein LLM-Aufruf akzeptiert — mit Herkunft im Text.

    Zwei Gruende, die Herkunft in den TEXT zu schreiben statt in ein eigenes Feld:
    die Chat-Completions-Schnittstelle weist unbekannte Felder zurueck, und das Modell
    liest ohnehin nur den Text. Nutzernachrichten bleiben unangetastet — bei ihnen ist die
    Herkunft nie fraglich.
    """
    out = []
    for m in history:
        rolle = m.get("role")
        text = m.get("content", "")
        etikett = label_for(m.get("agent_name")) if rolle == "assistant" else None
        out.append({"role": rolle, "content": f"[{etikett}] {text}" if etikett else text})
    return out


def get_recent_messages(messages: List, max_pairs: int = 5) -> List:
    """The sliding window: keep only the last N user+assistant pairs."""
    max_messages = max_pairs * 2
    if len(messages) <= max_messages:
        return messages
    return messages[-max_messages:]


def clear_focus_snapshot(session_id) -> None:
    """Beim Leeren einer Sitzung faellt auch ihr Snapshot-Bezug weg."""
    _focus_snapshots.pop(str(session_id), None)


def clear(session_id: str) -> bool:
    """Drop the in-memory history of a session. Returns False if it was not cached."""
    # Der Snapshot-Bezug gehoert zur Sitzung und muss mit ihr verschwinden — sonst
    # antwortet die geleerte Unterhaltung weiter zu einem Snapshot, der in ihr nicht
    # mehr vorkommt.
    clear_focus_snapshot(session_id)
    if session_id in _sessions:
        _sessions[session_id] = []
        return True
    return False


def register(session_id: str, db_session_id: int) -> None:
    """Announce a freshly created DB session, so the first message does not re-create it."""
    _sessions[str(session_id)] = []
    _db_session_ids[str(session_id)] = db_session_id
