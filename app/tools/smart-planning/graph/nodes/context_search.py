"""
Knoten 3 — Kontextsuche.

Beobachtungspunkt fuer *„leerer oder falscher Kontext"* — ein real beobachteter Fehlermodus
(fehlende `last_search_results.json`, Muster 1 aus `04_PT4/BEFUNDE_UND_LEHREN.md`).

Ausserdem der Knoten, der **Befund D** abfaengt: Dort berief sich ein Korrekturvorschlag auf
Artikel „aus Department 20100", waehrend die drei zitierten in 20200 lagen — es waren die
Array-Nachbarn. Niemand konnte das sehen, weil nirgends stand, welches Vergleichskollektiv
tatsaechlich im Kontext lag. `extracted_context` haelt das jetzt fest (`lines_used`,
`field_examples`, `results_hash`).

VERANTWORTUNGSSCHNITT (Kap. 9.0)
--------------------------------
Bis AP-D6 fuehrte `identify_error_llm.main()` die Suche selbst aus (`trigger_identify_tool`).
Jetzt bestimmt **Knoten 2** nur `search_mode` und `search_value`; **dieser Knoten fuehrt die
Suche aus**. Erst dadurch bekommt der Kontext einen eigenen Beobachtungspunkt.

MVP-ENTSCHEIDUNG — bewusst und dokumentiert
-------------------------------------------
`run_context_search()` ruft das bestehende `identify_snapshot.main()` **als Ganzes** auf, statt
dessen 295 Zeilen Ablaufsteuerung herauszuloesen. Der Masterplan erlaubt das ausdruecklich
(Kap. 9): derselbe, unveraenderte Code — kein Strohmann. Fuer die Forschungsfrage ist
entscheidend, WELCHER Kontext geliefert wurde, nicht WIE die Suche intern arbeitet.
Am 19.08.2026 ueber 7 Szenarien und 3 Suchmodi per SHA-256 nachgewiesen, dass die erzeugte
`last_search_results.json` byte-identisch zur Fassung vor der Aenderung ist.
"""
from datetime import datetime, timezone


def node_context_search(state: dict) -> dict:
    """
    Liest:    state["snapshot_id"], state["classified_error"] (Knoten 2)
    Schreibt: state["extracted_context"], haengt einen trace-Eintrag an.

    Beendet den Prozess NIE. Liefert Knoten 2 keinen `search_value` oder findet die Suche
    nichts, bleibt das ein Zustand — Knoten 8 entscheidet darueber (`stop_uncertain`).
    """
    import identify_snapshot as ids

    begonnen = datetime.now(timezone.utc)
    k = state.get("classified_error") or {}

    # Knoten 2 hat entschieden, WONACH gesucht wird — dieser Knoten fuehrt es aus.
    ergebnis = ids.run_context_search(
        snapshot_id=state["snapshot_id"],
        search_mode=k.get("search_mode"),
        search_value=k.get("search_value"),
    )
    state["extracted_context"] = ergebnis

    dauer_ms = int((datetime.now(timezone.utc) - begonnen).total_seconds() * 1000)
    state.setdefault("trace", []).append({
        "node": "context_search",
        "timestamp_utc": begonnen.isoformat(),
        "duration_ms": dauer_ms,
        "input_digest": {"search_mode": k.get("search_mode"),
                         "search_value": k.get("search_value"),
                         "should_investigate": k.get("should_investigate")},
        # Der Kontext selbst gehoert NICHT in den trace — er kann sechsstellig viele Zeichen
        # umfassen (Kap. 12.5). Hash, Anzahl und die benutzten Pfade genuegen als Beleg.
        "output_digest": {"results_count": ergebnis.get("results_count"),
                          "error_type": ergebnis.get("error_type"),
                          "results_hash": ergebnis.get("results_hash"),
                          "lines_used": ergebnis.get("lines_used"),
                          "field_examples": ergebnis.get("field_examples"),
                          "fehler": ergebnis.get("error")},
    })
    return state
