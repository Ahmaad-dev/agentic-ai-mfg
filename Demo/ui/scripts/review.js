/**
 * Review Board — AP4.1 (list) + AP4.2 (detail / before-after diff) + AP4.3.1 (approve/reject).
 * Lists open correction proposals and shows a detail view with a diff and the decision panel.
 * Reuses API_CONFIG.baseURL (config.js) and the same fetch/error style as chat.js.
 * Modify is not wired yet (AP4.3.2) — its button is present but disabled.
 */

const REVIEW_CONFIG = {
    REQUEST_TIMEOUT: 30000, // 30s — a plain DB read, no LLM in the loop
    // approve/modify apply synchronously: pipeline + two server validation jobs. The
    // backend's own worst case is far higher (3 tools x 3 retries x 90s), but a healthy
    // run is seconds; 180s covers a slow-but-working apply without hanging the UI forever.
    DECISION_TIMEOUT: 180000,
    API_ENDPOINT: API_CONFIG.baseURL + '/api/review/proposals',
};

/** Set when a decision was recorded, so the list is refetched on the way back. */
let listStale = false;

const proposalList = document.getElementById('proposalList');
const refreshBtn = document.getElementById('refreshBtn');
const filterBar = document.getElementById('filterBar');
const listView = document.getElementById('listView');
const detailView = document.getElementById('detailView');

/** Fixed, logical column order for workItemConfig objects (do NOT trust Object.keys). */
const WORKITEM_COLUMNS = ['workItemKey', 'rampUpTime', 'netTimeFactor', 'sequence'];

/**
 * Escape HTML to prevent XSS (same helper as chat.js).
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text == null ? '' : String(text);
    return div.innerHTML;
}

/**
 * Format an ISO timestamp for display; falls back to the raw value.
 */
function formatDate(iso) {
    if (!iso) return '—';
    const d = new Date(iso);
    if (isNaN(d.getTime())) return escapeHtml(iso);
    return d.toLocaleString('de-DE', {
        year: 'numeric', month: '2-digit', day: '2-digit',
        hour: '2-digit', minute: '2-digit',
    });
}

/**
 * Confidence as a labelled bar (0..1 -> 0..100%).
 */
function confidenceBar(score) {
    if (typeof score !== 'number') {
        return '<span class="rb-muted">n/a</span>';
    }
    const pct = Math.round(score * 100);
    const level = pct >= 75 ? 'high' : (pct >= 50 ? 'mid' : 'low');
    return `
        <div class="rb-confidence" title="${pct}% Konfidenz">
            <div class="rb-confidence-track">
                <div class="rb-confidence-fill ${level}" style="width:${pct}%"></div>
            </div>
            <span class="rb-confidence-value">${pct}%</span>
        </div>`;
}

/**
 * Render one proposal as a card. The AP3.5 fields (correction_kind,
 * target_entity_id) are shown only when present ("wenn vorhanden").
 */
function renderProposal(p) {
    const idParts = [];
    if (p.correction_kind) {
        idParts.push(`<span class="rb-chip rb-chip-kind">${escapeHtml(p.correction_kind)}</span>`);
    }
    if (p.target_entity_id) {
        const entity = p.target_entity_type ? `${escapeHtml(p.target_entity_type)}: ` : '';
        idParts.push(`<span class="rb-chip rb-chip-entity" title="Zielobjekt">${entity}${escapeHtml(p.target_entity_id)}</span>`);
    }
    const ap35 = idParts.length ? `<div class="rb-chips">${idParts.join('')}</div>` : '';

    return `
        <article class="rb-card" role="listitem" tabindex="0" data-proposal-id="${escapeHtml(p.proposal_id)}" aria-label="Vorschlag ${escapeHtml(p.error_type || '')} öffnen">
            <div class="rb-card-head">
                <span class="rb-error-type">${escapeHtml(p.error_type || 'UNKNOWN')}</span>
                <span class="rb-status rb-status-${escapeHtml((p.status || '').replace(/[^a-z_]/gi, ''))}">${escapeHtml(p.status || '—')}</span>
            </div>
            <div class="rb-card-body">
                <div class="rb-field rb-field-wide">
                    <span class="rb-label">Snapshot</span>
                    <span class="rb-snapshot">
                        <span class="rb-value rb-mono rb-selectable">${escapeHtml(p.snapshot_id || '—')}</span>
                        <button class="rb-copy" type="button" data-copy="${escapeHtml(p.snapshot_id || '')}" title="Snapshot-ID kopieren" aria-label="Snapshot-ID kopieren">
                            <span class="material-symbols-outlined" aria-hidden="true">content_copy</span>
                        </button>
                    </span>
                </div>
                <div class="rb-field">
                    <span class="rb-label">Ziel-Pfad</span>
                    <span class="rb-value rb-mono">${escapeHtml(p.target_path || '—')}</span>
                </div>
                <div class="rb-field">
                    <span class="rb-label">Konfidenz</span>
                    ${confidenceBar(p.confidence_score)}
                </div>
                <div class="rb-field">
                    <span class="rb-label">Erstellt</span>
                    <span class="rb-value">${formatDate(p.created_at)}</span>
                </div>
            </div>
            ${ap35}
        </article>`;
}

/**
 * Snapshot filter.
 *
 * The board lists open proposals SYSTEM-WIDE, not per snapshot. Without a filter a reviewer
 * who came here from one snapshot's chat sees proposals for other snapshots too and cannot
 * tell them apart ("this error doesn't even exist in my snapshot"). The filter is
 * client-side (the list is small) and can be preset via ?snapshot=<id>.
 */
let allProposals = [];
let snapshotFilter = new URLSearchParams(window.location.search).get('snapshot') || 'all';

