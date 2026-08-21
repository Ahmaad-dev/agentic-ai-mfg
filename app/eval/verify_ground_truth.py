"""
Schritt 1 — Ground-Truth-Herkunft der kombinierten Faelle 04..10 rekonstruieren.

VERFAHREN, und warum es unabhaengig ist
---------------------------------------
Der Generator `generate-error-snapshots.ps1` deklariert je Fehler Before/After. Das ist eine
BEHAUPTUNG. Geprueft wird sie durch einen **Deep-Diff** zwischen dem sauberen Snapshot und dem
jeweiligen Fehler-Snapshot: die Menge der abweichenden JSON-Pfade muss exakt der Menge der
deklarierten Aenderungen entsprechen - nicht mehr, nicht weniger.

Damit haengt die Ground Truth an den DATEN, nicht am Skript und schon gar nicht am
untersuchten System. `pt4-combined-results.json` wird nicht angefasst.

Nichts wird geschrieben. Reine Analyse.
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pfadaufloesung import aufloesen  # noqa: E402
D = REPO / "data" / "snapshots" / "pt4-manipulated_snapshots" / "kombinierte-fehler-snapshots"
SAUBER = REPO / "data" / "snapshots" / "ok-snapshot.json"

#: Aus dem Generator gelesen (Zeilen 58-143), NICHT aus dem Gedaechtnis.
FEHLER = {
    "E01": ("validate_unique_ids", [("demands[1].demandId", "D100005_002", "D100005_001")]),
    "E02": ("validate_demand_article_ids", [("demands[0].articleId", "100005", "100005_NOT_FOUND")]),
    "E03": ("validate_density_values", [("articles[0].relDensityMin", 1.017, 0)]),
    "E04": ("validate_work_plan_ids", [("articles[1].workPlanId", "SP10        SP01", "WP_NOT_FOUND")]),
    "E05": ("validate_packaging_references", [("demands[0].packaging", "71125", "99999")]),
    "E06": ("validate_unique_ids", [("equipment[0].equipmentId", "4c350df3-325d-427c-a8bf-5309d3b71910", "")]),
    "E07": ("validate_equipment_predecessor_references", [("equipment[0].predecessors[0]", "MTO02", "EQUIPMENT_NOT_FOUND")]),
    "E08": ("validate_equipment_worker_qualification_compatibility", [("equipment[0].qualification", "Aromen-Abf", "QUALIFICATION_NOT_FOUND")]),
    "E09": ("validate_packaging_references", [("articles[0].standardPackaging", "71125", "99998")]),
    "E10": ("validate_packaging_equipment_compatibility_references", [("packagingEquipmentCompatibility[0].predecessors[0]", "ACO04", "COMPAT_EQUIPMENT_NOT_FOUND")]),
    "E11": ("validate_unique_ids", [("demands[0].demandId", "D100005_001", "")]),
    "E12": ("validate_start_end_operation_existence", [
        ("articles[0].workItemConfigs[HE01].rampUpTime", 120, 0),
        ("articles[0].workItemConfigs[HE01].netTimeFactor", 0.3, 0)]),
}

FAELLE = {
    "snapshot-error-01.json": ["E01"],
    "snapshot-error-02.json": ["E02"],
    "snapshot-error-03.json": ["E03"],
    "snapshot-error-04.json": ["E01", "E02"],
    "snapshot-error-05.json": ["E03", "E04"],
    "snapshot-error-06.json": ["E05", "E06"],
    "snapshot-error-07.json": ["E07", "E08"],
    "snapshot-error-08.json": ["E01", "E02", "E03"],
    "snapshot-error-09.json": ["E04", "E09", "E10"],
    "snapshot-error-10.json": ["E11", "E07", "E12"],
}


def diff(a, b, pfad=""):
    """Alle abweichenden Blattpfade zwischen zwei JSON-Baeumen."""
    raus = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in set(a) | set(b):
            raus += diff(a.get(k), b.get(k), f"{pfad}.{k}" if pfad else k)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            raus.append((pfad, f"<Liste {len(a)}>", f"<Liste {len(b)}>"))
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                raus += diff(x, y, f"{pfad}[{i}]")
    elif a != b:
        raus.append((pfad, a, b))
    return raus


def normpfad(p, snapshot=None):
    """
    Bringt einen deklarierten Pfad auf die Form der Diff-Pfade.

    KORRIGIERT beim Uebernehmen ins Repo (BA-060). Die erste Fassung ersetzte nur die
    Klammern - dabei blieb `workItemConfigs[HE01]` als `workItemConfigs.HE01` stehen, waehrend
    der Diff `workItemConfigs.3` liefert. Ergebnis: ein dauerhafter FEHLALARM
    ">>> NICHT VOLLSTAENDIG REKONSTRUIERBAR <<<" fuer snapshot-error-10, obwohl alles stimmt
    (in BA-058 am Snapshot geprueft: Index 3 traegt workItemKey='HE01').

    Ein Werkzeug, das dauerhaft falschen Alarm schlaegt, wird ignoriert - und dann uebersieht
    man den echten. Deshalb wird der Pfad jetzt ueber `pfadaufloesung` KANONISIERT, wenn ein
    Snapshot vorliegt; sie loest semantische Selektoren deterministisch auf Indizes auf.
    """
    if snapshot is not None:
        r = aufloesen(p, snapshot)
        if r["status"] == "eindeutig":
            p = r["kanonisch"]
    return p.replace("[", ".").replace("]", "").strip(".")


sauber = json.loads(SAUBER.read_text(encoding="utf-8"))
print(f"Sauberer Snapshot: {SAUBER.relative_to(REPO)}  "
      f"({SAUBER.stat().st_size} Byte)\n")
print(f"{'Datei':26} {'dekl.':>5} {'Diff':>5}  Befund")
print("-" * 78)

alle_ok = True
befunde = {}
for datei, codes in FAELLE.items():
    fehl = json.loads((D / datei).read_text(encoding="utf-8"))
    d = diff(sauber, fehl)
    deklariert = [(p, vor, nach) for c in codes for (p, vor, nach) in FEHLER[c][1]]
    gefunden = {normpfad(p) for p, _, _ in d}
    erwartet = {normpfad(p, sauber) for p, _, _ in deklariert}
    passt = gefunden == erwartet
    alle_ok &= passt
    befunde[datei] = {"codes": codes, "deklariert": deklariert, "diff": d, "passt": passt}
    status = "OK - Diff == Deklaration" if passt else "ABWEICHUNG"
    print(f"{datei:26} {len(deklariert):>5} {len(d):>5}  {status}")
    if not passt:
        print(f"    nur im Diff : {sorted(gefunden - erwartet)}")
        print(f"    nur deklar. : {sorted(erwartet - gefunden)}")

print()
print("=" * 78)
print("ALLE SIEBEN REKONSTRUIERBAR" if alle_ok else ">>> NICHT VOLLSTAENDIG REKONSTRUIERBAR <<<")
print("=" * 78)
print()
print("Kombinierte Faelle 04-10, Details:")
for datei in [f"snapshot-error-{i:02d}.json" for i in range(4, 11)]:
    b = befunde[datei]
    print(f"\n  {datei}  ({len(b['deklariert'])} erwartete Korrekturen, Codes {b['codes']})")
    for (p, vor, nach), (dp, dvor, dnach) in zip(
            sorted(b["deklariert"], key=lambda x: normpfad(x[0], sauber)),
            sorted(b["diff"], key=lambda x: normpfad(x[0]))):
        gleich = (str(dvor) == str(vor) and str(dnach) == str(nach))
        print(f"    {normpfad(p, sauber):52} {vor!r} -> {nach!r}  {'werte ok' if gleich else 'WERTE ABWEICHEND: ' + repr((dvor, dnach))}")
