/**
 * Dashboard — AP6.2 (Seite, Charts) + AP6.4b (Zeitfilter, Reihenfolge, Zeitreihe).
 *
 * Charts sind handgebautes Inline-SVG, bewusst ohne Bibliothek. Chart.js käme mit ~200 KB
 * Abhängigkeit für Funktionen, die hier nicht gebraucht werden — und die CSP in
 * web_server.py (`script-src 'self'`) würde ein CDN-Chart.js ohnehin blocken.
 * Präzedenzfall: AP4.7 (bewusst kein Highlight.js).
 *
 * Seitenaufbau (AP6.4b, nach dem ersten Nutzer-Review geändert; Filterleiste 2026-08-02 auf
 * Wunsch nach unten verschoben):
 *   ZAHLEN → Filterleiste → Charts → offene Reviews → Belastbarkeit (ganz unten).
 * Vorher stand der Belastbarkeits-Textblock oben und war der erste Eindruck. Ein Dashboard,
 * das mit acht Absätzen Text beginnt, ist kein Dashboard. Die Vorbehalte sind nicht
 * verschwunden — sie hängen jetzt als Warnsymbol AN der Kennzahl, die sie betreffen, und
 * öffnen sich per Klick. Das ist auch die ehrlichere Stelle: die Warnung steht dort, wo die
 * Zahl gelesen wird.
 *
 * ACHTUNG beim Weiterbauen: die Filterleiste filtert ALLES auf der Seite, auch die
 * Kennzahlen ÜBER ihr. Dass ein Bedienelement unter dem steht, was es steuert, ist die
 * bewusst in Kauf genommene Kehrseite dieser Anordnung; getragen wird sie davon, dass die
 * Kacheln in ihrer Fußzeile selbst „im gewählten Zeitraum" sagen. Wer diese Fußzeilen
 * entfernt, nimmt der Leiste ihren einzigen Hinweis auf ihre Reichweite.
 *
 * Chart-Regeln (Spec, nicht Geschmack):
 *   - Balken ≤ 24 px, 4 px gerundetes Datenende, quadratisch an der Grundlinie.
 *   - 2 px Flächen-Lücke zwischen gestapelten Segmenten (nie eine Kontur drumherum).
 *   - Gitter/Achsen: einfarbige Haarlinien, zurücktretend, nie gestrichelt.
 *   - Werte als Direktlabel — ein Tooltip ergänzt, er ist NIE die einzige Art zu lesen.
 *   - ≥ 2 Serien ⇒ Legende ist Pflicht (Farbe allein ist kein Kanal).
 */

const DASH_CONFIG = {
    REQUEST_TIMEOUT: 30000,           // reiner DB-Read, kein LLM in der Schleife
    API_ENDPOINT: API_CONFIG.baseURL + '/api/dashboard/metrics',
};

/** AK2-Zielmarke: ≥ 80 % der Vorschläge ohne Änderung angenommen. */
const AK2_TARGET = 0.80;

/**
 * Farben. Alle gegen die Kartenfläche #171922 nachgerechnet, nicht geschätzt.
 *
 * Die drei Entscheidungsfarben sind eine KATEGORIALE Palette (gestapelte Zeitreihe) und
 * wurden mit dem Palette-Validator geprüft: Helligkeitsband PASS, Chroma PASS,
 * CVD-Trennung ΔE 95 (Ziel ≥ 12) PASS, Kontrast PASS. Die Farbfamilien sind bewusst die
 * des Review Boards (grün = freigegeben, indigo = korrigiert, rot = verworfen) — wer sie
 * dort gelernt hat, liest das Chart ohne Legende. Nur die Helligkeitsstufe ist dunkler:
 * im Board sind es Textfarben auf getönter Fläche, hier sind es Vollflächen.
 */
/* Redesign 2026-08-02: Die Kartenfläche ist jetzt themeabhängig (hell ODER dunkel), also
   dürfen die Chart-Farben nicht mehr fest gegen die dunkle Karte gerechnet sein. Sie kommen
   deshalb aus CSS-Variablen (styles.css), die je Theme gesetzt werden — die oben beschriebene
   kategoriale Trennung (grün/indigo/rot) bleibt in beiden Themes erhalten. Der Fallback
   entspricht den bisherigen, validierten Dark-Werten. */
function cssColor(name, fallback) {
    try {
        const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
        return v || fallback;
    } catch (_) { return fallback; }
}

const COLOR = {
    get bar()     { return cssColor('--chart-bar', '#818cf8'); },
    get legacy()  { return cssColor('--chart-legacy', '#eab308'); },
    get approve() { return cssColor('--chart-approve', '#16a34a'); },
    get modify()  { return cssColor('--chart-modify', '#6366f1'); },
    get reject()  { return cssColor('--chart-reject', '#ef4444'); },
    get grid()    { return cssColor('--chart-grid', '#2e3036'); },
    get axis()    { return cssColor('--chart-axis', '#949ba4'); },
    get ink()     { return cssColor('--ink', '#eff1f5'); },      // SVG-Textmarken
};

/* `color` als Getter, damit ein Theme-Wechsel zur Laufzeit greift — bei festen Werten wäre
   die Farbe beim Laden eingefroren und das Chart bliebe nach dem Umschalten falsch. */
const DECISION_SERIES = [
    { key: 'approve', label: 'freigegeben', get color() { return COLOR.approve; } },
    { key: 'modify', label: 'korrigiert', get color() { return COLOR.modify; } },
    { key: 'reject', label: 'verworfen', get color() { return COLOR.reject; } },
];

const root = document.getElementById('dashboardRoot');
const refreshBtn = document.getElementById('refreshBtn');

/**
 * Zeitraum UND Auflösung sind EIN Bedienelement (2026-08-02, war vorher zwei).
 *
 * Vorher gab es Voreinstellungen für die Länge (Woche/Monat/Jahr) und daneben ein
 * Auswahlfeld für die Auflösung (Tage/Wochen/Monate). Beides einzeln bedienbar heißt:
 * man kann sich unsinnige Kombinationen bauen — ein Jahr in Tagesbalken sind 365 Striche.
 * Der Server hat das hinterher wieder eingefangen und vergröbert; das Auswahlfeld zeigte
 * dann etwas anderes an als das Chart darunter.
 *
 * Jetzt wählt man nur noch die Auflösung, und wie viel Zeitraum dazugehört, ergibt sich:
 * 14 Tage, 12 Kalenderwochen, 12 Monate, und „Alles" zeigt den gesamten Bestand in Monaten.
 *
 * Der Server bleibt als Rückfallebene aktiv: ergibt eine Anfrage mehr als 92 Balken,
 * vergröbert er selbsttätig und sagt es in der Leiste an. Das greift hier nur noch in
 * Ausnahmefällen — die vier Voreinstellungen sind so gewählt, dass sie es nicht auslösen.
 */
