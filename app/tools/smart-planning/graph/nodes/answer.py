"""
Knoten 9 — Ausgabe und Finalisierung.

**Kein LLM-Aufruf. Keine Fachlogik. Kein Beobachtungspunkt fuer eine Halluzinationskategorie**
(BA_MASTERPLAN Kap. 15.1).

UMGESTELLT AM 20.08.2026 — UND WARUM (BA-031)
----------------------------------------------
Vorher erzeugte dieser Knoten einen LLM-Audit-Report ueber
`generate_audit_report.run_audit_report()`. Das war ein **vierter Modellaufruf**, den die
Monolith-Pipeline nicht macht: `full_correction` hat sieben Schritte und enthaelt
`generate_audit_report` **nicht** — genauso wenig wie `correction_from_validation`,
`analyze_only` oder `apply_and_upload`. Bedingung C hatte damit eine Faehigkeit, die A und B
fehlt (CLAUDE.md, Bauregel B).

Nachgewiesene Folgen im Durchstich AP-F1 (Fall I03): Knoten 9 brauchte **20.291 ms von
44.792 ms Gesamtlaufzeit — 45 %**, und C erzeugte `audit-report.md` sowie
`audit-report-stats.json`, die A nicht hat. Jeder Zeit- oder Tokenvergleich waere verzerrt
gewesen, und bei der Expertenbewertung haette C ein formuliertes Endergebnis gehabt und A
nicht — was die Blindung bricht (Kap. 16).

Deshalb erzeugt Knoten 9 jetzt **deterministisch** das variantenneutrale Endergebnis ueber
`core.ergebnis_format.aus_graph_state()`. Dieselbe Funktion bildet auch die Ergebnisse von A
und B ab, dort aber **ausserhalb** der Pipeline, allein fuer die Auswertung.
`generate_audit_report()` bleibt unveraendert als optionale, nachgelagerte Produktfunktion —
sie ist nicht mehr Bestandteil der A/B/C-Hauptmessung.

WAS DIESER KNOTEN NICHT TUT
----------------------------
Er **veraendert kein fachliches Ergebnis**. Weder `correction_proposal` noch
`final_validation`, `errors_after`, `decision`, `technical_check` oder `applied` werden
angefasst — er liest sie und formt sie um. Geschrieben werden ausschliesslich `final_answer`
und `finished_at` plus der `trace`-Eintrag. Das ist per Test belegt (BA-031).
"""
from datetime import datetime, timezone


def node_answer(state: dict) -> dict:
    """
    Liest:    den fachlichen Endzustand (Knoten 5–8)
    Schreibt: state["final_answer"], state["finished_at"], haengt einen trace-Eintrag an.

    Beendet den Prozess NIE und kann fachlich nichts kaputtmachen: die Umformung ist rein
    lesend. Scheitert sie dennoch, wird der Fehler protokolliert und der Lauf gilt weiterhin
    als abgeschlossen — die Entscheidung aus Knoten 8 bleibt unberuehrt.
    """
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
    from core.ergebnis_format import aus_graph_state, SCHEMA_VERSION

    begonnen = datetime.now(timezone.utc)
    entscheidung = (state.get("decision") or {}).get("action")

    fehler = None
    try:
        neutral = aus_graph_state(state)
    except Exception as exc:
        neutral = None
        fehler = f"{type(exc).__name__}: {exc}"

    state["final_answer"] = neutral
    state["finished_at"] = datetime.now(timezone.utc).isoformat()

    dauer_ms = int((datetime.now(timezone.utc) - begonnen).total_seconds() * 1000)
    state.setdefault("trace", []).append({
        "node": "answer",
        "timestamp_utc": begonnen.isoformat(),
        "duration_ms": dauer_ms,
        "input_digest": {"decision": entscheidung},
        # Das Ergebnis selbst steht im State; hier nur, dass und womit es gebildet wurde.
        "output_digest": {"schema_version": SCHEMA_VERSION,
                          "ergebnis": (neutral or {}).get("ergebnis"),
                          "llm_aufruf": False,
                          "fehler": fehler},
    })
    return state
