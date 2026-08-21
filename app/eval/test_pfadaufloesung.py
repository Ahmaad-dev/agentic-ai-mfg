"""
Pfadauflösung gegen ALLE 17 Ground-Truth-Fälle und 29 erwarteten Korrekturen — BA-059.

Prüft die Festlegung, die vor der Hauptmessung gilt:

> Zwei Zielpfade gelten fachlich als identisch, wenn sie im zugehörigen Snapshot
> deterministisch auf dasselbe JSON-Element bzw. Feld auflösen.

Zwei Richtungen, beide nötig:

    POSITIV   alle 29 GT-Pfade lösen eindeutig auf; verschiedene Notationen derselben
              Stelle werden als gleich erkannt
    NEGATIV   mehrdeutige oder unauflösbare Selektoren ergeben `nicht_bestimmbar` —
              und werden NICHT stillschweigend als Treffer gewertet

Ohne die zweite Richtung wäre der Test wertlos: ein Vergleicher, der alles gleich findet,
besteht jeden Positivtest.

**Kein LLM, keine Pipeline, kein Messlauf.** Es werden nur Snapshots gelesen.

Aufruf:  .venv/Scripts/python.exe app/eval/test_pfadaufloesung.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from graph_regression_harness import APP, Pruefung  # noqa: E402
from pfadaufloesung import (JA, NEIN, UNKLAR, aufloesen,  # noqa: E402
                            aufloesen_mit_referenz, pfade_gleich)

import run_ba_abc_suite as R  # noqa: E402

SAUBER = APP.parent / "data" / "snapshots" / "ok-snapshot.json"


def pruefen() -> Pruefung:
    p = Pruefung("Pfadauflösung — 17 Fälle, 29 Korrekturen")
    eintraege = R.lade_katalog("mess")

    # ---------------------------------------------------------- POSITIV
    referenz = json.loads(SAUBER.read_text(encoding="utf-8"))
    ungeloest, geloest, basen = [], {}, {}
    for fall, basis in eintraege:
        snap = json.loads((basis / fall["file"]).read_text(encoding="utf-8"))
        for c in fall["changes"]:
            r = aufloesen_mit_referenz(c["jsonPath"], snap, referenz)
            if r["status"] != "eindeutig":
                ungeloest.append((fall["code"], c["jsonPath"], r["grund"]))
            else:
                geloest[(fall["code"], c["jsonPath"])] = r["kanonisch"]
                basen[(fall["code"], c["jsonPath"])] = r["basis"]

    p.gleich("alle 29 GT-Pfade lösen EINDEUTIG auf", [], ungeloest)
    p.gleich("Anzahl aufgelöster Pfade", 29, len(geloest))

    # I07 und I09 nennen im Selektor einen Wert, den die Injektion zerstoert hat - sie
    # koennen NUR gegen die saubere Referenz aufloesen. Das muss sichtbar sein, nicht
    # stillschweigend passieren.
    ueber_referenz = {k[0] for k, v in basen.items() if v == "referenz"}
    p.gleich("genau I07 und I09 lösen über die Referenz auf", {"I07", "I09"}, ueber_referenz)
    p.gleich("alle übrigen über den Fehler-Snapshot selbst", 27,
             sum(1 for v in basen.values() if v == "snapshot"))

    # ---------------------------------------------------------- Kern der Sache
    # I08 (semantisch) und K10 (indexbasiert) beschreiben DIESELBE Stelle. Genau dafuer
    # existiert dieses Modul.
    sauber = json.loads(SAUBER.read_text(encoding="utf-8"))
    paare = [
        ("articles[articleId=100005].workItemConfigs[HE01].rampUpTime",
         "articles[0].workItemConfigs[3].rampUpTime"),
        ("articles[articleId=100005].workItemConfigs[HE01].netTimeFactor",
         "articles[0].workItemConfigs[3].netTimeFactor"),
        ("articles[articleId=100005].relDensityMin", "articles[0].relDensityMin"),
    ]
    for a, b in paare:
        r = pfade_gleich(a, b, sauber)
        p.gleich(f"gleich: {a.split('.')[-1]} (semantisch vs. indexbasiert)", JA, r["befund"])

    # Verschiedene Stellen muessen als VERSCHIEDEN erkannt werden.
    r = pfade_gleich("articles[0].relDensityMin", "articles[1].relDensityMin", sauber)
    p.gleich("verschieden: articles[0] vs. articles[1]", NEIN, r["befund"])
    r = pfade_gleich("articles[articleId=100005].relDensityMin",
                     "articles[articleId=100005].relDensityMax", sauber)
    p.gleich("verschieden: relDensityMin vs. relDensityMax", NEIN, r["befund"])

    # ---------------------------------------------------------- NEGATIV
    # Nichts davon darf still als Treffer durchgehen.
    for pfad, was in [
        ("articles[articleId=GIBTESNICHT].relDensityMin", "Selektor trifft nichts"),
        ("articles[99999].relDensityMin", "Index ausserhalb"),
        ("articles[0].gibtEsNichtFeld", "Feld existiert nicht"),
        ("articles[0]..relDensityMin", "Pfad syntaktisch kaputt"),
        ("articles[relDensityMin>1]", "unbekannter Selektortyp"),
    ]:
        r = aufloesen(pfad, sauber)
        p.gleich(f"nicht_bestimmbar: {was}", UNKLAR, r["status"])
        p.wahr(f"  Grund benannt bei {was}", bool(r["grund"]), r["grund"])

    # Mehrdeutigkeit: ein Label, das auf MEHRERE Elemente passt.
    kuenstlich = {"liste": [{"k": "X", "v": 1}, {"k": "X", "v": 2}]}
    r = aufloesen("liste[X].v", kuenstlich)
    p.gleich("nicht_bestimmbar: Selektor trifft ZWEI Elemente", UNKLAR, r["status"])
    p.wahr("  Grund nennt die Mehrdeutigkeit", "mehrdeutig" in (r["grund"] or ""), r["grund"])
    # ... und der Vergleich darf daraus kein 'gleich' machen.
    r = pfade_gleich("liste[X].v", "liste[0].v", kuenstlich)
    p.gleich("Vergleich mit mehrdeutiger Seite -> nicht_bestimmbar", UNKLAR, r["befund"])

    # Eindeutig, sobald das Label nur einmal vorkommt - die Gegenprobe zur Mehrdeutigkeit.
    eindeutig = {"liste": [{"k": "X", "v": 1}, {"k": "Y", "v": 2}]}
    r = pfade_gleich("liste[X].v", "liste[0].v", eindeutig)
    p.gleich("eindeutiges Label wird aufgelöst", JA, r["befund"])
    return p


def main():
    sys.path.insert(0, str(APP))
    from core.run_metadata import require_ba_env
    meta = require_ba_env("Pfadauflösung (BA-059)")
    print(f"Umgebung: {meta['umgebung']['sys_prefix']}")
    p = pruefen()
    p.drucken()
    return 0 if p.bestanden else 1


if __name__ == "__main__":
    sys.exit(main())