const VIEWS = {
    day:   { count: 14, unit: 'day',   label: 'Tage' },
    week:  { count: 12, unit: 'week',  label: 'Kalenderwochen' },
    month: { count: 12, unit: 'month', label: 'Monate' },
    all:   { count: 0,  unit: 'month', label: 'Monate' },
};

/** Auflösung, wie sie der SERVER aufgelöst hat — nicht, was wir angefragt haben. */
const GRAN_LABEL = { day: 'Tage', week: 'Kalenderwochen', month: 'Monate' };

/**
 * Voreinstellung „Alles": zeigt beim Öffnen den gesamten Datenbestand. Für ein
 * Management-Dashboard ist das der ehrliche Startpunkt — ein kürzeres Standardfenster
 * würde einen Teil der Belege verschweigen, ohne dass jemand danach gefragt hätte.
 */
const state = {
    view: 'all',
    anchor: null,        // 'YYYY-MM-DD' — Ende des Fensters; null = bis heute
};

/** Zuletzt geladene Antwort — die Filterleiste zeigt den vom Server AUFGELÖSTEN Zeitraum. */
let latest = null;

/* ------------------------------------------------------------------ Helfer */

function esc(text) {
    const d = document.createElement('div');
    d.textContent = text == null ? '' : String(text);
    return d.innerHTML;
}

function pct(v) {
    return typeof v === 'number' ? `${(v * 100).toFixed(1)} %` : 'n/a';
}

/* ---------------------------------------------------------- Zahlen hochzaehlen */
/* Kennzahlen zaehlen beim Aufbau von 0 auf ihren Wert hoch (wie im Entwurf: 950 ms,
   kubisch ausklingend). Das ist nicht nur Zierde — die Bewegung zeigt, dass die Zahl
   gerade FRISCH geladen wurde und nicht ein Rest der vorigen Filtereinstellung ist.
   Der Endwert steht von Anfang an im Markup, damit ein Screenshot oder ein Ausdruck
   vor Ablauf der Animation die richtige Zahl zeigt; die Animation ueberschreibt ihn
   nur waehrend sie laeuft. */
const COUNTUP_MS = 950;

/* Die Zwischenschritte werden von DERSELBEN Funktion formatiert wie der Endwert. Ein
   Parser, der das Format aus dem fertigen Text errät, wäre hier eine Fehlerquelle:
   `pct()` schreibt den Dezimalpunkt englisch, `compact()` wechselt bei 10 Tsd. und
   1 Mio. sogar die Einheit — eine geratene Formatierung würde also mitten im Zählen
   eine andere Zahl anzeigen als am Ende. */
const COUNT_FORMATS = {
    int: (v) => String(Math.round(v)),
    pct: (v) => `${v.toFixed(1)} %`,   // erwartet den bereits mit 100 multiplizierten Wert
    usd: (v) => `$${v.toFixed(2)}`,
};

/** Zählbare Zahl im Markup markieren; rendert sofort den korrekten Endwert. */
function countable(end, fmt) {
    const f = COUNT_FORMATS[fmt];
    if (typeof end !== 'number' || !isFinite(end) || !f) return 'n/a';
    return `<span class="db-count" data-end="${end}" data-fmt="${fmt}">${f(end)}</span>`;
}

/** Nach jedem Rendern aufrufen: startet die Animation für alle markierten Zahlen. */
function runCountUps(scope) {
    const reduce = window.matchMedia
        && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduce) return;   // Endwert steht bereits im Markup — nichts zu tun
    scope.querySelectorAll('.db-count').forEach((el) => {
        const end = Number(el.dataset.end);
        const f = COUNT_FORMATS[el.dataset.fmt];
        if (!f || !isFinite(end)) return;
        const final = f(end);
        let start = null;
        const tick = (t) => {
            if (start === null) start = t;
            const p = Math.min(1, (t - start) / COUNTUP_MS);
            /* kubisch ausklingend: schnell los, weich stehenbleiben (wie im Entwurf) */
            el.textContent = p < 1 ? f(end * (1 - Math.pow(1 - p, 3))) : final;
            if (p < 1) requestAnimationFrame(tick);
        };
        el.textContent = f(0);
        requestAnimationFrame(tick);
    });
}

function compact(n) {
    if (typeof n !== 'number') return 'n/a';
    if (Math.abs(n) >= 1e6) return `${(n / 1e6).toFixed(2)} Mio.`;
    if (Math.abs(n) >= 1e4) return `${(n / 1e3).toFixed(1)} Tsd.`;
    return n.toLocaleString('de-DE');
}

function duration(s) {
    if (typeof s !== 'number') return 'n/a';
    if (s < 90) return `${Math.round(s)} Sek.`;
    if (s < 5400) return `${Math.round(s / 60)} Min.`;
    if (s < 172800) return `${(s / 3600).toFixed(1)} Std.`;
    return `${(s / 86400).toFixed(1)} Tage`;
}

/**
 * Heute um 00:00 Uhr. Alle Zeitraumvergleiche laufen darüber, NICHT über `new Date()`:
 * `parseDay()` liefert Mitternacht, und ein Fenster, das heute endet, wäre gegen die
 * aktuelle Uhrzeit gemessen immer „noch nicht bei heute" — der Vorwärts-Knopf wäre also
 * am rechten Rand des Datenbestands weiterhin klickbar und würde in die Zukunft blättern.
 */
function todayStart() {
    const d = new Date();
    d.setHours(0, 0, 0, 0);
    return d;
}

/** 'YYYY-MM-DD' -> Date (lokal, ohne Zeitzonen-Verschiebung durch Date.parse). */
function parseDay(s) {
    const [y, m, d] = String(s).split('-').map(Number);
    return new Date(y, m - 1, d);
}

