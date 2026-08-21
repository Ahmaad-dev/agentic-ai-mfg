"""
H4a-Preflight + G5-Preflight. Rein statisch bzw. auf vorhandenen Pilotnachweisen.
Fuehrt NICHTS aus, das einen Messfall beruehrt.
"""
import ast
import io
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
RUNNER = REPO / "app" / "eval" / "run_ba_abc_suite.py"
K4 = REPO / "app" / "eval" / "kategorie4.py"
ARCHIV = REPO / "data" / "archive" / "ba-h4a" / "abc-pilot-20260820T215517Z.json"
AUSFALL = REPO / "data" / "archive" / "ba-h4a" / "abc-pilot-20260820T213134Z.json"

quelle = RUNNER.read_text(encoding="utf-8")
baum = ast.parse(quelle)
lauf = json.loads(ARCHIV.read_text(encoding="utf-8"))
ausfall = json.loads(AUSFALL.read_text(encoding="utf-8"))
zeilen = lauf["zeilen"]

ergebnisse = []


def pruef(nr, kriterium, ok, beleg):
    ergebnisse.append((nr, kriterium, bool(ok), str(beleg)[:150]))


# --- 1 Bedingungen ---------------------------------------------------------
bed = next((n.value for n in ast.walk(baum)
            if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "BEDINGUNGEN"),
           None)
bed_dict = ast.literal_eval(bed) if bed else {}
erwartet = {"A": {"SP_ARCHITECTURE_MODE": "monolith", "RULEBOOK_MODE": "monolith"},
            "B": {"SP_ARCHITECTURE_MODE": "monolith", "RULEBOOK_MODE": "cards"},
            "C": {"SP_ARCHITECTURE_MODE": "graph", "RULEBOOK_MODE": "cards"}}
for arm, soll in erwartet.items():
    ist = {k: v for k, v in (bed_dict.get(arm) or {}).items() if k in soll}
    pruef("1", f"Bedingung {arm} = {soll['SP_ARCHITECTURE_MODE']}+{soll['RULEBOOK_MODE']}",
          ist == soll, ist)
eff = [z["schalter_effektiv"] for z in zeilen]
pruef("1", "MEMORY_MODE=off in allen drei Armen (effektiv gemessen)",
      all(e["MEMORY_MODE"] == "off" for e in eff), [e["MEMORY_MODE"] for e in eff])
pruef("1", "HUMAN_IN_THE_LOOP=false in allen drei Armen",
      all(str(e.get("HUMAN_IN_THE_LOOP")).lower() == "false" for e in eff),
      [e.get("HUMAN_IN_THE_LOOP") for e in eff])

# --- 2 eigener Prozess je Arm ---------------------------------------------
pruef("2", "je Bedingung ein eigener Prozess (subprocess je Lauf)",
      "subprocess.run" in quelle and "--kind" in quelle,
      "subprocess.run + --kind im Runner")
pruef("2", "je Lauf ein FRISCHER Snapshot",
      len({z["snapshot_id"] for z in zeilen}) == len(zeilen),
      f"{len({z['snapshot_id'] for z in zeilen})} verschiedene IDs bei {len(zeilen)} Laeufen")

# --- 3 Schema --------------------------------------------------------------
schema = next((n.value for n in ast.walk(baum)
               if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "MESSSCHEMA"),
              None)
felder = [e.value for e in schema.elts]
pruef("3", "MESSSCHEMA hat 29 Felder", len(felder) == 29, len(felder))
pruef("3", "alle vier Kategorie-4-Felder im Schema",
      all(f in felder for f in ("errors_resolved", "errors_remaining",
                                "errors_new", "new_error_types")), "vorhanden")
pruef("3", "Schema in allen Zeilen identisch",
      len({tuple(sorted(z)) for z in zeilen}) == 1,
      f"{len({tuple(sorted(z)) for z in zeilen})} verschiedene Feldmengen")
