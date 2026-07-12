/**
 * Multi-Agent Chat Application
 * Production-ready version with enhanced error handling, retry logic, and accessibility
 */

const chatContainer = document.getElementById('chatContainer');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const micBtn = document.getElementById('micBtn');
const toolPickerBtn = document.getElementById('toolPickerBtn');
const toolPickerMenu = document.getElementById('toolPickerMenu');
const selectedToolChip = document.getElementById('selectedToolChip');
const clearSelectedToolBtn = document.getElementById('clearSelectedTool');

/**
 * AP4.6 — Chat-Sessions.
 *
 * Vorher: `const sessionId = 'session_' + Date.now()` — bei JEDEM Seitenaufruf eine neue
 * Session. Ein Wechsel ins Review Board und zurück war damit ein neuer Chat, der Verlauf war
 * weg (obwohl er seit AP2 in der DB stand, nur nie zurückgelesen wurde).
 *
 * Jetzt ist `sessionId` die DB-Id der Session. Sie kommt aus ?session=<id>, sonst aus dem
 * localStorage, sonst wird eine neue angelegt. Der Verlauf wird beim Laden aus der DB geholt.
 */
const SESSION_STORAGE_KEY = 'pt4.activeSessionId';
let sessionId = null;
let isFirstMessage = true;
let isRecording = false;
let recognizer = null;
let recognizedText = ''; // Speichert den bisher erkannten Text
let silenceTimer = null; // Timer für automatisches Senden nach Pause
let selectedTool = null;
const AUTO_SEND_DELAY = 5000; // 5 Sekunden Stille = Auto-Send

// Configuration
const CONFIG = {
    MAX_RETRIES: 3,
    RETRY_DELAY: 2000, // ms
    REQUEST_TIMEOUT: 300000, // 5 minutes
    API_ENDPOINT: API_CONFIG.baseURL + '/api/chat',
    // Azure Speech Configuration (wird vom Backend geladen)
    SPEECH_KEY: null,
    SPEECH_REGION: null,
    SPEECH_LANGUAGE: 'de-DE' // Deutsch
};

// Custom Hexagon Logo (Blue/Green Gradient)
const AGENT_ICON = `
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="agent_grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#06b6d4" />
            <stop offset="100%" style="stop-color:#84cc16" />
        </linearGradient>
    </defs>
    <path d="M12 2.5L20.66 7.5V17.5L12 22.5L3.34 17.5V7.5L12 2.5Z" stroke="url(#agent_grad)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M12 8L16.33 10.5V15.5L12 18L7.67 15.5V10.5L12 8Z" fill="url(#agent_grad)" fill-opacity="0.2" stroke="url(#agent_grad)" stroke-width="1"/>
</svg>`;

/**
 * Auto-resize textarea based on content
 */
function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
}

/**
 * Mehrzeiliges Eingabefeld: die Textarea wächst mit dem Inhalt.
 *
 * autoResize() gab es schon, wurde aber NUR aus der Spracherkennung heraus aufgerufen —
 * beim Tippen passierte nichts, das Feld blieb einzeilig (feste height: 24px im CSS).
 */
userInput.addEventListener('input', () => autoResize(userInput));

/**
 * Enter-Taste zum Senden abfangen (Shift+Enter für Zeilenumbruch)
 */
userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

/**
 * Send-Button Click Event
 */
sendBtn.addEventListener('click', () => {
    sendMessage();
});

function setSelectedTool(tool) {
    selectedTool = tool || null;
    selectedToolChip.hidden = selectedTool !== 'email';
    toolPickerMenu.hidden = true;
    toolPickerBtn.setAttribute('aria-expanded', 'false');
    userInput.placeholder = selectedTool === 'email'
        ? 'Beschreibe Empfänger und Inhalt der E-Mail…'
        : 'Frage etwas...';
    userInput.focus();
}

toolPickerBtn.addEventListener('click', () => {
    const opening = toolPickerMenu.hidden;
    toolPickerMenu.hidden = !opening;
    toolPickerBtn.setAttribute('aria-expanded', String(opening));
});

toolPickerMenu.addEventListener('click', (event) => {
    const item = event.target.closest('[data-tool]');
    if (item) setSelectedTool(item.dataset.tool);
});
clearSelectedToolBtn.addEventListener('click', () => setSelectedTool(null));
document.addEventListener('click', (event) => {
    if (!event.target.closest('.tool-picker')) {
        toolPickerMenu.hidden = true;
        toolPickerBtn.setAttribute('aria-expanded', 'false');
    }
});

