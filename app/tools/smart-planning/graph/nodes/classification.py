"""
Knoten 2 — Fehlerklassifikation.

Beobachtungspunkt fuer *„falscher Fehler priorisiert"* — bei mehreren gleichzeitigen Fehlern
wird hier zurechenbar, welchen das Modell gewaehlt hat und warum (BA_MASTERPLAN Kap. 9).

VERANTWORTUNGSSCHNITT (Kap. 9.0) — was dieser Knoten NICHT tut
--------------------------------------------------------------
`identify_error_llm.main()` erledigte bisher die Aufgaben von drei Knoten: klassifizieren,
Suchparameter bestimmen UND die Suche ausfuehren (`trigger_identify_tool`). Hier ist nur der
erste Teil. Die Suche gehoert zu **Knoten 3**; ohne die Trennung haette `extracted_context`
keinen eigenen Beobachtungspunkt.

Der Knoten **schlaegt** ausserdem Regelkarten vor (`relevant_cards`, aus dem LLM-Aufruf).
**Aufgeloest und protokolliert werden sie ausschliesslich in Knoten 4.** Genau eine
Aufloesungsstelle, obwohl zwei Knoten am Thema beteiligt sind.

DER PROMPT IST UNVERAENDERT
---------------------------
`run_classification()` ruft `analyze_validation_with_llm()` unveraendert auf. Der Prompt ist
in A, B und C identisch und damit Kontrollbedingung (Kap. 7.1.1) — am 19.08.2026 per SHA-256
vor/nach der Extraktion nachgewiesen. Ihn nur fuer C zu aendern, hiesse Prompt-Wortlaut statt
Orchestrierung zu messen (L09).
"""
from datetime import datetime, timezone


def node_classification(state: dict) -> dict:
    """
    Liest:    state["snapshot_id"], state["initial_validation"] (K1) bzw.
              state["final_validation"] (Rueckkante 8->2)
    Schreibt: state["classified_error"], erhoeht state["iteration"],
              haengt einen trace-Eintrag an.

    Beendet den Prozess NIE. Liefert das LLM keine verwertbare Klassifikation, bleibt
    `classified_error` None — Knoten 8 entscheidet dann auf `stop_uncertain`.
    """
    import identify_error_llm as ident

    begonnen = datetime.now(timezone.utc)

    # Rueckkante 8->2: bei einer neuen FACHLICHEN Iteration liegt bereits ein Ergebnis der
    # Re-Validierung vor - Knoten 7 legt es als `final_validation` ab (ROHE Liste). Das ist
    # dann der aktuelle Stand und schlaegt den Einstiegsstand aus Knoten 1.
    #
    # STATE-SCHNITT (20.08.2026): Bis dahin trugen Knoten 1 und Knoten 7 EIN gemeinsames Feld
    # in ZWEI Formen, und dieser Knoten musste raten, welche er bekommt. Ungefiltert
    # weitergereicht iterierte `run_classification()` ueber die SCHLUESSEL des Dicts und brach
    # mit `AttributeError: str object has no attribute get` ab - die ganze Kette lief danach
    # leer weiter (BA-026). Jetzt sind die Quellen eindeutig benannt; die Typpruefung bleibt
    # nur als Schutz, falls jemand die Felder von aussen setzt.
    if state.get("final_validation"):
        validierung = state["final_validation"]          # Stand nach der letzten Iteration
    else:
        anfang = state.get("initial_validation") or {}
        validierung = anfang.get("meldungen") if isinstance(anfang, dict) else None
    if not isinstance(validierung, list) or not validierung:
        validierung = None                                # dann laedt run_classification selbst

    ergebnis = ident.run_classification(state["snapshot_id"], validation_data=validierung)

    state["classified_error"] = ergebnis["classified_error"]

    # IDENTIFY-HANDOFF (20.08.2026), dieselbe Begruendung wie beim Regeltext aus Knoten 4 und
    # beim Suchkontext aus Knoten 3: Ohne Uebergabe suchte `run_correction_generation()` die
    # Datei ueber `get_latest_iteration_number()` selbst - und haette bei einem Fehlschlag in
    # Iteration 2 die Antwort aus Iteration 1 genommen und fuer aktuell gehalten.
    # Das volle Objekt wird deshalb hier am `classified_error` mitgefuehrt, genau wie
    # `results_object` am `extracted_context` haengt.
    if state["classified_error"] is not None and ergebnis.get("identify_response") is not None:
        state["classified_error"]["identify_response"] = ergebnis["identify_response"]
        state["classified_error"]["identify_response_sha256"] = ergebnis["identify_response_sha256"]
    state["iteration"] = state.get("iteration", 0) + 1
    # BA-043: die REAL angelegte Ordnernummer aus `save_llm_response()`. Bis hierher
    # landete sie nur im Trace; K5/K6/K7 mussten raten (BA-042).
    state["artifact_iteration_number"] = ergebnis.get("iteration_number")

    k = ergebnis["classified_error"] or {}
    dauer_ms = int((datetime.now(timezone.utc) - begonnen).total_seconds() * 1000)
    state.setdefault("trace", []).append({
        "node": "classification",
        "timestamp_utc": begonnen.isoformat(),
        "duration_ms": dauer_ms,
        "input_digest": {"iteration": state["iteration"],
                         "meldungen": len(validierung) if validierung else None},
        "output_digest": {
            "tag": k.get("tag"),
            "error_type": k.get("error_type"),
            "priority_index": k.get("priority_index"),
            # Fuer Knoten 3 bestimmt, hier nur weitergereicht:
            "search_mode": k.get("search_mode"),
            "search_value": k.get("search_value"),
            "should_investigate": k.get("should_investigate"),
            # VORSCHLAG fuer Knoten 4 — keine Aufloesung:
            "relevant_cards_vorgeschlagen": k.get("relevant_cards"),
            "iteration_number": ergebnis.get("iteration_number"),
            # Provenienz der Identifikationsantwort - Gegenstueck zu `identify_input_sha256`
            # in Knoten 5. Das Objekt selbst gehoert NICHT in den trace (Kap. 12.5).
            "identify_response_sha256": ergebnis.get("identify_response_sha256"),
            "fehler": ergebnis.get("error"),
        },
    })
    return state
