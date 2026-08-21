"""
AP-H4a — Der BA-Runner fuer die Hauptmessung A / B / C.

WARUM EIN EIGENER RUNNER (BA-025, Befund F4)
---------------------------------------------
Die PT4-Runner sind fuer diese Messung unbrauchbar und werden **nicht umgebaut**:
`run_combined_suite.py:97` und `run_iterative.py:33` erzwingen `RULEBOOK_MODE=cards`
**hart** (`{**os.environ, "RULEBOOK_MODE": "cards"}` - das Literal gewinnt gegen die Umgebung)
und setzen `MEMORY_MODE` gar nicht, sodass der Default `on` greift. Ein Lauf fuer **Bedingung
A** waere dort unbemerkt ein `cards`-Lauf **mit** Gedaechtnis. Sie sind PT4-Nachweise und
bleiben, wie sie sind (harte Regel 1).

WAS DIESER RUNNER NICHT TUT
----------------------------
Keine neue Fachlogik. Er startet die bestehenden Pipelines und schreibt auf, was passiert.
`generate_audit_report()` wird **nie** aufgerufen (Masterplan Kap. 3.6.2 - bedarfsgesteuert).

DIE DREI BEDINGUNGEN (Masterplan Kap. 7.1)
-------------------------------------------
    A   SP_ARCHITECTURE_MODE=monolith   RULEBOOK_MODE=monolith    Ausgangszustand
    B   SP_ARCHITECTURE_MODE=monolith   RULEBOOK_MODE=cards       realer Ist-Zustand
    C   SP_ARCHITECTURE_MODE=graph      RULEBOOK_MODE=cards       neue Gesamtarchitektur

In allen dreien: `MEMORY_MODE=off`, `HUMAN_IN_THE_LOOP=false`.

**Je Bedingung ein eigener Prozess.** `RULEBOOK_MODE` und `SP_ARCHITECTURE_MODE` werden beim
Import aus `agent_config` gelesen; `importlib.reload()` schaltet sie nicht um - dieser Fehler
hat BA-021 verdorben und BA-024 fast ein zweites Mal. Protokolliert wird der **effektiv
geltende** Wert, nicht der gesetzte.

**Je Lauf ein frischer Snapshot**, damit keine Bedingung auf dem Ergebnis einer anderen
aufsetzt.

KEIN FALSCHES GRUEN
--------------------
Ein Abbruch ist **kein** Ergebnis mit null Fehlern. `final_validation=None` oder
`revalidation_ok != True` werden als **Unsicherheit** gefuehrt (`ergebnis="unsicher"`), nie als
Erfolg. Ein Fehler in einem Arm markiert genau diesen Lauf und beendet die Suite nicht.

Aufruf:
    python eval/run_ba_abc_suite.py --katalog pilot --only P01,P04 --bedingungen A,B,C
    python eval/run_ba_abc_suite.py --katalog mess                      (erst in AP-H!)
"""
import argparse
import random
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
KATALOGE = {
    "pilot": SNAP / "ba-pilot-snapshots",
    "mess": SNAP / "pt4-manipulated_snapshots" / "isolated-error-snapshots",
}
ARCHIV = APP.parent / "data" / "archive" / "ba-h4a"

BEDINGUNGEN = {
    "A": {"SP_ARCHITECTURE_MODE": "monolith", "RULEBOOK_MODE": "monolith"},
    "B": {"SP_ARCHITECTURE_MODE": "monolith", "RULEBOOK_MODE": "cards"},
    "C": {"SP_ARCHITECTURE_MODE": "graph", "RULEBOOK_MODE": "cards"},
}

# =========================================================================
# H2 - WIEDERHOLUNGEN (UF2, Konsistenz)
# =========================================================================
#: Wiederholungen je Fall. **Verbindlich festgelegt am 21.08.2026, VOR der Hauptmessung**
#: (BA-055). Masterplan und Arbeitspakete nannten durchgaengig nur die Spanne "3-5x", also
#: keine verbindliche Zahl - die Festlegung war eine offene methodische Entscheidung und
#: wurde ausdruecklich getroffen, nicht abgeleitet.
#:
#: ⚠ **Wiederholungen sind KEINE zusaetzlichen Faelle** (Masterplan Kap. 15.3). 5 x 17 ergibt
#: NICHT n=85. Es bleiben **17 Faelle**, ergaenzt um eine **Within-Case-Stabilitaet** je Fall.
#: Wer die Wiederholungen als Fallzahl mitzaehlt, ueberschaetzt die Aussagekraft um das
#: Fuenffache. Der Runner erhebt sie deshalb bewusst als Wiederholung eines Falls, nicht als
#: eigenen Fall - erkennbar an identischer `fall`-ID und laufender `wiederholung`.
WIEDERHOLUNGEN = 5

