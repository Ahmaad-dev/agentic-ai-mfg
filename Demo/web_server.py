"""
Einfacher Web-Server für das Multi-Agent Chat Interface
"""
import os
import time
import logging
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

# Agent-Imports
from agents import ChatAgent, EmailAgent, RAGAgent, SPAgent, OrchestrationAgent
import agent_config
from agent_config import (
    CHAT_AGENT_CONFIG,
    EMAIL_AGENT_CONFIG,
    RAG_AGENT_CONFIG,
    ORCHESTRATOR_CONFIG,
    SP_AGENT_CONFIG,
    MAX_HISTORY_MESSAGES
)

load_dotenv()

# Flask App
app = Flask(__name__, template_folder='ui', static_folder='ui', static_url_path='')
CORS(app)

# AP3.1: Register the HitL review blueprint (read-only, /api/review/...)
from routes.review import review_bp
app.register_blueprint(review_bp)

# AP6.1: Register the dashboard metrics blueprint (read-only, /api/dashboard/...)
from routes.dashboard import dashboard_bp
app.register_blueprint(dashboard_bp)

# Security Headers
@app.after_request
def add_security_headers(response):
    """Add security headers for production deployment"""
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "script-src 'self' 'unsafe-eval' https://aka.ms https://*.core.windows.net https://*.microsoft.com blob:; "
        "img-src 'self' data: blob:; "
        "media-src 'self' blob:; "
        "worker-src 'self' blob:; "
        "connect-src 'self' https://aka.ms https://*.speech.microsoft.com https://*.cognitiveservices.azure.com https://*.cognitive.microsoft.com https://*.microsoft.com https://*.core.windows.net https://*.azure.com wss://*.speech.microsoft.com wss://*.stt.speech.microsoft.com wss://*.cognitiveservices.azure.com;"
    )
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

