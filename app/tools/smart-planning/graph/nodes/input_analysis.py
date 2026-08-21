"""
Knoten 1 — Eingabeanalyse.

Der Einstiegsknoten. **Kein LLM-Aufruf, keine neue Fachlogik** (BA_MASTERPLAN Kap. 9:
*„duenner Wrapper, kein LLM-Call"*). Er beantwortet genau eine Frage: *Womit haben wir es zu
tun?* — und schreibt die Antwort in den Zustand, damit sie spaeter zurechenbar ist.

WARUM ES IHN ERST JETZT GIBT (Befund F6 aus BA-025, 20.08.2026)
---------------------------------------------------------------
AP-D deckte die Knoten 2 bis 9 ab; Knoten 1 hatte *„kein dedizierter Code"* und fiel damit
durch die Paketbuchhaltung. Nach AP-D standen also **acht** Knotenmodule, waehrend das
Protokoll „alle neun Knoten stehen" behauptete. Dieses Modul schliesst die Luecke, bevor
AP-E den Graphen verdrahtet.

KEIN C-ONLY-VORTEIL (CLAUDE.md, Bauregel B)
--------------------------------------------
Die Vorrangregel beim Lesen der Validierungsmeldungen ist **woertlich dieselbe**, die der
Monolith in `sp_agent.py:552` benutzt: zuerst die Kopie im Iterationsordner (der Stand, auf
dem die Auswahl beruhte), sonst die Datei eine Ebene darueber. Sie wird hier nicht
verbessert, nur an einer zweiten Stelle angewandt. **Neu ist ausschliesslich, dass das
Ergebnis in einem expliziten Zustand landet** statt fluechtig zu bleiben — und genau das ist
der Untersuchungsgegenstand, keine zusaetzliche Faehigkeit.

Dieser Knoten **triggert keine Validierung**. Das Ausloesen ist ein Pipeline-Schritt
(`validate_snapshot`), den AP-E genauso verdrahtet, wie der Monolith ihn heute als ersten
Schritt fuehrt. Wuerde Knoten 1 zusaetzlich triggern, haette C eine Validierung mehr als
A und B.
"""
from datetime import datetime, timezone


def node_input_analysis(state: dict) -> dict:
    """
    Liest:    state["snapshot_id"]
    Schreibt: state["initial_validation"], state["errors_before"],
              haengt einen trace-Eintrag an.

    Beendet den Prozess NIE. Fehlt die Validierungsdatei, bleibt `errors_before` auf `None`
    — **nicht auf 0**. Dieselbe Unterscheidung wie bei `errors_after` (Kap. 7.1.2): `None`
    heisst „keine belastbare Angabe", `0` heisst „nachweislich fehlerfrei". Ein stilles
    Null-Ergebnis an dieser Stelle waere eine erfundene Zahl.
    """
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "runtime"))
    from runtime_storage import get_storage, get_latest_iteration_number

    begonnen = datetime.now(timezone.utc)
    snapshot_id = state["snapshot_id"]

    fehler = None
    meldungen = None
    quelle = None
    try:
        storage = get_storage()
        # Vorrang exakt wie im Monolithen (sp_agent.py:552).
        n = get_latest_iteration_number(snapshot_id, require_file="snapshot-validation.json")
        if n is not None:
            meldungen = storage.load_json(f"{snapshot_id}/iteration-{n}/snapshot-validation.json")
            if meldungen is not None:
                quelle = f"iteration-{n}/snapshot-validation.json"
        if meldungen is None:
            meldungen = storage.load_json(f"{snapshot_id}/snapshot-validation.json")
            if meldungen is not None:
                quelle = "snapshot-validation.json"
    except Exception as exc:
        fehler = f"{type(exc).__name__}: {exc}"

    if meldungen is None:
        # Kein Artefakt gefunden. KEINE Zahl erfinden.
        state["initial_validation"] = {
            "quelle": None, "meldungen": None, "errors": None, "warnings": None,
            "error": fehler or "keine snapshot-validation.json gefunden",
        }
        state["errors_before"] = None
    else:
        errors = [m for m in meldungen if isinstance(m, dict) and m.get("level") == "ERROR"]
        warnings = [m for m in meldungen if isinstance(m, dict) and m.get("level") == "WARNING"]
        state["initial_validation"] = {
            "quelle": quelle,
            "meldungen": meldungen,
            "errors": len(errors),
            "warnings": len(warnings),
            # Die Tags sind die Aufgabenbeschreibung: WAS ist zu korrigieren.
            "error_tags": sorted({t for m in errors
                                  for t in [_tag(m.get("message", ""))] if t}),
            "error": fehler,
        }
        state["errors_before"] = len(errors)

    vr = state["initial_validation"]
    dauer_ms = int((datetime.now(timezone.utc) - begonnen).total_seconds() * 1000)
    state.setdefault("trace", []).append({
        "node": "input_analysis",
        "timestamp_utc": begonnen.isoformat(),
        "duration_ms": dauer_ms,
        "input_digest": {"snapshot_id": snapshot_id},
        # Die Meldungen selbst gehoeren NICHT in den trace — sie koennen lang werden.
        # Anzahl, Tags und Herkunftsdatei genuegen als Beleg (Kap. 12.5).
        "output_digest": {"quelle": vr.get("quelle"), "errors": vr.get("errors"),
                          "warnings": vr.get("warnings"),
                          "error_tags": vr.get("error_tags"), "fehler": vr.get("error")},
    })
    return state


def _tag(message: str):
    """Zieht den `[validate_*]`-Tag aus einer Servermeldung. Rein textuell, keine Bewertung."""
    if not message:
        return None
    anfang = message.find("[validate_")
    if anfang == -1:
        return None
    ende = message.find("]", anfang)
    return message[anfang + 1:ende] if ende != -1 else None