#: Nur **A und C** werden wiederholt. **B ist Kontrollarm und laeuft einmal** - er dient nur
#: UF1 (Masterplan Kap. 7.1, AP-H5). Das ist keine Sparmassnahme, sondern Teil des Designs:
#: B beantwortet die Frage nach dem Kartensystem, nicht die nach der Konsistenz.
WIEDERHOLUNGSARME = ("A", "C")

# =========================================================================
# H4 - RANDOMISIERUNG
# =========================================================================
#: Fester Seed, **vor der Hauptmessung dokumentiert** (BA-055). Der Wert selbst ist beliebig
#: und darf es sein - entscheidend ist allein, dass er **vorher** feststeht und im Rohdatensatz
#: mitgeschrieben wird. Einen Seed nach dem Sehen der Ergebnisse zu waehlen oder zu wechseln
#: waere dasselbe wie das Nachjustieren einer Messvorschrift (harte Regel 5).
#:
#: Gewaehlt: das Datum der Festlegung. Keine Bedeutung ausser Nachvollziehbarkeit.
RANDOM_SEED = 20260821

#: WAS randomisiert wird: die REIHENFOLGE der Tripel (Fall x Bedingung x Wiederholung).
#: WAS NICHT: die Zuordnung von Schaltern zu Bedingungen, die Faelle selbst oder irgendetwas
#: an der A/B/C-Semantik. Jeder Lauf bleibt ein eigener Prozess mit eigenem frischen Snapshot.
#:
#: WOZU: Ohne Mischung liefe erst alles von A, dann alles von B, dann alles von C. Jede
#: Drift ueber die Zeit - Serverlast, Modellverhalten, Netzlatenz - fiele dann systematisch
#: mit der Bedingung zusammen und waere von einem Architektureffekt nicht zu trennen
#: (Masterplan Kap. 17).

#: Das gemeinsame **29-Feld-Messschema**. ALLE drei Bedingungen liefern genau diese
#: Schluessel - sonst waeren die Arme nicht vergleichbar. Reihenfolge fest.
#:
#: ⚠ `ergebnis` BEZEICHNET NUR DEN TECHNISCHEN ABSCHLUSS (BA-052).
#: `"fehlerfrei"` heisst: Apply, Upload und Re-Validierung waren erfolgreich und der Server
#: meldet 0 Fehler. Es heisst **NICHT**, dass die Korrektur fachlich richtig war. Pilotfall
#: P01 endete in allen drei Armen `fehlerfrei` und schlug dennoch **1.049** statt der Ground
#: Truth **1.063** vor. Die Ground-Truth-Korrektheit wird NICHT hier entschieden, sondern in
#: der Auswertung aus `new_value` gegen `artefakte.ground_truth` - beide liegen je Zeile vor.
#: Deshalb kein zusaetzliches Verdikt-Feld: die Rohwerte sind da, die Bewertung gehoert in
#: AP-I und nicht in den Runner.
MESSSCHEMA = (
    "fall", "bedingung", "snapshot_id", "abgebrochen", "abbruchgrund",
    "schalter_effektiv", "fehler_vorher", "fehler_tags_vorher",
    "action", "target_path", "new_value", "reasoning",
    "schema_gueltig", "schema_versuche",
    "applied_ok", "uploaded", "revalidation_ok", "fehler_nachher",
    # BA-052: `errors_remaining` fehlte hier - eines der vier Kategorie-4-Felder. Kein
    # Zusatzfeld fuer die Messinkonsistenz (die haengt an `provenienz`), sondern das
    # Schliessen einer Luecke im urspruenglichen Schema. Damit 29 Felder.
    "errors_resolved", "errors_remaining", "errors_new", "new_error_types",
    "ergebnis", "iterationen", "karten", "kontext", "provenienz",
    "artefakte", "lauf_metadaten",
)


