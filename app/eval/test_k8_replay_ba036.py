"""
Gegenprobe zum umgekehrten K8-Entscheidungsvertrag (BA-044).

**Die Frage:** Ändert der neue Vertrag eine Entscheidung, die in BA-036 bereits belegt wurde?
Wenn ja, wäre der "Fix" in Wahrheit eine Verhaltensänderung im gemessenen Pfad — und alles,
was BA-036 über die fachlich validierte Rückkante 8→2 sagt, stünde wieder offen.

**Das Verfahren:** Aus den archivierten Läufen P04 (`7a9a981d…`) und P10 (`f48a8d8d…`) wird je
Durchgang der EINGANG von Knoten 8 rekonstruiert und durch die HEUTIGE `node_evaluation()`
geschickt. Verglichen wird gegen die damals aufgezeichnete `action`.

**Was das ist und was nicht:** Ein *Replay der aufgezeichneten Eingänge*, kein erneuter Lauf
der Pipeline. Es beweist, dass der Entscheidungsvertrag bei identischem Eingang identisch
entscheidet — nicht, dass ein neuer Lauf denselben Eingang erzeugen würde. Letzteres ist
Gegenstand von R8 (P04/P10 auf frischen Pilot-Snapshots).

**Eine Quelle je Wert, ausdrücklich:** `revalidation_ok` stand im alten K8-Eingangsdigest gar
nicht (es war bis BA-044 kein Entscheidungsterm). Es wird deshalb aus dem `output_digest` von
Knoten 7 desselben Durchgangs gezogen — der Stelle, die es erzeugt. Das ist keine Annahme,
sondern die Schreibstelle (`apply_revalidate.py`, Registry in `graph/trace_keys.py`).

**Kein Messlauf.** Es wird nichts ausgeführt, nichts hochgeladen, nichts validiert; die
Snapshots werden nur gelesen.

Aufruf:  .venv/Scripts/python.exe app/eval/test_k8_replay_ba036.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from graph_regression_harness import APP, Pruefung, knoten_laden, pfade_setzen  # noqa: E402

pfade_setzen()

SNAP = APP.parent / "data" / "snapshots"

#: Die beiden in BA-036 ausgewerteten Läufe. Beide sind PILOT-Fälle, keiner der 17 Messfälle.
LAEUFE = {
    "P04": "7a9a981d-34ef-4e25-83a9-34066076aa5a",
    "P10": "f48a8d8d-1210-473d-8dda-7e2779572473",
}

#: Was BA-036 tabellarisch festgehalten hat — hier als unabhängige zweite Quelle, damit ein
#: stillschweigend veränderter Archivstand auffiele.
BA036 = {
    "P04": ["continue", "continue", "stop_uncertain"],
    "P10": ["continue", "continue", "stop_uncertain"],
}


def _trace(sid: str) -> list:
    for n in range(6, 0, -1):
        f = SNAP / sid / f"iteration-{n}" / "graph_state.json"
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8"))["trace"]
    raise FileNotFoundError(f"kein graph_state.json unter {SNAP / sid}")


def _durchgaenge(trace: list) -> list:
    """Je Durchgang die drei Digests, die den K8-Eingang bilden."""
    tc = [t for t in trace if t["node"] == "technical_check"]
    ar = [t for t in trace if t["node"] == "apply_revalidate"]
    ev = [t for t in trace if t["node"] == "evaluation"]
    return list(zip(tc, ar, ev))


def _state_aus_trace(tc, ar, ev) -> dict:
    """Rekonstruiert den K8-Eingang aus den aufgezeichneten Digests."""
    a_out, e_in = ar["output_digest"], ev["input_digest"]
    revalidation = ({"ok": a_out["revalidation_ok"], "job_id": a_out.get("revalidation_job"),
                     "waited_s": a_out.get("revalidation_waited_s")}
                    if a_out.get("revalidation_ok") is not None else None)
    return {
        "technical_check": {"schema_valid": tc["output_digest"]["schema_valid"],
                            "retries": tc["output_digest"]["retries"], "errors": []},
        "applied": {"applied_ok": a_out["applied_ok"], "uploaded": a_out["uploaded"],
                    "revalidation": revalidation,
                    "errors_resolved": a_out.get("errors_resolved"),
                    "errors_remaining": a_out.get("errors_remaining"),
                    "errors_new": a_out.get("errors_new"),
                    "errors": a_out.get("fehler") or []},
        # Der Vorschlagsinhalt spielt für K8 keine Rolle, nur ob ein `target_path` da war.
        "correction_proposal": ({"target_path": "aus/archiv"}
                                if e_in["hat_target_path"] else {}),
        "errors_after": a_out["errors_after"],
        "iteration": e_in["iteration"],
        "max_iterations": e_in["max_iterations"],
        "trace": [],
    }


def replay() -> Pruefung:
    p = Pruefung("Replay — P04/P10 aus BA-036 gegen den neuen K8-Vertrag")
    k8 = knoten_laden("evaluation")

    for fall, sid in LAEUFE.items():
        dg = _durchgaenge(_trace(sid))
        p.gleich(f"{fall}: Anzahl Durchgänge", 3, len(dg))
        damals_alle, heute_alle = [], []
        for i, (tc, ar, ev) in enumerate(dg, start=1):
            damals = ev["output_digest"]["action"]
            heute = k8.node_evaluation(_state_aus_trace(tc, ar, ev))["decision"]["action"]
            damals_alle.append(damals)
            heute_alle.append(heute)
            p.gleich(f"{fall} D{i}: action (damals -> heute)", damals, heute)
        p.gleich(f"{fall}: Archiv deckt sich mit der Tabelle in BA-036",
                 BA036[fall], damals_alle)
        p.gleich(f"{fall}: Verlauf unverändert", BA036[fall], heute_alle)
    return p


def main():
    sys.path.insert(0, str(APP))
    from core.run_metadata import require_ba_env
    meta = require_ba_env("K8-Replay gegen BA-036 (BA-044)")
    print(f"Umgebung: {meta['umgebung']['sys_prefix']}")
    p = replay()
    p.drucken()
    return 0 if p.bestanden else 1


if __name__ == "__main__":
    sys.exit(main())
