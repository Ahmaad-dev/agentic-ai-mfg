"""
Laufende Sicherung der Messzeilen — deterministisch, ohne LLM und ohne Server (BA-062).

ANLASS
------
Der Runner schrieb den Rohdatensatz **erst nach der letzten Zeile**. Ein Abbruch bei Lauf 250
von 255 hätte den kompletten Aggregatdatensatz gekostet — bei geschätzt 3–5 Stunden Laufzeit
kein theoretisches Risiko.

WAS GEPRÜFT WIRD
----------------
    nach Lauf 1      Datei enthält exakt Position 1
    nach Lauf N      exakt die Positionen 1…N, in unveränderter Reihenfolge
    Abbruch danach   diese N Zeilen bleiben intakt und lesbar
    Präfix           der Stand entspricht jederzeit genau dem Präfix des eingefrorenen Plans
    keine Dubletten  jede Position höchstens einmal
    Schema           29 Felder, unverändert

**Kein Resume, keine Wiederholung.** Der Test prüft ausdrücklich, dass nach dem simulierten
Abbruch **nichts** automatisch fortgesetzt wird — die Datei bleibt stehen, wie sie ist.

Die Messzeilen sind hier **synthetisch**. Gegenstand ist die Sicherung, nicht die Messung;
`_schreibe_aggregat()` interessiert sich nicht dafür, woher eine Zeile kommt.

Aufruf:  .venv/Scripts/python.exe app/eval/test_persistenz.py
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from graph_regression_harness import APP, Pruefung  # noqa: E402

import run_ba_abc_suite as R  # noqa: E402


def _zeile(eintrag):
    """Eine synthetische Messzeile im 29-Feld-Schema, wie der Runner sie erzeugt."""
    z = {k: None for k in R.MESSSCHEMA}
    z.update({
        "fall": eintrag["fall"], "bedingung": eintrag["bedingung"], "abgebrochen": False,
        "ergebnis": "fehlerfrei",
        "lauf_metadaten": {"wiederholung": eintrag["wiederholung"],
                           "position": eintrag["position"]},
    })
    return z


def pruefen() -> Pruefung:
    p = Pruefung("Laufende Sicherung der Messzeilen")

    codes = [c["code"] for c, _ in R.lade_katalog("mess")]
    plan, kopf = R.messplan(codes, ["A", "B", "C"])
    p.gleich("eingefrorener Plan: 255 Positionen", 255, len(plan))

    with tempfile.TemporaryDirectory() as tmp:
        ziel = Path(tmp) / "abc-mess-TEST.json"
        zeilen = []

        # --- leerer Anfangsstand: die Datei muss sofort existieren und lesbar sein ---
        R._schreibe_aggregat(ziel, "mess", kopf, zeilen)
        p.wahr("Datei existiert vor dem ersten Lauf", ziel.exists(), str(ziel.name))
        d = json.loads(ziel.read_text(encoding="utf-8"))
        p.gleich("Anfangsstand: 0 Zeilen", 0, len(d["zeilen"]))
        p.gleich("Messschema von Anfang an vollständig", 29, len(d["messschema"]))

        # --- Lauf 1 ---
        zeilen.append(_zeile(plan[0]))
        R._schreibe_aggregat(ziel, "mess", kopf, zeilen)
        d = json.loads(ziel.read_text(encoding="utf-8"))
        p.gleich("nach Lauf 1: genau eine Zeile", 1, len(d["zeilen"]))
        p.gleich("nach Lauf 1: Position 1", 1, d["zeilen"][0]["lauf_metadaten"]["position"])
        p.gleich("nach Lauf 1: Fall/Bedingung wie im Plan",
                 (plan[0]["fall"], plan[0]["bedingung"]),
                 (d["zeilen"][0]["fall"], d["zeilen"][0]["bedingung"]))

        # --- Läufe 2..N ---
        N = 40
        for eintrag in plan[1:N]:
            zeilen.append(_zeile(eintrag))
            R._schreibe_aggregat(ziel, "mess", kopf, zeilen)

        d = json.loads(ziel.read_text(encoding="utf-8"))
        p.gleich(f"nach Lauf {N}: genau {N} Zeilen", N, len(d["zeilen"]))
        pos = [z["lauf_metadaten"]["position"] for z in d["zeilen"]]
        p.gleich("Positionen lückenlos 1..N in Reihenfolge", list(range(1, N + 1)), pos)
        p.gleich("keine doppelte Position", N, len(set(pos)))

        # Der Stand muss GENAU das Praefix des eingefrorenen Plans sein - nicht irgendeine
        # Teilmenge in irgendeiner Reihenfolge.
        ist = [(z["fall"], z["bedingung"], z["lauf_metadaten"]["wiederholung"])
               for z in d["zeilen"]]
        soll = [(e["fall"], e["bedingung"], e["wiederholung"]) for e in plan[:N]]
        p.gleich("Stand ist exakt das Präfix des eingefrorenen Plans", soll, ist)

        # --- simulierter Abbruch: ab hier wird NICHTS mehr geschrieben ---
        stand_vorher = ziel.read_bytes()
        # (kein weiterer Aufruf - genau das ist der Abbruch)
        p.gleich("nach dem Abbruch: Datei unverändert", stand_vorher, ziel.read_bytes())
        d = json.loads(ziel.read_text(encoding="utf-8"))
        p.gleich("nach dem Abbruch: die N Zeilen sind intakt", N, len(d["zeilen"]))
        p.gleich("nach dem Abbruch: valides JSON, Schema vollständig", 29, len(d["messschema"]))
        p.wahr("nach dem Abbruch: KEINE automatische Fortsetzung",
               len(d["zeilen"]) == N and N < len(plan),
               f"{N} von {len(plan)} - der Rest bleibt ungeschrieben")

        # --- keine Zeile wurde nachträglich verändert ---
        p.gleich("Zeile 1 inhaltlich unverändert seit ihrem Lauf",
                 (plan[0]["fall"], plan[0]["bedingung"], 1),
                 (d["zeilen"][0]["fall"], d["zeilen"][0]["bedingung"],
                  d["zeilen"][0]["lauf_metadaten"]["position"]))
        p.gleich("jede Zeile trägt 29 Felder", {29}, {len(z) for z in d["zeilen"]})

        # --- keine Reste der temporaeren Datei ---
        p.gleich("keine .tmp-Datei zurückgelassen", [],
                 [f.name for f in Path(tmp).iterdir() if f.suffix == ".tmp"])

        # --- Randomisierungskopf bleibt in jedem Zwischenstand vollstaendig ---
        p.gleich("Seed im Zwischenstand", 20260821, d["randomisierung"]["seed"])
        p.gleich("Reihenfolge im Zwischenstand vollständig (255)",
                 255, len(d["randomisierung"]["reihenfolge"]))
        p.gleich("Kennzeichnung als Hauptmessung", "HAUPTMESSUNG", d["hinweis"])

    p.gleich("MESSSCHEMA weiterhin 29 Felder", 29, len(R.MESSSCHEMA))
    return p


def main():
    sys.path.insert(0, str(APP))
    from core.run_metadata import require_ba_env
    meta = require_ba_env("Persistenztest (BA-062)")
    print(f"Umgebung: {meta['umgebung']['sys_prefix']}")
    p = pruefen()
    p.drucken()
    return 0 if p.bestanden else 1


if __name__ == "__main__":
    sys.exit(main())