/**
 * Utility: Sleep/Delay function
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Send message with retry logic and enhanced error handling
 */
async function sendMessage(retryCount = 0) {
    const text = userInput.value.trim();
    if (!text) return;

    // Übergang zum Chat-Modus beim ersten Senden
    if (isFirstMessage) {
        document.body.classList.add('chat-started');
        isFirstMessage = false;
        await sleep(400); // Smooth animation delay
    }

    // User Nachricht hinzufügen
    addMessage(text, 'user');
    userInput.value = '';
    userInput.style.height = '24px';

    // UI deaktivieren
    sendBtn.disabled = true;
    userInput.disabled = true;

    // Typing Indicator anzeigen
    showTypingIndicator();

    // Cold-Start Hinweis nach 10s - nur in Production (Container App Scale-to-Zero)
    const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    const coldStartTimer = !isLocal ? setTimeout(() => {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) {
            indicator.querySelector('.bubble').innerHTML += '<p style="font-size:0.75rem;opacity:0.6;margin-top:4px">⏳ Backend startet... (Scale-to-Zero, bitte kurz warten)</p>';
        }
    }, 10000) : null;

    try {
        // API-Aufruf mit Timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), CONFIG.REQUEST_TIMEOUT);
        
        const response = await fetch(CONFIG.API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: text,
                session_id: sessionId,
                selected_tool: selectedTool
            }),
            signal: controller.signal
        });

        clearTimeout(timeoutId);
        clearTimeout(coldStartTimer);

        // Rate Limiting Detection (429 Status)
        if (response.status === 429) {
            hideTypingIndicator();
            const retryAfter = response.headers.get('Retry-After') || 60;
            addMessage(`Zu viele Anfragen. Bitte warte ${retryAfter} Sekunden und versuche es erneut.`, 'agent', 'Error');
            return;
        }

        // Server Error Detection (5xx)
        if (response.status >= 500) {
            throw new Error(`Server-Fehler (${response.status}). Bitte versuche es später erneut.`);
        }

        // 4xx Fehler (z.B. 404 wenn Backend-URL falsch oder SWA abfängt)
        if (!response.ok) {
            let errorBody = '';
            try { errorBody = await response.text(); } catch (_) {}
            throw new Error(`HTTP ${response.status}: ${errorBody || 'Keine Antwort vom Backend.'}`);
        }

        // JSON sicher parsen
        let data;
        try {
            data = await response.json();
        } catch (parseError) {
            const rawText = '(leer)';
            throw new Error(`Backend-Antwort ist kein JSON. Backend-URL prüfen. Details: ${parseError.message}`);
        }
        hideTypingIndicator();

        if (data.error) {
            addMessage('Fehler: ' + data.error, 'agent', 'Error');
        } else {
            addMessage(data.response, 'agent', data.agent);
        }

        if (data.metadata && ['sent', 'cancelled'].includes(data.metadata.email_status)) {
            setSelectedTool(null);
        }

        // Sidebar auffrischen: ein frischer Chat bekommt jetzt erst seinen Titel (= erste
        // Nachricht) und taucht damit überhaupt in der Liste auf.
        if (window.AppShell) window.AppShell.refreshSessions(sessionId);

    } catch (error) {
        clearTimeout(coldStartTimer);
        hideTypingIndicator();

        // Retry logic for network errors
        if ((error.name === 'TypeError' || error.message.includes('Failed to fetch')) && retryCount < CONFIG.MAX_RETRIES) {
            const nextRetry = retryCount + 1;
            addMessage(`Verbindungsfehler. Versuche erneut (${nextRetry}/${CONFIG.MAX_RETRIES})...`, 'agent', 'Error');
            await sleep(CONFIG.RETRY_DELAY);
            // Retry mit gleicher Nachricht
            userInput.value = text;
            return sendMessage(nextRetry);
        }

        // Timeout Error
        if (error.name === 'AbortError') {
            addMessage('Die Anfrage hat zu lange gedauert. Bitte versuche es erneut.', 'agent', 'Error');
        } 
        // Network Error
        else if (error.name === 'TypeError') {
            addMessage('Verbindungsfehler: Keine Verbindung zum Server möglich. Bitte überprüfe deine Internetverbindung.', 'agent', 'Error');
        }
        // Other Errors
        else {
            addMessage('Fehler: ' + error.message, 'agent', 'Error');
        }
    } finally {
        // UI aktivieren
        sendBtn.disabled = false;
        userInput.disabled = false;
        userInput.focus();
    }
}

