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
}