pruef("3", "jede Zeile traegt 29 Felder",
      all(len(z) == 29 for z in zeilen), [len(z) for z in zeilen])

# --- 4 Kategorie 4 aus derselben Funktion ---------------------------------
pruef("4", "Runner importiert kategorie4() als einzige Quelle",
      "from kategorie4 import kategorie4 as _k4" in quelle, "Import belegt")
pruef("4", "kategorie4-Basis in ALLEN Armen identisch",
      len({z["provenienz"]["kategorie4_basis"] for z in zeilen}) == 1,
      {z["provenienz"]["kategorie4_basis"] for z in zeilen})
pruef("4", "A und B tragen Kategorie-4-Werte (nicht None)",
      all(z["errors_resolved"] is not None for z in zeilen if z["bedingung"] in ("A", "B")),
      {z["bedingung"]: z["errors_resolved"] for z in zeilen})
pruef("4", "kategorie4() importiert _fehler_identitaeten aus Knoten 7",
      "_fehler_identitaeten" in K4.read_text(encoding="utf-8"), "gemeinsame Definition")

# --- 5 Cross-Check nur Gegenprobe -----------------------------------------
c = next(z for z in zeilen if z["bedingung"] == "C")
cc = c["provenienz"]["kategorie4_cross_check"]
pruef("5", "C-Cross-Check durchgefuehrt und identisch",
      cc.get("durchgefuehrt") and cc.get("identisch"), cc.get("abweichungen"))
pruef("5", "A/B ohne Cross-Check (kein GraphState) - korrekt ausgewiesen",
      all(z["provenienz"]["kategorie4_cross_check"]["durchgefuehrt"] is False
          for z in zeilen if z["bedingung"] in ("A", "B")), "durchgefuehrt=false")
pruef("5", "bei Abweichung wird NICHT ueberschrieben, sondern gekennzeichnet",
      'messinkonsistenz_kategorie4|' in quelle, "Praefix statt Ueberschreiben")

# --- 6 Kette vollstaendig --------------------------------------------------
pruef("6", "Apply/Upload/Revalidation in allen Armen erfasst und True",
      all(z["applied_ok"] and z["uploaded"] and z["revalidation_ok"] for z in zeilen),
      [(z["bedingung"], z["applied_ok"], z["uploaded"], z["revalidation_ok"]) for z in zeilen])

# --- 7 keine falschen Nullen ----------------------------------------------
az = ausfall.get("zeilen") or []
pruef("7", "Ausfall-Lauf: fehler_nachher=None, NICHT 0",
      all(z["fehler_nachher"] is None for z in az), [z["fehler_nachher"] for z in az])
pruef("7", "Ausfall-Lauf: Kategorie 4 nicht 0",
      all(z["errors_new"] in (None, "nicht_bestimmbar") for z in az),
      [z["errors_new"] for z in az])
pruef("7", "kategorie4() liefert nicht_bestimmbar ohne Revalidierung",
      "NICHT_BESTIMMBAR for f in FELDER" in K4.read_text(encoding="utf-8"), "Codebeleg")

# --- 8 kein Audit-Report, keine Messfaelle --------------------------------
# AST statt Textsuche: der Name steht im Docstring ("wird NIE aufgerufen") und ein
# grep meldet ihn als Treffer. Beim ersten Preflight genau so passiert - dieselbe Lehre
# wie beim Exit-Code-Zaehler in BA-025.
_ruft_audit = [n.lineno for n in ast.walk(baum) if isinstance(n, ast.Call) and
               ((isinstance(n.func, ast.Name) and n.func.id == "generate_audit_report") or
                (isinstance(n.func, ast.Attribute) and n.func.attr == "generate_audit_report"))]
_importiert_audit = [n.lineno for n in ast.walk(baum)
                     if isinstance(n, (ast.Import, ast.ImportFrom))
                     and "audit" in ast.dump(n)]
