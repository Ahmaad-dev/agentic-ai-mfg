/**
 * App-Shell für alle Seiten.  (AP4.6 — Redesign 2026-08-02)
 *
 * Warum als Skript und nicht als HTML-Block je Seite: die Shell erscheint auf index.html,
 * review.html UND dashboard.html. Als kopiertes Markup würde sie unweigerlich auseinander-
 * laufen; hier wird sie einmal gebaut und überall injiziert.
 *
 * REDESIGN: Die Navigation ist von der linken Sidebar in eine **Topbar mit Pill-Nav**
 * gewandert (Design "Agentic AI — Demo"). Der Chat-Verlauf bleibt als Drawer, aber nur noch
 * auf der Chat-Seite — Review Board und Dashboard bekommen dadurch die volle Breite.
 *
 * WICHTIG: Die öffentliche Schnittstelle `window.AppShell` ist UNVERÄNDERT geblieben
 * (activeSessionId, onSelectSession, onNewChat, refreshSessions, setActiveSession, page).
 * chat.js hängt daran und musste nicht angefasst werden.
 *
 * Enthält:
 *   - Topbar: Marke, Pill-Navigation (Chat / Review Board / Dashboard) inkl. Pending-Badge,
 *     Theme-Umschalter (hell/dunkel, in localStorage gemerkt)
 *   - Chat-Drawer: "Neuer Chat" + die Sessions aus der DB (GET /api/sessions) — der Grund,
 *     warum ein Wechsel ins Review Board den Verlauf nicht mehr verliert.
 */