function renderFilterBar() {
    const ids = [...new Set(allProposals.map(p => p.snapshot_id))];
    if (!filterBar) return;

    // Only worth showing when more than one snapshot is involved.
    if (ids.length < 2) {
        filterBar.hidden = true;
        return;
    }
    if (!ids.includes(snapshotFilter)) snapshotFilter = 'all';

    const count = id => allProposals.filter(p => p.snapshot_id === id).length;
    const options = [
        `<option value="all"${snapshotFilter === 'all' ? ' selected' : ''}>Alle Snapshots (${allProposals.length})</option>`,
        ...ids.map(id => `<option value="${escapeHtml(id)}"${snapshotFilter === id ? ' selected' : ''}>`
            + `${escapeHtml(id.slice(0, 8))}… (${count(id)})</option>`),
    ].join('');

    filterBar.hidden = false;
    filterBar.innerHTML = `
        <label class="rb-label" for="snapshotFilter">Snapshot</label>
        <select id="snapshotFilter" class="rb-filter-select">${options}</select>`;

    document.getElementById('snapshotFilter').addEventListener('change', (e) => {
        snapshotFilter = e.target.value;
        renderList();
    });
}

/** Render the (optionally filtered) list plus the filter bar. */
function renderList() {
    renderFilterBar();
    const shown = snapshotFilter === 'all'
        ? allProposals
        : allProposals.filter(p => p.snapshot_id === snapshotFilter);

    if (shown.length === 0) {
        renderEmpty();
        return;
    }
    proposalList.innerHTML = shown.map(renderProposal).join('');
}

/**
 * Render helpers for the non-list states.
 */
function renderEmpty() {
    proposalList.innerHTML = `
        <div class="rb-empty">
            <span class="material-symbols-outlined" aria-hidden="true">inbox</span>
            <p>Keine offenen Vorschläge</p>
            <span class="rb-muted">Sobald das System einen Korrekturvorschlag erzeugt, erscheint er hier.</span>
        </div>`;
}

function renderError(message) {
    proposalList.innerHTML = `
        <div class="rb-error" role="alert">
            <span class="material-symbols-outlined" aria-hidden="true">error</span>
            <p>Vorschläge konnten nicht geladen werden</p>
            <span class="rb-muted">${escapeHtml(message)}</span>
        </div>`;
}

function renderLoading() {
    proposalList.innerHTML = `
        <div class="rb-loading" aria-busy="true">
            <span class="material-symbols-outlined rb-spin" aria-hidden="true">progress_activity</span>
            <span class="rb-muted">Lade offene Vorschläge…</span>
        </div>`;
}

/**
 * Fetch and render the open proposals. Same error handling shape as chat.js:
 * timeout via AbortController, explicit 5xx / non-ok / non-JSON / network branches.
 */
async function loadProposals() {
    renderLoading();
    refreshBtn.disabled = true;

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), REVIEW_CONFIG.REQUEST_TIMEOUT);

        const response = await fetch(REVIEW_CONFIG.API_ENDPOINT, {
            method: 'GET',
            headers: { 'Accept': 'application/json' },
            signal: controller.signal,
        });
        clearTimeout(timeoutId);

        if (response.status >= 500) {
            throw new Error(`Server-Fehler (${response.status}). Bitte später erneut versuchen.`);
        }
        if (!response.ok) {
            let body = '';
            try { body = await response.text(); } catch (_) {}
            throw new Error(`HTTP ${response.status}: ${body || 'Keine Antwort vom Backend.'}`);
        }

        let data;
        try {
            data = await response.json();
        } catch (parseError) {
            throw new Error(`Backend-Antwort ist kein JSON. Backend-URL prüfen. Details: ${parseError.message}`);
        }

        if (!Array.isArray(data)) {
            throw new Error('Unerwartetes Antwortformat (kein Array).');
        }

        allProposals = data;
        renderList();

    } catch (error) {
        if (error.name === 'AbortError') {
            renderError('Zeitüberschreitung — das Backend hat nicht rechtzeitig geantwortet.');
        } else if (error.name === 'TypeError' || error.message.includes('Failed to fetch')) {
            renderError('Keine Verbindung zum Backend. Läuft der Server (web_server.py)?');
        } else {
            renderError(error.message);
        }
    } finally {
        refreshBtn.disabled = false;
    }
}

// =============================================================================
// AP4.2 — detail view (before/after diff, read-only)
// =============================================================================

/** Snapshot id block with the full, selectable id + copy button (reused from AP4.1). */
function snapshotIdBlock(snapshotId) {
    return `
        <span class="rb-snapshot">
            <span class="rb-value rb-mono rb-selectable">${escapeHtml(snapshotId || '—')}</span>
            <button class="rb-copy" type="button" data-copy="${escapeHtml(snapshotId || '')}" title="Snapshot-ID kopieren" aria-label="Snapshot-ID kopieren">
                <span class="material-symbols-outlined" aria-hidden="true">content_copy</span>
            </button>
        </span>`;
}

/** True for values shown as a single scalar (Fall A). */
function isScalar(v) {
    return v === null || ['string', 'number', 'boolean'].includes(typeof v);
}

/** True when v is a non-empty array whose items are all plain objects (Fall B). */
function isArrayOfObjects(v) {
    return Array.isArray(v) && v.length > 0
        && v.every(x => x && typeof x === 'object' && !Array.isArray(x));
}

/** Render one cell value; undefined/absent -> empty string (never "undefined"). */
function cell(v) {
    if (v === undefined) return '';
    if (v === null) return '<span class="rb-muted">null</span>';
    return escapeHtml(v);
}

/**
 * Choose columns for an array of objects: the fixed workItemConfig order when the objects
 * look like workItemConfigs, otherwise the union of keys in first-seen order (never
 * Object.keys of a single object, which would miss optional keys like `sequence`).
 */
