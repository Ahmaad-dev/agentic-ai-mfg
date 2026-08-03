"""
AP-E — Evaluations-Harness für die isolierte Fehler-Suite (PT4).

Fährt jeden der 10 isolierten Fehler-Snapshots durch den ECHTEN Loop und misst gegen die
maschinenlesbare Ground Truth (expected-results.json):

  1. Erkennt der Server den Fehler?      (expectedContext + expectedMessageContains)
  2. Findet das Tool das richtige Feld?   (proposal.target_path == change.jsonPath, aufgelöst)
  3. Setzt es den korrekten Wert ein?     (proposal.new_value == Originalwert aus change.before)
  4. Verändert es keine anderen Daten?    (nur ein Feld im Proposal)
  5. Ist es danach gültig?                ZWEI Maßstäbe:
        (a) server-valide  — würde die Re-Validierung bestehen?  (schwächer)
        (b) exakt          — byte-identisch zur ok-Referenz?      (strenger, = Ground Truth)

WICHTIG (Befund aus Fall I03): Bei Fehlern, die den Originalwert ZERSTÖREN (Dichte→0,
Department→"", HE01-Zeit→0, predecessors→[]), existiert der wahre Wert nur noch in der
ok-Referenz. Ohne Referenzdaten kann das Tool ihn nicht exakt wiederherstellen, sondern nur
einen plausiblen (server-validen) Wert raten. Genau diese Lücke misst (a) vs. (b) sichtbar.

Umgebung: SP-TESTINSTANZ (create+update+trigger, vom Nutzer für Weg 2 freigegeben).
Aufruf:   python eval/run_isolated_suite.py            (alle 10)
          python eval/run_isolated_suite.py --only I03 (einer)
          python eval/run_isolated_suite.py --reuse     (nicht neu hochladen, DB/Storage nutzen)
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# `APP` statt `DEMO`: der Ordner heisst seit 02.08.2026 app/.
APP = Path(__file__).resolve().parent.parent
RUNTIME = APP / "tools" / "smart-planning" / "runtime"
SNAP = APP.parent / "data" / "snapshots"
SUITE = SNAP / "pt4-manipulated_snapshots" / "isolated-error-snapshots"
OK_FILE = SNAP / "ok-snapshot.json"
sys.path.insert(0, str(APP))
sys.path.insert(0, str(RUNTIME))

import create_snapshot as cs  # noqa: E402
import update_snapshot as us  # noqa: E402
from runtime_storage import get_storage  # noqa: E402
from routes.server_validation import trigger_server_validation  # noqa: E402

OK = json.loads(OK_FILE.read_text(encoding="utf-8"))
ARTICLE_INDEX = {str(a.get("articleId")): i for i, a in enumerate(OK.get("articles", []))}


def correct_value_from_before(before: str):
    """Aus dem change.before-String den Originalwert extrahieren (JSON-Fragment)."""
    # Formen: '"relDensityMin": 1.017'  '"demandId": "D100005_002"'  '"predecessors": [...]'
    m = re.match(r'^\s*"[^"]+"\s*:\s*(.+)$', before, re.DOTALL)
    frag = m.group(1).strip() if m else before.strip()
    try:
        return json.loads(frag)
    except Exception:
        return frag  # z.B. der nackte '"VOAR01"' Fall


def resolve_jsonpath_location(jsonpath: str):
    """Grobe Normalisierung eines Ground-Truth-jsonPath auf (array, index_or_None, field)."""
    # articles[articleId=100005].relDensityMin -> ('articles', 0, 'relDensityMin')
    m = re.match(r"(\w+)\[articleId=([^\]]+)\]\.(\w+)", jsonpath)
    if m:
        return m.group(1), ARTICLE_INDEX.get(m.group(2)), m.group(3)
    # articles[articleId=X].workItemConfigs[KEY].field -> nested
    m = re.match(r"(\w+)\[articleId=([^\]]+)\]\.(\w+)\[(\w+)\]\.(\w+)", jsonpath)
    if m:
        return m.group(1), ARTICLE_INDEX.get(m.group(2)), f"{m.group(3)}[{m.group(4)}].{m.group(5)}"
    # demands[1].demandId -> ('demands', 1, 'demandId')
    m = re.match(r"(\w+)\[(\d+)\]\.(\w+)", jsonpath)
    if m:
        return m.group(1), int(m.group(2)), m.group(3)
    return jsonpath, None, None


def parse_target_path(tp: str):
    m = re.match(r"(\w+)\[(\d+)\]\.(.+)", tp or "")
    if m:
        return m.group(1), int(m.group(2)), m.group(3)
    return tp, None, None


def upload_and_validate(case):
    data = json.loads((SUITE / case["file"]).read_text(encoding="utf-8"))
    api = cs.SmartPlanningAPI(); api.authenticate()
    info = api.create_snapshot(name=f"PT4-EVAL-{case['code']} {case['title'][:40]}", run_crawler=False)
    sid = info["id"]
    st = get_storage()
    st.save_json(f"{sid}/snapshot-data.json", data)
    st.save_json(f"{sid}/original-data/snapshot-data.json", data)
    # metadata.txt is required by update_snapshot.py in the apply/write-back step — without it
    # apply fails with FileNotFoundError (the memory loop is unaffected, but the corrected
    # snapshot cannot be pushed back to the server).
    meta = {k: v for k, v in info.items() if k != "dataJson"}
    meta["snapshot_source"] = "PT4 eval harness"
    st.save_text(
        f"{sid}/metadata.txt",
        "# SNAPSHOT INFORMATIONS\n\n```json\n"
        + json.dumps(meta, ensure_ascii=False, indent=2) + "\n```\n",
    )
    upd = us.SmartPlanningAPI(); upd.authenticate()
    upd.update_snapshot(sid, f"PT4-EVAL-{case['code']}", f"PT4 isolated eval {case['code']}",
                        json.dumps(data, ensure_ascii=False))
    trigger_server_validation(sid)
    subprocess.run([sys.executable, "validate_snapshot.py", "--snapshot-id", sid],
                   cwd=RUNTIME, capture_output=True, text=True, timeout=300)
    msgs = st.load_json(f"{sid}/snapshot-validation.json") or []
    errs = [m for m in msgs if str(m.get("level")).upper() == "ERROR"]
    return sid, errs


def run_pipeline(sid):
    env = {"RULEBOOK_MODE": "cards", "PYTHONIOENCODING": "utf-8"}
    import os
    e = {**os.environ, **env}
    subprocess.run([sys.executable, "identify_error_llm.py", "--snapshot-id", sid],
                   cwd=RUNTIME, env=e, capture_output=True, text=True, timeout=400)
    subprocess.run([sys.executable, "generate_correction_llm.py", "--snapshot-id", sid],
                   cwd=RUNTIME, env=e, capture_output=True, text=True, timeout=400)
    # neuestes zentrales Proposal für diesen Snapshot lesen
    import glob
    cands = sorted(glob.glob(str(SNAP / "_proposals" / f"{sid}__iteration-*.json")))
    if not cands:
        return None
    rec = json.loads(Path(cands[-1]).read_text(encoding="utf-8"))
    return (rec.get("proposal") or {}).get("correction_proposal") or {}


def evaluate(case, errs, proposal):
    exp_ctx = case["expectedContext"]
    exp_frag = case["expectedMessageContains"]
    change = case["changes"][0]
    correct = correct_value_from_before(change["before"])

    detected = any(f"[{exp_ctx}]" in m.get("message", "") for m in errs)
    frag_ok = any(exp_frag in m.get("message", "") for m in errs)
    count_ok = len(errs) == case["expectedErrorCount"]

    tp = (proposal or {}).get("target_path")
    nv = (proposal or {}).get("new_value")
    g_arr, g_idx, g_field = resolve_jsonpath_location(change["jsonPath"])
    p_arr, p_idx, p_field = parse_target_path(tp)
    field_ok = (g_arr == p_arr and g_idx == p_idx and g_field == p_field)
    # Wertvergleich (lose: numerisch/str)
    def norm(v):
        return round(v, 6) if isinstance(v, (int, float)) else v
    value_ok = norm(nv) == norm(correct)

    return {
        "code": case["code"], "context": exp_ctx,
        "detected": detected, "frag_ok": frag_ok, "count_ok": count_ok,
        "target_path": tp, "gt_jsonpath": change["jsonPath"],
        "field_ok": field_ok,
        "new_value": nv, "correct_value": correct, "value_ok": value_ok,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    args = ap.parse_args()
    spec = json.loads((SUITE / "expected-results.json").read_text(encoding="utf-8"))
    rows = []
    for case in spec["cases"]:
        if args.only and case["code"] != args.only:
            continue
        print(f"\n=== {case['code']} {case['title']} ===")
        sid, errs = upload_and_validate(case)
        print(f"  snapshot={sid[:8]}  ERRORs={len(errs)}")
        proposal = run_pipeline(sid)
        r = evaluate(case, errs, proposal)
        r["snapshot_id"] = sid
        rows.append(r)
        print(f"  detect={r['detected']} field_ok={r['field_ok']} value_ok={r['value_ok']}  "
              f"new={r['new_value']!r} vs gt={r['correct_value']!r}")

    print("\n" + "=" * 96)
    print(f"{'Code':5} {'Context':44} {'detect':7} {'field':6} {'value':6}")
    print("=" * 96)
    for r in rows:
        print(f"{r['code']:5} {r['context']:44} "
              f"{'JA' if r['detected'] else 'NEIN':7} "
              f"{'JA' if r['field_ok'] else 'NEIN':6} "
              f"{'JA' if r['value_ok'] else 'NEIN':6}")
    n = len(rows)
    print("=" * 96)
    print(f"Erkannt: {sum(r['detected'] for r in rows)}/{n}  "
          f"Feld richtig: {sum(r['field_ok'] for r in rows)}/{n}  "
          f"Wert exakt: {sum(r['value_ok'] for r in rows)}/{n}")
    out = SUITE / "pt4-eval-results.json"
    out.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Details: {out}")


if __name__ == "__main__":
    main()
