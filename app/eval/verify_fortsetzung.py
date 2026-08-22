"""
Deterministische Vorpruefung der H5-Fortsetzung ab Position 134 (BA-063).

ANLASS
------
Der H5-Lauf vom 22.08.2026 brach nach Position 155 ab: ab Position 134 fiel die Verbindung
zur Test-VM aus (22 technische Abbrueche, kein fachliches Ergebnis), danach starb der
Runner-Prozess an `os.replace` (WinError 5). Gueltig erhoben sind die Positionen **1..133**.

Fortgesetzt wird ab **134** - aus demselben eingefrorenen Plan, ohne Neurandomisierung.

WAS GEPRUEFT WIRD - jede Bedingung des Auftrags einzeln
-------------------------------------------------------
    1  Plan wird identisch reproduziert (Seed, Fallliste, Arme, Wiederholungen)
    2  Reproduzierter Plan == archivierte Reihenfolge in den Rohdaten
    3  Fortsetzungsplan ist EXAKT der Suffix 134..255
    4  Fortsetzungsplan enthaelt KEINE Position aus 1..133
    5  Uebernahme ist exakt 1..133, lueckenlos, ohne technischen Abbruch
    6  Uebernommene Zeilen sind INHALTLICH identisch mit der Quelle
    7  Der projizierte Gesamtdatensatz erfuellt die Abnahmekriterien:
       255 eindeutige Positionen | 1..255 vollstaendig | keine Duplikate
       | A/B/C je 85 | jeder der 17 Faelle je Arm 5x

Es wird **nichts ausgefuehrt** und **nichts geschrieben**. Reine Lesepruefung.

Aufruf:  .venv/Scripts/python.exe app/eval/verify_fortsetzung.py <uebernahmedatei> [ab-position]
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from graph_regression_harness import APP, Pruefung  # noqa: E402

import run_ba_abc_suite as R  # noqa: E402


def _tripel(e):
    return (e["fall"], e["bedingung"], e["wiederholung"])


def _tripel_zeile(z):
    return (z["fall"], z["bedingung"], z["lauf_metadaten"]["wiederholung"])


def pruefen(quelle: Path, ab: int) -> Pruefung:
    p = Pruefung(f"H5-Fortsetzung ab Position {ab}")

    # --- 1) Plan identisch reproduzieren -------------------------------------------------
    codes = [c["code"] for c, _ in R.lade_katalog("mess")]
    plan, kopf = R.messplan(codes, ["A", "B", "C"])
    p.gleich("voller Plan: 255 Positionen", 255, len(plan))
    p.gleich("Seed unveraendert", 20260821, kopf["seed"])
    p.gleich("Wiederholungen unveraendert", 5, kopf["wiederholungen"])
    p.gleich("je Bedingung 85", {"A": 85, "B": 85, "C": 85}, kopf["laeufe_je_bedingung"])

    # Zweiter Aufruf muss dasselbe liefern - sonst waere die Reihenfolge nicht reproduzierbar.
    plan2, _ = R.messplan(codes, ["A", "B", "C"])
    p.gleich("Plan ist deterministisch (zweiter Aufruf identisch)",
             [_tripel(e) for e in plan], [_tripel(e) for e in plan2])

    # --- 2) gegen die archivierte Reihenfolge ---------------------------------------------
    vorher = json.loads(quelle.read_text(encoding="utf-8"))
    p.gleich("archivierter Seed == Plan-Seed", kopf["seed"], vorher["randomisierung"]["seed"])
    p.gleich("archivierte Reihenfolge == reproduzierter Plan (alle 255)",
             kopf["reihenfolge"], vorher["randomisierung"]["reihenfolge"])

    # --- 3+4) Fortsetzungsplan ist exakt der Suffix ---------------------------------------
    rest = [e for e in plan if e["position"] >= ab]
    p.gleich(f"Fortsetzungsplan: {256 - ab} Positionen", 256 - ab, len(rest))
    p.gleich(f"Positionen exakt {ab}..255", list(range(ab, 256)),
             [e["position"] for e in rest])
    p.gleich("Fortsetzungsplan == Suffix des eingefrorenen Plans",
             [_tripel(e) for e in plan[ab - 1:]], [_tripel(e) for e in rest])
    p.wahr(f"KEINE Position aus 1..{ab - 1} enthalten",
           all(e["position"] >= ab for e in rest),
           f"kleinste Position: {min(e['position'] for e in rest)}")

    # --- 5) Uebernahme --------------------------------------------------------------------
    uebernahme = [z for z in vorher["zeilen"] if z["lauf_metadaten"]["position"] < ab]
    pos = [z["lauf_metadaten"]["position"] for z in uebernahme]
    p.gleich(f"Uebernahme: {ab - 1} Zeilen", ab - 1, len(uebernahme))
    p.gleich(f"Uebernahme lueckenlos 1..{ab - 1}", list(range(1, ab)), pos)
    p.gleich("keine doppelte Position in der Uebernahme", len(pos), len(set(pos)))
    p.gleich("Uebernahme enthaelt KEINEN technischen Abbruch", 0,
             sum(1 for z in uebernahme if z.get("abgebrochen")))
    p.gleich("Uebernahme traegt durchgehend 29 Felder", {29}, {len(z) for z in uebernahme})
    p.gleich("Uebernahme durchgehend MEMORY_MODE=off", {"off"},
             {z["schalter_effektiv"]["MEMORY_MODE"] for z in uebernahme})

    # Uebernahme muss dem Planpraefix entsprechen - nicht irgendeiner Teilmenge.
    p.gleich("Uebernahme == Praefix des eingefrorenen Plans",
             [_tripel(e) for e in plan[:ab - 1]], [_tripel_zeile(z) for z in uebernahme])

    # --- 6) inhaltlich unveraendert -------------------------------------------------------
    p.gleich("uebernommene Zeilen inhaltlich identisch mit der Quelle",
             vorher["zeilen"][:ab - 1], uebernahme)

    # --- 7) projizierter Gesamtdatensatz --------------------------------------------------
    projektion = [_tripel_zeile(z) for z in uebernahme] + [_tripel(e) for e in rest]
    ppos = pos + [e["position"] for e in rest]
    p.gleich("Projektion: 255 Positionen", 255, len(ppos))
    p.gleich("Projektion: Positionen 1..255 vollstaendig", list(range(1, 256)), ppos)
    p.gleich("Projektion: keine Duplikate", 255, len(set(ppos)))
    p.gleich("Projektion: A/B/C je 85", {"A": 85, "B": 85, "C": 85},
             dict(Counter(b for _, b, _ in projektion)))
    zellen = Counter((f, b) for f, b, _ in projektion)
    p.gleich("Projektion: 51 Fall-x-Bedingung-Zellen", 51, len(zellen))
    p.gleich("Projektion: jede Zelle genau 5 Wiederholungen", {5}, set(zellen.values()))
    p.gleich("Projektion: 17 Faelle", 17, len({f for f, _, _ in projektion}))
    p.gleich("Projektion == eingefrorener Plan, Position fuer Position",
             [_tripel(e) for e in plan], projektion)

    return p


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    quelle = Path(sys.argv[1])
    ab = int(sys.argv[2]) if len(sys.argv) > 2 else 134
    sys.path.insert(0, str(APP))
    from core.run_metadata import require_ba_env
    meta = require_ba_env("Fortsetzungspruefung (BA-063)")
    print(f"Umgebung: {meta['umgebung']['sys_prefix']}")
    print(f"Quelle  : {quelle}")
    p = pruefen(quelle, ab)
    p.drucken()
    return 0 if p.bestanden else 1


if __name__ == "__main__":
    sys.exit(main())
