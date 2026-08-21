"""
AP-G3 — First-Pass-Baseline ueber die zehn Pilotfaelle.

**Unveraendert.** Waehrend dieses Durchgangs wird kein Produktcode, kein Prompt und keine
Regelkarte angefasst. Der Lauf beantwortet zwei Fragen:

  1. Trifft jeder Pilotfall den Prozesspfad, fuer den er gebaut wurde?
  2. Wo genau liegt eine Auffaelligkeit - Knoten 2, 3, 4, 5, 6, 7 oder 8?

`generate_audit_report()` wird NICHT aufgerufen (Masterplan Kap. 3.6.2 - bedarfsgesteuert).

Jeder Fall laeuft in einem EIGENEN Prozess auf einem FRISCHEN Snapshot: `RULEBOOK_MODE` und
`SP_ARCHITECTURE_MODE` werden beim Import aus `agent_config` gelesen, `importlib.reload()`
schaltet sie nicht um (BA-021).

Aufruf:  python eval/run_pilot_suite.py [--only P06,P07] [--bedingung C]
"""
import argparse
import contextlib
import io
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

APP = Path(__file__).resolve().parent.parent
SP = APP / "tools" / "smart-planning"
SNAP = APP.parent / "data" / "snapshots"
PILOT = SNAP / "ba-pilot-snapshots"
ARCHIV = APP.parent / "data" / "archive" / "ba-g3-pilot"

BEDINGUNGEN = {
    "A": {"SP_ARCHITECTURE_MODE": "monolith", "RULEBOOK_MODE": "monolith"},
    "B": {"SP_ARCHITECTURE_MODE": "monolith", "RULEBOOK_MODE": "cards"},
    "C": {"SP_ARCHITECTURE_MODE": "graph", "RULEBOOK_MODE": "cards"},
}


class Stumm(io.StringIO):
    def reconfigure(self, *a, **k):
        return None


# --------------------------------------------------------------- Kindprozess
def kind(code: str, bedingung: str) -> dict:
    for p in (str(APP), str(SP), str(SP / "runtime"), str(APP / "eval")):
        sys.path.insert(0, p)
    logging.disable(logging.CRITICAL)

    from core.run_metadata import require_ba_env
    from core.agent_config import RULEBOOK_MODE, SP_ARCHITECTURE_MODE, MEMORY_MODE
    from runtime_storage import get_storage
    import create_snapshot as cs
    import update_snapshot as us
    from routes.server_validation import trigger_server_validation
    from agents.sp_agent import SPAgent

    # Harter Umgebungszwang - ein Pilotlauf unter dem falschen Interpreter waere wertlos.
    meta = require_ba_env(f"Pilotlauf {code} / Bedingung {bedingung}")

    spec = json.loads((PILOT / "expected-results.json").read_text(encoding="utf-8"))
    fall = next(c for c in spec["cases"] if c["code"] == code)
    daten = json.loads((PILOT / fall["file"]).read_text(encoding="utf-8"))

    buf = Stumm()
    with contextlib.redirect_stdout(buf):
        api = cs.SmartPlanningAPI(); api.authenticate()
        info = api.create_snapshot(name=f"BA-PILOT-{code} {fall['prozesspfad'][:40]}",
                                   run_crawler=False)
        sid = info["id"]
        st = get_storage()
        st.save_json(f"{sid}/snapshot-data.json", daten)
        st.save_json(f"{sid}/original-data/snapshot-data.json", daten)
        m = {k: v for k, v in info.items() if k != "dataJson"}
        m["snapshot_source"] = "BA Pilotkatalog (AP-G1)"
        st.save_text(f"{sid}/metadata.txt",
                     "# SNAPSHOT INFORMATIONS\n\n```json\n"
                     + json.dumps(m, ensure_ascii=False, indent=2) + "\n```\n")
        upd = us.SmartPlanningAPI(); upd.authenticate()
        upd.update_snapshot(snapshot_id=sid, name=m.get("name"), comment="",
                            data_json=json.dumps(daten, ensure_ascii=False))
        trig = trigger_server_validation(sid)
        import validate_snapshot as vs
        vs.validate_snapshot(sid)
        vorher = st.load_json(f"{sid}/snapshot-validation.json") or []
        errs = [x for x in vorher if x.get("level") == "ERROR"]

        agent = SPAgent(runtime_dir=str((SP / "runtime").resolve()))
        r = agent.execute_pipeline("full_correction", sid)

    # --- Belege fuer den tatsaechlich gegangenen Pfad ---
    gs, it_nr = None, None
    for n in range(6, 0, -1):
        d = st.load_json(f"{sid}/iteration-{n}/graph_state.json")
        if d:
            gs, it_nr = d, n
            break
    suche = st.load_json(f"{sid}/last_search_results.json") or {}
    treffer = suche.get("results") or []
    fuzzy = any(isinstance(x, dict) and x.get("fuzzy_match") for x in treffer)
    trace = (gs or {}).get("trace") or []
    klassifikationen = [t for t in trace if t.get("node") == "classification"]

    vorschlag = None
    for n in range(6, 0, -1):
        d = st.load_json(f"{sid}/iteration-{n}/llm_correction_proposal.json")
        if d:
            vorschlag = d.get("correction_proposal")
            break

    return {
        "code": code, "bedingung": bedingung, "snapshot_id": sid,
        "prozesspfad_vorgesehen": fall["prozesspfad"],
        "ziel_artikel": fall["ziel_artikel"],
        "erwartete_fehler": fall["erwartete_fehler"],
        "ground_truth": fall["changes"],
        "schalter_effektiv": {"RULEBOOK_MODE": RULEBOOK_MODE,
                              "SP_ARCHITECTURE_MODE": SP_ARCHITECTURE_MODE,
                              "MEMORY_MODE": MEMORY_MODE},
        "fehler_vorher": len(errs),
        "fehler_tags_vorher": sorted({_tag(x.get("message", "")) for x in errs} - {None}),
        "trigger_vor_lauf": {"ok": trig.get("ok"), "status": trig.get("status")},
        "rueckgabe": {k: r.get(k) for k in ("success", "pipeline", "total_iterations",
                                            "final_validation", "architecture_mode", "error")},
        "completed_steps": r.get("completed_steps"),
        "vorschlag": vorschlag,
        # --- Pfadbelege ---
        "kontext": {"search_mode": suche.get("search_mode"),
                    "search_value": suche.get("search_value"),
                    "results_count": suche.get("results_count"),
                    "error_type_heuristik": suche.get("error_type"),
                    "fuzzy_verwendet": fuzzy},
        "karten": ((gs or {}).get("matched_rules") or {}).get("cards_loaded"),
        "decision": (gs or {}).get("decision"),
        "iterationen_state": (gs or {}).get("iteration"),
        "klassifikationen_im_trace": len(klassifikationen),
        "rueckkante_durchlaufen": len(klassifikationen) > 1,
        "trace_knoten": [t.get("node") for t in trace],
        "graph_state_iteration": it_nr,
        "lauf_metadaten": meta,
    }