function fmtDay(date) {
    return date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

function toISO(date) {
    const p = n => String(n).padStart(2, '0');
    return `${date.getFullYear()}-${p(date.getMonth() + 1)}-${p(date.getDate())}`;
}

/** Achsenbeschriftung eines Buckets — je nach Granularität. */
/** ISO-Kalenderwoche (Woche 1 ist die mit dem ersten Donnerstag des Jahres). */
function isoWeek(date) {
    const t = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
    t.setUTCDate(t.getUTCDate() + 4 - (t.getUTCDay() || 7));   // auf den Donnerstag
    const yearStart = new Date(Date.UTC(t.getUTCFullYear(), 0, 1));
    return Math.ceil(((t - yearStart) / 86400000 + 1) / 7);
}

/**
 * Achsenbeschriftung eines Buckets. Der Schlüssel kommt vom Server: 'YYYY-MM' für Monate,
 * sonst ein Datum — bei Wochen ist es der MONTAG der Woche.
 * Wochen werden als Kalenderwoche beschriftet, nicht als Datum: „KW 31" ist die Einheit,
 * in der über Zeiträume geredet wird; „27.07." sieht dagegen aus wie ein einzelner Tag.
 */
function bucketLabel(key, granularity) {
    if (granularity === 'month') {
        const [y, m] = key.split('-').map(Number);
        return new Date(y, m - 1, 1).toLocaleDateString('de-DE', { month: 'short', year: '2-digit' });
    }
    const d = parseDay(key);
    if (granularity === 'week') return `KW ${isoWeek(d)}`;
    return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' });
}

/**
 * Der Zeitraum eines Buckets im Klartext — Überschrift des Tooltips. Bei Wochen und
 * Monaten muss dort die volle Spanne stehen: „KW 31" allein beantwortet nicht, welche
 * Tage gemeint sind.
 */
function bucketSpan(key, granularity) {
    if (granularity === 'month') {
        const [y, m] = key.split('-').map(Number);
        return `${fmtDay(new Date(y, m - 1, 1))} – ${fmtDay(new Date(y, m, 0))}`;
    }
    const from = parseDay(key);
    if (granularity === 'week') {
        const to = new Date(from);
        to.setDate(to.getDate() + 6);
        return `KW ${isoWeek(from)} · ${fmtDay(from)} – ${fmtDay(to)}`;
    }
    return fmtDay(from);
}

function barPath(x, y, w, h, horizontal) {
    const r = Math.min(4, horizontal ? w : h, horizontal ? h / 2 : w / 2);
    if (r <= 0) return '';
    if (horizontal) {
        return `M${x},${y} H${x + w - r} A${r},${r} 0 0 1 ${x + w},${y + r} `
             + `V${y + h - r} A${r},${r} 0 0 1 ${x + w - r},${y + h} H${x} Z`;
    }
    return `M${x},${y + h} V${y + r} A${r},${r} 0 0 1 ${x + r},${y} `
         + `H${x + w - r} A${r},${r} 0 0 1 ${x + w},${y + r} V${y + h} Z`;
}

/** Rechteck ohne Rundung — für Stapelsegmente, die NICHT das Datenende sind. */
function rectPath(x, y, w, h) {
    return `M${x},${y} h${w} v${h} h${-w} Z`;
}

/**
 * Obergrenze einer ZÄHL-Achse. Immer geradzahlig, damit der Mittel-Tick eine ganze Zahl
 * ist: bei Maximum 3 wäre die Achse sonst 0 / 1.5 / 3 — und einen halben Vorschlag gibt es
 * nicht. Also 3 -> 4 (Ticks 0/2/4), 5 -> 6 (Ticks 0/3/6).
 */
function niceMaxCount(value) {
    const v = Math.max(1, Math.ceil(value));
    return v % 2 === 0 ? v : v + 1;
}

/* ------------------------------------------------- Vorbehalte an der Kennzahl */

/** Alle Hinweise, die eine bestimmte Kennzahl betreffen. */
function flagsFor(...keys) {
    if (!latest) return [];
    return latest.data_quality.filter(f => f.affects.some(a => keys.includes(a)));
}

/**
 * Das Warnsymbol AN der Kennzahl. Klick öffnet den Klartext direkt darunter — der
 * Vorbehalt steht damit dort, wo die Zahl gelesen wird, statt in einem Textblock, den
 * niemand liest. `warning` färbt, `info` bleibt dezent.
 */
function caveat(...keys) {
    const fs = flagsFor(...keys);
    if (!fs.length) return '';
    const worst = fs.some(f => f.severity === 'warning') ? 'warning' : 'info';
    const body = fs.map(f => `<p><code>${esc(f.code)}</code> ${esc(f.message)}</p>`).join('');
    return `
        <details class="db-caveat db-caveat-${worst}">
            <summary title="Was diese Zahl einschränkt">
                <span class="material-symbols-outlined" aria-hidden="true">
                    ${worst === 'warning' ? 'warning' : 'info'}
                </span>
                <span class="db-caveat-count">${fs.length}</span>
                <span class="sr-only">Hinweise zur Belastbarkeit dieser Zahl</span>
            </summary>
            <div class="db-caveat-body">${body}</div>
        </details>`;
}

/* ------------------------------------------------------------------ Charts */

/**
 * Chart 0 (NEU, AP6.4b) — „Wann wurde entschieden?"
 * Gestapelte Säulen je Tag/Woche/Monat, aufgeteilt nach Entscheidungstyp.
 * Verankert auf `decided_at`: gefragt ist, wann der MENSCH gehandelt hat, nicht wann die
 * KI den Vorschlag erzeugt hat.
 * Leere Buckets werden gezeichnet (als Lücke) — ein Chart, das stille Tage weglässt,
 * lässt die Aktivität durchgehend aussehen. Sind ALLE Buckets leer, gilt das Argument
 * nicht mehr: dann gibt es keine Aktivität, die verzerrt dargestellt werden könnte,
 * und vierzehn Grundlinienstriche sind eine schlechtere Auskunft als ein Satz.
 * (Der Server liefert für jeden Zeitraum die volle Bucket-Reihe, notfalls mit Nullen —
 * eine leere Liste kommt nur bei kaputter Antwort. Beide Fälle enden hier gleich.)
 */
function timelineChart(rows, granularity) {
    if (!rows.length || rows.every(r => !r.total)) {
        return `
            <div class="db-empty">
                <span class="material-symbols-outlined" aria-hidden="true">event_busy</span>
                <p>Keine Entscheidungen in diesem Zeitraum</p>
                <span>Blättere zurück oder wähle einen größeren Zeitraum.</span>
            </div>`;
    }

    const w = 720, h = 250, padL = 34, padR = 10, padT = 16, padB = 46;
    const plotW = w - padL - padR, plotH = h - padT - padB;
    const max = niceMaxCount(Math.max(1, ...rows.map(r => r.total)));
    const slot = plotW / rows.length;
    const barW = Math.min(24, Math.max(3, slot - 6));
    const GAP = 2;   // Flächen-Lücke zwischen Stapelsegmenten — nie eine Kontur

    const grid = [0, max / 2, max].map(t => {
        const y = padT + plotH - (t / max) * plotH;
        return `<line x1="${padL}" y1="${y}" x2="${w - padR}" y2="${y}"
                      stroke="${COLOR.grid}" stroke-width="1"/>
                <text x="${padL - 8}" y="${y + 4}" fill="${COLOR.axis}" font-size="11"
                      text-anchor="end" class="db-tick">${t}</text>`;
    }).join('');

    /* Achsenbeschriftungen nur ausdünnen, wenn sie sonst KOLLIDIEREN — vorher hing das an
       einer festen Zahl (mehr als 12 Buckets ⇒ nur jeder zweite), wodurch die 14-Tage-Ansicht
       jeden zweiten Tag verschluckte, obwohl reichlich Platz war. Jetzt entscheidet die
       Geometrie: „20.07." braucht bei 10 px Schrift rund 38 px Breite. */
    const LABEL_W = 38;
    const every = Math.max(1, Math.ceil(LABEL_W / slot));

    const bars = rows.map((r, i) => {
        const x = padL + i * slot + (slot - barW) / 2;
        const label = bucketLabel(r.bucket, granularity);
        const tick = (i % every === 0)
            ? `<text x="${x + barW / 2}" y="${h - 26}" fill="${COLOR.axis}" font-size="10"
                     text-anchor="middle" class="db-tick">${esc(label)}</text>` : '';

        const parts = DECISION_SERIES.map(s => ({ ...s, n: r[s.key] })).filter(s => s.n > 0);
        const body = parts.length
            ? parts.map(s => `${s.n}× ${s.label}`).join(' · ')
            : 'keine Entscheidungen';
        const head = `${bucketSpan(r.bucket, granularity)} — `
            + `${r.total} ${r.total === 1 ? 'Entscheidung' : 'Entscheidungen'}`;

        /* Trefferfläche über die volle Spaltenhöhe: der Zeiger muss den (womöglich sehr
           niedrigen) Balken nicht treffen, es reicht, in der Spalte zu sein — so verhält es
           sich auch im Entwurf. Sie liegt VOR den Balken im Markup, damit sie nichts
           überdeckt, was gezeichnet werden soll.
           `role="img"` + `aria-label` statt <title>: <title> erzeugt zusätzlich den nativen
           Browser-Tooltip, der dann verzögert NEBEN unserem eigenen aufgeht. Der Text bleibt
           damit für Screenreader erhalten, ohne doppelt sichtbar zu werden. */
        const hit = `<rect x="${padL + i * slot}" y="${padT}" width="${slot}" height="${plotH}"
                           fill="transparent"/>`;
        const meta = `data-head="${esc(head)}" data-body="${esc(body)}"`
            + ` data-cx="${x + barW / 2}"`;

        if (!r.total) {
            // Leerer Bucket: kurze Grundlinien-Marke. Kein Nullbalken — „nichts passiert"
            // und „null von etwas" sind verschiedene Aussagen.
            return `
                <g class="db-bar-g" role="img" aria-label="${esc(head)}"
                   ${meta} data-cy="${padT + plotH}">
                    ${hit}
                    <line x1="${x}" y1="${padT + plotH}" x2="${x + barW}" y2="${padT + plotH}"
                          stroke="${COLOR.grid}" stroke-width="2"/>
                    ${tick}
                </g>`;
        }

        // Von unten stapeln. Nur das oberste Segment bekommt das gerundete Datenende.
        let cursor = padT + plotH;
        const segs = parts.map((s, idx) => {
            const segH = (s.n / max) * plotH - (idx < parts.length - 1 ? GAP : 0);
            const y = cursor - segH;
            cursor = y - (idx < parts.length - 1 ? GAP : 0);
            const isTop = idx === parts.length - 1;
            const d = isTop ? barPath(x, y, barW, Math.max(segH, 2), false)
                            : rectPath(x, y, barW, Math.max(segH, 2));
            return `<path d="${d}" fill="${s.color}"/>`;
        }).join('');

        const topY = cursor;
        return `
            <g class="db-bar-g" role="img" aria-label="${esc(head)}: ${esc(body)}"
               ${meta} data-cy="${topY - 18}">
                ${hit}
                ${segs}
                <text x="${x + barW / 2}" y="${topY - 6}" fill="${COLOR.ink}" font-size="11"
                      text-anchor="middle" class="db-val">${r.total}</text>
                ${tick}
            </g>`;
    }).join('');

    // ≥ 2 Serien ⇒ Legende ist Pflicht. Identität darf nie nur an der Farbe hängen.
    const legend = DECISION_SERIES.map(s => `
        <span class="db-legend-item">
            <span class="db-legend-dot" style="background:${s.color}"></span>${s.label}
        </span>`).join('');

    /* Der Tooltip ist ein HTML-Element ÜBER dem SVG, kein SVG-Element: er soll Schatten,
       Rundung und Umbruch der übrigen Oberfläche haben und darf über den Chart-Rand
       hinausragen. `data-vw` hält die Breite des Koordinatensystems fest — daraus rechnet
       wireChartTooltip() SVG-Einheiten in Bildpunkte um. */
    return `
        <div class="db-legend">${legend}</div>
        <div class="db-chart-wrap" data-vw="${w}">
            <div class="db-tip" hidden></div>
            <svg viewBox="0 0 ${w} ${h}" class="db-svg" role="img"
                 aria-label="Gestapelte Säulen: Entscheidungen je Zeitraum, nach Typ">
                ${grid}
                ${bars}
            </svg>
        </div>`;
}

/**
 * Zeigt beim Überfahren einer Säule den Zeitraum und die Aufschlüsselung.
 *
 * Die Umrechnung geht über EINEN Faktor für beide Achsen. Das ist zulässig, weil
 * `.db-svg { width:100%; height:auto }` das Seitenverhältnis exakt erhält — würde die
 * Höhe je unabhängig gesetzt, träfe der Tooltip die Balkenspitze nicht mehr.
 */
function wireChartTooltip() {
    root.querySelectorAll('.db-chart-wrap').forEach(wrap => {
        const svg = wrap.querySelector('svg');
        const tip = wrap.querySelector('.db-tip');
        const vw = Number(wrap.dataset.vw) || 720;

        const show = (g) => {
            tip.innerHTML = `<b>${esc(g.dataset.head)}</b>${esc(g.dataset.body)}`;
            tip.hidden = false;
            const scale = svg.clientWidth / vw;
            /* Am linken und rechten Rand würde der Tooltip sonst aus der Karte laufen;
               er wird hineingeschoben, statt abgeschnitten zu werden. */
            const half = tip.offsetWidth / 2;
            const cx = Number(g.dataset.cx) * scale;
            tip.style.left = `${Math.min(Math.max(cx, half), wrap.clientWidth - half)}px`;
            tip.style.top = `${Number(g.dataset.cy) * scale}px`;
        };

        wrap.querySelectorAll('.db-bar-g').forEach(g => {
            g.addEventListener('mouseenter', () => show(g));
            g.addEventListener('mouseleave', () => { tip.hidden = true; });
        });
    });
}

function errorTypeChart(rows) {
    if (!rows.length) return '<p class="rb-muted">Keine Vorschläge in diesem Zeitraum.</p>';

    // Das Label steht ÜBER dem Balken, nicht daneben. Eine linke Beschriftungsspalte
    // müsste "WORK_ITEM_CONFIGS_COMPLETENESS" (29 Zeichen ≈ 210 px) fassen — das läuft aus
    // dem SVG heraus oder erzwingt eine Kürzung. Ein Label, das nicht passt, wird nicht
    // abgeschnitten; es bekommt eine Form, in der es passt.
    // padL = 6, nicht 0: der "0"-Tick sitzt MITTIG auf der Nulllinie und ragt sonst mit
    // seiner halben Glyphenbreite links aus der viewBox.
    const rowH = 46, barH = 18, padL = 6, padR = 40, padT = 4, padB = 26;
    const w = 720, plotW = w - padL - padR;
    const h = padT + rows.length * rowH + padB;
    const plotBottom = padT + rows.length * rowH;
    const max = niceMaxCount(Math.max(...rows.map(r => r.count)));

    const ticks = [0, max / 2, max].map(t => {
        const x = padL + (t / max) * plotW;
        return `<line x1="${x}" y1="${padT}" x2="${x}" y2="${plotBottom}"
                      stroke="${COLOR.grid}" stroke-width="1"/>
                <text x="${x}" y="${h - 8}" fill="${COLOR.axis}" font-size="11"
                      text-anchor="middle" class="db-tick">${t}</text>`;
    }).join('');

    const bars = rows.map((r, i) => {
        const top = padT + i * rowH;
        const y = top + 20;
        const bw = Math.max((r.count / max) * plotW, 2);
        const fill = r.legacy_label ? COLOR.legacy : COLOR.bar;
        // Gelb allein trägt keine Bedeutung — die Textmarke daneben tut es.
        const tag = r.legacy_label
            ? ` <tspan class="db-legacy-tag">⚠ Alt-Label (Zähl-Heuristik)</tspan>` : '';
        return `
            <g class="db-bar-g">
                <title>${esc(r.error_type)}: ${r.count} Vorschlag/Vorschläge${
                    r.legacy_label ? ' — Label stammt aus der alten Zähl-Heuristik, nicht aus einer Fehlerklassifikation' : ''}</title>
                <text x="${padL}" y="${top + 12}" fill="${COLOR.ink}" font-size="12"
                      class="db-cat">${esc(r.error_type)}${tag}</text>
                <path d="${barPath(padL, y, bw, barH, true)}" fill="${fill}"/>
                <text x="${padL + bw + 8}" y="${y + barH / 2 + 4}" fill="${COLOR.ink}"
                      font-size="12" class="db-val">${r.count}</text>
            </g>`;
    }).join('');

    return `<svg viewBox="0 0 ${w} ${h}" class="db-svg" role="img"
                 aria-label="Balkendiagramm: Anzahl Vorschläge je Fehlerart">
                ${ticks}
                ${bars}
            </svg>`;
}

function distributionChart(rows) {
    const w = 720, h = 220, padL = 40, padR = 12, padT = 14, padB = 44;
    const plotW = w - padL - padR, plotH = h - padT - padB;
    const max = niceMaxCount(Math.max(1, ...rows.map(r => r.count)));
    const slot = plotW / rows.length;
    const barW = Math.min(24, slot - 18);   // Balken nie den Slot füllen — Rest ist Luft

    const grid = [0, max / 2, max].map(t => {
        const y = padT + plotH - (t / max) * plotH;
        return `<line x1="${padL}" y1="${y}" x2="${w - padR}" y2="${y}"
                      stroke="${COLOR.grid}" stroke-width="1"/>
                <text x="${padL - 8}" y="${y + 4}" fill="${COLOR.axis}" font-size="11"
                      text-anchor="end" class="db-tick">${t}</text>`;
    }).join('');

    const bars = rows.map((r, i) => {
        const bh = (r.count / max) * plotH;
        const x = padL + i * slot + (slot - barW) / 2;
        const y = padT + plotH - bh;
        const cap = r.count > 0
            ? `<text x="${x + barW / 2}" y="${y - 7}" fill="${COLOR.ink}" font-size="12"
                     text-anchor="middle" class="db-val">${r.count}</text>`
            : `<text x="${x + barW / 2}" y="${padT + plotH - 7}" fill="${COLOR.axis}"
                     font-size="12" text-anchor="middle" class="db-val">0</text>`;
        return `
            <g class="db-bar-g">
                <title>Konfidenz ${esc(r.bucket)}: ${r.count} Vorschlag/Vorschläge</title>
                ${r.count > 0 ? `<path d="${barPath(x, y, barW, bh, false)}" fill="${COLOR.bar}"/>` : ''}
                ${cap}
                <text x="${x + barW / 2}" y="${h - 22}" fill="${COLOR.axis}" font-size="11"
                      text-anchor="middle" class="db-tick">${esc(r.bucket)}</text>
            </g>`;
    }).join('');

    return `<svg viewBox="0 0 ${w} ${h}" class="db-svg" role="img"
                 aria-label="Säulendiagramm: Verteilung der Konfidenzwerte über fünf Bänder">
                ${grid}
                ${bars}
                <text x="${padL + plotW / 2}" y="${h - 5}" fill="${COLOR.axis}" font-size="11"
                      text-anchor="middle">Konfidenz-Band</text>
            </svg>`;
}

/**
 * Kalibrierung: Anteil „ohne Änderung angenommen" je Konfidenz-Band.
 * Ein Band ohne Entscheidungen bekommt KEINEN Nullbalken — „keine Daten" und
 * „0 % angenommen" sind verschiedene Aussagen, und ein Nullbalken würde sie
 * verwechselbar machen. Es bekommt stattdessen ein sichtbares „n=0".
 */
function calibrationChart(rows) {
    const w = 720, h = 240, padL = 44, padR = 12, padT = 14, padB = 60;
    const plotW = w - padL - padR, plotH = h - padT - padB;
    const slot = plotW / rows.length;
    const barW = Math.min(24, slot - 18);

    const grid = [0, 0.5, 1].map(t => {
        const y = padT + plotH - t * plotH;
        return `<line x1="${padL}" y1="${y}" x2="${w - padR}" y2="${y}"
                      stroke="${COLOR.grid}" stroke-width="1"/>
                <text x="${padL - 8}" y="${y + 4}" fill="${COLOR.axis}" font-size="11"
                      text-anchor="end" class="db-tick">${t * 100} %</text>`;
    }).join('');

    const bars = rows.map((r, i) => {
        const x = padL + i * slot + (slot - barW) / 2;
        const nLabel = `<text x="${x + barW / 2}" y="${h - 24}" fill="${COLOR.axis}" font-size="10"
                              text-anchor="middle" class="db-tick">n=${r.decisions}</text>`;
        const band = `<text x="${x + barW / 2}" y="${h - 38}" fill="${COLOR.axis}" font-size="11"
                            text-anchor="middle" class="db-tick">${esc(r.bucket)}</text>`;

        if (r.decisions === 0) {
            return `
                <g class="db-bar-g">
                    <title>Konfidenz ${esc(r.bucket)}: keine Entscheidungen</title>
                    <line x1="${x}" y1="${padT + plotH}" x2="${x + barW}" y2="${padT + plotH}"
                          stroke="${COLOR.grid}" stroke-width="2"/>
                    <text x="${x + barW / 2}" y="${padT + plotH - 8}" fill="${COLOR.axis}"
                          font-size="11" text-anchor="middle" class="db-val">–</text>
                    ${band}${nLabel}
                </g>`;
        }
        const bh = r.accept_rate * plotH;
        const y = padT + plotH - bh;
        return `
            <g class="db-bar-g">
                <title>Konfidenz ${esc(r.bucket)}: ${r.accepted_unchanged} von ${r.decisions} ohne Änderung angenommen</title>
                ${bh > 0 ? `<path d="${barPath(x, y, barW, bh, false)}" fill="${COLOR.bar}"/>` : ''}
                <text x="${x + barW / 2}" y="${(bh > 0 ? y : padT + plotH) - 7}" fill="${COLOR.ink}"
                      font-size="12" text-anchor="middle" class="db-val">${pct(r.accept_rate)}</text>
                ${band}${nLabel}
            </g>`;
    }).join('');

    return `<svg viewBox="0 0 ${w} ${h}" class="db-svg" role="img"
                 aria-label="Säulendiagramm: Annahmequote ohne Änderung je Konfidenz-Band">
                ${grid}
                ${bars}
            </svg>`;
}

/**
 * Die Kalibrierungskurve ist nur dann eine Aussage, wenn sie überhaupt streut. Streuen die
 * belegten Bänder um weniger als 5 Prozentpunkte, sagt die Konfidenz nichts vorher — das
 * muss AN der Kurve stehen, sonst liest man sie als Befund.
 */
function calibrationWarning(calibration) {
    const filled = calibration.filter(b => b.decisions > 0);
    if (filled.length < 2) return '';
    const rates = filled.map(b => b.accept_rate);
    if (Math.max(...rates) - Math.min(...rates) >= 0.05) return '';
    return `
        <p class="db-callout warn">
            <span class="material-symbols-outlined" aria-hidden="true">warning</span>
            <span>Die Kurve ist <strong>flach</strong>: eine hohe Konfidenz sagt derzeit nicht
            voraus, ob der Mensch den Wert unverändert übernimmt. Das ist kein Messergebnis,
            sondern konstruktionsbedingt — die entschiedenen Vorschläge tragen noch die alte
            Konfidenz-Formel. Aussagekräftig wird die Kurve erst mit Entscheidungen auf
            Vorschlägen, die nach AP4.5 bewertet wurden.</span>
        </p>`;
}

/* ------------------------------------------------------------------ Bausteine */

function tile(label, value, note, caveatKeys) {
    return `
        <div class="db-tile">
            <div class="db-tile-head">
                <div class="db-tile-label">${esc(label)}</div>
                ${caveatKeys ? caveat(...caveatKeys) : ''}
            </div>
            <div class="db-tile-value">${value}</div>
            ${note ? `<div class="db-tile-note">${note}</div>` : ''}
        </div>`;
}

function card(title, sub, content, caveatKeys) {
    return `
        <section class="db-card">
            <div class="db-card-head">
                <h2 class="db-section-title">${esc(title)}</h2>
                ${caveatKeys ? caveat(...caveatKeys) : ''}
            </div>
            ${sub ? `<p class="db-section-sub">${sub}</p>` : ''}
            ${content}
        </section>`;
}

/**
 * Hero + Meter: die AK2-Quote gegen ihre Zielmarke (≥ 80 %).
 * Genau EINE Heldenzahl pro Ansicht — es ist die Zahl, an der das Projekt gemessen wird.
 */
function ak2Meter(k) {
    const rate = k.accepted_unchanged_rate;
    const has = typeof rate === 'number';
    const width = has ? Math.min(100, rate * 100) : 0;
    const reached = has && rate >= AK2_TARGET;
    return `
        <section class="db-hero">
            <div class="db-hero-head">
                <div>
                    <div class="db-tile-head">
                        <div class="db-tile-label">Angenommen ohne Änderung (AK2)</div>
                        ${caveat('approval_rate')}
                    </div>
                    <div class="db-hero-value">
                        ${has ? countable(rate * 100, 'pct') : 'n/a'}
                    </div>
                    <div class="db-tile-note">
                        ${k.approve_count} von ${k.decisions_total} Entscheidungen —
                        der Mensch hat den KI-Wert unverändert übernommen.
                    </div>
                </div>
                <div class="db-hero-target ${reached ? 'ok' : 'below'}">
                    <span class="material-symbols-outlined" aria-hidden="true">
                        ${reached ? 'check_circle' : 'flag'}
                    </span>
                    Ziel ≥ ${AK2_TARGET * 100} %
                    <strong>${reached ? 'erreicht' : 'nicht erreicht'}</strong>
                </div>
            </div>
            <div class="db-meter" role="img"
                 aria-label="Annahmequote ${has ? pct(rate) : 'nicht verfügbar'} von Zielmarke ${AK2_TARGET * 100} Prozent">
                <div class="db-meter-fill ${reached ? 'ok' : 'below'}" style="width:${width}%"></div>
                <div class="db-meter-target" style="left:${AK2_TARGET * 100}%"></div>
            </div>
            <div class="db-meter-legend">
                <span>0 %</span><span>100 %</span>
            </div>
        </section>`;
}

/**
 * Filterleiste — EINE Reihe über allem, was sie einschränkt (nie ein Filter pro Chart).
 * Zeigt den vom SERVER aufgelösten Zeitraum, nicht den angefragten: wenn der Server die
 * Auflösung vergröbert oder eine ungültige Eingabe ersetzt hat, muss hier das stehen,
 * was wirklich gerechnet wurde.
 */
function filterBar(range) {
    const presets = [
        ['day', 'Tage'], ['week', 'Wochen'], ['month', 'Monate'], ['all', 'Alles'],
    ];

    /* „Alles" hat kein verschiebbares Fenster, und über heute hinaus gibt es nichts zu
       sehen — beides schaltet die Pfeile ab, statt sie ins Leere klicken zu lassen. */
    const isAll = state.view === 'all';
    const atToday = !state.anchor || parseDay(state.anchor) >= todayStart();
    const gran = GRAN_LABEL[range.granularity] || range.granularity;

    return `
        <div class="db-filter">
            <div class="db-filter-nav">
                <button type="button" id="fPrev"
                        class="db-icon-btn ${isAll ? 'off' : ''}" aria-label="Früherer Zeitraum">
                    <span class="material-symbols-outlined" aria-hidden="true">chevron_left</span>
                </button>
                <span class="db-filter-range">
                    ${esc(fmtDay(parseDay(range.from)))} <span class="rb-muted">—</span>
                    ${esc(fmtDay(parseDay(range.to)))}
                </span>
                <button type="button" id="fNext"
                        class="db-icon-btn ${isAll || atToday ? 'off' : ''}"
                        aria-label="Späterer Zeitraum">
                    <span class="material-symbols-outlined" aria-hidden="true">chevron_right</span>
                </button>
            </div>

            <div class="db-filter-presets" role="group" aria-label="Zeitraum und Auflösung">
                ${presets.map(([k, l]) => `
                    <button type="button" class="db-chip ${state.view === k ? 'active' : ''}"
                            data-view="${k}" aria-pressed="${state.view === k}">${l}</button>`).join('')}
            </div>

            <span class="db-filter-gran">
                <span class="material-symbols-outlined" aria-hidden="true">calendar_month</span>
                Auflösung: <b>${esc(gran)}</b>
                ${range.granularity_adjusted_from ? `
                    <span class="db-filter-note"
                          title="Der Zeitraum ergäbe in ${esc(GRAN_LABEL[range.granularity_adjusted_from]
                              || range.granularity_adjusted_from)} zu viele Balken">
                        <span class="material-symbols-outlined" aria-hidden="true">info</span>
                        automatisch vergröbert
                    </span>` : ''}
            </span>
        </div>`;
}