/**
 * Add message to chat container with proper ARIA announcements
 */
function addMessage(text, sender, agentName = null) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', sender);
    msgDiv.setAttribute('role', sender === 'agent' ? 'article' : 'article');

    let avatarHtml = '';
    let bubbleContent = '';

    if (sender === 'agent') {
        avatarHtml = `<div class="avatar agent" aria-hidden="true">${AGENT_ICON}</div>`;
        
        let agentLabel = '';
        if (agentName) {
            const agentClass = agentName.toLowerCase().replace('_', '');
            agentLabel = `<span class="agent-label ${agentClass}" role="status">${agentName}</span>`;
        }
        
        // Markdown parsen und rendern mit Sanitization
        const htmlContent = marked.parse(text);
        bubbleContent = `<div class="bubble">${agentLabel}${htmlContent}</div>`;
        msgDiv.innerHTML = avatarHtml + bubbleContent;
    } else {
        // User message - kein Markdown, nur escapen
        bubbleContent = `<div class="bubble"><p>${escapeHtml(text)}</p></div>`;
        msgDiv.innerHTML = bubbleContent;
    }

    chatContainer.appendChild(msgDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    // Screen Reader Announcement für neue Nachrichten
    announceToScreenReader(sender === 'agent' ? 'Antwort vom Agenten erhalten' : 'Nachricht gesendet');
}

/**
 * Show typing indicator
 */