(function () {
    const API = (typeof API_CONFIG !== 'undefined' ? API_CONFIG.baseURL : '');
    /* Seitenerkennung: primär über die Body-Klasse (die die Seite ohnehin für ihr Layout
       setzt), erst danach über den Dateinamen. Rein dateinamensbasiert war es brüchig —
       jede Kopie/Umbenennung einer Seite bekam stillschweigend das Chat-Layout. */
    const PATH = window.location.pathname.toLowerCase();
    const BODY = document.body.classList;
    const PAGE = BODY.contains('dashboard-page') || PATH.includes('dashboard.html') ? 'dashboard'
               : BODY.contains('review-page') || PATH.includes('review.html') ? 'review'
               : 'chat';

    /* ---------------------------------------------------------------- theme
       Light ist der Standard (wie im Design). Die Wahl überlebt den Seitenwechsel,
       sonst würde sie beim Sprung ins Review Board jedes Mal zurückspringen. */
    const THEME_KEY = 'agentic-theme';
    function applyTheme(mode) {
        document.documentElement.setAttribute('data-theme', mode === 'dark' ? 'dark' : 'light');
        try { localStorage.setItem(THEME_KEY, mode); } catch (_) { /* private mode */ }
    }
    function currentTheme() {
        // ?theme=dark|light gewinnt — praktisch für Deep-Links und für reproduzierbare
        // Screenshots (Doku/Bericht), ohne vorher im UI umschalten zu müssen.
        const forced = new URLSearchParams(window.location.search).get('theme');
        if (forced === 'dark' || forced === 'light') return forced;
        try {
            const saved = localStorage.getItem(THEME_KEY);
            if (saved === 'dark' || saved === 'light') return saved;
        } catch (_) { /* private mode */ }
        /* Noch nie umgeschaltet: der Systemeinstellung folgen statt stur hell zu starten.
           Eine EIGENE Wahl gewinnt aber immer — wer einmal auf hell gestellt hat, soll nicht
           beim nächsten Sonnenuntergang wieder im dunklen Theme sitzen. */
        try {
            if (window.matchMedia('(prefers-color-scheme: dark)').matches) return 'dark';
        } catch (_) { /* sehr alte Browser */ }
        return 'light';
    }
    applyTheme(currentTheme());

    const LOGO = `
        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="shell_grad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#3f7d5c" />
                    <stop offset="100%" style="stop-color:#8fae5d" />
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

    /* ------------------------------------------------------------- topbar */
    function buildTopbar() {
        const dark = currentTheme() === 'dark';
        const el = document.createElement('header');
        el.className = 'topbar';
        el.innerHTML = `
            <a class="brand" href="index.html" aria-label="Agentic AI — zur Startseite">
                <span class="brand-mark" aria-hidden="true">${LOGO}</span>
                <span class="brand-text">Agentic&nbsp;AI</span>
            </a>
            <nav class="pillnav" aria-label="Hauptnavigation">
                <a class="pill ${PAGE === 'chat' ? 'active' : ''}" href="index.html"
                   ${PAGE === 'chat' ? 'aria-current="page"' : ''}>
                    <span class="material-symbols-outlined" aria-hidden="true">forum</span>Chat
                </a>
                <a class="pill ${PAGE === 'review' ? 'active' : ''}" href="review.html"
                   ${PAGE === 'review' ? 'aria-current="page"' : ''}>
                    <span class="material-symbols-outlined" aria-hidden="true">rule</span>Review Board
                    <span class="pill-badge" id="sbPending" hidden></span>
                </a>
                <a class="pill ${PAGE === 'dashboard' ? 'active' : ''}" href="dashboard.html"
                   ${PAGE === 'dashboard' ? 'aria-current="page"' : ''}>
                    <span class="material-symbols-outlined" aria-hidden="true">monitoring</span>Management Dashboard
                </a>
            </nav>
            <div class="topbar-sp"></div>
            <button class="top-icon" id="sbTheme" type="button"
                    title="${dark ? 'Helles Design' : 'Dunkles Design'}"
                    aria-label="${dark ? 'Helles Design' : 'Dunkles Design'}">
                <span class="material-symbols-outlined" aria-hidden="true">${dark ? 'light_mode' : 'dark_mode'}</span>
            </button>`;
        return el;
    }

    /* ------------------------------------------------- chat sessions drawer */
    function buildDrawer() {
        const el = document.createElement('aside');
        el.className = 'app-sidebar';
        el.innerHTML = `
            <button class="sb-new" id="sbNewChat" type="button">
                <span class="material-symbols-outlined" aria-hidden="true">add</span>
                Neuer Chat
            </button>
            <div class="sb-search">
                <span class="material-symbols-outlined" aria-hidden="true">search</span>
                <input id="sbSearch" type="search" placeholder="Verlauf durchsuchen…"
                       aria-label="Verlauf durchsuchen" autocomplete="off">
                <button class="sb-search-clear" id="sbSearchClear" type="button"
                        aria-label="Suche leeren" hidden>
                    <span class="material-symbols-outlined" aria-hidden="true">close</span>
                </button>
            </div>
            <div class="sb-sessions" id="sbSessions" role="list">
                <div class="sb-section-label">Verlauf</div>
                <div class="sk-row"><span class="sk" style="height:13px;width:70%"></span></div>
                <div class="sk-row"><span class="sk" style="height:11px;width:45%"></span></div>
                <div class="sk-row"><span class="sk" style="height:13px;width:82%"></span></div>
                <div class="sk-row"><span class="sk" style="height:11px;width:38%"></span></div>
            </div>
            <div class="sb-foot">
                <button class="sb-collapse" id="sbCollapse" type="button" aria-label="Leiste einklappen">
                    <span class="material-symbols-outlined" aria-hidden="true">left_panel_close</span>
                    Leiste einklappen
                </button>
            </div>`;
        return el;
    }

    /* --------------------------------------------------- drawer ein/ausklappen
       Der Zustand überlebt den Seitenwechsel (wie das Theme) — wer die Leiste zuklappt,
       will sie nicht beim nächsten Chat-Aufruf wieder offen haben. */
    const COLLAPSE_KEY = 'agentic-sidebar-collapsed';
    function isCollapsed() {
        try { return localStorage.getItem(COLLAPSE_KEY) === '1'; } catch (_) { return false; }
    }
    function applyCollapsed(collapsed) {
        document.body.classList.toggle('sidebar-collapsed', collapsed);
        try { localStorage.setItem(COLLAPSE_KEY, collapsed ? '1' : '0'); } catch (_) { /* private mode */ }
        const drawer = document.querySelector('.app-sidebar');
        if (drawer) drawer.setAttribute('aria-hidden', collapsed ? 'true' : 'false');
    }

    /* ----------------------------------------------------------- assemble
       Die Topbar sitzt über allem, darunter eine Zeile aus (optionalem) Drawer und dem
       bereits vorhandenen Seiteninhalt. Die vorhandenen Knoten werden VERSCHOBEN, nicht neu
       erzeugt — Referenzen und getElementById in chat.js/review.js bleiben damit gültig. */
    const topbar = buildTopbar();
    const row = document.createElement('div');
    row.className = 'app-row';
    while (document.body.firstChild) row.appendChild(document.body.firstChild);
    document.body.appendChild(topbar);
    document.body.appendChild(row);

    let listEl = null;
    if (PAGE === 'chat') {
        const drawer = buildDrawer();
        row.insertBefore(drawer, row.firstChild);
        listEl = drawer.querySelector('#sbSessions');
        drawer.querySelector('#sbNewChat').addEventListener('click', () => {
            if (window.AppShell.onNewChat) window.AppShell.onNewChat();
            else window.location.href = 'index.html?new=1';
        });

        // Wiedereinblende-Knopf in den Inhaltsbereich hängen (der ist position:relative).
        const main = row.querySelector('.app-main') || row;
        const reopen = document.createElement('button');
        reopen.className = 'sb-reopen';
        reopen.id = 'sbReopen';
        reopen.type = 'button';
        reopen.title = 'Leiste ausklappen';
        reopen.setAttribute('aria-label', 'Leiste ausklappen');
        reopen.innerHTML = '<span class="material-symbols-outlined" aria-hidden="true">left_panel_open</span>';
        main.appendChild(reopen);

        drawer.querySelector('#sbCollapse').addEventListener('click', () => applyCollapsed(true));
        reopen.addEventListener('click', () => applyCollapsed(false));
        applyCollapsed(isCollapsed());
    }
    const badgeEl = topbar.querySelector('#sbPending');

    topbar.querySelector('#sbTheme').addEventListener('click', (e) => {
        const next = currentTheme() === 'dark' ? 'light' : 'dark';
        applyTheme(next);
        const btn = e.currentTarget;
        const label = next === 'dark' ? 'Helles Design' : 'Dunkles Design';
        btn.title = label;
        btn.setAttribute('aria-label', label);
        btn.querySelector('.material-symbols-outlined').textContent =
            next === 'dark' ? 'light_mode' : 'dark_mode';
    });

    /** Aktive Session hervorheben (chat.js meldet die aktuelle Id). */
    function markActive(sessionId) {
        if (!listEl) return;
        listEl.querySelectorAll('.sb-session').forEach(a => {
            a.classList.toggle('active', String(a.dataset.sessionId) === String(sessionId));
        });
    }

    /* Zuletzt geladene Sitzungen. Gehalten, damit die Suche beim Tippen NICHT jedes Mal
       den Server fragt — der Verlauf ist eine kurze Liste, die filtert man im Browser. */
    let allSessions = [];
    let sessQuery = '';

    /**
     * Zeitgruppen wie im Entwurf. Die Grenzen sind grob mit Absicht: gefragt ist
     * „diese Woche / diesen Monat / davor", nicht ein exaktes Alter. Ohne Zeitstempel
     * landet eine Sitzung bei „Älter" — nach unten, nicht fälschlich nach oben.
     */
    const SESSION_GROUPS = [
        ['week', 'Letzte 7 Tage', 7],
        ['month', 'Letzte 30 Tage', 30],
        ['older', 'Älter', Infinity],
    ];
    function groupOf(iso) {
        const ts = Date.parse(iso);
        if (!isFinite(ts)) return 'older';
        const days = (Date.now() - ts) / 86400000;
        return days < 7 ? 'week' : days < 30 ? 'month' : 'older';
    }

    function renderSessions(activeId) {
        if (!listEl) return;
        if (!allSessions.length) {
            listEl.innerHTML = `<div class="sb-muted">Noch keine Unterhaltungen</div>`;
            return;
        }
        const q = sessQuery.trim().toLowerCase();
        const hits = q ? allSessions.filter(s => (s.title || '').toLowerCase().includes(q))
                       : allSessions;
        if (!hits.length) {
            listEl.innerHTML = `<div class="sb-muted">Keine Unterhaltung gefunden</div>`;
            return;
        }
        /* Der Link und die beiden Aktionsknoepfe sind GESCHWISTER, nicht verschachtelt:
           ein <button> in einem <a> ist ungueltiges HTML, und der Browser wuerde beim Klick
           auf den Knopf trotzdem der Verlinkung folgen. */
        const item = (s) => `
            <div class="sb-session-row" data-session-id="${s.session_id}">
                <a class="sb-session" role="listitem" href="index.html?session=${s.session_id}"
                   data-session-id="${s.session_id}" title="${esc(s.title)}">
                    <span class="sb-session-title">${esc(s.title)}</span>
                    <span class="sb-session-meta">${esc(relTime(s.last_activity))} · ${s.message_count}</span>
                </a>
                <span class="sb-session-act">
                    <button type="button" data-act="rename" data-tooltip="Umbenennen"
                            aria-label="Unterhaltung umbenennen">
                        <span class="material-symbols-outlined" aria-hidden="true">edit</span>
                    </button>
                    <button type="button" data-act="hide" data-tooltip="Aus dem Verlauf nehmen"
                            aria-label="Aus dem Verlauf nehmen">
                        <span class="material-symbols-outlined" aria-hidden="true">delete</span>
                    </button>
                </span>
            </div>`;
        /* Bei aktiver Suche keine Zeitgruppen: wer sucht, will Treffer sehen, nicht
           drei Überschriften mit je einem Eintrag darunter. */
        listEl.innerHTML = q
            ? `<div class="sb-section-label">${hits.length} Treffer</div>${hits.map(item).join('')}`
            : SESSION_GROUPS
                .map(([key, label]) => [label, hits.filter(s => groupOf(s.last_activity) === key)])
                .filter(([, items]) => items.length)
                .map(([label, items]) =>
                    `<div class="sb-section-label">${label}</div>${items.map(item).join('')}`)
                .join('');

        // Auf der Chat-Seite wird in-place gewechselt (kein Reload), sonst navigiert der Link.
        if (window.AppShell.onSelectSession) {
            listEl.querySelectorAll('.sb-session').forEach(a => {
                a.addEventListener('click', (e) => {
                    e.preventDefault();
                    window.AppShell.onSelectSession(Number(a.dataset.sessionId));
                });
            });
        }
        listEl.querySelectorAll('[data-act]').forEach(b => {
            b.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const id = Number(b.closest('.sb-session-row').dataset.sessionId);
                if (b.dataset.act === 'rename') startRename(id);
                else hideSession(id);
            });
        });
        markActive(activeId ?? window.AppShell.activeSessionId);
    }

    /** PATCH auf die Session. Wirft, damit der Aufrufer den Fehler NICHT verschluckt. */
    async function patchSession(id, body) {
        const res = await fetch(`${API}/api/sessions/${id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
            body: JSON.stringify(body),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
    }

    /**
     * Umbenennen direkt in der Zeile. Enter uebernimmt, Escape verwirft, Verlassen des
     * Feldes uebernimmt ebenfalls — sonst verliert man seine Eingabe durch einen Klick
     * daneben, ohne dass irgendetwas darauf hingewiesen haette.
     * Ein LEERER Titel ist kein Fehler: er setzt auf den aus der ersten Nachricht
     * abgeleiteten Titel zurueck. Das ist die einzige Art, eine Umbenennung rueckgaengig
     * zu machen, ohne den alten Text zu kennen.
     */
    function startRename(id) {
        const row = listEl.querySelector(`.sb-session-row[data-session-id="${id}"]`);
        const titleEl = row && row.querySelector('.sb-session-title');
        if (!titleEl || row.querySelector('.sb-rename')) return;
        const before = titleEl.textContent;
        const input = document.createElement('input');
        input.className = 'sb-rename';
        input.type = 'text';
        input.value = before;
        input.setAttribute('aria-label', 'Neuer Titel');
        titleEl.replaceWith(input);
        /* Erst im naechsten Frame fokussieren. Direkt nach `replaceWith` ist das Element
           zwar im Dokument, aber der Fokus geht in manchen Browsern noch verloren, weil
           der Klick auf den Knopf gerade erst abgearbeitet wird. */
        requestAnimationFrame(() => { input.focus(); input.select(); });

        let settled = false;
        const finish = async (commit) => {
            if (settled) return;
            settled = true;
            const value = input.value.trim();
            const span = document.createElement('span');
            span.className = 'sb-session-title';
            span.textContent = commit ? (value || before) : before;
            input.replaceWith(span);
            if (!commit || value === before) return;
            try {
                await patchSession(id, { title: value });
                await loadSessions();
                window.AppShell.toast(value ? 'Umbenannt' : 'Titel zurückgesetzt', 'edit');
            } catch (_) {
                window.AppShell.toast('Umbenennen fehlgeschlagen', 'error');
                loadSessions();
            }
        };
        input.addEventListener('keydown', (e) => {
            e.stopPropagation();                       // nicht die Palette oeffnen
            if (e.key === 'Enter') { e.preventDefault(); finish(true); }
            else if (e.key === 'Escape') { e.preventDefault(); finish(false); }
        });
        input.addEventListener('blur', () => finish(true));
        input.addEventListener('click', (e) => e.stopPropagation());
    }

    /**
     * Aus dem Verlauf nehmen — mit „Rueckgaengig".
     *
     * Das ist der eine Ort, an dem ein Rueckgaengig-Knopf ehrlich ist: es wird NICHTS
     * geloescht. Der Server setzt nur `hidden_at`; Nachrichten und Agent-Laeufe bleiben
     * stehen, damit sich die Dashboard-Kennzahlen nicht rueckwirkend aendern. Der Knopf
     * setzt das Feld wieder zurueck.
     */
    async function hideSession(id) {
        const row = listEl.querySelector(`.sb-session-row[data-session-id="${id}"]`);
        const name = row ? row.querySelector('.sb-session-title').textContent : 'Unterhaltung';
        try {
            await patchSession(id, { hidden: true });
        } catch (_) {
            window.AppShell.toast('Konnte nicht ausgeblendet werden', 'error');
            return;
        }
        await loadSessions();
        // War es die gerade offene Unterhaltung, muss der Chat einen frischen Stand bekommen.
        if (window.AppShell.activeSessionId === id && window.AppShell.onNewChat) {
            window.AppShell.onNewChat();
        }
        window.AppShell.toastAction(
            `„${name}" aus dem Verlauf genommen`, 'inbox', 'Rückgängig',
            async () => {
                try {
                    await patchSession(id, { hidden: false });
                    await loadSessions();
                    window.AppShell.toast('Wieder im Verlauf', 'check_circle');
                } catch (_) {
                    window.AppShell.toast('Wiederherstellen fehlgeschlagen', 'error');
                }
            });
    }

    async function loadSessions(activeId) {
        if (!listEl) return;   // Review/Dashboard führen keinen Verlauf
        try {
            const res = await fetch(`${API}/api/sessions`, { headers: { Accept: 'application/json' } });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            allSessions = await res.json();
            renderSessions(activeId);
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

    /* ---------------------------------------------------------------- Meldungen
       Kurze Bestätigung unten rechts, statt den Nutzer raten zu lassen, ob eine Aktion
       angekommen ist. Bewusst NICHT für Fehler: die gehören an die Stelle, an der sie
       entstanden sind, und dürfen nicht nach ein paar Sekunden verschwinden.
       `toastAction` trägt einen Knopf (z. B. „Rückgängig") und bleibt länger stehen. */
    let toastWrap = null;
    function pushToast({ msg, icon, actionLabel, onAction }) {
        if (!toastWrap) {
            toastWrap = document.createElement('div');
            toastWrap.className = 'toast-wrap';
            toastWrap.setAttribute('role', 'status');
            toastWrap.setAttribute('aria-live', 'polite');
            document.body.appendChild(toastWrap);
        }
        const el = document.createElement('div');
        el.className = 'toast';
        el.innerHTML =
            '<span class="material-symbols-outlined" aria-hidden="true">'
            + esc(icon || 'check_circle') + '</span>'
            + '<span class="toast-msg">' + esc(msg) + '</span>';
        if (actionLabel && onAction) {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'toast-act';
            btn.textContent = actionLabel;
            btn.addEventListener('click', () => { remove(); onAction(); });
            el.appendChild(btn);
        }
        toastWrap.appendChild(el);
        let done = false;
        function remove() {
            if (done) return;
            done = true;
            el.classList.add('out');
            setTimeout(() => el.remove(), 220);
        }
        // Mit Knopf länger stehenlassen — sonst ist die Aktion weg, bevor man sie liest.
        setTimeout(remove, actionLabel ? 6000 : 2800);
        return remove;
    }

    /* ------------------------------------------------------------ Kommandopalette
       Strg/Cmd+K. Die Einträge werden bei jedem Öffnen NEU gebaut, damit der Verlauf und
       der Theme-Eintrag den aktuellen Stand zeigen und nicht den beim Seitenaufbau. */
    let cmdEl = null, cmdSel = 0, cmdItems = [];

    function baseCommands() {
        const dark = currentTheme() === 'dark';
        const cmds = [
            { icon: 'forum', title: 'Chat öffnen', desc: 'Zur Unterhaltung',
              run: () => go('index.html') },
            { icon: 'rule', title: 'Review Board öffnen', desc: 'Offene Vorschläge prüfen',
              run: () => go('review.html') },
            { icon: 'monitoring', title: 'Management Dashboard öffnen', desc: 'Kennzahlen und Charts',
              run: () => go('dashboard.html') },
            { icon: 'add', title: 'Neuer Chat', desc: 'Frische Unterhaltung starten',
              run: () => {
                  if (PAGE === 'chat' && window.AppShell.onNewChat) window.AppShell.onNewChat();
                  else go('index.html?new=1');
              } },
            { icon: dark ? 'light_mode' : 'dark_mode',
              title: dark ? 'Helles Design' : 'Dunkles Design',
              desc: 'Erscheinungsbild wechseln',
              run: () => document.getElementById('sbTheme').click() },
        ];
        if (PAGE === 'chat') {
            cmds.push({
                icon: isCollapsed() ? 'left_panel_open' : 'left_panel_close',
                title: isCollapsed() ? 'Leiste ausklappen' : 'Leiste einklappen',
                desc: 'Verlauf ein- oder ausblenden',
                run: () => applyCollapsed(!isCollapsed()),
            });
            allSessions.slice(0, 30).forEach(s => cmds.push({
                icon: 'forum',
                title: s.title || 'Unterhaltung',
                desc: 'Verlauf, ' + relTime(s.last_activity),
                run: () => {
                    if (window.AppShell.onSelectSession) {
                        window.AppShell.onSelectSession(Number(s.session_id));
                    } else {
                        go('index.html?session=' + s.session_id);
                    }
                },
            }));
        }
        return cmds;
    }

    function go(href) { window.location.href = href; }

    function renderCmd(query) {
        const q = query.trim().toLowerCase();
        cmdItems = baseCommands().filter(c =>
            !q || (c.title + ' ' + c.desc).toLowerCase().includes(q));
        if (cmdSel >= cmdItems.length) cmdSel = Math.max(0, cmdItems.length - 1);
        const list = cmdEl.querySelector('.cmd-list');
        list.innerHTML = cmdItems.length
            ? cmdItems.map((c, i) =>
                '<button class="cmd-item ' + (i === cmdSel ? 'sel' : '') + '" role="option"'
                + ' aria-selected="' + (i === cmdSel) + '" data-i="' + i + '">'
                + '<span class="ci"><span class="material-symbols-outlined" aria-hidden="true">'
                + esc(c.icon) + '</span></span>'
                + '<span><span class="ct">' + esc(c.title) + '</span>'
                + '<span class="cd">' + esc(c.desc) + '</span></span></button>').join('')
            : '<div class="cmd-empty">Kein Treffer</div>';
        list.querySelectorAll('.cmd-item').forEach(b => {
            b.addEventListener('click', () => runCmd(Number(b.dataset.i)));
            b.addEventListener('mousemove', () => {
                cmdSel = Number(b.dataset.i);
                list.querySelectorAll('.cmd-item').forEach((x, i) =>
                    x.classList.toggle('sel', i === cmdSel));
            });
        });
        const sel = list.querySelector('.cmd-item.sel');
        if (sel) sel.scrollIntoView({ block: 'nearest' });
    }

    function runCmd(i) {
        const c = cmdItems[i];
        closeCmd();
        if (c) c.run();
    }

    /* Wohin der Fokus nach dem Schliessen zurueckkehrt. Ohne das landet er am
       Dokumentanfang, und wer die Palette per Tastatur geoeffnet hat, faengt von vorn an. */
    let cmdReturnFocus = null;

    function openCmd() {
        if (cmdEl) return;
        cmdSel = 0;
        cmdReturnFocus = document.activeElement;
        cmdEl = document.createElement('div');
        cmdEl.className = 'cmd-layer';
        cmdEl.innerHTML =
            '<div class="cmd-scrim"></div>'
            + '<div class="cmd" role="dialog" aria-modal="true" aria-label="Befehle">'
            + '<div class="cmd-in">'
            + '<span class="material-symbols-outlined" aria-hidden="true">search</span>'
            + '<input type="text" id="cmdInput" autocomplete="off"'
            + ' placeholder="Springe zu… oder tippe einen Befehl" aria-label="Befehl suchen">'
            + '<span class="esc">ESC</span></div>'
            + '<div class="cmd-list" role="listbox" aria-label="Befehle"></div></div>';
        document.body.appendChild(cmdEl);
        const input = cmdEl.querySelector('#cmdInput');
        renderCmd('');
        input.focus();
        input.addEventListener('input', () => { cmdSel = 0; renderCmd(input.value); });
        input.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                cmdSel = Math.min(cmdItems.length - 1, cmdSel + 1);
                renderCmd(input.value);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                cmdSel = Math.max(0, cmdSel - 1);
                renderCmd(input.value);
            } else if (e.key === 'Enter') {
                e.preventDefault();
                runCmd(cmdSel);
            } else if (e.key === 'Escape') {
                e.preventDefault();
                closeCmd();
            }
        });
        cmdEl.querySelector('.cmd-scrim').addEventListener('click', closeCmd);

        /* Tastaturfalle. `aria-modal="true"` behauptet gegenueber Screenreadern, der Rest
           der Seite sei stillgelegt — ohne das hier waere das schlicht falsch: gemessen
           blieben 13 Elemente HINTER der Verdunkelung mit Tab erreichbar. Der Fokus laeuft
           jetzt im Kreis innerhalb des Dialogs. */
        cmdEl.addEventListener('keydown', (e) => {
            if (e.key !== 'Tab') return;
            const f = cmdEl.querySelectorAll(
                'input, button, [href], [tabindex]:not([tabindex="-1"])');
            if (!f.length) return;
            const first = f[0], last = f[f.length - 1];
            if (e.shiftKey && document.activeElement === first) {
                e.preventDefault(); last.focus();
            } else if (!e.shiftKey && document.activeElement === last) {
                e.preventDefault(); first.focus();
            }
        });
    }

    function closeCmd() {
        if (!cmdEl) return;
        cmdEl.remove();
        cmdEl = null;
        if (cmdReturnFocus && document.contains(cmdReturnFocus)) {
            try { cmdReturnFocus.focus(); } catch (_) { /* entfernt oder nicht fokussierbar */ }
        }
        cmdReturnFocus = null;
    }

    document.addEventListener('keydown', (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            if (cmdEl) closeCmd(); else openCmd();
        }
    });

    window.AppShell = {
        page: PAGE,
        activeSessionId: null,
        onSelectSession: null,   // wird von chat.js gesetzt
        onNewChat: null,         // wird von chat.js gesetzt
        refreshSessions: loadSessions,
        toast: (msg, icon) => pushToast({ msg, icon }),
        toastAction: (msg, icon, actionLabel, onAction) =>
            pushToast({ msg, icon, actionLabel, onAction }),
        openCommandPalette: openCmd,
        setActiveSession(id) {
            this.activeSessionId = id;
            markActive(id);
        },
    };

    /* `document` statt der lokalen `drawer`-Variablen: die ist auf den Chat-Zweig
       beschraenkt, hier unten liefe sie in einen ReferenceError. */
    const searchEl = document.getElementById('sbSearch');
    const clearEl = document.getElementById('sbSearchClear');
    if (searchEl) {
        searchEl.addEventListener('input', () => {
            sessQuery = searchEl.value;
            clearEl.hidden = !sessQuery;
            renderSessions();
        });
        // Escape leert das Feld, statt (wie bei type="search" ueblich) nur den Fokus zu behalten.
        searchEl.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && searchEl.value) { e.stopPropagation(); clearSearch(); }
        });
        clearEl.addEventListener('click', clearSearch);
    }
    function clearSearch() {
        searchEl.value = '';
        sessQuery = '';
        clearEl.hidden = true;
        renderSessions();
        searchEl.focus();
    }

    loadSessions();
    loadPendingCount();
})();