function openReviewsTable(rows) {
    if (!rows.length) {
        return `<p class="rb-muted">Kein Vorschlag wartet auf eine Entscheidung.</p>`;
    }
    const body = rows.map(r => {
        const grounded = r.value_grounded === 1
            ? '<span class="db-grounded ok">belegt</span>'
            : (r.value_grounded === 0
                ? '<span class="db-grounded warn">nicht belegt</span>'
                : '<span class="rb-muted">–</span>');
        return `
            <tr>
                <td>${esc(r.error_type || '—')}</td>
                <td class="rb-mono db-ellipsis" title="${esc(r.target_path)}">${esc(r.target_path || '—')}</td>
                <td class="db-num">${typeof r.confidence_score === 'number' ? pct(r.confidence_score) : 'n/a'}</td>
                <td>${grounded}</td>
                <td><a class="db-link" href="review.html?proposal=${encodeURIComponent(r.proposal_id)}">
                    Im Review Board öffnen
                    <span class="material-symbols-outlined" aria-hidden="true">arrow_forward</span>
                </a></td>
            </tr>`;
    }).join('');

    return `
        <div class="db-table-wrap">
            <table class="db-table">
                <thead>
                    <tr>
                        <th>Fehlerart</th><th>Zielpfad</th><th class="db-num">Konfidenz</th>
                        <th>Wert belegt?</th><th>Aktion</th>
                    </tr>
                </thead>
                <tbody>${body}</tbody>
            </table>
        </div>`;
}

