/**
 * AP4.6 — App-Shell (Sidebar) für alle Seiten.
 *
 * Warum als Skript und nicht als HTML-Block je Seite: die Sidebar erscheint auf index.html
 * UND review.html (später auch im Dashboard). Als kopiertes Markup würde sie unweigerlich
 * auseinanderlaufen; hier wird sie einmal gebaut und überall injiziert.
 *
 * Enthält:
 *   - Navigation (Chat / Review Board / Dashboard)
 *   - "Neuer Chat"
 *   - die Chat-Sessions aus der DB (GET /api/sessions) — der Grund, warum ein Wechsel ins
 *     Review Board den Verlauf nicht mehr verliert.
 *
 * chat.js hängt sich über `window.AppShell` ein (Sessions neu laden, aktive markieren).
 */
(function () {
    const API = (typeof API_CONFIG !== 'undefined' ? API_CONFIG.baseURL : '');
    const PAGE = window.location.pathname.toLowerCase().includes('review.html') ? 'review' : 'chat';

    const LOGO = `
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="shell_grad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#06b6d4" />
                    <stop offset="100%" style="stop-color:#84cc16" />
                </linearGradient>
            </defs>
            <path d="M12 2.5L20.66 7.5V17.5L12 22.5L3.34 17.5V7.5L12 2.5Z" stroke="url(#shell_grad)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M12 8L16.33 10.5V15.5L12 18L7.67 15.5V10.5L12 8Z" fill="url(#shell_grad)" fill-opacity="0.2" stroke="url(#shell_grad)" stroke-width="1"/>
        </svg>`;

    function esc(text) {
        const d = document.createElement('div');
        d.textContent = text == null ? '' : String(text);
        return d.innerHTML;
    }

    /** "vor 5 Min." / "Gestern" / Datum — kompakt genug für die schmale Spalte. */
    function relTime(iso) {
        if (!iso) return '';
        const d = new Date(iso);
        if (isNaN(d.getTime())) return '';
        const mins = Math.round((Date.now() - d.getTime()) / 60000);
        if (mins < 1) return 'gerade eben';
        if (mins < 60) return `vor ${mins} Min.`;
        if (mins < 60 * 24) return `vor ${Math.round(mins / 60)} Std.`;
        if (mins < 60 * 48) return 'gestern';
        return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' });
    }

    function build() {
        const el = document.createElement('aside');
        el.className = 'app-sidebar';
        el.innerHTML = `
            <div class="sb-brand">
                <span class="sb-logo" aria-hidden="true">${LOGO}</span>
                <span class="sb-brand-text">Agentic&nbsp;AI</span>
            </div>

            <button class="sb-new" id="sbNewChat" type="button">
                <span class="material-symbols-outlined" aria-hidden="true">add</span>
                Neuer Chat
            </button>

            <nav class="sb-nav" aria-label="Bereiche">
                <a class="sb-nav-item ${PAGE === 'chat' ? 'active' : ''}" href="index.html">
                    <span class="material-symbols-outlined" aria-hidden="true">forum</span>
                    Chat
                </a>
                <a class="sb-nav-item ${PAGE === 'review' ? 'active' : ''}" href="review.html">
                    <span class="material-symbols-outlined" aria-hidden="true">rule</span>
                    Review Board
                    <span class="sb-badge" id="sbPending" hidden></span>
                </a>
                <span class="sb-nav-item disabled" title="Kommt mit AP6">
                    <span class="material-symbols-outlined" aria-hidden="true">monitoring</span>
                    Dashboard
                    <span class="sb-soon">bald</span>
                </span>
            </nav>

            <div class="sb-section-label">Verlauf</div>
            <div class="sb-sessions" id="sbSessions" role="list">
                <div class="sb-muted">Lade…</div>
            </div>`;
        document.body.insertBefore(el, document.body.firstChild);
        return el;
    }

    const sidebar = build();
    const listEl = sidebar.querySelector('#sbSessions');
    const badgeEl = sidebar.querySelector('#sbPending');

    /** Aktive Session hervorheben (chat.js meldet die aktuelle Id). */
    function markActive(sessionId) {
        listEl.querySelectorAll('.sb-session').forEach(a => {
            a.classList.toggle('active', String(a.dataset.sessionId) === String(sessionId));
        });
    }

    async function loadSessions(activeId) {
        try {
            const res = await fetch(`${API}/api/sessions`, { headers: { Accept: 'application/json' } });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const sessions = await res.json();

            if (!sessions.length) {
                listEl.innerHTML = `<div class="sb-muted">Noch keine Unterhaltungen</div>`;
                return;
            }
            listEl.innerHTML = sessions.map(s => `
                <a class="sb-session" role="listitem" href="index.html?session=${s.session_id}"
                   data-session-id="${s.session_id}" title="${esc(s.title)}">
                    <span class="sb-session-title">${esc(s.title)}</span>
                    <span class="sb-session-meta">${esc(relTime(s.last_activity))} · ${s.message_count}</span>
                </a>`).join('');

            // Auf der Chat-Seite wird in-place gewechselt (kein Reload), sonst navigiert der Link.
            if (PAGE === 'chat' && window.AppShell.onSelectSession) {
                listEl.querySelectorAll('.sb-session').forEach(a => {
                    a.addEventListener('click', (e) => {
                        e.preventDefault();
                        window.AppShell.onSelectSession(Number(a.dataset.sessionId));
                    });
                });
            }
            markActive(activeId ?? window.AppShell.activeSessionId);
        } catch (err) {
            listEl.innerHTML = `<div class="sb-muted">Verlauf nicht ladbar</div>`;
        }
    }

    /** Anzahl offener Vorschläge als Badge — der Grund, überhaupt ins Board zu gehen. */
    async function loadPendingCount() {
        try {
            const res = await fetch(`${API}/api/review/proposals`, { headers: { Accept: 'application/json' } });
            if (!res.ok) return;
            const list = await res.json();
            if (Array.isArray(list) && list.length) {
                badgeEl.textContent = list.length;
                badgeEl.hidden = false;
            }
        } catch (_) { /* Badge ist Beiwerk — Fehler bleiben still */ }
    }

    window.AppShell = {
        page: PAGE,
        activeSessionId: null,
        onSelectSession: null,   // wird von chat.js gesetzt
        onNewChat: null,         // wird von chat.js gesetzt
        refreshSessions: loadSessions,
        setActiveSession(id) {
            this.activeSessionId = id;
            markActive(id);
        },
    };

    sidebar.querySelector('#sbNewChat').addEventListener('click', () => {
        if (PAGE === 'chat' && window.AppShell.onNewChat) {
            window.AppShell.onNewChat();
        } else {
            window.location.href = 'index.html?new=1';
        }
    });

    loadSessions();
    loadPendingCount();
})();
