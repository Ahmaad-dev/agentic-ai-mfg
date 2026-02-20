// API Configuration für Frontend
const API_CONFIG = {
    // Automatische Erkennung: lokal vs. production
    baseURL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:8000'  // Local development
        : 'https://' + 'BACKEND_URL_PLACEHOLDER',  // Production - wird von deploy-frontend.yml ersetzt
};

// Schutz: Warnung wenn Placeholder nicht ersetzt wurde
if (API_CONFIG.baseURL.includes('BACKEND_URL_PLACEHOLDER')) {
    console.error('[CONFIG] BACKEND_URL_PLACEHOLDER wurde nicht ersetzt! deploy-frontend.yml neu ausführen.');
    API_CONFIG.baseURL = '';
    // Zeige Fehler im Chat sobald DOM bereit ist
    window.addEventListener('DOMContentLoaded', () => {
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.innerHTML = `<div style="color:#ff6b6b;padding:1rem;border:1px solid #ff6b6b;border-radius:8px;margin:1rem">
                ⚠️ <strong>Konfigurationsfehler:</strong> Backend-URL nicht gesetzt.<br>
                Bitte den Workflow <code>deploy-frontend.yml</code> in GitHub Actions ausführen.
            </div>`;
        }
    });
}