/**
 * Der Belastbarkeits-Block. Steht jetzt GANZ UNTEN und eingeklappt (AP6.4b) — die
 * Vorbehalte selbst hängen an den Kennzahlen. Er bleibt als vollständige Liste erhalten,
 * damit man alles an einer Stelle nachlesen kann, ohne jede Kachel aufzuklappen.
 */
function dataQuality(flags) {
    if (!flags.length) return '';
    const item = f => `
        <li class="db-flag db-flag-${esc(f.severity)}">
            <span class="material-symbols-outlined" aria-hidden="true">
                ${f.severity === 'warning' ? 'warning' : 'info'}
            </span>
            <div>
                <code class="db-flag-code">${esc(f.code)}</code>
                <p>${esc(f.message)}</p>
            </div>
        </li>`;
    const warnN = flags.filter(f => f.severity === 'warning').length;

    return `
        <details class="db-quality">
            <summary>
                <span class="material-symbols-outlined" aria-hidden="true">fact_check</span>
                Belastbarkeit der Zahlen — ${flags.length} Hinweise${warnN ? `, davon ${warnN} Warnungen` : ''}
            </summary>
            <p class="db-section-sub">
                Nichts auf dieser Seite ist herausgefiltert. Jeder Hinweis hängt zusätzlich
                als Symbol an der Kennzahl, die er betrifft.
            </p>
            <ul class="db-flags">${flags.map(item).join('')}</ul>
        </details>`;
}