# Logging
logs_dir = Path(__file__).parent / "logs"
logs_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(
            logs_dir / f'web_{datetime.now().strftime("%Y%m%d")}.log',
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Globale Variablen für Agenten
orchestrator = None
agents = None
chat_sessions = {}

# DB persistence (AP2): map web chat-session-id (str) -> DB session id (int)
from db import repository as db_repo
from cost_model import estimate_cost
db_session_ids = {}


def _get_db_session_id(chat_session_id, snapshot_id=None):
    """
    Resolve the web chat-session id to a DB session id. Never breaks chat.

    AP4.6: the frontend now sends the DB session id itself (an integer as string), so a chat
    survives a page reload and a server restart. A numeric id that exists in the DB is used
    as-is. Anything else keeps the old lazy-create behaviour (backwards compatible with
    'default' and the old 'session_<timestamp>' ids).
    """
    if chat_session_id in db_session_ids:
        return db_session_ids[chat_session_id]

    # Numeric id -> an existing DB session (the AP4.6 case).
    try:
        numeric = int(str(chat_session_id))
    except (TypeError, ValueError):
        numeric = None
    if numeric is not None:
        try:
            if db_repo.session_exists(numeric):
                db_session_ids[chat_session_id] = numeric
                return numeric
        except Exception as e:
            logger.warning(f"DB: could not look up session {numeric}: {e}")

    try:
        db_id = db_repo.create_session(snapshot_id=snapshot_id, user_ref=str(chat_session_id))
        db_session_ids[chat_session_id] = db_id
        return db_id
    except Exception as e:
        logger.warning(f"DB: could not create session row: {e}")
        return None


def must_env(name: str) -> str:
    """Lade Environment Variable oder raise Error"""
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing env var: {name}")
    return v


def initialize_system():
    """Initialisiert das gesamte Agent-System"""
    global orchestrator, agents
    
    if orchestrator is not None:
        logger.info("Agent-System bereits initialisiert, überspringe")
        return
    
    # Clients initialisieren
    aoai_chat = AzureOpenAI(
        azure_endpoint=must_env("AZURE_OPENAI_CHAT_ENDPOINT"),
        api_key=must_env("AZURE_OPENAI_CHAT_KEY"),
        api_version=must_env("AZURE_OPENAI_CHAT_API_VERSION")
    )
    
    aoai_rag = AzureOpenAI(
        azure_endpoint=must_env("AZURE_OPENAI_RAG_ENDPOINT"),
        api_key=must_env("AZURE_OPENAI_RAG_KEY"),
        api_version=must_env("AZURE_OPENAI_RAG_API_VERSION")
    )
    
    aoai_orchestration = AzureOpenAI(
        azure_endpoint=must_env("AZURE_OPENAI_ORCHESTRATION_ENDPOINT"),
        api_key=must_env("AZURE_OPENAI_ORCHESTRATION_KEY"),
        api_version=must_env("AZURE_OPENAI_ORCHESTRATION_API_VERSION")
    )

    search = SearchClient(
        endpoint=must_env("AZURE_SEARCH_ENDPOINT"),
        index_name=must_env("AZURE_SEARCH_INDEX"),
        credential=AzureKeyCredential(must_env("AZURE_SEARCH_ADMIN_KEY"))
    )
    
    # Deployment-Namen
    chat_model = must_env("AZURE_OPENAI_CHAT_DEPLOYMENT")
    rag_model = must_env("AZURE_OPENAI_RAG_DEPLOYMENT")
    orchestrator_model = must_env("AZURE_OPENAI_ORCHESTRATION_DEPLOYMENT")
    embeddings_deployment = must_env("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT")
    
    # Agenten initialisieren
    chat_agent = ChatAgent(
        aoai_client=aoai_chat,
        model_name=chat_model,
        **CHAT_AGENT_CONFIG
    )
    
    rag_agent = RAGAgent(
        aoai_client=aoai_rag,
        model_name=rag_model,
        emb_model_name=embeddings_deployment,
        search_client=search,
        **RAG_AGENT_CONFIG
    )
    
    sp_agent = SPAgent(
        runtime_dir=Path(__file__).parent / "smart-planning" / "runtime",
        routing_description=agent_config.SP_AGENT_CONFIG["routing_description"]
    )

    email_agent = EmailAgent(
        aoai_client=aoai_chat,
        model_name=chat_model,
        **EMAIL_AGENT_CONFIG,
    )
    
    agents = {
        "chat": chat_agent,
        "rag": rag_agent,
        "sp": sp_agent,
        "email": email_agent,
    }
    
    orchestrator = OrchestrationAgent(
        aoai_client=aoai_orchestration,
        model_name=orchestrator_model,
        agents=agents,
        **ORCHESTRATOR_CONFIG
    )
    
    logger.info("Multi-Agent System initialisiert")


def get_session_history(session_id: str):
    """
    Hole oder erstelle Chat-Historie für eine Session.

    AP4.6: Der In-Memory-Cache ist nicht mehr die Quelle der Wahrheit. Ist eine Session dort
    nicht bekannt (Serverneustart, oder der Nutzer wechselt zurück in einen alten Chat), wird
    die Historie aus der DB nachgeladen — sonst antwortet der Agent ohne jeden Kontext,
    obwohl der Verlauf längst persistiert ist. DB-Fehler brechen den Chat nie.
    """
    if session_id not in chat_sessions:
        history = []
        db_sid = _get_db_session_id(session_id)
        if db_sid is not None:
            try:
                history = [
                    {"role": m["role"], "content": m["content"]}
                    for m in db_repo.get_messages_as_dicts(db_sid)
                ]
                if history:
                    logger.info(
                        f"Session {session_id}: {len(history)} Nachrichten aus der DB geladen"
                    )
            except Exception as e:
                logger.warning(f"DB: could not load history for session {session_id}: {e}")
        chat_sessions[session_id] = history
    return chat_sessions[session_id]


def get_recent_messages(messages, max_pairs: int = 5):
    """Behält nur die letzten N Nachrichten-Paare"""
    max_messages = max_pairs * 2
    if len(messages) <= max_messages:
        return messages
    return messages[-max_messages:]


@app.route('/')
def index():
    """Hauptseite"""
    return render_template('index.html')


@app.route('/api/speech-config', methods=['GET'])
def get_speech_config():
    """
    Liefert Azure Speech Service Credentials für Frontend
    WICHTIG: Nur für Development! In Production sollte ein Token-Service verwendet werden.
    """
    try:
        speech_key = os.getenv('AZURE_SPEECH_KEY')
        speech_region = os.getenv('AZURE_SPEECH_REGION', 'westeurope')
        
        if not speech_key or speech_key == 'DEIN_AZURE_SPEECH_KEY':
            return jsonify({
                'error': 'Speech Service not configured',
                'configured': False
            }), 200
        
        return jsonify({
            'key': speech_key,
            'region': speech_region,
            'configured': True
        })
    except Exception as e:
        logger.error(f"Error fetching speech config: {str(e)}")
        return jsonify({'error': str(e), 'configured': False}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat-Endpunkt"""
    try:
        data = request.json
        user_message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        selected_tool = data.get('selected_tool')
        
        if not user_message:
            return jsonify({'error': 'Keine Nachricht erhalten'}), 400
        
        logger.info(f"Session {session_id} - User: {user_message}")

        # DB (AP2): ensure a session row exists + persist the user message
        db_sid = _get_db_session_id(session_id)
        if db_sid is not None:
            try:
                db_repo.add_message(db_sid, role="user", content=user_message)
            except Exception as e:
                logger.warning(f"DB: could not persist user message: {e}")

        # Session-Historie holen
        messages = get_session_history(session_id)
        
        # Kontext vorbereiten
        recent_history = get_recent_messages(messages, max_pairs=MAX_HISTORY_MESSAGES // 2)
        active_email_draft = None
        if db_sid is not None:
            try:
                active_email_draft = db_repo.get_latest_email_draft_for_session(
                    db_sid, status="draft"
                )
            except Exception as e:
                logger.warning(f"DB: could not load active email draft: {e}")
        context = {
            "chat_history": recent_history,
            "db_session_id": db_sid,
            "selected_tool": selected_tool,
            "active_email_draft": active_email_draft,
        }
        
        # Orchestrator ausführen (mit Zeitmessung für agent_runs)
        _t0 = time.perf_counter()
        result = orchestrator.execute(user_message, context)
        duration_ms = int((time.perf_counter() - _t0) * 1000)
        
        # Antwort extrahieren
        response = result["response"]
        metadata = result["metadata"]
        
        # Historie aktualisieren
        messages.append({"role": "user", "content": user_message})
        messages.append({"role": "assistant", "content": response})
        
        # Agent-Name extrahieren
        agent_name = metadata.get("agent", "Unknown")

        # DB (AP2/AP2.5): persist assistant message + agent run incl. token/cost telemetry
        if db_sid is not None:
            try:
                db_repo.add_message(db_sid, role="assistant", content=str(response), agent_name=agent_name)
                _tok_p = metadata.get("tokens_prompt") or None
                _tok_c = metadata.get("tokens_completion") or None
                # AP6.3: input and output are billed at their own rates (see cost_model.py).
                _cost = estimate_cost(_tok_p, _tok_c)
                db_repo.add_agent_run(
                    db_sid,
                    agent_name=agent_name,
                    tool_name=(metadata.get("pipeline") or metadata.get("tool")),
                    input_summary=user_message[:1000],
                    output_summary=str(response)[:1000],
                    status="success" if metadata.get("success", True) else "failed",
                    duration_ms=duration_ms,
                    tokens_prompt=_tok_p,
                    tokens_completion=_tok_c,
                    cost_estimate=_cost,
                )
            except Exception as e:
                logger.warning(f"DB: could not persist assistant/agent_run: {e}")
        
        logger.info(f"Session {session_id} - Agent {agent_name}: {response[:100]}...")
        
        return jsonify({
            'response': response,
            'agent': agent_name,
            'metadata': metadata
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Chat: {str(e)}", exc_info=True)
        return jsonify({'error': f'Fehler: {str(e)}'}), 500


@app.route('/api/clear', methods=['POST'])
def clear_session():
    """Chat-Historie löschen"""
    try:
        data = request.json
        session_id = data.get('session_id', 'default')
        
        if session_id in chat_sessions:
            chat_sessions[session_id] = []
            logger.info(f"Session {session_id} - Historie gelöscht")
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        logger.error(f"Fehler beim Löschen: {str(e)}", exc_info=True)
        return jsonify({'error': f'Fehler: {str(e)}'}), 500


# --------------------------------------------------------------------------- #
# AP4.6 — Chat-Sessions aus der DB (die Nachrichten liegen seit AP2 dort, wurden
# aber nie zurueckgelesen: jeder Seitenaufruf erzeugte eine neue Session und der
# Verlauf war verloren).
# --------------------------------------------------------------------------- #
@app.route('/api/sessions', methods=['GET'])
def list_sessions():
    """Alle Chat-Sessions mit Inhalt, neueste Aktivitaet zuerst."""
    try:
        return jsonify(db_repo.list_sessions_as_dicts()), 200
    except Exception as e:
        logger.error(f"Fehler beim Laden der Sessions: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions', methods=['POST'])
def create_chat_session():
    """Neue Chat-Session anlegen und ihre DB-Id zurueckgeben."""
    try:
        new_id = db_repo.create_session(user_ref="web")
        chat_sessions[str(new_id)] = []
        db_session_ids[str(new_id)] = new_id
        logger.info(f"Neue Chat-Session angelegt: {new_id}")
        return jsonify({'session_id': new_id}), 201
    except Exception as e:
        logger.error(f"Fehler beim Anlegen der Session: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions/<int:session_id>/messages', methods=['GET'])
def get_session_messages(session_id: int):
    """Vollstaendiger Verlauf einer Session (zum Wiederherstellen im UI)."""
    try:
        if not db_repo.session_exists(session_id):
            return jsonify({'error': 'Session not found', 'session_id': session_id}), 404
        return jsonify(db_repo.get_messages_as_dicts(session_id)), 200
    except Exception as e:
        logger.error(f"Fehler beim Laden der Nachrichten: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # System initialisieren
    initialize_system()
    
    # Server starten
    print("\n" + "="*60)
    print("  Multi-Agent Chat Server")
    print("="*60)
    print("\n  Server läuft auf: http://localhost:8000")
    print("\n  Zum Beenden: Ctrl+C")
    print("\n" + "="*60 + "\n")
    
    # Nutze 'stat' reloader statt 'watchdog' - vermeidet Probleme mit SP Tool Execution
    # 'stat' überwacht nur main files, nicht alle Python-Dateien im Workspace
    app.run(debug=True, port=8000, use_reloader=True, reloader_type='stat')