function columnsFor(objects) {
    if (objects.every(o => 'workItemKey' in o)) return WORKITEM_COLUMNS;
    const seen = [];
    for (const o of objects) {
        for (const k of Object.keys(o)) if (!seen.includes(k)) seen.push(k);
    }
    return seen;
}

/** Table of objects with a fixed column order; `variant` = 'old' | 'new' for colouring. */
function objectTable(objects, variant) {
    const cols = columnsFor(objects);
    const head = cols.map(c => `<th>${escapeHtml(c)}</th>`).join('');
    const rows = objects.map(o => `
        <tr class="rb-diff-row rb-diff-${variant}">
            ${cols.map(c => `<td>${cell(o[c])}</td>`).join('')}
        </tr>`).join('');
    return `<table class="rb-diff-table"><thead><tr>${head}</tr></thead><tbody>${rows}</tbody></table>`;
}

/** The before/after diff, dispatching on the type of suggested_value. */
function renderDiff(oldValue, newValue) {
    // Fall B — array of objects (e.g. the 13 workItemConfigs).
    if (isArrayOfObjects(newValue)) {
        const before = (Array.isArray(oldValue) && oldValue.length === 0)
            ? `<div class="rb-empty-before">(leer) — 0 Einträge</div>`
            : (isArrayOfObjects(oldValue)
                ? objectTable(oldValue, 'old')
                : `<div class="rb-diff-scalar rb-old">${cell(oldValue)}</div>`);
        return `
            <div class="rb-diff">
                <div class="rb-diff-side">
                    <div class="rb-diff-head rb-diff-head-old">Vorher</div>
                    ${before}
                </div>
                <div class="rb-diff-side">
                    <div class="rb-diff-head rb-diff-head-new">Nachher — ${newValue.length} neue Einträge</div>
                    ${objectTable(newValue, 'new')}
                </div>
            </div>`;
    }

    // Fallback — array of scalars: show as a list.
    if (Array.isArray(newValue)) {
        const before = (Array.isArray(oldValue) && oldValue.length === 0)
            ? `<div class="rb-empty-before">(leer) — 0 Einträge</div>`
            : `<ul class="rb-list-old">${(Array.isArray(oldValue) ? oldValue : [oldValue]).map(x => `<li>${cell(x)}</li>`).join('')}</ul>`;
        return `
            <div class="rb-diff">
                <div class="rb-diff-side">
                    <div class="rb-diff-head rb-diff-head-old">Vorher</div>${before}
                </div>
                <div class="rb-diff-side">
                    <div class="rb-diff-head rb-diff-head-new">Nachher — ${newValue.length} Einträge</div>
                    <ul class="rb-list-new">${newValue.map(x => `<li>${cell(x)}</li>`).join('')}</ul>
                </div>
            </div>`;
    }

    // Fall A — single scalar: old struck through in red, new in green.
    const emptyOld = (oldValue === '' || oldValue === null || oldValue === undefined);
    return `
        <div class="rb-diff rb-diff-scalar-wrap">
            <div class="rb-diff-side">
                <div class="rb-diff-head rb-diff-head-old">Vorher</div>
                ${emptyOld ? '<div class="rb-empty-before">(leer)</div>' : `<div class="rb-diff-scalar rb-old"><s>${cell(oldValue)}</s></div>`}
            </div>
            <div class="rb-diff-side">
                <div class="rb-diff-head rb-diff-head-new">Nachher</div>
                <div class="rb-diff-scalar rb-new">${cell(newValue)}</div>
            </div>
        </div>`;
}

/** Additional proposal updates arrive under the detail API's `evidence` alias. */
function renderAdditionalUpdates(evidence) {
    if (!Array.isArray(evidence) || evidence.length === 0) return '';

    const updates = evidence.map((update, index) => {
        const item = (update && typeof update === 'object' && !Array.isArray(update))
            ? update : {};
        return `
            <div class="rb-detail-section">
                <div class="rb-field rb-field-wide">
                    <span class="rb-label">Update ${index + 1} · Ziel-Pfad</span>
                    <span class="rb-value rb-mono">${escapeHtml(item.target_path || '—')}</span>
                </div>
                ${renderDiff(item.current_value, item.new_value)}
            </div>`;
    }).join('');

    return `
        <div class="rb-detail-section">
            <h3>Zusatz-Updates</h3>
            ${updates}
        </div>`;
}

/** Full detail view for one proposal. */
function renderDetail(p) {
    const ctxChips = [
        p.error_type ? `<span class="rb-chip rb-chip-error">${escapeHtml(p.error_type)}</span>` : '',
        p.correction_kind ? `<span class="rb-chip rb-chip-kind">${escapeHtml(p.correction_kind)}</span>` : '',
        p.target_entity_id ? `<span class="rb-chip rb-chip-entity">${escapeHtml(p.target_entity_type || 'entity')}: ${escapeHtml(p.target_entity_id)}</span>` : '',
        p.status ? `<span class="rb-status rb-status-${escapeHtml((p.status || '').replace(/[^a-z_]/gi, ''))}">${escapeHtml(p.status)}</span>` : '',
    ].filter(Boolean).join('');

    const evidenceBlock = (Array.isArray(p.evidence) && p.evidence.length > 0)
        ? `<div class="rb-detail-section">
               <h3>Evidence</h3>
               <pre class="rb-code">${escapeHtml(JSON.stringify(p.evidence, null, 2))}</pre>
           </div>`
        : '';
    const additionalUpdatesBlock = renderAdditionalUpdates(p.evidence);

    detailView.innerHTML = `
        <div class="rb-detail-topbar">
            <button class="review-refresh" id="backBtn" type="button">
                <span class="material-symbols-outlined" aria-hidden="true">arrow_back</span>
                Zurück zur Liste
            </button>
        </div>

        <div class="rb-detail-context">
            <div class="rb-chips rb-chips-top">${ctxChips}</div>
            <div class="rb-field rb-field-wide">
                <span class="rb-label">Ziel-Pfad</span>
                <span class="rb-value rb-mono">${escapeHtml(p.target_path || '—')}</span>
            </div>
            <div class="rb-field rb-field-wide">
                <span class="rb-label">Snapshot</span>
                ${snapshotIdBlock(p.snapshot_id)}
            </div>
            <div class="rb-field">
                <span class="rb-label">Konfidenz</span>
                ${confidenceBar(p.confidence_score)}
            </div>
        </div>

        ${renderConfidenceBreakdown(p)}

        <div class="rb-detail-section" id="codeContextSection" hidden>
            <h3>Fehlerstelle im Original (<code>snapshot-data.json</code>)</h3>
            <div id="codeContext"></div>
        </div>

        <div class="rb-detail-section">
            <h3>Änderung (Vorher / Nachher)</h3>
            ${renderDiff(p.old_value, p.suggested_value)}
        </div>

        <div class="rb-detail-section">
            <h3>Begründung</h3>
            <p class="rb-reasoning">${escapeHtml(p.reasoning || '—')}</p>
        </div>

        ${additionalUpdatesBlock}

        ${evidenceBlock}

        ${renderDecisionPanel(p)}
    `;

    document.getElementById('backBtn').addEventListener('click', showList);
    wireDecisionPanel(p);
    loadCodeContext(p.proposal_id);   // asynchron nachladen, blockiert die Ansicht nicht
    showDetail();
}