/* ------------------------------------------------------------------ Render */

function render(d) {
    latest = d;
    const k = d.kpis;
    const r = d.range;

    root.innerHTML = `
        ${ak2Meter(k)}

        <div class="db-tiles">
            ${tile('Offene Reviews', countable(k.proposals_open, 'int'),
                   k.proposals_open
                       ? 'warten auf eine Entscheidung <em>(unabhängig vom Zeitraum)</em>'
                       : 'nichts offen')}
            ${tile('Vorschläge erzeugt', countable(k.proposals_total, 'int'),
                   'im gewählten Zeitraum')}
            ${tile('Entscheidungen', countable(k.decisions_total, 'int'),
                   `${k.approve_count}× freigegeben · ${k.modify_count}× korrigiert · ${k.reject_count}× verworfen`)}
            ${tile('Ø Konfidenz', countable(k.avg_confidence * 100, 'pct'),
                   'über die Vorschläge im Zeitraum',
                   ['avg_confidence'])}
            ${tile('Revalidierung erfolgreich',
                   countable(k.revalidation_success_rate * 100, 'pct'),
                   `${k.revalidation_success} von ${k.revalidation_attempts} belastbaren Anwendungen`
                   + (k.revalidation_untrusted ? ` · ${k.revalidation_untrusted} ausgenommen` : ''),
                   ['revalidation_success_rate'])}
            ${tile('Ø Bearbeitungszeit', duration(k.handling_time_median_s),
                   `Median über ${k.handling_time_n} Entscheidung(en)`
                   + (k.handling_time_excluded_fixtures ? ` · ${k.handling_time_excluded_fixtures} Fixture(s) ausgenommen` : ''),
                   ['handling_time'])}
            ${tile('Validierungen', countable(k.validations, 'int'),
                   `über ${k.snapshots_tracked} Snapshots`,
                   ['validations'])}
            ${tile('Tokens', compact(k.tokens_total),
                   `${compact(k.tokens_prompt)} Prompt · ${compact(k.tokens_completion)} Antwort`,
                   ['tokens'])}
            ${tile('Kosten (geschätzt)',
                   countable(k.cost_estimate_usd, 'usd'),
                   `${k.agent_runs} Agent-Läufe · ${esc(d.pricing.model)}: `
                   + `$${d.pricing.input_per_1k_usd.toFixed(4)} in / $${d.pricing.output_per_1k_usd.toFixed(4)} out je 1K`,
                   ['cost'])}
        </div>

        ${filterBar(r)}

        ${card('Wann wurde entschieden?',
               'Gestapelt nach Entscheidungstyp — so ist sichtbar, '
               + '<strong>wann</strong> korrigiert wurde und <strong>wie</strong>.',
               timelineChart(d.charts.timeline, r.granularity),
               ['timeline', 'range'])}

        ${card('Entscheidungsquoten', 'Woran der Mensch den KI-Vorschlag gemessen hat.', `
            <div class="db-rates">
                <div class="db-rate"><span class="db-rate-val">${pct(k.approval_rate)}</span>
                     <span class="db-rate-lbl">freigegeben</span></div>
                <div class="db-rate"><span class="db-rate-val">${pct(k.modify_rate)}</span>
                     <span class="db-rate-lbl">korrigiert</span></div>
                <div class="db-rate"><span class="db-rate-val">${pct(k.reject_rate)}</span>
                     <span class="db-rate-lbl">verworfen</span></div>
            </div>`, ['approval_rate'])}

        ${card('Fehlerarten', 'Wie oft welche Fehlerart einen Vorschlag ausgelöst hat.',
               errorTypeChart(d.charts.error_types), ['error_types'])}

        ${card('Konfidenz-Verteilung', 'Wie sich die Konfidenzwerte über die Vorschläge verteilen.',
               distributionChart(d.charts.confidence_distribution), ['confidence_distribution'])}

        ${card('Kalibrierung — sagt die Konfidenz die menschliche Entscheidung voraus?',
               'Anteil der Vorschläge, die der Mensch je Konfidenz-Band <strong>unverändert</strong> '
               + 'übernommen hat. Wäre die Konfidenz aussagekräftig, müsste dieser Anteil nach rechts steigen.',
               calibrationChart(d.charts.calibration) + calibrationWarning(d.charts.calibration),
               ['calibration'])}

        ${card('Offene Reviews', 'Aktueller Rückstand — bewusst unabhängig vom Zeitraum.',
               openReviewsTable(d.open_reviews))}

        ${dataQuality(d.data_quality)}

        <p class="db-generated">Stand: ${esc(new Date(d.generated_at).toLocaleString('de-DE'))}</p>`;

    wireFilter();
    wireChartTooltip();
    runCountUps(root);
}

