"""
Wiederholungen (H2) und Randomisierung (H4) des Messplans — BA-055.

WAS HIER GEPRÜFT WIRD
----------------------
`messplan()` erzeugt die Reihenfolge der Tripel (Fall × Bedingung × Wiederholung) für die
Hauptmessung. Der Plan entsteht **vor** dem ersten Lauf und wird samt Seed in die Rohdaten
geschrieben. Er ist damit selbst ein Messinstrument und muss geprüft werden wie eines.

Zwei Eigenschaften tragen alles:

    REPRODUZIERBAR   gleicher Seed + gleiche Eingabe -> exakt gleiche Reihenfolge
    WIRKSAM          anderer Seed -> andere Reihenfolge

Die zweite ist die leicht zu vergessende: eine „Randomisierung", die immer dasselbe liefert,
ist keine — und sie fiele nicht auf, solange nur die erste geprüft wird.

**Es wird ausschliesslich mit synthetischen Fall-IDs gerechnet.** Keiner der 17 Messfälle wird
geladen, gelesen oder ausgeführt; `messplan()` bekommt eine Liste von Strings und interessiert
sich nicht dafür, woher sie kommt. Ein einziger Fall benutzt echte **Pilot**-IDs.

Aufruf:  .venv/Scripts/python.exe app/eval/test_messplan.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from graph_regression_harness import APP, Pruefung  # noqa: E402

import run_ba_abc_suite as R  # noqa: E402

#: Synthetische IDs. Bewusst NICHT die Messfall-Kennungen - der Plan darf nie ein Anlass
#: sein, den Messkatalog zu oeffnen.
SYNTH = [f"S{i:02d}" for i in range(1, 18)]      # 17 Stueck, wie die Hauptmessung
PILOT = ["P01", "P02", "P03"]


def pruefen() -> Pruefung:
    p = Pruefung("Messplan — Wiederholungen (H2) und Randomisierung (H4)")

    # --- Festlegungen, die vor der Messung feststehen muessen ---
    p.gleich("WIEDERHOLUNGEN verbindlich auf 5", 5, R.WIEDERHOLUNGEN)
    p.gleich("Wiederholungsarme sind A, B und C (BA-056)",
             ("A", "B", "C"), R.WIEDERHOLUNGSARME)
    p.wahr("RANDOM_SEED ist eine feste Zahl", isinstance(R.RANDOM_SEED, int), R.RANDOM_SEED)

    # --- Umfang: alle drei Arme je 5 (BA-056) ---
    plan, kopf = R.messplan(SYNTH, ["A", "B", "C"])
    p.gleich("Gesamtzahl Laeufe (17 Faelle x 3 Bedingungen x 5)", 17 * 3 * 5, len(plan))
    p.gleich("Laeufe je Bedingung", {"A": 85, "B": 85, "C": 85}, kopf["laeufe_je_bedingung"])
    p.gleich("A: jeder Fall genau 5x",
             {5}, {sum(1 for e in plan if e["fall"] == f and e["bedingung"] == "A")
                   for f in SYNTH})
    # BA-056: B wird jetzt EBENFALLS wiederholt. Ohne das laesst sich ein
    # Stabilitaetsunterschied A -> C nicht zerlegen (Kartenform vs. Orchestrierung).
    p.gleich("B: jeder Fall genau 5x (seit BA-056, vorher 1x)",
             {5}, {sum(1 for e in plan if e["fall"] == f and e["bedingung"] == "B")
                   for f in SYNTH})
    p.gleich("alle drei Arme gleich oft - kein Arm bevorzugt",
             1, len({sum(1 for e in plan if e["bedingung"] == b) for b in ("A", "B", "C")}))
    p.gleich("Wiederholungsnummern lueckenlos 1..5",
             {1, 2, 3, 4, 5}, {e["wiederholung"] for e in plan if e["bedingung"] == "C"})

    # --- Reproduzierbarkeit ---
    a, _ = R.messplan(SYNTH, ["A", "B", "C"], seed=R.RANDOM_SEED)
    b, _ = R.messplan(SYNTH, ["A", "B", "C"], seed=R.RANDOM_SEED)
    schluessel = lambda pl: [(e["fall"], e["bedingung"], e["wiederholung"]) for e in pl]
    # Nur die Laenge und ein Auszug in die Ausgabe - eine 255-elementige Liste im
    # Testprotokoll macht den Bericht unlesbar (vermerkt in BA-055).
    p.gleich("gleicher Seed -> identische Reihenfolge",
             (len(a), schluessel(a)[:5]), (len(b), schluessel(b)[:5]))
    p.wahr("gleicher Seed -> identisch auf ALLEN Positionen",
           schluessel(a) == schluessel(b), f"{len(a)} Positionen geprueft")

    # --- Wirksamkeit: ein anderer Seed MUSS eine andere Reihenfolge geben ---
    c, _ = R.messplan(SYNTH, ["A", "B", "C"], seed=R.RANDOM_SEED + 1)
    p.wahr("anderer Seed -> andere Reihenfolge (die Mischung wirkt wirklich)",
           schluessel(a) != schluessel(c),
           f"{sum(1 for x, y in zip(schluessel(a), schluessel(c)) if x != y)} von "
           f"{len(a)} Positionen unterschiedlich")

    # --- Die Mischung muss die Bedingungen wirklich verschraenken ---
    # Ohne Randomisierung liefe erst alles A, dann alles B, dann alles C. Dann fiele jede
    # zeitliche Drift mit der Bedingung zusammen. Ein einfacher, aussagekraeftiger Test:
    # in der ersten Haelfte des Plans muessen alle drei Arme vorkommen.
    haelfte = {e["bedingung"] for e in a[: len(a) // 2]}
    p.gleich("alle drei Bedingungen bereits in der ersten Planhaelfte",
             {"A", "B", "C"}, haelfte)
    wechsel = sum(1 for x, y in zip(a, a[1:]) if x["bedingung"] != y["bedingung"])
    p.wahr("haeufige Bedingungswechsel (keine Bloecke)", wechsel > len(a) // 3,
           f"{wechsel} Wechsel bei {len(a)} Laeufen")

    # --- Positionen ---
    p.wahr("Positionen lueckenlos 1..n",
           [e["position"] for e in a] == list(range(1, len(a) + 1)), f"1..{len(a)}")

    # --- Kopf: was in die Rohdaten geht ---
    for feld in ("seed", "wiederholungen", "wiederholungsarme", "laeufe_gesamt",
                 "laeufe_je_bedingung", "reihenfolge"):
        p.wahr(f"Messmetadaten enthalten {feld!r}", feld in kopf, sorted(kopf)[:7])
    p.gleich("Reihenfolge im Kopf deckt sich mit dem Plan (Laenge und Inhalt)",
             (len(a), [f"{e['fall']}/{e['bedingung']}/W{e['wiederholung']}" for e in a][:5]),
             (len(R.messplan(SYNTH, ["A", "B", "C"])[1]["reihenfolge"]),
              R.messplan(SYNTH, ["A", "B", "C"])[1]["reihenfolge"][:5]))
    p.wahr("Kopf warnt davor, Wiederholungen als Faelle zu zaehlen",
           "KEINE zusaetzlichen Faelle" in kopf["hinweis"], kopf["hinweis"][:60])

    # --- Mit echten Pilot-IDs (keine Messfaelle) ---
    pp, pk = R.messplan(PILOT, ["A", "B", "C"])
    p.gleich("Pilot: 3 Faelle -> 45 Laeufe", 45, pk["laeufe_gesamt"])
    p.gleich("Pilot: Faelle unveraendert", set(PILOT), {e["fall"] for e in pp})

    # --- Das Schema darf sich NICHT geaendert haben ---
    p.gleich("MESSSCHEMA weiterhin 29 Felder", 29, len(R.MESSSCHEMA))
    p.wahr("kein neues Wiederholungs-Schemafeld (gehoert in lauf_metadaten)",
           "wiederholung" not in R.MESSSCHEMA, "Schema unveraendert")
    return p


def main():
    sys.path.insert(0, str(APP))
    from core.run_metadata import require_ba_env
    meta = require_ba_env("Messplan-Pruefung (BA-055)")
    print(f"Umgebung: {meta['umgebung']['sys_prefix']}")
    p = pruefen()
    p.drucken()
    return 0 if p.bestanden else 1


if __name__ == "__main__":
    sys.exit(main())