function showTypingIndicator() {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', 'agent');
    msgDiv.id = 'typingIndicator';
    msgDiv.setAttribute('role', 'status');
    msgDiv.setAttribute('aria-live', 'polite');
    msgDiv.setAttribute('aria-label', 'Agent antwortet...');
    msgDiv.innerHTML = `
        <div class="avatar agent" aria-hidden="true">${AGENT_ICON}</div>
        <div class="bubble">
            <div class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    chatContainer.appendChild(msgDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

/**
 * Hide typing indicator
 */
function hideTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Screen Reader Announcements (Accessibility)
 */
function announceToScreenReader(message) {
    const announcement = document.createElement('div');
    announcement.setAttribute('role', 'status');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    announcement.style.position = 'absolute';
    announcement.style.left = '-10000px';
    announcement.style.width = '1px';
    announcement.style.height = '1px';
    announcement.style.overflow = 'hidden';
    
    document.body.appendChild(announcement);
    
    // Remove after announcement
    setTimeout(() => {
        document.body.removeChild(announcement);
    }, 1000);
}

/**
 * Marked.js Configuration with Sanitization
 */
if (typeof marked !== 'undefined') {
    marked.setOptions({
        breaks: true,
        gfm: true,
        headerIds: false,
        mangle: false,
        sanitize: false, // We use DOMPurify instead for better control
        // Note: For production, consider adding DOMPurify for HTML sanitization
    });
}

// =============================================================================
// SPEECH-TO-TEXT FUNCTIONALITY (Azure Speech Services)
// =============================================================================

/**
 * Initialize Speech-to-Text
 */
async function initializeSpeechRecognition() {
    if (typeof SpeechSDK === 'undefined') {
        console.error('Azure Speech SDK not loaded');
        micBtn.disabled = true;
        micBtn.title = 'Spracheingabe nicht verfügbar';
        return;
    }

    // Load credentials from backend
    try {
        const response = await fetch(API_CONFIG.baseURL + '/api/speech-config');
        const config = await response.json();
        
        if (!config.configured) {
            console.warn('Azure Speech not configured');
            micBtn.disabled = true;
            micBtn.title = 'Azure Speech nicht konfiguriert';
            return;
        }
        
        CONFIG.SPEECH_KEY = config.key;
        CONFIG.SPEECH_REGION = config.region;
        
        console.log('Azure Speech configured:', config.region);
        micBtn.addEventListener('click', toggleRecording);
        
    } catch (error) {
        console.error('Failed to load speech config:', error);
        micBtn.disabled = true;
        micBtn.title = 'Fehler beim Laden der Speech-Konfiguration';
    }
}

/**
 * Toggle Speech Recording
 */
async function toggleRecording() {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
}

/**
 * Start Speech Recognition
 */
function startRecording() {
    try {
        // Create speech config
        const speechConfig = SpeechSDK.SpeechConfig.fromSubscription(
            CONFIG.SPEECH_KEY, 
            CONFIG.SPEECH_REGION
        );
        speechConfig.speechRecognitionLanguage = CONFIG.SPEECH_LANGUAGE;

        // Create audio config (use default microphone)
        const audioConfig = SpeechSDK.AudioConfig.fromDefaultMicrophoneInput();

        // Create recognizer
        recognizer = new SpeechSDK.SpeechRecognizer(speechConfig, audioConfig);

        // Initialer State: Verbindung wird aufgebaut (kein Blinken)
        micBtn.classList.add('connecting');
        micBtn.setAttribute('data-tooltip', 'Verbindung...');
        sendBtn.disabled = true;
        userInput.placeholder = 'Verbindung zu Azure Speech...';

        // Event: Session Started (wenn tatsächlich verbunden)
        recognizer.sessionStarted = (s, e) => {
            console.log('Speech session started');
            // Reset des erkannten Textes bei neuer Session
            recognizedText = userInput.value || ''; // Behalte existierenden Text
            // Jetzt erst das Blinken starten
            isRecording = true;
            micBtn.classList.remove('connecting');
            micBtn.classList.add('recording');
            micBtn.setAttribute('data-tooltip', 'Stoppen');
            userInput.placeholder = 'Sprechen Sie jetzt...';
        };

        // Event: Recognizing (interim results)
        recognizer.recognizing = (s, e) => {
            if (e.result.reason === SpeechSDK.ResultReason.RecognizingSpeech) {
                // Timer zurücksetzen bei jeder Sprache-Erkennung
                clearTimeout(silenceTimer);
                
                // Zeige bisherigen Text + aktuell erkannten Text
                userInput.value = recognizedText + (recognizedText ? ' ' : '') + e.result.text;
                autoResize(userInput);
            }
        };

        // Event: Recognized (final result)
        recognizer.recognized = (s, e) => {
            if (e.result.reason === SpeechSDK.ResultReason.RecognizedSpeech) {
                // Hänge erkannten Text an den bisherigen Text an
                if (e.result.text) {
                    recognizedText += (recognizedText ? ' ' : '') + e.result.text;
                    userInput.value = recognizedText;
                    autoResize(userInput);
                    
                    // Starte Timer für automatisches Senden nach 5 Sekunden Stille
                    clearTimeout(silenceTimer);
                    silenceTimer = setTimeout(() => {
                        console.log('5 Sekunden Stille - sende automatisch');
                        stopRecording();
                        if (userInput.value.trim()) {
                            sendMessage();
                        }
                    }, AUTO_SEND_DELAY);
                }
            } else if (e.result.reason === SpeechSDK.ResultReason.NoMatch) {
                console.log('Keine Sprache erkannt');
            }
        };

        // Event: Canceled (error handling)
        recognizer.canceled = (s, e) => {
            console.error('Speech recognition canceled:', e.errorDetails);
            
            if (e.reason === SpeechSDK.CancellationReason.Error) {
                if (e.errorCode === SpeechSDK.CancellationErrorCode.ConnectionFailure) {
                    userInput.placeholder = 'Verbindungsfehler - Prüfe Azure Credentials';
                } else {
                    userInput.placeholder = 'Fehler bei Spracherkennung: ' + e.errorDetails;
                }
            }
            
            stopRecording();
        };

        // Start continuous recognition
        recognizer.startContinuousRecognitionAsync(
            () => {
                console.log('Speech recognition started');
            },
            (err) => {
                console.error('Failed to start speech recognition:', err);
                userInput.placeholder = 'Mikrofon-Zugriff verweigert oder Fehler';
                stopRecording();
            }
        );

    } catch (error) {
        console.error('Error starting speech recognition:', error);
        userInput.placeholder = 'Fehler beim Starten der Spracherkennung';
        stopRecording();
    }
}

/**
 * Stop Speech Recognition
 */
function stopRecording() {
    // Timer abbrechen
    clearTimeout(silenceTimer);
    silenceTimer = null;
    
    if (recognizer) {
        recognizer.stopContinuousRecognitionAsync(
            () => {
                console.log('Speech recognition stopped');
                recognizer.close();
                recognizer = null;
            },
            (err) => {
                console.error('Error stopping speech recognition:', err);
                recognizer.close();
                recognizer = null;
            }
        );
    }

    // Update UI
    isRecording = false;
    micBtn.classList.remove('recording');
    micBtn.classList.remove('connecting');
    micBtn.setAttribute('data-tooltip', 'Diktieren');
    sendBtn.disabled = false;
    userInput.placeholder = 'Frage etwas...';
    
    // Reset erkannten Text
    recognizedText = '';
}

// Initialize Speech Recognition on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeSpeechRecognition();
});

// Initial Focus
userInput.focus();

// Accessibility: Focus management
document.addEventListener('DOMContentLoaded', () => {
    userInput.setAttribute('aria-label', 'Nachricht eingeben');
    sendBtn.setAttribute('aria-label', 'Nachricht senden');

    // Initialize Speech Recognition
    initializeSpeechRecognition();
});


// =============================================================================
// AP4.6 — Session-Verwaltung (Verlauf überlebt Seitenwechsel und Serverneustart)
// =============================================================================

/** Alle Nachrichten aus dem Chatfenster entfernen und zurück in den Willkommens-Zustand. */
function resetChatView() {
    chatContainer.innerHTML = '';
    document.body.classList.remove('chat-started');
    isFirstMessage = true;
}

/** Den Chat in den "läuft bereits"-Zustand versetzen (Welcome-Screen weg). */
function enterChatMode() {
    document.body.classList.add('chat-started');
    isFirstMessage = false;
}

/** Eine neue Session anlegen und in sie wechseln. */
async function startNewSession() {
    const res = await fetch(`${API_CONFIG.baseURL}/api/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: '{}',
    });
    if (!res.ok) throw new Error(`Session konnte nicht angelegt werden (HTTP ${res.status})`);
    const data = await res.json();
    setActiveSession(data.session_id);
    resetChatView();
    setSelectedTool(null);
    if (window.AppShell) window.AppShell.refreshSessions(data.session_id);
    userInput.focus();
    return data.session_id;
}