class Stumm(io.StringIO):
    def reconfigure(self, *a, **k):
        return None


def _tag(msg):
    if not msg or "[validate_" not in msg:
        return None
    a = msg.find("[validate_")
    e = msg.find("]", a)
    return msg[a + 1:e] if e != -1 else None


def kind(fall: str, bedingung: str, katalog: str, wiederholung: str = "1") -> dict:
    """Ein Lauf, ein Prozess, ein frischer Snapshot."""
    for p in (str(APP), str(SP), str(SP / "runtime"), str(APP / "eval")):
        sys.path.insert(0, p)
    logging.disable(logging.CRITICAL)

    from core.run_metadata import require_ba_env
    from core.agent_config import RULEBOOK_MODE, SP_ARCHITECTURE_MODE, MEMORY_MODE, HUMAN_IN_THE_LOOP
    from runtime_storage import get_storage
    import create_snapshot as cs
    import update_snapshot as us
    from routes.server_validation import trigger_server_validation
    from agents.sp_agent import SPAgent

    # HARTER Umgebungszwang, vor dem ersten Fall. Ein Messlauf unter dem falschen Interpreter
    # ist nicht "unbrauchbar mit Vermerk", sondern schlicht nicht vergleichbar (BA-027).
    meta = require_ba_env(f"BA-Messlauf {fall} / Bedingung {bedingung}")

    basis = KATALOGE[katalog]
    spec = json.loads((basis / "expected-results.json").read_text(encoding="utf-8"))
    f = next(c for c in spec["cases"] if c["code"] == fall)
    daten = json.loads((basis / f["file"]).read_text(encoding="utf-8"))

    zeile = {k: None for k in MESSSCHEMA}
    zeile.update({
        "fall": fall, "bedingung": bedingung, "abgebrochen": False,
        "schalter_effektiv": {"RULEBOOK_MODE": RULEBOOK_MODE,
                              "SP_ARCHITECTURE_MODE": SP_ARCHITECTURE_MODE,
                              "MEMORY_MODE": MEMORY_MODE,
                              "HUMAN_IN_THE_LOOP": HUMAN_IN_THE_LOOP},
        "lauf_metadaten": meta,
    })
    # H2: Die Wiederholungsnummer wandert in `lauf_metadaten` - ein bestehendes Feld des
    # 29-Feld-Schemas. **Kein neues Schemafeld**: das Schema bleibt unveraendert, sein Inhalt
    # wird praeziser. Masterplan Kap. 17 verlangt die Wiederholungsnummer je Lauf.
    zeile["lauf_metadaten"]["wiederholung"] = int(wiederholung)
    zeile["lauf_metadaten"]["wiederholungen_gesamt"] = (
        WIEDERHOLUNGEN if bedingung in WIEDERHOLUNGSARME else 1)

    buf = Stumm()
    try:
        with contextlib.redirect_stdout(buf):
            api = cs.SmartPlanningAPI(); api.authenticate()
            # Die Wiederholungsnummer gehoert in den Snapshot-Namen: sonst tragen fuenf
            # Snapshots desselben Falls denselben Namen und sind auf dem Server nicht
            # auseinanderzuhalten.
            info = api.create_snapshot(name=f"BA-{bedingung}-{fall}-W{wiederholung}",
                                       run_crawler=False)
            sid = info["id"]
            zeile["snapshot_id"] = sid
            st = get_storage()
            st.save_json(f"{sid}/snapshot-data.json", daten)
            st.save_json(f"{sid}/original-data/snapshot-data.json", daten)
            m = {k: v for k, v in info.items() if k != "dataJson"}
            m["snapshot_source"] = f"BA {katalog}-Katalog (AP-H4a)"
            st.save_text(f"{sid}/metadata.txt", "# SNAPSHOT INFORMATIONS\n\n```json\n"
                         + json.dumps(m, ensure_ascii=False, indent=2) + "\n```\n")
            upd = us.SmartPlanningAPI(); upd.authenticate()
            upd.update_snapshot(snapshot_id=sid, name=m.get("name"), comment="",
                                data_json=json.dumps(daten, ensure_ascii=False))
            # Expliziter Trigger VOR der Messung - sonst ist der Ausgangsbefund veraltet.
            trigger_server_validation(sid)
            import validate_snapshot as vs
            vs.validate_snapshot(sid)
            # VORHER-Meldungen sichern, BEVOR die Re-Validierung dieselbe Datei
            # ueberschreibt. Spaeter nachladen wuerde den Nach-Zustand liefern und
            # Kategorie 4 zu 0 rechnen (BA-052). Format geprueft: list[dict] mit
            # `level`/`message` - genau das, was `_fehler_identitaeten()` erwartet.
            vorher_meldungen = st.load_json(f"{sid}/snapshot-validation.json") or []
            errs = [x for x in vorher_meldungen if x.get("level") == "ERROR"]

            agent = SPAgent(runtime_dir=str((SP / "runtime").resolve()))
            r = agent.execute_pipeline("full_correction", sid)
    except BaseException as exc:
        zeile["abgebrochen"] = True
        zeile["abbruchgrund"] = f"{type(exc).__name__}: {exc}"
        zeile["ergebnis"] = "abgebrochen"      # NIE 0 Fehler
        return zeile

    zeile["fehler_vorher"] = len(errs)
    zeile["fehler_tags_vorher"] = sorted({_tag(x.get("message", "")) for x in errs} - {None})

    fv = r.get("final_validation") or {}
    zeile["iterationen"] = r.get("total_iterations")
    zeile["revalidation_ok"] = fv.get("revalidation_ok")
    zeile["fehler_nachher"] = fv.get("errors") if r.get("final_validation") else None

    # --- Artefakte je Arm: gleiche Quellen, gleiche Auswertung ---
    vorschlag, schema, gs = None, None, None
    for n in range(6, 0, -1):
        if vorschlag is None:
            d = st.load_json(f"{sid}/iteration-{n}/llm_correction_proposal.json")
            if d:
                vorschlag = d.get("correction_proposal")
        if gs is None:
            gs = st.load_json(f"{sid}/iteration-{n}/graph_state.json")
    if gs:
        schema = gs.get("technical_check")
        zeile["karten"] = (gs.get("matched_rules") or {}).get("cards_loaded")
        ec = gs.get("extracted_context") or {}
        zeile["kontext"] = {"search_mode": ec.get("search_mode"),
                            "results_count": ec.get("results_count"),
                            "results_hash": ec.get("results_hash")}
        zeile["provenienz"] = {"rule_text_hash": (gs.get("matched_rules") or {}).get("rule_text_hash"),
                               "artifact_iteration_number": gs.get("artifact_iteration_number")}
        ap = gs.get("applied") or {}
        zeile["applied_ok"] = ap.get("applied_ok")
        zeile["uploaded"] = ap.get("uploaded")
    else:
        # A und B: kein GraphState. Was belegbar ist, kommt aus den Artefakten; der Rest
        # bleibt None - NICHT geraten (BA-033).
        up = st.load_json(f"{sid}/upload-result.json") or {}
        zeile["uploaded"] = bool(up.get("success")) if up else None
        zeile["applied_ok"] = True if r.get("success") else None

    if vorschlag:
        zeile.update({"action": vorschlag.get("action"),
                      "target_path": vorschlag.get("target_path"),
                      "new_value": vorschlag.get("new_value"),
                      "reasoning": vorschlag.get("reasoning")})
    if schema:
        zeile["schema_gueltig"] = schema.get("schema_valid")
        zeile["schema_versuche"] = schema.get("retries")

    # --- KATEGORIE 4: eine gemeinsame Funktion fuer A, B und C (BA-052) ---
    # Vorher aus der gesicherten Liste, Nachher NUR bei nachweislich abgeschlossener
    # Re-Validierung. Der GraphState ist fuer Kategorie 4 NICHT die privilegierte Quelle.
    from kategorie4 import kategorie4 as _k4, cross_check_graphstate as _cc
    nachher_meldungen = None
    if zeile["revalidation_ok"] is True:
        nachher_meldungen = st.load_json(f"{sid}/snapshot-validation.json")
    k4 = _k4(vorher_meldungen, nachher_meldungen, zeile["revalidation_ok"])
    for _f in ("errors_resolved", "errors_remaining", "errors_new", "new_error_types"):
        zeile[_f] = k4[_f]

    # Fuer C: Gegenprobe gegen die persistierten Werte. Kein Wert "gewinnt" - eine Abweichung
    # ist ein Befund ueber das MESSINSTRUMENT und wird als solcher ausgewiesen, nicht als
    # fachlicher Abbruch. Kein neues Schemafeld: das Ergebnis haengt an `provenienz`.
    cc = _cc(k4, gs)
    zeile["provenienz"] = (zeile["provenienz"] or {}) | {
        "kategorie4_basis": k4["basis"], "kategorie4_hinweis": k4["hinweis"],
        "kategorie4_cross_check": cc}

    # --- Ergebnis: Unsicherheit ist kein Erfolg ---
    if zeile["fehler_nachher"] is None or zeile["revalidation_ok"] is not True:
        zeile["ergebnis"] = "unsicher"
    elif zeile["fehler_nachher"] == 0:
        zeile["ergebnis"] = "fehlerfrei"
    else:
        zeile["ergebnis"] = f"verbleibend:{zeile['fehler_nachher']}"

    if cc.get("durchgefuehrt") and not cc.get("identisch"):
        # Technisch erfolgreicher Lauf, aber das Messinstrument widerspricht sich.
        # Ausdruecklich NICHT als Pipeline-Abbruch oder stop_uncertain ausgeben.
        zeile["ergebnis"] = f"messinkonsistenz_kategorie4|{zeile['ergebnis']}"

    zeile["artefakte"] = {"snapshot": f"data/snapshots/{sid}",
                          "graph_state": bool(gs),
                          "ground_truth": f.get("changes")}
    return zeile


