"""
AP-E — Evaluations-Harness für die KOMBINIERTE Fehler-Suite (PT4).

Anders als die isolierte Suite testet diese: mehrere Fehler pro Snapshot, Wiedererkennung
bekannter Fehler durch das Gedächtnis, und (curriculum) das Lernen über die Reihenfolge.

Was das Gedächtnis aus dem isolierten Review bereits kennt (gleiche Entitäten, da alle
Snapshots Kopien von ok-snapshot sind):
  E01 validate_unique_ids (Duplikat demandId)  -> demands:D100005_001 -> D100005_002
  E02 validate_demand_article_ids               -> demands:D100005_001 -> 100005
  E03 validate_density_values                    -> articles:100005     -> 1.017
  E04 validate_work_plan_ids                     -> articles:100079     -> "SP10        SP01"

Pro Snapshot misst die Harness:
  1. Erkennung: findet der Server ALLE erwarteten Validatoren? (Anzahl + Kontexte)
  2. Top-Fehler: identify+generate für den höchstpriorisierten Fehler
  3. Gedächtnis-Wiedererkennung: memory_support des erzeugten Vorschlags (1.0 = erkannt)

Ein voller iterativer Apply-Loop (alle N Fehler nacheinander) ist mechanisch identisch zur
isolierten Suite, nur wiederholt — hier NICHT gefahren, um Server-/LLM-Last zu begrenzen.

Aufruf:  python eval/run_combined_suite.py            (alle 10)
         python eval/run_combined_suite.py --only 08
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

DEMO = Path(__file__).resolve().parent.parent
RUNTIME = DEMO / "smart-planning" / "runtime"
SNAP = DEMO / "smart-planning" / "Snapshots"
SUITE = SNAP / "pt4-manipulated_snapshots" / "kombinierte-fehler-snapshots"
sys.path.insert(0, str(DEMO))
sys.path.insert(0, str(RUNTIME))

import create_snapshot as cs  # noqa: E402
import update_snapshot as us  # noqa: E402
from runtime_storage import get_storage  # noqa: E402
from routes.server_validation import trigger_server_validation  # noqa: E402

# Erwartete Validatoren je Datei (aus ERROR-SNAPSHOTS.md) + welche Fehler dem Gedächtnis
# aus dem isolierten Review bereits bekannt sind.
EXPECTED = {
    "01": (["validate_unique_ids"], "E01 bekannt"),
    "02": (["validate_demand_article_ids"], "E02 bekannt"),
    "03": (["validate_density_values"], "E03 bekannt"),
    "04": (["validate_unique_ids", "validate_demand_article_ids"], "E01+E02 bekannt"),
    "05": (["validate_density_values", "validate_work_plan_ids"], "E03 bekannt + E04 bekannt"),
    "06": (["validate_packaging_references", "validate_unique_ids"], "neu"),
    "07": (["validate_equipment_predecessor_references",
            "validate_equipment_worker_qualification_compatibility"], "neu"),
    "08": (["validate_unique_ids", "validate_demand_article_ids", "validate_density_values"],
           "E01+E02+E03 bekannt"),
    "09": (["validate_work_plan_ids", "validate_packaging_references",
            "validate_packaging_equipment_compatibility_references"], "E04 bekannt + 2 neu"),
    "10": (["validate_unique_ids", "validate_equipment_predecessor_references",
            "validate_start_end_operation_existence"], "1 Typ bekannt + E07 + neu"),
}


def upload_and_validate(entry_id):
    data = json.loads((SUITE / f"snapshot-error-{entry_id}.json").read_text(encoding="utf-8"))
    api = cs.SmartPlanningAPI(); api.authenticate()
    info = api.create_snapshot(name=f"PT4-COMB-{entry_id}", run_crawler=False)
    sid = info["id"]
    st = get_storage()
    st.save_json(f"{sid}/snapshot-data.json", data)
    st.save_json(f"{sid}/original-data/snapshot-data.json", data)
    meta = {"name": f"PT4-COMB-{entry_id}", "comment": "combined eval"}
    st.save_text(f"{sid}/metadata.txt",
                 "# SNAPSHOT INFORMATIONS\n\n```json\n" + json.dumps(meta, indent=2) + "\n```\n")
    upd = us.SmartPlanningAPI(); upd.authenticate()
    upd.update_snapshot(sid, f"PT4-COMB-{entry_id}", "combined eval",
                        json.dumps(data, ensure_ascii=False))
    trigger_server_validation(sid)
    subprocess.run([sys.executable, "validate_snapshot.py", "--snapshot-id", sid],
                   cwd=RUNTIME, capture_output=True, text=True, timeout=300)
    msgs = st.load_json(f"{sid}/snapshot-validation.json") or []
    errs = [m for m in msgs if str(m.get("level")).upper() == "ERROR"]
    return sid, errs


def detected_contexts(errs):
    out = []
    for m in errs:
        msg = m.get("message", "")
        if msg.startswith("[validate_"):
            out.append(msg[1:msg.index("]")])
    return out


def run_top_proposal(sid):
    e = {**os.environ, "RULEBOOK_MODE": "cards", "PYTHONIOENCODING": "utf-8"}
    subprocess.run([sys.executable, "identify_error_llm.py", "--snapshot-id", sid],
                   cwd=RUNTIME, env=e, capture_output=True, text=True, timeout=400)
    gen = subprocess.run([sys.executable, "generate_correction_llm.py", "--snapshot-id", sid],
                         cwd=RUNTIME, env=e, capture_output=True, text=True, timeout=400)
    import glob
    cands = sorted(glob.glob(str(SNAP / "_proposals" / f"{sid}__iteration-*.json")))
    proposal = {}
    if cands:
        rec = json.loads(Path(cands[-1]).read_text(encoding="utf-8"))
        proposal = (rec.get("proposal") or {}).get("correction_proposal") or {}
    # memory_support aus dem Generator-Output ziehen
    ms = None
    for line in (gen.stdout or "").splitlines():
        if "- Memory support:" in line:
            try:
                ms = float(line.split("Memory support:")[1].split("(")[0].strip())
            except Exception:
                pass
    return proposal, ms


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    args = ap.parse_args()
    rows = []
    for entry_id, (expected_ctx, mem_note) in EXPECTED.items():
        if args.only and entry_id != args.only:
            continue
        print(f"\n=== snapshot-error-{entry_id} ({mem_note}) ===")
        sid, errs = upload_and_validate(entry_id)
        got = detected_contexts(errs)
        all_found = all(any(c in g for g in got) for c in expected_ctx)
        print(f"  erwartet {len(expected_ctx)} Fehler {expected_ctx}")
        print(f"  erkannt  {len(errs)}: {got}  -> alle da: {all_found}")
        proposal, ms = run_top_proposal(sid)
        print(f"  Top-Vorschlag: {proposal.get('target_path')} = {str(proposal.get('new_value'))[:40]}  "
              f"memory_support={ms}")
        rows.append({"id": entry_id, "note": mem_note, "expected": expected_ctx,
                     "got": got, "all_found": all_found,
                     "top_target": proposal.get("target_path"),
                     "top_value": proposal.get("new_value"), "memory_support": ms,
                     "snapshot_id": sid})

    print("\n" + "=" * 92)
    print(f"{'Datei':6} {'Erw.':4} {'Erk.':4} {'alle':5} {'mem_support':11} {'Situation'}")
    print("=" * 92)
    for r in rows:
        print(f"error-{r['id']} {len(r['expected']):<4} {len(r['got']):<4} "
              f"{'JA' if r['all_found'] else 'NEIN':5} {str(r['memory_support']):11} {r['note']}")
    print("=" * 92)
    total_exp = sum(len(r["expected"]) for r in rows)
    total_got = sum(len(r["got"]) for r in rows)
    print(f"Fehler erwartet: {total_exp}  erkannt: {total_got}  "
          f"alle-erkannt-Snapshots: {sum(r['all_found'] for r in rows)}/{len(rows)}")
    recognized = sum(1 for r in rows if r["memory_support"] and r["memory_support"] >= 1.0)
    print(f"Gedächtnis-Wiedererkennung (memory_support=1.0): {recognized} Snapshots")
    out = SUITE / "pt4-combined-results.json"
    out.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Details: {out}")


if __name__ == "__main__":
    main()