/**
 * AP4.7 — die betroffene Stelle 1:1 aus snapshot-data.json, mit echten Zeilennummern.
 *
 * Ein `target_path` allein ist für eine Entscheidung zu wenig: der Reviewer muss den
 * Datensatz im Original sehen (im sdfsdf-Fall steht z. B. die `demandId D122873_001` direkt
 * über der Fehlerzeile — genau der Beleg, aus dem die KI ihren Wert ableitet).
 * Darstellung wie ein Diff-Hunk: Zeilennummern-Spalte, Fehlerzeilen rot hinterlegt.
 */
async function loadCodeContext(proposalId) {
    const section = document.getElementById('codeContextSection');
    const host = document.getElementById('codeContext');
    if (!section || !host) return;

    try {
        const res = await fetch(
            `${REVIEW_CONFIG.API_ENDPOINT}/${encodeURIComponent(proposalId)}/context`,
            { headers: { Accept: 'application/json' } }
        );
        if (!res.ok) return;   // kein Kontext ermittelbar -> Block bleibt einfach aus
        const ctx = await res.json();
        if (!Array.isArray(ctx.lines) || !ctx.lines.length) return;

        const rows = ctx.lines.map(l => `
            <div class="rb-code-line${l.highlight ? ' err' : ''}">
                <span class="rb-code-num">${l.n}</span>
                <span class="rb-code-text">${escapeHtml(l.text)}</span>
            </div>`).join('');

        host.innerHTML = `
            <div class="rb-codeview">
                <div class="rb-code-head">
                    <span class="material-symbols-outlined" aria-hidden="true">data_object</span>
                    <span class="rb-mono">${escapeHtml(ctx.file)}</span>
                    <span class="rb-muted">Zeile ${ctx.error_line} von ${ctx.total_lines}</span>
                </div>
                <div class="rb-code-body">${rows}</div>
                ${ctx.truncated ? '<div class="rb-code-foot rb-muted">… Wertblock gekürzt</div>' : ''}
            </div>`;
        section.hidden = false;
    } catch (_) {
        /* Kontext ist Zusatzinfo — ein Fehler darf die Detailansicht nicht stören */
    }
}

/**
 * AP4.5 — why is the confidence what it is?
 *
 * A bare percentage is not reviewable. The decisive part is `value_grounded`: a DETERMINISTIC
 * check of whether the proposed value is provable from the data or was constructed by the LLM.
 * It is the signal that catches an overconfident model — e.g. a de-duplication ID the LLM
 * rated 0.9 that already existed on another record (which would have created a NEW duplicate).
 * Shown as a warning when not grounded, so the reviewer looks closer exactly there.
 */
function renderConfidenceBreakdown(p) {
    if (p.value_grounded === null || p.value_grounded === undefined) return '';

    const grounded = Number(p.value_grounded) >= 1;
    const cls = grounded ? 'ok' : 'warn';
    const icon = grounded ? 'verified' : 'warning';
    const title = grounded
        ? 'Wert ist in den Daten belegt'
        : 'Wert ist NICHT in den Daten belegt — bitte genau prüfen';

    const rationale = p.confidence_rationale
        ? `<p class="rb-muted rb-conf-rationale">Selbsteinschätzung der KI:
             ${escapeHtml(p.confidence_rationale)}</p>`
        : '';

    return `
        <div class="rb-detail-section">
            <h3>Woher kommt die Konfidenz?</h3>
            <div class="rb-grounded ${cls}">
                <span class="material-symbols-outlined" aria-hidden="true">${icon}</span>
                <div>
                    <strong>${escapeHtml(title)}</strong>
                    <p class="rb-muted">${escapeHtml(p.value_grounded_reason || '—')}</p>
                </div>
            </div>
            ${rationale}
        </div>`;
}

// =============================================================================
// AP4.3.1 — decision panel (approve / reject; modify follows in AP4.3.2)
// =============================================================================

/**
 * The decision panel. Only a `pending_review` proposal can be decided — for any other
 * status the backend answers 409-A ("already decided"), so the buttons are not offered.
 */