/* ------------------------------------------------------------------ Filter */

/**
 * Das konkrete Fenster zur gewählten Ansicht. `anchor` ist das ENDE des Fensters.
 *
 * Wochen und Monate werden auf ihre Grenzen gerundet (Montag–Sonntag, Monatserster bis
 * Monatsletzter). Ohne das wäre der letzte Balken ein angeschnittener Teilzeitraum und
 * würde neben den vollen davor wie ein Einbruch aussehen, obwohl nur weniger Tage
 * hineinfallen.
 */
function windowFor(view, anchorISO) {
    const cfg = VIEWS[view];
    const anchor = anchorISO ? parseDay(anchorISO) : new Date();
    let from, to;
    if (view === 'week') {
        to = new Date(anchor);
        to.setDate(to.getDate() + (7 - (to.getDay() || 7)));            // bis Sonntag
        from = new Date(to);
        from.setDate(from.getDate() - (cfg.count * 7 - 1));             // ab Montag
    } else if (view === 'month') {
        to = new Date(anchor.getFullYear(), anchor.getMonth() + 1, 0);  // Monatsletzter
        from = new Date(anchor.getFullYear(), anchor.getMonth() - (cfg.count - 1), 1);
    } else {
        to = new Date(anchor);
        from = new Date(to);
        from.setDate(from.getDate() - (cfg.count - 1));
    }
    /* Das Aufrunden auf Wochen-/Monatsgrenzen schiebt das Ende der AKTUELLEN Periode in
       die Zukunft (im August steht der Monatsletzte auf dem 31.). Angezeigt wird aber der
       angefragte Zeitraum — „bis 31.08.2026" zu behaupten, während heute der 2. ist, wäre
       schlicht falsch. Daten liegen dort ohnehin keine, also kostet das Kappen nichts. */
    const today = todayStart();
    if (to > today) to = today;
    return { from: toISO(from), to: toISO(to) };
}

