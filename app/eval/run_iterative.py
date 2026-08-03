"""
AP-E — Iterativer Mehrfehler-Korrektur-Loop (#9), EVAL-MODUS.

Zeigt, dass die Pipeline einen Snapshot mit MEHREREN Fehlern schrittweise auf „valide" bringt:
pro Runde identify -> generate -> schema-check -> apply -> upload -> re-validate, bis 0 Fehler
oder max. Runden.

WICHTIG (Governance): In PRODUKTION wird NIE ohne menschliche Freigabe angewendet (HitL, AP1/AP3).
Dieser Runner ist ausdrücklich ein EVAL-Werkzeug: er wendet den KI-Vorschlag DIREKT an, um die
Korrektur-FÄHIGKEIT der Pipeline zu messen — er erzeugt KEINE Review-Zeile und KEINEN
Gedächtnisfall (fabriziert also keine menschliche Entscheidung).

Aufruf: python eval/run_iterative.py --snapshot-id <sid> [--max 5]
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# `APP` statt `DEMO`: der Ordner heisst seit 02.08.2026 app/.
APP = Path(__file__).resolve().parent.parent
RUNTIME = APP / "tools" / "smart-planning" / "runtime"
SNAP = APP.parent / "data" / "snapshots"
sys.path.insert(0, str(APP))
sys.path.insert(0, str(RUNTIME))
from runtime_storage import get_storage  # noqa: E402
from routes.server_validation import trigger_server_validation  # noqa: E402


def step(script, sid, extra=None):
    e = {**os.environ, "RULEBOOK_MODE": "cards", "PYTHONIOENCODING": "utf-8"}
    cmd = [sys.executable, script, "--snapshot-id", sid] + (extra or [])
    p = subprocess.run(cmd, cwd=RUNTIME, env=e, capture_output=True, text=True, timeout=400)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def error_count(sid):
    trigger_server_validation(sid)
    step("validate_snapshot.py", sid)
    msgs = get_storage().load_json(f"{sid}/snapshot-validation.json") or []
    return [m for m in msgs if str(m.get("level")).upper() == "ERROR"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot-id", required=True)
    ap.add_argument("--max", type=int, default=5)
    args = ap.parse_args()
    sid = args.snapshot_id

    errs = error_count(sid)
    print(f"Start: {len(errs)} Fehler")
    for m in errs:
        print(f"   - {m.get('message','')[:80]}")

    history = [len(errs)]
    for rnd in range(1, args.max + 1):
        if not errs:
            break
        print(f"\n--- Runde {rnd} ---")
        rc, out = step("identify_error_llm.py", sid)
        rc, out = step("generate_correction_llm.py", sid)
        for line in out.splitlines():
            if any(k in line for k in ("- Target:", "- New Value (final)", "MEMORY-OVERRIDE")):
                print(f"   {line.strip()}")
        rc, _ = step("validate_correction_schema_llm.py", sid)
        rc, applyout = step("apply_correction.py", sid)
        if rc != 0:
            print(f"   apply fehlgeschlagen: {applyout.strip()[-160:]}")
            break
        rc, _ = step("update_snapshot.py", sid)
        errs = error_count(sid)
        history.append(len(errs))
        print(f"   -> nach Runde {rnd}: {len(errs)} Fehler")

    print(f"\nFehler-Verlauf: {' -> '.join(str(h) for h in history)}")
    print("Ergebnis:", "VALIDE (0 Fehler)" if not errs else f"{len(errs)} Fehler verbleiben")


if __name__ == "__main__":
    main()