function renderDecisionPanel(p) {
    if (p.status !== 'pending_review') {
        return `
            <div class="rb-detail-section rb-actions">
                <h3>Entscheidung</h3>
                <div class="rb-decision-status info">
                    Dieser Vorschlag ist bereits entschieden (Status:
                    <strong>${escapeHtml(p.status || '—')}</strong>) und kann nicht erneut
                    entschieden werden.
                </div>
            </div>`;
    }

    return `
        <div class="rb-detail-section rb-actions">
            <h3>Entscheidung</h3>
            <label class="rb-label" for="rbComment">
                Kommentar <span class="rb-muted">(Pflicht beim Ablehnen)</span>
            </label>
            <textarea id="rbComment" class="rb-comment" rows="3"
                      placeholder="Begründung der Entscheidung…"></textarea>

            <div class="rb-btn-row">
                <button class="rb-btn rb-btn-approve" id="approveBtn" type="button">
                    <span class="material-symbols-outlined" aria-hidden="true">check_circle</span>
                    <span class="rb-btn-text">Genehmigen &amp; anwenden</span>
                </button>
                <button class="rb-btn rb-btn-reject" id="rejectBtn" type="button">
                    <span class="material-symbols-outlined" aria-hidden="true">cancel</span>
                    <span class="rb-btn-text">Ablehnen</span>
                </button>
                <button class="rb-btn rb-btn-modify" id="modifyBtn" type="button">
                    <span class="material-symbols-outlined" aria-hidden="true">edit</span>
                    <span class="rb-btn-text">Wert ändern…</span>
                </button>
            </div>

            <p class="rb-muted rb-hint">
                „Genehmigen" wendet die Korrektur nach der Freigabe direkt auf die
                Snapshot-Daten an und validiert erneut — das kann einige Sekunden dauern.
                „Ablehnen" ist endgültig und ändert nichts. „Wert ändern" wendet den
                <strong>von dir bearbeiteten</strong> Wert an; der KI-Vorschlag bleibt als
                Historie erhalten.
            </p>

            ${renderModifyEditor(p)}

            <div class="rb-decision-status" id="decisionStatus" role="status" hidden></div>
        </div>`;
}

/**
 * AP4.3.2b — the modify editor.
 *
 * `final_value` is the WHOLE value, not a delta (AP4.3.0/AP4.3.2a): for
 * …__iteration-5 that is the complete 13-object workItemConfigs array. Hence a JSON
 * textarea rather than a single input. The textarea is pre-filled from `suggested_value`
 * (pretty-printed) and edited in place; on submit the text is JSON.parse'd and the
 * PARSED value is posted — never the raw string. (apply_correction has an auto-parse for
 * strings starting with `[`/`{`, so posting a string would work by accident; we do not
 * rely on that runtime workaround — AP4.3.2a, Fallstrick 3.)
 */
function renderModifyEditor(p) {
    // additional_updates travel in the `evidence` field (see backlog). They keep the AI's
    // values even after a modify (PT4 guardrail: one approval per proposal) — say so.
    const extraNote = (Array.isArray(p.evidence) && p.evidence.length > 0)
        ? `<p class="rb-muted rb-hint">Hinweis: die
             ${p.evidence.length} Zusatz-Update(s) dieses Vorschlags bleiben unverändert
             die KI-Werte — geändert wird nur der Hauptwert.</p>`
        : '';

    return `
        <div class="rb-modify-editor" id="modifyEditor" hidden>
            <label class="rb-label" for="rbFinalValue">
                Finaler Wert (JSON) — ersetzt den KI-Vorschlag für
                <code>${escapeHtml(p.target_path || '—')}</code>
            </label>
            <textarea id="rbFinalValue" class="rb-json" rows="16" spellcheck="false"
                      aria-describedby="jsonHint"></textarea>
            <div class="rb-json-hint" id="jsonHint" role="status"></div>
            ${extraNote}
            <div class="rb-btn-row">
                <button class="rb-btn rb-btn-approve" id="modifySubmitBtn" type="button">
                    <span class="material-symbols-outlined" aria-hidden="true">save</span>
                    <span class="rb-btn-text">Übernehmen &amp; anwenden</span>
                </button>
                <button class="rb-btn" id="modifyCancelBtn" type="button">
                    <span class="material-symbols-outlined" aria-hidden="true">close</span>
                    <span class="rb-btn-text">Abbrechen</span>
                </button>
            </div>
        </div>`;
}

function wireDecisionPanel(p) {
    const approveBtn = document.getElementById('approveBtn');
    const rejectBtn = document.getElementById('rejectBtn');
    if (!approveBtn || !rejectBtn) return; // already-decided panel has no buttons
    approveBtn.addEventListener('click', () => submitDecision(p.proposal_id, 'approve'));
    rejectBtn.addEventListener('click', () => submitDecision(p.proposal_id, 'reject'));

    const modifyBtn = document.getElementById('modifyBtn');
    const editor = document.getElementById('modifyEditor');
    const textarea = document.getElementById('rbFinalValue');
    if (!modifyBtn || !editor || !textarea) return;

    // Pre-fill via .value (not innerHTML) — no escaping problem, and the textarea keeps
    // exactly the JSON the backend sent.
    textarea.value = JSON.stringify(p.suggested_value, null, 2);

    modifyBtn.addEventListener('click', () => {
        editor.hidden = !editor.hidden;
        if (!editor.hidden) {
            validateJsonInput(p);
            textarea.focus();
        }
    });
    textarea.addEventListener('input', () => validateJsonInput(p));
    document.getElementById('modifyCancelBtn').addEventListener('click', () => {
        editor.hidden = true;
    });
    document.getElementById('modifySubmitBtn').addEventListener('click', () => {
        const parsed = validateJsonInput(p);
        if (parsed === INVALID) return; // hint already explains why
        submitDecision(p.proposal_id, 'modify', parsed);
    });
}

/** Sentinel: distinguishes "invalid" from a legitimately parsed `null`/`false`/`0`. */
const INVALID = Symbol('invalid');