def _tag(msg):
    if not msg or "[validate_" not in msg:
        return None
    a = msg.find("[validate_")
    e = msg.find("]", a)
    return msg[a + 1:e] if e != -1 else None


# --------------------------------------------------------------- Elternprozess
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None, help="Komma-Liste, z. B. P06,P07")
    ap.add_argument("--bedingung", default="C", choices=list(BEDINGUNGEN))
    ap.add_argument("--kind", nargs=2, default=None, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    if args.kind:
        print("###JSON###" + json.dumps(kind(args.kind[0], args.kind[1]),
                                        ensure_ascii=False, default=str))
        return 0

    spec = json.loads((PILOT / "expected-results.json").read_text(encoding="utf-8"))
    codes = [c["code"] for c in spec["cases"]]
    if args.only:
        gewuenscht = {x.strip() for x in args.only.split(",")}
        codes = [c for c in codes if c in gewuenscht]

    ARCHIV.mkdir(parents=True, exist_ok=True)
    schalter = BEDINGUNGEN[args.bedingung]
    ergebnisse = []
    for code in codes:
        env = {**os.environ, **schalter, "MEMORY_MODE": "off", "HUMAN_IN_THE_LOOP": "false",
               "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
        print(f"--- {code} / Bedingung {args.bedingung} {schalter} ---")
        p = subprocess.run([sys.executable, __file__, "--kind", code, args.bedingung],
                           env=env, capture_output=True, text=True, timeout=2400)
        zeile = next((l for l in p.stdout.splitlines() if l.startswith("###JSON###")), None)
        if not zeile:
            print(f"  FEHLGESCHLAGEN (exit {p.returncode})")
            print("  " + (p.stderr or p.stdout)[-500:])
            ergebnisse.append({"code": code, "bedingung": args.bedingung,
                               "fehlgeschlagen": True, "stderr": (p.stderr or "")[-2000:]})
            continue
        e = json.loads(zeile[len("###JSON###"):])
        ergebnisse.append(e)
        fv = e["rueckgabe"]["final_validation"] or {}
        print(f"  snapshot={e['snapshot_id'][:8]} fehler_vorher={e['fehler_vorher']} "
              f"tags={e['fehler_tags_vorher']}")
        print(f"  kontext: mode={e['kontext']['search_mode']} value={e['kontext']['search_value']} "
              f"treffer={e['kontext']['results_count']} fuzzy={e['kontext']['fuzzy_verwendet']}")
        print(f"  karten={e['karten']}  decision={(e['decision'] or {}).get('action')}  "
              f"iterationen={e['rueckgabe']['total_iterations']} "
              f"rueckkante={e['rueckkante_durchlaufen']}")
        print(f"  errors_after={fv.get('errors')} is_valid={fv.get('is_valid')} "
              f"vorschlag={(e['vorschlag'] or {}).get('new_value')}")

    stempel = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ziel = ARCHIV / f"pilot-firstpass-{args.bedingung}-{stempel}.json"
    ziel.write_text(json.dumps({
        "zweck": "AP-G3 First-Pass-Baseline - PILOT, KEIN MESSERGEBNIS",
        "bedingung": args.bedingung, "schalter": schalter,
        "unveraendert": "kein Produktcode, kein Prompt, keine Regelkarte waehrend dieses Laufs",
        "ergebnisse": ergebnisse,
    }, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"\n  Rohdaten: {ziel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