def messplan(codes, arme, wiederholungen=WIEDERHOLUNGEN, seed=RANDOM_SEED):
    """
    Erzeugt die randomisierte Reihenfolge der Tripel (Fall, Bedingung, Wiederholung).

    **Reproduzierbar:** gleicher Seed + gleiche Eingabe -> gleiche Reihenfolge. Ein eigener
    `random.Random(seed)` statt des globalen Moduls, damit nichts anderes im Prozess den
    Zustand beeinflusst.

    B laeuft einmal (Kontrollarm), A und C je `wiederholungen` mal.

    Returns (plan, kopf) - `kopf` sind die Messmetadaten, die in den Rohdatensatz gehoeren.
    """
    plan = []
    for fall in codes:
        for b in arme:
            n = wiederholungen if b in WIEDERHOLUNGSARME else 1
            for w in range(1, n + 1):
                plan.append({"fall": fall, "bedingung": b, "wiederholung": w})

    random.Random(seed).shuffle(plan)
    for i, e in enumerate(plan, start=1):
        e["position"] = i

    kopf = {
        "seed": seed,
        "wiederholungen": wiederholungen,
        "wiederholungsarme": list(WIEDERHOLUNGSARME),
        "laeufe_gesamt": len(plan),
        "laeufe_je_bedingung": {b: sum(1 for e in plan if e["bedingung"] == b) for b in arme},
        "hinweis": ("Wiederholungen sind KEINE zusaetzlichen Faelle - die Fallzahl bleibt die "
                    "Zahl der Faelle, ergaenzt um Within-Case-Stabilitaet (Masterplan 15.3)."),
        "reihenfolge": [f"{e['fall']}/{e['bedingung']}/W{e['wiederholung']}" for e in plan],
    }
    return plan, kopf


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--katalog", default="pilot", choices=list(KATALOGE))
    ap.add_argument("--only", default=None)
    ap.add_argument("--bedingungen", default="A,B,C")
    ap.add_argument("--wiederholungen", type=int, default=WIEDERHOLUNGEN,
                    help=f"Wiederholungen je Fall fuer {'/'.join(WIEDERHOLUNGSARME)} "
                         f"(Default {WIEDERHOLUNGEN}, verbindlich seit BA-055)")
    ap.add_argument("--seed", type=int, default=RANDOM_SEED,
                    help=f"Random-Seed der Reihenfolge (Default {RANDOM_SEED})")
    ap.add_argument("--trockenlauf", action="store_true",
                    help="nur den Messplan erzeugen und ausgeben - fuehrt NICHTS aus")
    ap.add_argument("--kind", nargs=4, default=None, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    if args.kind:
        print("###JSON###" + json.dumps(kind(*args.kind), ensure_ascii=False, default=str))
        return 0

    spec = json.loads((KATALOGE[args.katalog] / "expected-results.json").read_text(encoding="utf-8"))
    codes = [c["code"] for c in spec["cases"]]
    if args.only:
        w = {x.strip() for x in args.only.split(",")}
        codes = [c for c in codes if c in w]
    arme = [b.strip() for b in args.bedingungen.split(",")]

    plan, kopf = messplan(codes, arme, args.wiederholungen, args.seed)

    print(f"  Messplan: {kopf['laeufe_gesamt']} Laeufe, Seed {kopf['seed']}, "
          f"{kopf['wiederholungen']}x fuer {'/'.join(WIEDERHOLUNGSARME)}")
    print(f"  je Bedingung: {kopf['laeufe_je_bedingung']}")
    if args.trockenlauf:
        print("\n  TROCKENLAUF - es wird NICHTS ausgefuehrt.\n")
        for e in plan:
            print(f"    {e['position']:>4}. {e['fall']}/{e['bedingung']}/W{e['wiederholung']}")
        return 0

    ARCHIV.mkdir(parents=True, exist_ok=True)
    zeilen = []
    for eintrag in plan:
        fall, b, w = eintrag["fall"], eintrag["bedingung"], eintrag["wiederholung"]
        env = {**os.environ, **BEDINGUNGEN[b], "MEMORY_MODE": "off",
               "HUMAN_IN_THE_LOOP": "false",
               "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
        p = subprocess.run([sys.executable, __file__, "--kind", fall, b, args.katalog, str(w)],
                           env=env, capture_output=True, text=True, timeout=2400)
        z = next((l for l in p.stdout.splitlines() if l.startswith("###JSON###")), None)
        if not z:
            zeilen.append({k: None for k in MESSSCHEMA} | {
                "fall": fall, "bedingung": b, "abgebrochen": True,
                "abbruchgrund": f"Prozess exit {p.returncode}: {(p.stderr or '')[-300:]}",
                "ergebnis": "abgebrochen",
                # Auch ein abgebrochener Lauf muss seine Position und Wiederholung tragen -
                # sonst laesst sich die Reihenfolge hinterher nicht rekonstruieren.
                "lauf_metadaten": {"wiederholung": w, "position": eintrag["position"],
                                   "wiederholungen_gesamt": kopf["wiederholungen"]
                                   if b in WIEDERHOLUNGSARME else 1}})
            print(f"  [{eintrag['position']}/{len(plan)}] {fall}/{b}/W{w}: "
                  f"ABGEBROCHEN (exit {p.returncode})")
            continue
        e = json.loads(z[len("###JSON###"):])
        e["lauf_metadaten"]["position"] = eintrag["position"]
        zeilen.append(e)
        sch = e["schalter_effektiv"] or {}
        print(f"  [{eintrag['position']}/{len(plan)}] {fall}/{b}/W{w}: "
              f"{sch.get('SP_ARCHITECTURE_MODE')}+{sch.get('RULEBOOK_MODE')} "
              f"mem={sch.get('MEMORY_MODE')} | vorher={e['fehler_vorher']} "
              f"nachher={e['fehler_nachher']} reval={e['revalidation_ok']} "
              f"-> {e['ergebnis']} | {e['action']} {str(e['new_value'])[:14]}")

    stempel = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ziel = ARCHIV / f"abc-{args.katalog}-{stempel}.json"
    ziel.write_text(json.dumps({
        "zweck": f"AP-H4a BA-Runner, Katalog={args.katalog}",
        "hinweis": ("PILOT - kein Messergebnis" if args.katalog == "pilot"
                    else "HAUPTMESSUNG"),
        "messschema": list(MESSSCHEMA),
        # H4: Seed UND die tatsaechlich erzeugte Reihenfolge gehoeren in die Rohdaten.
        # Der Seed allein genuegt nicht - er belegt Reproduzierbarkeit nur, solange der
        # Planungscode unveraendert bleibt. Die ausgeschriebene Reihenfolge belegt, was
        # WIRKLICH gelaufen ist.
        "randomisierung": kopf,
        "zeilen": zeilen,
    }, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"\n  {len(zeilen)} Laeufe, davon abgebrochen: "
          f"{sum(1 for z in zeilen if z.get('abgebrochen'))}")
    print(f"  Rohdaten: {ziel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
