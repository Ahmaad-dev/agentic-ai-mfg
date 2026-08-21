"""
Knoten 5 — Korrekturgenerierung.

Beobachtungspunkt fuer **Kategorie 1: fachliche Halluzination** (BA_MASTERPLAN Kap. 15.1) —
der falsche Korrekturwert entsteht und wird hier sichtbar.

Gemeinsam mit `matched_rules` aus Knoten 4 ausserdem der Punkt, an dem **Kategorie 3
(Regelhalluzination)** pruefbar wird: Knoten 4 belegt, welche Karten geladen WAREN, dieser
Knoten liefert die Behauptung darueber. Erst das Paar macht sie messbar — deshalb war
"ein Knoten pro Kategorie" zu einfach gedacht (Kap. 15.1).

Der Knoten ruft `generate_correction_llm.run_correction_generation()`. Das ist dieselbe
Funktion, die auch die CLI benutzt — eine Implementierung, kein Drift (Kap. 12.2).
"""
import hashlib
import json
from datetime import datetime, timezone


def _sha256(obj):
    """
    Kanonischer Hash eines Objekts. GLEICHE Definition wie `_proposal_sha256` in
    `validate_correction_schema_llm.py:251-256` - sonst liessen sich die Hashes der beiden
    Knoten nicht gegeneinander halten, und die Invariante waere nicht pruefbar.
    """
    if obj is None:
        return None
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def node_correction(state: dict) -> dict:
    """
    Liest:    state["snapshot_id"], state["matched_rules"] (Knoten 4)
    Schreibt: state["correction_proposal"], haengt einen trace-Eintrag an.

    Beendet den Prozess NIE. Eine offene HitL-Sperre oder ein Fehler ist ein ZUSTAND —
    die bedingte Kante entscheidet darueber (Kap. 11), nicht ein sys.exit.
    """
    import generate_correction_llm as gen
    import identify_snapshot as ids
    import identify_error_llm as ident

    begonnen = datetime.now(timezone.utc)

    # Knoten 4 hat das Regelwerk geladen UND protokolliert, welche Karten es waren.
    # Wir reichen genau diesen Text weiter, statt ihn ein zweites Mal zu laden — sonst
    # koennte `matched_rules` etwas anderes ausweisen als das, was das Modell gesehen hat.
    matched = state.get("matched_rules") or {}
    fix_rules = matched.get("rule_text")

    # Hash des TATSAECHLICH uebergebenen Regeltexts. Ohne ihn liesse sich spaeter nicht
    # beweisen, dass das Modell genau die Regeln gesehen hat, die `matched_rules` ausweist —
    # und damit waere die Regelprovenienz (Kategorie 3, Kap. 15.1) wertlos.
    # `run_correction_generation` prueft `fix_rules is None`, nicht truthy: ein LEERER String
    # wird durchgereicht und loest KEIN Nachladen aus.
    regel_hash = (hashlib.sha256(fix_rules.encode("utf-8")).hexdigest()
                  if fix_rules is not None else None)

    # Knoten 3 hat den Kontext geholt UND protokolliert, welchen. Wir reichen genau dieses
    # Objekt weiter - dieselbe Begruendung wie beim Regeltext. Ohne das laedt
    # `run_correction_generation()` die Datei ein zweites Mal von Platte
    # (generate_correction_llm.py:930), und `results_hash` aus Knoten 3 waere keine
    # Zusicherung, sondern nur eine Behauptung ueber einen frueheren Dateizustand.
    kontext = state.get("extracted_context") or {}
    kontext_objekt = kontext.get("results_object")
    kontext_hash = ids.context_sha256(kontext_objekt) if kontext_objekt is not None else None
    # HANDOFF-ZUSICHERUNG: derselbe Hash wie in Knoten 3, ueber DIESELBE Funktion gebildet.
    handoff_ok = (kontext_hash is not None and kontext_hash == kontext.get("results_hash"))

    # Knoten 2 hat klassifiziert UND die Antwort protokolliert. Auch sie wird durchgereicht,
    # statt sie ein zweites Mal von Platte zu suchen (generate_correction_llm.py:931).
    klassifikation = state.get("classified_error") or {}
    identify_objekt = klassifikation.get("identify_response")
    identify_hash = (ident.identify_sha256(identify_objekt)
                     if identify_objekt is not None else None)
    identify_handoff_ok = (identify_hash is not None
                           and identify_hash == klassifikation.get("identify_response_sha256"))

    # BA-044: PRUEFUNG VOR DEM AUFRUF, nicht danach.
    # BA-043 hat die Nummer hier nur durchgereicht. `run_correction_generation()` behandelt
    # `iteration_number=None` aber als Legacy-Weg und loest die neueste Iteration selbst auf
    # (generate_correction_llm.py:913-914 -> get_latest_iteration_number_local, def :94).
    # Fuer CLI/A/B ist das RICHTIG und bleibt unveraendert; im Graph-Pfad ist es genau der
    # stille Fallback, den BA-043 ausschliessen wollte - und er greift NACH dem teuren Teil,
    # es entstuende ein LLM-Aufruf auf dem falschen Ordner.
    #
    # Gleiche Behandlung wie in Knoten 6: fehlende Artefaktnummer ist ein FEHLERZUSTAND,
    # kein Anlass zu raten. Kein Aufruf, kein Resolver, kein LLM.
    artefakt_nr = state.get("artifact_iteration_number")
    if artefakt_nr is None:
        meldung = ("artifact_iteration_number fehlt - Knoten 2 hat keine Artefakt-Iteration "
                   "hinterlassen. Im Graph-Pfad ist das ein Fehlerzustand, kein "
                   "latest-Fallback (BA-044). run_correction_generation() NICHT gerufen.")
        state["correction_proposal"] = None
        state["correction_response"] = None
        state.setdefault("trace", []).append({
            "node": "correction",
            "timestamp_utc": begonnen.isoformat(),
            "duration_ms": 0,
            "input_digest": {
                "regeln_von_knoten4": fix_rules is not None,
                "regeln_zeichen": len(fix_rules) if fix_rules is not None else None,
                "regeln_sha256": regel_hash,
                "karten": matched.get("cards_loaded"),
                "context_input_sha256": kontext_hash,
                "context_handoff_ok": handoff_ok,
                "context_results_count": (kontext_objekt or {}).get("results_count"),
                "identify_input_sha256": identify_hash,
                "identify_handoff_ok": identify_handoff_ok,
                "artifact_iteration_number": None,
            },
            "output_digest": {
                "action": None, "target_path": None, "new_value": None,
                "value_source": None, "confidence_score": None,
                "blockiert": False, "fehler": meldung,
            },
        })
        return state

    fehler = None
    try:
        ergebnis = gen.run_correction_generation(
            snapshot_id=state["snapshot_id"],
            fix_rules=fix_rules,
            identify_response=identify_objekt,
            search_results=kontext_objekt,
            # BA-043: explizit statt 'latest'. Im Graph-Pfad entscheidet K2 ueber den
            # Ordner, nicht das Dateisystem. BA-044: oben bereits als vorhanden geprueft.
            iteration_number=artefakt_nr,
            check_open_proposal=True,
        )
    except Exception as exc:
        # Defensiv wie in Knoten 6: ein LLM-Timeout oder ein fehlender Eingang darf den
        # Graphen nicht toeten, sondern muss als Zustand sichtbar werden.
        ergebnis = {"proposal": None, "output_data": None, "llm_call": None,
                    "iteration_number": None, "blocked_by": None,
                    "error": f"{type(exc).__name__}: {exc}"}
        fehler = ergebnis["error"]

    state["correction_proposal"] = ergebnis["proposal"]
    # BA-047: Die vollstaendige Huelle wandert MIT in den State.
    # `run_correction_generation()` liefert unter "proposal" nur den INNEREN Vorschlag; die
    # vollstaendige `LLMCorrectionResponse` steht daneben unter "output_data" - und zwar
    # BITGLEICH das Objekt, das `save_correction_proposal()` nach
    # `iteration-N/llm_correction_proposal.json` schreibt (generate_correction_llm.py:1117-1131).
    # Sie hier zu uebernehmen kostet nichts und macht Knoten 6 pruefbar: er validiert dann
    # dieselbe Einheit, die auch der A/B-Pfad validiert, OHNE sie ueber "latest" von Platte
    # zurueckzuholen.
    state["correction_response"] = ergebnis.get("output_data")
    if ergebnis.get("blocked_by"):
        # Nur unter HUMAN_IN_THE_LOOP=true erreichbar; in Messlaeufen (false) nie.
        state["manual_intervention_required"] = True

    vorschlag = ergebnis["proposal"] or {}
    dauer_ms = int((datetime.now(timezone.utc) - begonnen).total_seconds() * 1000)
    state.setdefault("trace", []).append({
        "node": "correction",
        "timestamp_utc": begonnen.isoformat(),
        "duration_ms": dauer_ms,
        "input_digest": {
            "regeln_von_knoten4": fix_rules is not None,
            "regeln_zeichen": len(fix_rules) if fix_rules is not None else None,
            "regeln_sha256": regel_hash,
            "karten": matched.get("cards_loaded"),
            # Kontextprovenienz - beweist, WELCHEN Suchkontext das Modell wirklich sah.
            "context_input_sha256": kontext_hash,
            "context_handoff_ok": handoff_ok,
            "context_results_count": (kontext_objekt or {}).get("results_count"),
            # Identifikationsprovenienz - beweist, WELCHE Klassifikation das Modell sah.
            "identify_input_sha256": identify_hash,
            "identify_handoff_ok": identify_handoff_ok,
            # BA-044: belegt, AUF WELCHEM Iterationsordner generiert wurde.
            "artifact_iteration_number": artefakt_nr,
        },
        # BA-047: Hash der erzeugten Huelle. Zusammen mit dem Eingangshash von Knoten 6
        # belegt er die harte Invariante "K6 prueft genau das, was K5 erzeugt hat" -
        # nachrechenbar aus den Rohdaten, nicht behauptet.
        "provenienz": {"response_sha256": _sha256(ergebnis.get("output_data"))},
        "output_digest": {
            "action": vorschlag.get("action"),
            "target_path": vorschlag.get("target_path"),
            "new_value": vorschlag.get("new_value"),
            "value_source": vorschlag.get("value_source", "llm"),
            "confidence_score": vorschlag.get("confidence_score"),
            "blockiert": bool(ergebnis.get("blocked_by")),
            "fehler": fehler,
        },
    })
    return state
