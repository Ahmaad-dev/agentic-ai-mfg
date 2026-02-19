"""
Einfacher Web-Server für das Multi-Agent Chat Interface
"""
import os
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
from agents import ChatAgent, RAGAgent, SPAgent, OrchestrationAgent
import agent_config
from agent_config import (
    CHAT_AGENT_CONFIG,
    RAG_AGENT_CONFIG,
    ORCHESTRATOR_CONFIG,
    SP_AGENT_CONFIG,
    MAX_HISTORY_MESSAGES
)

load_dotenv()

# Flask App
app = Flask(__name__, template_folder='ui', static_folder='ui', static_url_path='')
CORS(app)

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
    
    agents = {
        "chat": chat_agent,
        "rag": rag_agent,
        "sp": sp_agent
    }
    
    orchestrator = OrchestrationAgent(
        aoai_client=aoai_orchestration,
        model_name=orchestrator_model,
        agents=agents,
        **ORCHESTRATOR_CONFIG
    )
    
    logger.info("Multi-Agent System initialisiert")


def get_session_history(session_id: str):
    """Hole oder erstelle Chat-Historie für eine Session"""
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []
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
        
        if not user_message:
            return jsonify({'error': 'Keine Nachricht erhalten'}), 400
        
        logger.info(f"Session {session_id} - User: {user_message}")
        
        # Session-Historie holen
        messages = get_session_history(session_id)
        
        # Kontext vorbereiten
        recent_history = get_recent_messages(messages, max_pairs=MAX_HISTORY_MESSAGES // 2)
        context = {"chat_history": recent_history}
        
        # Orchestrator ausführen
        result = orchestrator.execute(user_message, context)
        
        # Antwort extrahieren
        response = result["response"]
        metadata = result["metadata"]
        
        # Historie aktualisieren
        messages.append({"role": "user", "content": user_message})
        messages.append({"role": "assistant", "content": response})
        
        # Agent-Name extrahieren
        agent_name = metadata.get("agent", "Unknown")
        
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


if __name__ == '__main__':
    # System initialisieren
    initialize_system()
    
    # Server starten
    print("\n" + "="*60)
    print("  Multi-Agent Chat Server")
    print("="*60)
    print("\n  Server läuft auf: http://localhost:5000")
    print("\n  Zum Beenden: Ctrl+C")
    print("\n" + "="*60 + "\n")
    
    # Nutze 'stat' reloader statt 'watchdog' - vermeidet Probleme mit SP Tool Execution
    # 'stat' überwacht nur main files, nicht alle Python-Dateien im Workspace
    app.run(debug=True, port=5000, use_reloader=True, reloader_type='stat')
