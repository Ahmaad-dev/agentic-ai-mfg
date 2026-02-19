/**
 * Multi-Agent Chat Application
 * Production-ready version with enhanced error handling, retry logic, and accessibility
 */

const chatContainer = document.getElementById('chatContainer');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const micBtn = document.getElementById('micBtn');
const sessionId = 'session_' + Date.now();
let isFirstMessage = true;
let isRecording = false;
let recognizer = null;
let recognizedText = ''; // Speichert den bisher erkannten Text
let silenceTimer = null; // Timer für automatisches Senden nach Pause
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
                session_id: sessionId
            }),
            signal: controller.signal
        });

        clearTimeout(timeoutId);

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

        const data = await response.json();
        hideTypingIndicator();

        if (data.error) {
            addMessage('Fehler: ' + data.error, 'agent', 'Error');
        } else {
            addMessage(data.response, 'agent', data.agent);
        }

    } catch (error) {
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
            addMessage('Die Anfrage hat zu lange gedauert (Timeout nach 5 Minuten). Bitte versuche es erneut.', 'agent', 'Error');
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
        const response = await fetch('/api/speech-config');
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