pruef("8", "kein generate_audit_report()-AUFRUF und kein Import im Runner (AST)",
      not _ruft_audit and not _importiert_audit,
      f"Aufrufe={_ruft_audit or 'keine'} Imports={_importiert_audit or 'keine'}")
pruef("8", "Katalog 'mess' nicht ausgefuehrt - alle Laeufe sind Pilot",
      lauf.get("hinweis", "").startswith("PILOT"), lauf.get("hinweis"))
messfaelle = {"I01", "I02", "I03", "I04", "I05", "I06", "I07", "I08", "I09", "I10"}
pruef("8", "kein Messfall in den Rohdaten referenziert",
      not (messfaelle & {z["fall"] for z in zeilen}), {z["fall"] for z in zeilen})
pruef("8", "require_ba_env() hart im Runner",
      "require_ba_env" in quelle, "vorhanden")

# --- 9 H2/H4: Wiederholungen und Randomisierung (BA-055) ---
import importlib.util as _u
_sp = _u.spec_from_file_location("_runner", RUNNER)
_R = _u.module_from_spec(_sp)
import sys as _sys
_sys.path.insert(0, str(REPO / "app" / "eval"))
_sp.loader.exec_module(_R)

pruef("9", "Wiederholungen verbindlich = 5", _R.WIEDERHOLUNGEN == 5, _R.WIEDERHOLUNGEN)
pruef("9", "alle drei Arme werden wiederholt (BA-056)",
      _R.WIEDERHOLUNGSARME == ("A", "B", "C"), _R.WIEDERHOLUNGSARME)
pruef("9", "Random-Seed ist fest und dokumentiert",
      isinstance(_R.RANDOM_SEED, int), _R.RANDOM_SEED)
_synth = [f"S{i:02d}" for i in range(1, 18)]
_p1, _k1 = _R.messplan(_synth, ["A", "B", "C"])
_p2, _ = _R.messplan(_synth, ["A", "B", "C"])
_p3, _ = _R.messplan(_synth, ["A", "B", "C"], seed=_R.RANDOM_SEED + 1)
_key = lambda pl: [(e["fall"], e["bedingung"], e["wiederholung"]) for e in pl]
pruef("9", "Umfang der Hauptmessung = 255 Laeufe (85+85+85)",
      _k1["laeufe_je_bedingung"] == {"A": 85, "B": 85, "C": 85}, _k1["laeufe_je_bedingung"])
pruef("9", "reproduzierbar: gleicher Seed -> gleiche Reihenfolge",
      _key(_p1) == _key(_p2), "identisch")
pruef("9", "wirksam: anderer Seed -> andere Reihenfolge",
      _key(_p1) != _key(_p3), "unterschiedlich")
pruef("9", "Seed UND Reihenfolge gehen in die Messmetadaten",
      "seed" in _k1 and "reihenfolge" in _k1 and len(_k1["reihenfolge"]) == 255,
      sorted(_k1)[:6])
pruef("9", "Trockenlauf vorhanden (Plan ohne Ausfuehrung)",
      "--trockenlauf" in quelle, "Argument belegt")
pruef("9", "Wiederholung in lauf_metadaten, NICHT im Schema",
      "wiederholung" not in felder and 'lauf_metadaten"]["wiederholung"' in quelle,
      "Schema unveraendert bei 29")

gut = sum(1 for e in ergebnisse if e[2])
print(f"=== H4a-PREFLIGHT: {gut}/{len(ergebnisse)} ===\n")
for nr, k, ok, beleg in ergebnisse:
    print(f"  [{'ok  ' if ok else 'FAIL'}] ({nr}) {k}")
    if not ok:
        print(f"          Beleg: {beleg}")
print()
print("ALLE KRITERIEN ERFUELLT" if gut == len(ergebnisse) else ">>> FAIL VORHANDEN <<<")