/**
 * Der Filter lebt in der URL — ein Reload oder ein geteilter Link behält den Zeitraum.
 * In die URL gehen die ANFRAGE-Parameter (der Server versteht nur die) UND die Ansicht,
 * damit nach einem Reload derselbe Knopf aktiv ist. `view`/`anchor` ignoriert der Server.
 */
function syncUrl() {
    const p = new URLSearchParams();
    if (state.view === 'all') {
        p.set('preset', 'all');
    } else {
        const w = windowFor(state.view, state.anchor);
        p.set('from', w.from);
        p.set('to', w.to);
    }
    p.set('granularity', VIEWS[state.view].unit);
    p.set('view', state.view);
    if (state.anchor) p.set('anchor', state.anchor);
    history.replaceState(null, '', `?${p}`);
    return p;
}

function readUrl() {
    const p = new URLSearchParams(window.location.search);
    const view = p.get('view');
    if (view && VIEWS[view]) state.view = view;
    const anchor = p.get('anchor');
    if (anchor && /^\d{4}-\d{2}-\d{2}$/.test(anchor)) state.anchor = anchor;
}

/**
 * Vor/Zurück verschiebt das Fenster um SEINE EIGENE LÄNGE — verschoben wird dabei der
 * Anker, nicht das ausgerechnete Fenster. Würde man stattdessen das gerundete Ergebnis
 * weiterschieben, sammelten sich die Rundungen bei jedem Klick auf.
 */
function shiftRange(direction) {
    const cfg = VIEWS[state.view];
    if (!cfg.count) return;                       // „Alles" hat kein Fenster
    const a = state.anchor ? parseDay(state.anchor) : new Date();
    if (state.view === 'month') a.setMonth(a.getMonth() + direction * cfg.count);
    else a.setDate(a.getDate() + direction * cfg.count * (state.view === 'week' ? 7 : 1));
    if (a >= todayStart()) { state.anchor = null; }   // zurück auf „bis heute"
    else state.anchor = toISO(a);
    load();
}

function wireFilter() {
    root.querySelector('#fPrev').addEventListener('click', () => shiftRange(-1));
    root.querySelector('#fNext').addEventListener('click', () => shiftRange(+1));

    root.querySelectorAll('[data-view]').forEach(btn => {
        btn.addEventListener('click', () => {
            state.view = btn.dataset.view;
            state.anchor = null;      // Ansichtswechsel startet wieder bei heute
            load();
        });
    });
}

/** Vom „Neu laden"-Knopf gesetzt; unterscheidet ihn vom Laden nach Filterwechsel. */
let reloadRequested = false;

/* ------------------------------------------------------------------ Laden */

async function load() {
    refreshBtn.disabled = true;
    // Kein Skeleton-Flash beim Nachladen: den alten Stand gedimmt stehen lassen,
    // sonst springt das Layout bei jedem Filterklick.
    root.classList.add('db-loading');

    const params = syncUrl();
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), DASH_CONFIG.REQUEST_TIMEOUT);
    try {
        const res = await fetch(`${DASH_CONFIG.API_ENDPOINT}?${params}`, {
            headers: { Accept: 'application/json' },
            signal: ctrl.signal,
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        render(await res.json());
    } catch (err) {
        const reason = err.name === 'AbortError'
            ? 'Zeitüberschreitung beim Laden der Kennzahlen.'
            : `Kennzahlen nicht ladbar (${esc(err.message)}).`;
        root.innerHTML = `
            <p class="db-callout error">
                <span class="material-symbols-outlined" aria-hidden="true">error</span>
                <span>${reason} Läuft der Server?</span>
            </p>`;
    } finally {
        clearTimeout(timer);
        root.classList.remove('db-loading');
        /* Nur beim ausdruecklichen Klick auf „Neu laden" quittieren — beim Filterwechsel
           waere eine Meldung Laerm, dort sieht man das Ergebnis ja unmittelbar. */
        if (reloadRequested && window.AppShell && window.AppShell.toast) {
            reloadRequested = false;
            window.AppShell.toast('Kennzahlen neu geladen', 'refresh');
        }
        refreshBtn.disabled = false;
    }
}

refreshBtn.addEventListener('click', () => { reloadRequested = true; load(); });
readUrl();
load();