/**
 * Validate the textarea and render the live hint. Returns the parsed value, or INVALID.
 * Blocks: JSON syntax errors, an empty string and null (AP4.3.0 Lücke 4 — the backend
 * only rejects a missing/null final_value, so "" would otherwise be applied verbatim).
 */
function validateJsonInput(p) {
    const textarea = document.getElementById('rbFinalValue');
    const hint = document.getElementById('jsonHint');
    if (!textarea || !hint) return INVALID;

    const raw = textarea.value.trim();
    if (!raw) {
        hint.className = 'rb-json-hint error';
        hint.textContent = 'Kein Wert eingegeben.';
        return INVALID;
    }

    let parsed;
    try {
        parsed = JSON.parse(raw);
    } catch (e) {
        hint.className = 'rb-json-hint error';
        hint.textContent = `Kein gültiges JSON: ${e.message}`;
        return INVALID;
    }

    if (parsed === null || parsed === '') {
        hint.className = 'rb-json-hint error';
        hint.textContent = 'Leerer Wert (null bzw. "") wird nicht angewendet.';
        return INVALID;
    }

    // Type mismatch is NOT blocked (the backend schema accepts any JSON type and would
    // write it verbatim — AP4.3.2a, Lücke 2), but it must be visible.
    const aiIsArray = Array.isArray(p.suggested_value);
    const newIsArray = Array.isArray(parsed);
    const describe = v => Array.isArray(v) ? `Array mit ${v.length} Einträgen` : typeof v;

    if (aiIsArray !== newIsArray) {
        hint.className = 'rb-json-hint warn';
        hint.textContent = `Gültiges JSON, aber der Typ weicht vom KI-Vorschlag ab: `
            + `${describe(p.suggested_value)} → ${describe(parsed)}. Wird so angewendet.`;
        return parsed;
    }

    const keyProblems = checkObjectKeys(parsed, p.suggested_value);
    if (keyProblems.length) {
        hint.className = 'rb-json-hint warn';
        hint.textContent = `Gültiges JSON — ${describe(parsed)}. Achtung: ${keyProblems.join('; ')}. `
            + `Wird so angewendet.`;
        return parsed;
    }

    hint.className = 'rb-json-hint ok';
    hint.textContent = `Gültiges JSON — ${describe(parsed)}.`;
    return parsed;
}

/**
 * Per-object key check for an array of objects (AP4.3.2b-Ergänzung).
 *
 * Catches hand-edit typos (`netTimeFacotr`) and dropped keys BEFORE they are written
 * verbatim to the server: the backend schema accepts any JSON, so nothing downstream
 * would notice. Warns only — a reviewer may deliberately deviate, so this never blocks.
 *
 * Expected keys come from the AI proposal itself (union of the keys it used), falling
 * back to WORKITEM_COLUMNS for workItemConfig objects. `sequence` is genuinely optional
 * in the AI data (only BA01 carries it), so a MISSING key is only reported when it is
 * missing from the corresponding AI object too — otherwise every row would warn.
 */
function checkObjectKeys(parsed, aiValue) {
    if (!isArrayOfObjects(parsed) || !isArrayOfObjects(aiValue)) return [];

    const expected = new Set(columnsFor(aiValue));
    const unexpected = new Map(); // key -> [row indices]
    const missing = new Map();

    parsed.forEach((obj, i) => {
        if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return;
        const keys = Object.keys(obj);
        for (const k of keys) {
            if (!expected.has(k)) {
                if (!unexpected.has(k)) unexpected.set(k, []);
                unexpected.get(k).push(i);
            }
        }
        // Only flag a missing key if the AI object at the same position had it — that
        // keeps optional keys (e.g. `sequence`) from producing noise on every row.
        const aiObj = aiValue[i];
        if (aiObj && typeof aiObj === 'object') {
            for (const k of Object.keys(aiObj)) {
                if (!keys.includes(k)) {
                    if (!missing.has(k)) missing.set(k, []);
                    missing.get(k).push(i);
                }
            }
        }
    });

    const rows = idx => idx.map(i => `#${i}`).join(', ');
    const problems = [];
    for (const [k, idx] of unexpected) {
        problems.push(`unbekannter Key "${k}" in Objekt ${rows(idx)} (Tippfehler?)`);
    }
    for (const [k, idx] of missing) {
        problems.push(`fehlender Key "${k}" in Objekt ${rows(idx)}`);
    }
    if (parsed.length !== aiValue.length) {
        problems.push(`Anzahl geändert: ${aiValue.length} → ${parsed.length} Objekte`);
    }
    return problems;
}

/** `kind` = 'ok' | 'warn' | 'error' | 'info'. */
function showDecisionStatus(kind, html) {
    const el = document.getElementById('decisionStatus');
    if (!el) return;
    el.className = `rb-decision-status ${kind}`;
    el.innerHTML = html;
    el.hidden = false;
}

/** Every button that must be locked once a decision is recorded. */
const DECISION_BUTTON_IDS = ['approveBtn', 'rejectBtn', 'modifyBtn', 'modifySubmitBtn'];

function decisionButtons() {
    return DECISION_BUTTON_IDS.map(id => document.getElementById(id)).filter(Boolean);
}

/** The button that shows the spinner for a given decision. */
function actingButton(decision) {
    const id = { reject: 'rejectBtn', modify: 'modifySubmitBtn' }[decision] || 'approveBtn';
    return document.getElementById(id);
}

/** Disable/enable the decision buttons; `busy` shows a spinner on the acting one. */
function setDecisionBusy(busy, acting) {
    decisionButtons().forEach(b => { b.disabled = busy; });
    const btn = actingButton(acting);
    if (btn) btn.classList.toggle('busy', busy);
}

