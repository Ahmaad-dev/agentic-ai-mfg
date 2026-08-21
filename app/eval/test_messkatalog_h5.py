"""
Schritt-5-Validierung des finalen H5-Messkatalogs und -plans — BA-058.

ANLASS
------
Der erste H5-Trockenlauf ergab **150 statt 255 Läufe**: `KATALOGE["mess"]` zeigte nur auf den
isolierten Katalog (10 Fälle). Die 17 setzen sich anders zusammen — 10 isolierte plus 7
distinkte kombinierte (Masterplan Kap. 13.1). Der Fund kam **vor der ersten Datenerhebung**;
kein Messwert war betroffen.

Dieser Test hält den korrigierten Zustand fest. Er prüft **ausschliesslich Katalog und Plan** —
keine Pipeline, kein LLM, kein Server, kein Messlauf.

WAS GEPRÜFT WIRD
----------------
    Katalog      genau 17 Fälle: 10 isolierte + 7 kombinierte, keine Duplikate
    Ground Truth für ALLE 17 ladbar, mit Mehrfachkorrekturen wo vorhanden
    Plan         255 Positionen, A/B/C je 85, jeder Fall je Arm genau 5x
                 keine fehlenden oder doppelten (Fall, Bedingung, Wiederholung)-Tripel
    Seed         20260821

Aufruf:  .venv/Scripts/python.exe app/eval/test_messkatalog_h5.py
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from graph_regression_harness import APP, Pruefung  # noqa: E402

import run_ba_abc_suite as R  # noqa: E402

ISOLIERT = {f"I{i:02d}" for i in range(1, 11)}
KOMBINIERT = {f"K{i:02d}" for i in range(4, 11)}


def pruefen() -> Pruefung:
    p = Pruefung("H5-Messkatalog und Messplan")

    # ---------------------------------------------------------- Katalog
    eintraege = R.lade_katalog("mess")
    codes = [c["code"] for c, _ in eintraege]
    p.gleich("Katalog 'mess' umfasst 17 Fälle", 17, len(codes))
    p.gleich("Fall-Codes eindeutig (keine Duplikate)", 17, len(set(codes)))
    p.gleich("10 isolierte Fälle", ISOLIERT, set(codes) & ISOLIERT)
    p.gleich("7 distinkte kombinierte Fälle", KOMBINIERT, set(codes) & KOMBINIERT)
    p.gleich("keine unerwarteten Codes", set(), set(codes) - ISOLIERT - KOMBINIERT)

    # Die redundanten kombinierten Faelle 01-03 duerfen NICHT als eigene Faelle auftauchen.
    kombi_basis = next(b for c, b in eintraege if c["code"] in KOMBINIERT)
    spec = json.loads((kombi_basis / "expected-results.json").read_text(encoding="utf-8"))
    dateien = {c["file"] for c in spec["cases"]}
    p.gleich("snapshot-error-01..03 sind NICHT als Messfälle geführt", set(),
             dateien & {f"snapshot-error-{i:02d}.json" for i in (1, 2, 3)})
    p.wahr("Ausschluss von 01-03 ist im Katalog begründet",
           "ausgeschlossen" in spec and spec["ausgeschlossen"].get("grund"),
           str(spec.get("ausgeschlossen", {}).get("grund"))[:60])

    # ---------------------------------------------------------- Ground Truth
    ohne_gt, ohne_datei, korrekturen = [], [], {}
    for fall, basis in eintraege:
        ch = fall.get("changes")
        if not ch:
            ohne_gt.append(fall["code"])
        else:
            korrekturen[fall["code"]] = len(ch)
            for c in ch:
                if not all(k in c for k in ("jsonPath", "before", "after")):
                    ohne_gt.append(f"{fall['code']}:unvollstaendig")
        if not (basis / fall["file"]).exists():
            ohne_datei.append(fall["code"])
    p.gleich("alle 17 Fälle haben Ground Truth (changes)", [], ohne_gt)
    p.gleich("alle 17 Snapshot-Dateien vorhanden", [], ohne_datei)
    # 11 isoliert (I08 hat ZWEI - der HE01-Fall braucht zwei Zeitwerte) + 18 kombiniert.
    p.gleich("Korrekturen insgesamt über alle Fälle", 11 + 18, sum(korrekturen.values()))

    # Mehrfachkorrekturen duerfen NICHT still auf eine reduziert werden.
    mehrfach = {k: v for k, v in korrekturen.items() if v > 1}
    p.gleich("Fälle mit mehreren erwarteten Korrekturen", 8, len(mehrfach))
    # WICHTIG fuer AP-I: Mehrfach-Ground-Truth ist NICHT neu. Der isolierte Katalog fuehrt sie
    # seit jeher bei I08. Es braucht also keine neue Bewertungslogik - nur eine, die `changes`
    # als Liste behandelt, was das Format ohnehin vorgibt.
    p.gleich("I08 hatte schon vor BA-058 zwei Korrekturen", 2, korrekturen.get("I08"))
    p.gleich("Mehrfachfälle: I08 plus die sieben kombinierten",
             {"I08", "K04", "K05", "K06", "K07", "K08", "K09", "K10"}, set(mehrfach))
    p.gleich("K10 hat 4 Korrekturen bei 3 Fehlern (E12 = zwei Zeitwerte)",
             4, korrekturen.get("K10"))
    for c, _ in eintraege:
        if c["code"] in KOMBINIERT:
            p.gleich(f"{c['code']}: expectedErrors deckt sich mit expectedErrorCount",
                     c["expectedErrorCount"], len(c["expectedErrors"]))

    # ---------------------------------------------------------- Messplan
    plan, kopf = R.messplan(codes, ["A", "B", "C"])
    p.gleich("Plan: 255 Positionen", 255, len(plan))
    p.gleich("Plan: A/B/C je 85", {"A": 85, "B": 85, "C": 85}, kopf["laeufe_je_bedingung"])
    p.gleich("Plan: Seed", 20260821, kopf["seed"])
    p.wahr("Positionen lückenlos 1..255",
           [e["position"] for e in plan] == list(range(1, 256)), "1..255")

    tripel = Counter((e["fall"], e["bedingung"], e["wiederholung"]) for e in plan)
    p.gleich("keine doppelten (Fall, Bedingung, Wiederholung)-Tripel",
             [], [t for t, n in tripel.items() if n > 1])
    soll = {(f, b, w) for f in codes for b in ("A", "B", "C") for w in range(1, 6)}
    p.gleich("keine fehlenden Tripel", set(), soll - set(tripel))
    p.gleich("Tripel-Menge exakt 255", 255, len(soll))
    je_fall = Counter((e["fall"], e["bedingung"]) for e in plan)
    p.gleich("jeder Fall je Arm genau 5x", {5}, set(je_fall.values()))
    p.gleich("jeder Fall in allen drei Armen", 17 * 3, len(je_fall))

    # Die erzeugte Reihenfolge muss vollstaendig in den Rohdaten landen.
    p.gleich("Reihenfolge im Kopf: 255 Einträge", 255, len(kopf["reihenfolge"]))
    return p


def main():
    sys.path.insert(0, str(APP))
    from core.run_metadata import require_ba_env
    meta = require_ba_env("H5-Messkatalogpruefung (BA-058)")
    print(f"Umgebung: {meta['umgebung']['sys_prefix']}")
    p = pruefen()
    p.drucken()
    return 0 if p.bestanden else 1


if __name__ == "__main__":
    sys.exit(main())
