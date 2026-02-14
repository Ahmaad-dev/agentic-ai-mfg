// API Configuration für Frontend
const API_CONFIG = {
    // Automatische Erkennung: lokal vs. production
    baseURL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:8000'  // Local development
        : 'https://' + 'BACKEND_URL_PLACEHOLDER',  // Production - wird von Terraform output ersetzt
    
    endpoints: {
        chat: '/chat'
    }
};

// Helper function für API calls
async function callAPI(endpoint, data) {
    const response = await fetch(`${API_CONFIG.baseURL}${endpoint}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
    
    if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
}