/** Lock the panel for good — the decision is recorded and cannot be repeated. */
function lockDecisionPanel() {
    decisionButtons().forEach(b => {
        b.disabled = true;
        b.classList.remove('busy');
    });
    const comment = document.getElementById('rbComment');
    if (comment) comment.disabled = true;
    const textarea = document.getElementById('rbFinalValue');
    if (textarea) textarea.disabled = true;
}

/** Human-readable errors_before -> errors_after line, when the backend reported it. */
function revalidationLine(rr) {
    if (!rr) return '';
    const before = rr.errors_before;
    const after = rr.errors_after;
    if (typeof before !== 'number' && typeof after !== 'number') return '';
    const fmt = v => (typeof v === 'number' ? v : '?');
    return ` Server-Validierung: <strong>${fmt(before)}</strong> Fehler vorher →
             <strong>${fmt(after)}</strong> Fehler nachher.`;
}

/** Progress line while the request is in flight. */
const BUSY_TEXT = {
    approve: 'Vorschlag wird genehmigt und angewendet — Snapshot wird neu validiert…',
    modify: 'Geänderter Wert wird übernommen und angewendet — Snapshot wird neu validiert…',
    reject: 'Ablehnung wird gespeichert…',
};

/**
 * POST one decision. Contract (AP4.3.0):
 *   approve → {comment?}                        | 200: applied=true, status="applied"
 *   reject  → {comment REQUIRED}                | 200: status="rejected", applied=false
 *   modify  → {final_value REQUIRED, comment?}  | 200: applied=true, value_source=human_modify
 * Two different 409s exist and mean opposite things:
 *   409-A "already decided"  → nothing was written; the proposal was not pending.
 *   409-B apply guard blocked → the DECISION IS RECORDED, only the apply was refused.
 * 409-B carries the decide fields (review_id/decision); that is how we tell them apart.
 * 502 → decision recorded, apply pipeline failed.
 * All three decisions share this response handling (AP4.3.2c — no separate modify path).
 */
async function submitDecision(proposalId, decision, finalValue) {
    const commentEl = document.getElementById('rbComment');
    const comment = (commentEl ? commentEl.value : '').trim();

    // The backend rejects an empty comment on reject with 400; catch it before the round trip.
    if (decision === 'reject' && !comment) {
        showDecisionStatus('error', 'Für eine Ablehnung ist ein Kommentar erforderlich.');
        if (commentEl) commentEl.focus();
        return;
    }

    const payload = comment ? { comment } : {};
    if (decision === 'modify') {
        payload.final_value = finalValue; // the PARSED value, never the raw textarea string
    }

    setDecisionBusy(true, decision);
    showDecisionStatus('info', BUSY_TEXT[decision]);

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), REVIEW_CONFIG.DECISION_TIMEOUT);

        const response = await fetch(
            `${REVIEW_CONFIG.API_ENDPOINT}/${encodeURIComponent(proposalId)}/${decision}`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                body: JSON.stringify(payload),
                signal: controller.signal,
            }
        );
        clearTimeout(timeoutId);

        let data = {};
        try { data = await response.json(); } catch (_) { /* keep {} — handled below */ }

        // --- 200: decided (and, for approve, applied) ---------------------------------
        if (response.ok) {
            listStale = true;
            lockDecisionPanel();
            if (decision === 'reject') {
                showDecisionStatus('ok',
                    `Vorschlag <strong>abgelehnt</strong>. Neuer Status:
                     <strong>${escapeHtml(data.status || 'rejected')}</strong>.
                     Es wurde nichts angewendet.`);
            } else {
                const what = decision === 'modify'
                    ? 'Geänderter Wert <strong>übernommen und angewendet</strong>'
                    : 'Vorschlag <strong>genehmigt und angewendet</strong>';
                showDecisionStatus('ok',
                    `${what}. Neuer Status:
                     <strong>${escapeHtml(data.status || 'applied')}</strong>
                     (Wertquelle: ${escapeHtml(data.value_source || '—')}).
                     ${revalidationLine(data.revalidation_result)}`);
            }
            return;
        }

        // --- 409: two opposite meanings ------------------------------------------------
        if (response.status === 409) {
            const decisionRecorded = (data.review_id !== undefined || data.decision !== undefined);
            if (decisionRecorded) {
                // 409-B — the guard refused to apply, but the decision stands.
                listStale = true;
                lockDecisionPanel();
                const guard = data.guard ? ` (${escapeHtml(data.guard)})` : '';
                showDecisionStatus('warn',
                    `Entscheidung <strong>gespeichert</strong> (Status:
                     <strong>${escapeHtml(data.status || '—')}</strong>), aber das Anwenden wurde
                     <strong>blockiert</strong>${guard}: ${escapeHtml(data.reason || data.error || '')}
                     — an den Snapshot-Daten wurde nichts geändert.`);
            } else {
                // 409-A — nothing was written; the proposal was not pending any more.
                listStale = true;
                lockDecisionPanel();
                showDecisionStatus('warn',
                    `Dieser Vorschlag wurde bereits entschieden (Status:
                     <strong>${escapeHtml(data.status || '—')}</strong>). Es wurde nichts geändert.`);
            }
            return;
        }

        // --- 502: decision stands, the apply pipeline failed ---------------------------
        if (response.status === 502) {
            listStale = true;
            lockDecisionPanel();
            showDecisionStatus('error',
                `Entscheidung <strong>gespeichert</strong> (Status:
                 <strong>${escapeHtml(data.status || '—')}</strong>), aber das Anwenden ist
                 <strong>fehlgeschlagen</strong>${data.failed_at ? ` bei Schritt
                 <code>${escapeHtml(data.failed_at)}</code>` : ''}:
                 ${escapeHtml(data.detail || data.error || 'Unbekannter Fehler.')}`);
            return;
        }

        // --- 400 / 404 / other ---------------------------------------------------------
        if (response.status === 400) {
            showDecisionStatus('error', escapeHtml(data.error || 'Ungültige Anfrage (400).'));
            setDecisionBusy(false, decision);
            return;
        }
        if (response.status === 404) {
            showDecisionStatus('error', 'Vorschlag nicht gefunden (404).');
            lockDecisionPanel();
            return;
        }
        if (response.status >= 500) {
            showDecisionStatus('error', `Server-Fehler (${response.status}). Bitte später erneut versuchen.`);
            setDecisionBusy(false, decision);
            return;
        }
        showDecisionStatus('error',
            `HTTP ${response.status}: ${escapeHtml(data.error || 'Unerwartete Antwort vom Backend.')}`);
        setDecisionBusy(false, decision);

    } catch (error) {
        // A timeout here is genuinely ambiguous: the apply may still be running server-side.
        if (error.name === 'AbortError') {
            showDecisionStatus('warn',
                'Zeitüberschreitung — das Backend hat nicht rechtzeitig geantwortet. ' +
                'Die Entscheidung kann trotzdem gespeichert worden sein; Status über die Liste prüfen.');
            listStale = true;
            lockDecisionPanel();
        } else if (error.name === 'TypeError' || error.message.includes('Failed to fetch')) {
            showDecisionStatus('error', 'Keine Verbindung zum Backend. Läuft der Server (web_server.py)?');
            setDecisionBusy(false, decision);
        } else {
            showDecisionStatus('error', escapeHtml(error.message));
            setDecisionBusy(false, decision);
        }
    }
}

