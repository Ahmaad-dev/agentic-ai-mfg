// API Configuration für Frontend
const API_CONFIG = {
    // Automatische Erkennung: lokal vs. production
    baseURL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:8000'  // Local development
        : 'https://' + 'BACKEND_URL_PLACEHOLDER',  // Production - wird von deploy-frontend.yml ersetzt
};

// Schutz: Warnung wenn Placeholder nicht ersetzt wurde.
// WICHTIG: String ist gesplittet damit sed nur den echten Placeholder ersetzt, nicht diesen Guard.
const _unreplacedMarker = 'BACKEND_URL' + '_PLACEHOLDER';
if (API_CONFIG.baseURL.includes(_unreplacedMarker)) {
    console.error('[CONFIG] Backend-URL nicht konfiguriert! deploy-frontend.yml ausführen.');
    API_CONFIG.baseURL = '';
}