function setActiveSession(id) {
    sessionId = String(id);
    localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
    if (window.AppShell) window.AppShell.setActiveSession(id);
    // Die Session-Id in der URL halten, damit ein Reload denselben Chat zeigt.
    const url = new URL(window.location.href);
    url.searchParams.set('session', sessionId);
    url.searchParams.delete('new');
    window.history.replaceState({}, '', url);
}

/** Den Verlauf einer Session aus der DB holen und rendern. */
async function loadSessionMessages(id) {
    const res = await fetch(`${API_CONFIG.baseURL}/api/sessions/${id}/messages`, {
        headers: { Accept: 'application/json' },
    });
    if (res.status === 404) return false;          // Session existiert nicht (mehr)
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const messages = await res.json();
    resetChatView();
    if (!messages.length) return true;

    enterChatMode();
    messages.forEach(m => {
        // addMessage() kennt genau zwei Sender: 'user' und 'agent'.
        addMessage(m.content, m.role === 'user' ? 'user' : 'agent',
                   m.role === 'user' ? null : (m.agent_name || null));
    });
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return true;
}

/** In eine andere Session wechseln (Klick in der Sidebar) — ohne Seiten-Reload. */
async function switchToSession(id) {
    if (String(id) === String(sessionId)) return;
    try {
        const ok = await loadSessionMessages(id);
        if (!ok) return;
        setSelectedTool(null);
        setActiveSession(id);
    } catch (err) {
        console.error('[Sessions] Wechsel fehlgeschlagen:', err);
    }
}

/**
 * Startzustand bestimmen:
 *   ?new=1        -> neue Session
 *   ?session=<id> -> diese Session öffnen (Deep-Link aus der Sidebar)
 *   localStorage  -> die zuletzt benutzte Session fortsetzen
 *   sonst         -> neue Session
 */
async function initSession() {
    const params = new URLSearchParams(window.location.search);
    const wantsNew = params.get('new') === '1';
    const fromUrl = params.get('session');
    const stored = localStorage.getItem(SESSION_STORAGE_KEY);

    try {
        if (wantsNew) {
            await startNewSession();
            return;
        }
        const candidate = fromUrl || stored;
        if (candidate) {
            const ok = await loadSessionMessages(candidate);
            if (ok) {
                setActiveSession(candidate);
                return;
            }
            // Session gibt es nicht mehr -> sauber neu anfangen
            localStorage.removeItem(SESSION_STORAGE_KEY);
        }
        await startNewSession();
    } catch (err) {
        console.error('[Sessions] Initialisierung fehlgeschlagen:', err);
        // Fallback: Chat bleibt benutzbar, das Backend legt dann selbst eine Session an.
        sessionId = stored || 'default';
    }
}

// Die Sidebar (shell.js) delegiert ihre Klicks hierher.
if (window.AppShell) {
    window.AppShell.onSelectSession = switchToSession;
    window.AppShell.onNewChat = () => startNewSession().catch(e => console.error(e));
}

document.addEventListener('DOMContentLoaded', initSession);