function showDetail() {
    listView.hidden = true;
    detailView.hidden = false;
    window.scrollTo(0, 0);
}

function showList() {
    detailView.hidden = true;
    listView.hidden = false;
    // A decided proposal is no longer pending, so it must drop out of the list.
    if (listStale) {
        listStale = false;
        loadProposals();
    }
}

/** Fetch one proposal's full detail (same fetch/error shape as loadProposals). */
async function openProposal(proposalId) {
    detailView.innerHTML = `
        <div class="rb-detail-topbar">
            <button class="review-refresh" type="button" onclick="showList()">
                <span class="material-symbols-outlined" aria-hidden="true">arrow_back</span> Zurück zur Liste
            </button>
        </div>
        <div class="rb-loading" aria-busy="true">
            <span class="material-symbols-outlined rb-spin" aria-hidden="true">progress_activity</span>
            <span class="rb-muted">Lade Details…</span>
        </div>`;
    showDetail();

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), REVIEW_CONFIG.REQUEST_TIMEOUT);
        const response = await fetch(`${REVIEW_CONFIG.API_ENDPOINT}/${encodeURIComponent(proposalId)}`, {
            method: 'GET', headers: { 'Accept': 'application/json' }, signal: controller.signal,
        });
        clearTimeout(timeoutId);

        if (response.status === 404) throw new Error('Vorschlag nicht gefunden (404).');
        if (response.status >= 500) throw new Error(`Server-Fehler (${response.status}).`);
        if (!response.ok) {
            let body = ''; try { body = await response.text(); } catch (_) {}
            throw new Error(`HTTP ${response.status}: ${body || 'Keine Antwort.'}`);
        }
        const data = await response.json();
        renderDetail(data);
    } catch (error) {
        const msg = (error.name === 'AbortError') ? 'Zeitüberschreitung.'
            : (error.name === 'TypeError' || error.message.includes('Failed to fetch'))
                ? 'Keine Verbindung zum Backend.' : error.message;
        detailView.innerHTML = `
            <div class="rb-detail-topbar">
                <button class="review-refresh" type="button" onclick="showList()">
                    <span class="material-symbols-outlined" aria-hidden="true">arrow_back</span> Zurück zur Liste
                </button>
            </div>
            <div class="rb-error" role="alert">
                <span class="material-symbols-outlined" aria-hidden="true">error</span>
                <p>Details konnten nicht geladen werden</p>
                <span class="rb-muted">${escapeHtml(msg)}</span>
            </div>`;
    }
}

/**
 * Delegated click on the list: copy button (AP4.1) OR open a card's detail (AP4.2).
 */
proposalList.addEventListener('click', async (e) => {
    const copyBtn = e.target.closest('.rb-copy');
    if (copyBtn) {
        const id = copyBtn.getAttribute('data-copy');
        if (!id) return;
        try {
            await navigator.clipboard.writeText(id);
            const icon = copyBtn.querySelector('.material-symbols-outlined');
            const prev = icon.textContent;
            icon.textContent = 'check';
            copyBtn.classList.add('copied');
            setTimeout(() => { icon.textContent = prev; copyBtn.classList.remove('copied'); }, 1200);
        } catch (_) { /* clipboard may be blocked; id stays selectable */ }
        return; // do not open the detail when copying
    }
    const card = e.target.closest('.rb-card');
    if (card && card.dataset.proposalId) {
        openProposal(card.dataset.proposalId);
    }
});

// Keyboard: open a focused card with Enter/Space.
proposalList.addEventListener('keydown', (e) => {
    if (e.key !== 'Enter' && e.key !== ' ') return;
    const card = e.target.closest('.rb-card');
    if (card && card.dataset.proposalId) {
        e.preventDefault();
        openProposal(card.dataset.proposalId);
    }
});

refreshBtn.addEventListener('click', loadProposals);

/**
 * Deep link: /review.html?proposal=<id> opens that proposal's detail straight away.
 * The chat links here after generating a correction, so the reviewer lands on the case
 * instead of on a list he has to search. The list is loaded underneath either way, so
 * "Zurück zur Liste" works.
 */
document.addEventListener('DOMContentLoaded', () => {
    loadProposals();
    const params = new URLSearchParams(window.location.search);
    const wanted = params.get('proposal') || params.get('id'); // AP5 email uses ?id=
    if (wanted) openProposal(wanted);
});
