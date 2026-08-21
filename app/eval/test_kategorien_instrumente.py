"""
AP-G3b.4 — Validierung der vier Mess-/Fehlerkategorien gegen REALE und kontrolliert
konstruierte Pilot-Traces (BA-047).

Harte Regel 6 verlangt, das Instrument vor der Messung zu prüfen. Zwei von vier Kategorien
haben in BA-046 nacheinander auf das Instrument statt auf das System gezeigt — das ist kein
Zufall mehr, sondern ein Muster. Dieser Test schliesst es.

Je Kategorie werden **drei** Ausgänge geprüft, nicht zwei: Positivfall, Negativfall und der
jeweils bekannte **Confounder**. Ein Klassifikator, der seinen eigenen Confounder nicht
erkennt, ist kein Messinstrument.

DATENHERKUNFT — ausdrücklich unterschieden
-------------------------------------------
    REAL          aus einem archivierten Pilot-Trace, Snapshot-ID genannt
    KONTROLLIERT  gezielt konstruierter Eingang, weil kein realer Fall vorliegt

**Keiner der 17 Messfälle wird gelesen oder ausgeführt.** Es entsteht kein Messwert; das hier
prüft ausschliesslich, ob die Klassifikatoren tun, was sie behaupten.

Aufruf:  .venv/Scripts/python.exe app/eval/test_kategorien_instrumente.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from graph_regression_harness import APP, Pruefung  # noqa: E402
from kategorien import (JA, NEIN, UNKLAR, kategorie1_fachlich,  # noqa: E402
                        kategorie2_strukturell, kategorie3_regel, kategorie4_folgefehler)

SNAP = APP.parent / "data" / "snapshots"

#: Reale Pilot-Läufe. Alle aus AP-G3, keiner aus dem Messkatalog.
P01 = "c13a6303"      # Dichtefehler, Vorschlag 1.049, Ground Truth 1.063
P03 = "d0083bed"      # Dichtefehler, Vorschlag 1.049, Ground Truth 1.1
P04_VOR_FIX = "7a9a981d"   # der Lauf aus BA-036: D2 erzeugte real einen neuen Fehler


def _voll(praefix):
    return next(d for d in SNAP.iterdir() if d.name.startswith(praefix))


def _trace(praefix):
    d = _voll(praefix)
    it = max(int(p.name.split("-")[1]) for p in d.glob("iteration-*"))
    return json.loads((d / f"iteration-{it}" / "graph_state.json").read_text(encoding="utf-8"))


def _evidenz(praefix):
    """Die Statistiken, die dem Modell TATSAECHLICH vorlagen — aus dem Artefakt."""
    d = _voll(praefix)
    such = json.loads((d / "last_search_results.json").read_text(encoding="utf-8"))
    raus = {}
    for i, r in enumerate(such.get("results") or []):
        stats = ((r or {}).get("array_context") or {}).get("similar_items_stats") or {}
        for feld, s in stats.items():
            for kennzahl, wert in (s or {}).items():
                if kennzahl in ("min", "max", "median"):
                    raus[f"results[{i}].array_context.similar_items_stats.{feld}.{kennzahl}"] = wert
    return raus


# ===================================================================== Kategorie 1
def k1() -> Pruefung:
    p = Pruefung("Kategorie 1 — fachliche Halluzination")

    # NEGATIV (KONTROLLIERT): Wert trifft die Ground Truth.
    p.gleich("negativ: Wert == Ground Truth", NEIN,
             kategorie1_fachlich(1.063, 1.063)["befund"])

    # POSITIV (KONTROLLIERT): Wert weicht ab und steht nirgends in der Evidenz.
    r = kategorie1_fachlich(9.999, 1.063, evidenz_werte={"median": 1.049})
    p.gleich("positiv: abweichend und nicht in der Evidenz", JA, r["befund"])

    # CONFOUNDER (REAL, P01 und P03): abweichend, aber exakt der vorgelegte Median.
    for name, praefix, gt in (("P01", P01, 1.063), ("P03", P03, 1.1)):
        ev = _evidenz(praefix)
        r = kategorie1_fachlich(1.049, gt, evidenz_werte=ev)
        p.gleich(f"confounder REAL {name}: gestuetzter Wert zaehlt NICHT", NEIN, r["befund"])
        p.wahr(f"confounder REAL {name}: Begruendung nennt die Fundstelle",
               any("median" in q for q in r["belege"].get("gestuetzt_durch", [])),
               r["belege"].get("gestuetzt_durch"))

    # CONFOUNDER (KONTROLLIERT): Gedaechtnis-Override ist keine Modellleistung.
    p.gleich("confounder: value_source=memory", UNKLAR,
             kategorie1_fachlich(1.017, 1.063, value_source="memory")["befund"])
    # Ehrliches Nein ist kein Halluzinationsfall.
    p.gleich("kein Wert vorgeschlagen -> nicht bestimmbar", UNKLAR,
             kategorie1_fachlich(None, 1.063)["befund"])
    return p


# ===================================================================== Kategorie 2
def k2() -> Pruefung:
    p = Pruefung("Kategorie 2 — strukturelle Halluzination")

    p.gleich("negativ: erster Versuch gueltig", NEIN,
             kategorie2_strukturell(True, 0, [])["befund"])

    # POSITIV (KONTROLLIERT): Pflichtfeld des INNEREN Vorschlags fehlt.
    r = kategorie2_strukturell(True, 1, [
        "1 validation error for LLMCorrectionResponse\n"
        "correction_proposal.reasoning\n  Field required"])
    p.gleich("positiv: inneres Pflichtfeld fehlt", JA, r["befund"])

    # CONFOUNDER (REAL, P04-Lauf nach BA-043): nur Huellenfelder in der Meldung.
    z = _trace("da0cae38")
    tc = z.get("technical_check") or {}
    r = kategorie2_strukturell(tc.get("schema_valid"), tc.get("retries"), tc.get("errors"))
    p.gleich("confounder REAL da0cae38: Huellen-Mismatch zaehlt NICHT", NEIN, r["befund"])
    p.gleich("confounder REAL: alle fuenf Huellenfelder fehlen gleichzeitig", 5,
             len(r["belege"].get("huellenfelder", [])))

    # PROVENIENZ schlaegt die SIGNATUR (BA-048).
    # (a) K5-Response war gueltig -> der Schaden entstand danach -> Handoff.
    r = kategorie2_strukturell(True, 1, ["iteration\n  Field required"],
                               k5_response_valide=True)
    p.gleich("provenienz: K5-Response valide -> Handoff", NEIN, r["befund"])
    p.wahr("provenienz: Begruendung weist den Weg aus",
           r["begruendung"].startswith("PROVENIENZ"), r["begruendung"][:50])
    # (b) K5-Response war bereits invalide -> echte strukturelle Halluzination, AUCH wenn
    #     die Meldung wie ein Huellen-Mismatch aussieht. Genau diesen Fall haette die
    #     Signatur allein FALSCH klassifiziert - der Grund fuer die Praezisierung.
    r = kategorie2_strukturell(True, 1, ["5 validation errors for LLMCorrectionResponse\niteration\n  Field required\nsnapshot_id\n  Field required\noriginal_error\n  Field required\nerror_analyzed\n  Field required\ncorrection_proposal\n  Field required"],
                               k5_response_valide=False)
    p.gleich("provenienz: K5-Response invalide -> Modellfehler TROTZ Huellensignatur",
             JA, r["befund"])
    # (c) ohne Provenienzbeleg bleibt die Signatur - aber als DIAGNOSE gekennzeichnet.
    z2 = _trace("da0cae38"); tc2 = z2.get("technical_check") or {}
    r = kategorie2_strukturell(tc2.get("schema_valid"), tc2.get("retries"), tc2.get("errors"))
    p.wahr("ohne Provenienz: Ergebnis ist als SIGNATUR/diagnostisch ausgewiesen",
           r["begruendung"].startswith("SIGNATUR"), r["begruendung"][:50])

    # Abgrenzung: ein geglueckter Retry heilt den ersten Fehlversuch NICHT.
    p.gleich("geglueckter Retry auf innerem Feld bleibt Kategorie 2", JA,
             kategorie2_strukturell(True, 1,
                                    ["correction_proposal.action\n  Field required"])["befund"])
    return p


# ===================================================================== Kategorie 3
def k3() -> Pruefung:
    p = Pruefung("Kategorie 3 — Regelhalluzination")

    # NEGATIV (REAL, P01): Karten, die tatsaechlich geladen waren.
    z = _trace(P01)
    karten = ((z.get("matched_rules") or {}).get("cards_loaded")) or []
    p.wahr("REAL P01: Karten aus Knoten 4 vorhanden", bool(karten), karten)
    p.gleich("negativ REAL P01: benannte Karte war geladen", NEIN,
             kategorie3_regel(["density-values.md"], karten)["befund"])

    # POSITIV (KONTROLLIERT): eine Karte, die es nicht gab.
    r = kategorie3_regel(["dichte-sonderregel-2019.md"], karten)
    p.gleich("positiv: erfundene Karte", JA, r["befund"])

    # CONFOUNDER 1: keine Regel benannt -> keine Regelbehauptung.
    p.gleich("confounder: allgemeine Begruendung ohne Regelbezug", NEIN,
             kategorie3_regel([], karten)["befund"])

    # CONFOUNDER 2 (REAL, P01): geladene, aber fachlich UNPASSENDE Karte.
    # `negative-dichtewerte.md` ist fuer NEGATIVE Werte gedacht, der Fall hat 0 - trotzdem
    # keine Halluzination, denn sie wurde vorgelegt (BA-046).
    p.wahr("REAL P01: negative-dichtewerte.md war wirklich geladen",
           any("negative-dichtewerte" in k for k in karten), karten)
    p.gleich("confounder REAL: unpassende, aber geladene Karte zaehlt NICHT", NEIN,
             kategorie3_regel(["negative-dichtewerte.md"], karten)["befund"])

    # CONFOUNDER 3 (BA-048): die Regel steht INHALTLICH im uebergebenen Regeltext, ihre
    # Karte wurde aber nicht namentlich geladen. "Karte nicht geladen" allein genuegt NICHT.
    p.gleich("confounder: im Regeltext gestuetzt, Karte nicht benannt", NEIN,
             kategorie3_regel(["Dichtewerte muessen groesser 0 sein"], ["_core.md"],
                              regeltext="... Dichtewerte muessen groesser 0 sein ...")["befund"])

    p.gleich("ohne Knoten-4-Beleg nicht bestimmbar", UNKLAR,
             kategorie3_regel(["irgendwas.md"], None)["befund"])
    return p


# ===================================================================== Kategorie 4
def k4() -> Pruefung:
    p = Pruefung("Kategorie 4 — Folgefehlererzeugung")

    z = _trace(P04_VOR_FIX)
    ar = [t for t in z["trace"] if t["node"] == "apply_revalidate"]
    p.gleich("REAL 7a9a981d: drei Durchgaenge im Trace", 3, len(ar))

    def aus(i):
        o = ar[i]["output_digest"]
        return kategorie4_folgefehler(o["applied_ok"], o["uploaded"], o["revalidation_ok"],
                                      o["errors_after"], o["errors_new"],
                                      o.get("new_error_types"))

    # POSITIV (REAL): D2 erzeugte nachweislich einen neuen Fehler (BA-036).
    r = aus(1)
    p.gleich("positiv REAL D2: neuer Fehler erzeugt", JA, r["befund"])
    p.gleich("positiv REAL D2: errors_new", 1, r["belege"]["errors_new"])

    # NEGATIV (REAL): D1 behob einen Fehler, ohne einen neuen zu erzeugen.
    p.gleich("negativ REAL D1: keine neuen Fehler", NEIN, aus(0)["befund"])

    # CONFOUNDER (REAL): D3 scheiterte am Anwenden -> nicht bestimmbar, NICHT "nein".
    r = aus(2)
    p.gleich("confounder REAL D3: Apply gescheitert -> nicht bestimmbar", UNKLAR, r["befund"])

    # CONFOUNDER (KONTROLLIERT): Revalidierung nicht belegt, obwohl angewandt und hochgeladen.
    p.gleich("confounder: Revalidierung nicht belegt", UNKLAR,
             kategorie4_folgefehler(True, True, None, None, None)["befund"])
    # Abgrenzung: ein VERBLIEBENER Fehler ist kein Folgefehler.
    p.gleich("abgrenzung: verbliebener Fehler ist kein Folgefehler", NEIN,
             kategorie4_folgefehler(True, True, True, 2, 0)["befund"])
    return p


KATEGORIEN = {"K1": k1, "K2": k2, "K3": k3, "K4": k4}


def main():
    sys.path.insert(0, str(APP))
    from core.run_metadata import require_ba_env
    meta = require_ba_env("Kategorien-Instrumentenpruefung (AP-G3b.4)")
    print(f"Umgebung: {meta['umgebung']['sys_prefix']}")
    ergebnisse = []
    for name, fn in KATEGORIEN.items():
        pr = fn()
        pr.drucken()
        ergebnisse.append((name, pr.bestanden, pr.anzahl))
    print("\n=== Zusammenfassung ===")
    for n, ok, (gut, alle) in ergebnisse:
        print(f"  {n}: {'PASS' if ok else 'FAIL'}  {gut}/{alle}")
    return 0 if all(ok for _, ok, _ in ergebnisse) else 1


if __name__ == "__main__":
    sys.exit(main())
