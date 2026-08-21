"""
Knoten 6 — Technische Pruefung.

Beobachtungspunkt fuer **Kategorie 2: strukturelle Halluzination** (BA_MASTERPLAN Kap. 15.1).
Wichtig fuer die Formulierung in der Arbeit: Die strukturelle Halluzination ENTSTEHT in
Knoten 5 — hier wird sie nur ERKANNT. "Beobachtungspunkt", nicht "Entstehungsort".

Der Knoten ruft `validate_correction_schema_llm.run_technical_check()` auf, das seinerseits
dieselbe `validate_with_retry()` nutzt wie der CLI-Pfad. Es gibt also genau EINE
Implementierung der Retry-Logik; hier kommt nur die Zustandsformung dazu.
"""
import hashlib
import json
from datetime import datetime, timezone


def _sha256(obj):
    """
    Kanonischer Hash. GLEICHE Definition wie `_proposal_sha256`
    (`validate_correction_schema_llm.py:251-256`) und wie in Knoten 5 - nur dann lassen sich
    die Hashes der Knoten gegeneinander halten, und nur dann ist die Invariante pruefbar.
    """
    if obj is None:
        return None
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def node_technical_check(state: dict) -> dict:
    """
    Liest:    state["snapshot_id"], state["correction_proposal"] (aus Knoten 5)
    Schreibt: state["technical_check"], haengt einen trace-Eintrag an.

    Beendet den Prozess NIE. Ein fehlgeschlagener Schema-Check ist ein Zustand, ueber den
    die bedingte Kante A entscheidet (Kap. 11): Retries uebrig -> zurueck zu Knoten 5,
    sonst -> Knoten 8 mit "stop_uncertain".
    """
    import validate_correction_schema_llm as schema

    begonnen = datetime.now(timezone.utc)

    # Knoten 5 hat den Vorschlag samt Iterationsnummer hinterlassen. Fehlt er, laedt
    # run_technical_check die neueste Iteration selbst — derselbe Weg wie die CLI.
    # BA-047: PRUEFGEGENSTAND IST DIE VOLLSTAENDIGE HUELLE, nicht der innere Vorschlag.
    #
    # `validate_correction_proposal()` prueft gegen `LLMCorrectionResponse`
    # (validate_correction_schema_llm.py:35, Modell in correction_models.py:66-72) - also
    # gegen {iteration, snapshot_id, original_error, error_analyzed, correction_proposal}.
    # Bekam dieser Knoten den INNEREN Vorschlag, fehlten vier Pflichtfelder, und es entstand
    # ein erzwungener LLM-Retry, den A und B nicht haben (BA-046, Bauregel B). Schlimmer:
    # der Retry ueberschrieb `llm_correction_proposal.json` mit einer Huelle, deren
    # `iteration`/`snapshot_id` das MODELL geraten hatte - in P04 stand danach in
    # `iteration-2/` ein Artefakt mit `iteration: 1`. Das beschaedigt die Rohdaten (Regel 7).
    #
    # Die Huelle wird von Knoten 5 verlustfrei durchgereicht (`state["correction_response"]`)
    # und NICHT hier neu konstruiert: nur so ist belegbar, dass geprueft wird, was Knoten 5
    # wirklich erzeugt hat. Der innere Vorschlag bleibt fuer Knoten 7 erhalten.
    huelle = state.get("correction_response")
    vorschlag = state.get("correction_proposal")
    eingang_sha256 = _sha256(huelle)
    # BA-043: NICHT mehr aus der eigenen vorigen Ausgabe (Zirkelbezug, BA-042 - der Wert
    # fror auf dem ersten Durchgang ein). Ausschliesslich die aktuelle Artefaktnummer.
    iteration = state.get("artifact_iteration_number")

    # BA-043: Im Graph-Pfad ist eine fehlende Artefaktnummer ein UNGUELTIGER ZUSTAND,
    # kein Anlass fuer ein stilles "nimm die neueste". Lieber ehrlich unsicher als
    # heimlich auf dem falschen Ordner arbeiten.
    if iteration is None:
        state["technical_check"] = {
            "schema_valid": False, "retries": 0,
            "errors": ["artifact_iteration_number fehlt - Knoten 2 hat keine "
                       "Artefakt-Iteration hinterlassen. Im Graph-Pfad ist das ein "
                       "Fehlerzustand, kein latest-Fallback (BA-043)."],
            "proposal": None, "iteration_number": None,
            "proposal_sha256_before": None, "proposal_sha256_after": None}
        state.setdefault("trace", []).append({
            "node": "technical_check", "timestamp_utc": begonnen.isoformat(),
            "duration_ms": 0,
            "input_digest": {"hat_vorschlag": vorschlag is not None,
                             "artifact_iteration_number": None,
                             "response_sha256_eingang": eingang_sha256},
            "output_digest": {"schema_valid": False, "retries": 0, "fehleranzahl": 1,
                              "fehler": "artifact_iteration_number fehlt"}})
        return state

    # BA-047: Fehlt die Huelle, waere der einzige Ausweg wieder ein Disk- oder
    # Neubau-Fallback - also genau das, was BA-044 ausgeschlossen hat. Ehrlich unsicher
    # statt heimlich etwas anderes pruefen.
    if huelle is None and vorschlag is not None:
        state["technical_check"] = {
            "schema_valid": False, "retries": 0,
            "errors": ["correction_response fehlt - Knoten 5 hat keine vollstaendige "
                       "LLMCorrectionResponse hinterlassen. Der innere Vorschlag allein ist "
                       "KEIN gueltiger Pruefgegenstand (BA-047)."],
            "proposal": None, "iteration_number": iteration,
            "proposal_sha256_before": None, "proposal_sha256_after": None}
        state.setdefault("trace", []).append({
            "node": "technical_check", "timestamp_utc": begonnen.isoformat(),
            "duration_ms": 0,
            "input_digest": {"hat_vorschlag": True,
                             "artifact_iteration_number": iteration,
                             "response_sha256_eingang": None},
            "output_digest": {"schema_valid": False, "retries": 0, "fehleranzahl": 1,
                              "fehler": "correction_response fehlt"}})
        return state

    ergebnis = schema.run_technical_check(
        snapshot_id=state["snapshot_id"],
        iteration_number=iteration,
        correction_proposal=huelle,
    )

    state["technical_check"] = ergebnis
    # BA-043/BA-047: Nach der Pruefung ist die FINALE Huelle autoritativ - bei einem
    # legitimen Retry ist das eine ANDERE als die von Knoten 5. Beides wandert zurueck in
    # den State: die Huelle fuer die Nachvollziehbarkeit, der darin enthaltene innere
    # Vorschlag fuer Knoten 7. Ohne das arbeitete Knoten 7 mit dem Stand von Knoten 5
    # weiter und meldete zu Recht Drift (BA-042).
    if ergebnis.get("proposal") is not None:
        _final = ergebnis["proposal"]
        if isinstance(_final, dict) and "correction_proposal" in _final:
            state["correction_response"] = _final
            state["correction_proposal"] = _final["correction_proposal"]
        else:
            # Legacy-Form (innerer Vorschlag). Tritt im Graph-Pfad ab BA-047 nicht mehr auf,
            # wird aber nicht stillschweigend als Huelle ausgegeben.
            state["correction_proposal"] = _final

    dauer_ms = int((datetime.now(timezone.utc) - begonnen).total_seconds() * 1000)
    state.setdefault("trace", []).append({
        "node": "technical_check",
        "timestamp_utc": begonnen.isoformat(),
        "duration_ms": dauer_ms,
        # Digests statt Rohdaten: der trace soll lesbar bleiben (Kap. 12.5). Die vollen
        # Artefakte liegen ohnehin im Iterationsordner.
        "input_digest": {"hat_vorschlag": vorschlag is not None,
                         "artifact_iteration_number": iteration,
                         # BA-047: HARTE INVARIANTE. Dieser Hash muss dem
                         # `provenienz.response_sha256` von Knoten 5 desselben Durchgangs
                         # entsprechen - dann ist bewiesen, dass hier genau die Huelle
                         # geprueft wurde, die Knoten 5 erzeugt hat. Nachrechenbar aus den
                         # Rohdaten, nicht behauptet.
                         "response_sha256_eingang": eingang_sha256},
        "provenienz": {"proposal_sha256_before": ergebnis.get("proposal_sha256_before"),
                       "proposal_sha256_after": ergebnis.get("proposal_sha256_after"),
                       "retry_hat_vorschlag_geaendert":
                           ergebnis.get("proposal_sha256_before") != ergebnis.get("proposal_sha256_after"),
                       # Die FINALE Huelle nach einem etwaigen Retry.
                       "response_sha256_final": _sha256(state.get("correction_response"))},
        "output_digest": {"schema_valid": ergebnis["schema_valid"],
                          "retries": ergebnis["retries"],
                          "fehleranzahl": len(ergebnis["errors"])},
    })
    return state
