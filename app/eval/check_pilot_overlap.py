"""
AP-G2 — Ueberschneidungsnachweis Pilotkatalog gegen Messkatalog.

Regel 5 verlangt, dass Pilot- und Messfaelle sich **nicht ueberschneiden - auch nicht in den
Entitaeten**. Diese Datei beweist das maschinell, statt es zu behaupten.

WARUM DIE ENTITAETEN UND NICHT NUR DIE DATEINAMEN
--------------------------------------------------
Zwei verschiedene Snapshots, die denselben `articleId` korrigieren, sind fuer die Frage
"habe ich auf die Testmenge hin optimiert?" **derselbe Fall**. Und das episodische Gedaechtnis
sucht objektgenau: eine im Piloten bestaetigte Korrektur laege beim Messlauf fuer dasselbe
Objekt vor (deshalb zusaetzlich `MEMORY_MODE=off`, Masterplan Kap. 7.2).

Verglichen werden deshalb:
  * Snapshot-Dateien und Fall-Codes,
  * `articleId`, `demandId`, `departmentId`, `workPlanId`, `packaging` und jeder weitere
    Bezeichner, der in den Ground-Truth-Aenderungen beider Kataloge vorkommt,
  * die JSON-Zielpfade der Korrekturen.

Aufruf:  python eval/check_pilot_overlap.py
Exit 0 = ueberschneidungsfrei, Exit 1 = Ueberschneidung gefunden.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

APP = Path(__file__).resolve().parent.parent
SNAP = APP.parent / "data" / "snapshots"
MESS_ISO = SNAP / "pt4-manipulated_snapshots" / "isolated-error-snapshots" / "expected-results.json"
MESS_KOMB = SNAP / "pt4-manipulated_snapshots" / "kombinierte-fehler-snapshots" / "ERROR-SNAPSHOTS.md"
PILOT = SNAP / "ba-pilot-snapshots" / "expected-results.json"
ARCHIV = APP.parent / "data" / "archive" / "ba-g2-ueberschneidung"

#: Bezeichner, die als Entitaet zaehlen. Bewusst breit - lieber ein Fehlalarm als eine
#: uebersehene Ueberschneidung.
ID_MUSTER = re.compile(
    r'"(articleId|demandId|departmentId|workPlanId|equipmentId|equipmentKey|packaging|'
    r'standardPackaging|defaultPackaging)"\s*:\s*"?([\w\-\.]+)')
PFAD_MUSTER = re.compile(r'(\w+)\[(?:\w+=)?([^\]]+)\]\.(\w+)')
DEMAND_MUSTER = re.compile(r'\b(D\d{6}_\d{3})\b')
ARTIKEL_MUSTER = re.compile(r'\b(1\d{5})\b')


def entitaeten_aus_text(text: str) -> set:
    e = set()
    for k, v in ID_MUSTER.findall(text):
        e.add(f"{k}={v}")
    for d in DEMAND_MUSTER.findall(text):
        e.add(f"demandId={d}")
    for a in ARTIKEL_MUSTER.findall(text):
        e.add(f"artikelnummer={a}")
    return e


def mess_entitaeten():
    """Aus BEIDEN Messkatalogen - der isolierte und der kombinierte."""
    e, quellen = set(), {}
    iso = json.loads(MESS_ISO.read_text(encoding="utf-8"))
    for c in iso["cases"]:
        roh = json.dumps(c.get("changes") or [], ensure_ascii=False) + str(c.get("correction", ""))
        gefunden = entitaeten_aus_text(roh)
        # Zielpfade zusaetzlich
        for ch in (c.get("changes") or []):
            for m in PFAD_MUSTER.finditer(str(ch.get("jsonPath"))):
                gefunden.add(f"pfad={m.group(1)}.{m.group(3)}")
        e |= gefunden
        quellen[c["code"]] = sorted(gefunden)
    if MESS_KOMB.exists():
        komb = entitaeten_aus_text(MESS_KOMB.read_text(encoding="utf-8"))
        e |= komb
        quellen["kombinierte-fehler-snapshots"] = sorted(komb)
    return e, quellen


def pilot_entitaeten():
    e, quellen = set(), {}
    spec = json.loads(PILOT.read_text(encoding="utf-8"))
    for c in spec["cases"]:
        roh = json.dumps(c.get("changes") or [], ensure_ascii=False)
        gefunden = entitaeten_aus_text(roh)
        gefunden.add(f"artikelnummer={c['ziel_artikel']}")
        for ch in (c.get("changes") or []):
            for m in PFAD_MUSTER.finditer(str(ch.get("jsonPath"))):
                gefunden.add(f"pfad={m.group(1)}.{m.group(3)}")
        e |= gefunden
        quellen[c["code"]] = sorted(gefunden)
    return e, quellen


def main():
    if not PILOT.exists():
        print(f"FEHLER: kein Pilotkatalog unter {PILOT} - zuerst build_pilot_catalog.py")
        return 1

    mess, mess_je_fall = mess_entitaeten()
    pilot, pilot_je_fall = pilot_entitaeten()

    # Zielpfade (z. B. articles.relDensityMin) sind ABSICHTLICH gleich - der Pilot soll
    # dieselben Fehlerklassen ueben. Verglichen wird auf ENTITAETEN, nicht auf Fehlerarten.
    mess_ent = {x for x in mess if not x.startswith("pfad=")}
    pilot_ent = {x for x in pilot if not x.startswith("pfad=")}
    schnitt = mess_ent & pilot_ent

    # Dateien und Codes
    mess_codes = set(mess_je_fall) - {"kombinierte-fehler-snapshots"}
    pilot_codes = set(pilot_je_fall)
    code_schnitt = mess_codes & pilot_codes

    print("=" * 88)
    print("AP-G2 - UEBERSCHNEIDUNGSNACHWEIS  Pilotkatalog gegen Messkatalog")
    print("=" * 88)
    print(f"  Messkatalog:   {len(mess_codes)} isolierte Faelle + kombinierter Katalog, "
          f"{len(mess_ent)} Entitaetsbezeichner")
    print(f"  Pilotkatalog:  {len(pilot_codes)} Faelle, {len(pilot_ent)} Entitaetsbezeichner")
    print()
    print(f"  Fall-Codes gemeinsam:   {sorted(code_schnitt) or 'keine'}")
    print(f"  ENTITAETEN gemeinsam:   {sorted(schnitt) or 'KEINE'}")
    print()
    gemeinsame_pfade = {x for x in mess if x.startswith("pfad=")} & {x for x in pilot if x.startswith("pfad=")}
    print(f"  (gemeinsame Zielpfad-ARTEN, absichtlich: {sorted(gemeinsame_pfade) or 'keine'})")
    print("   Dieselben Fehlerklassen zu ueben ist gewollt - dieselben OBJEKTE waeren der Verstoss.")
    print()
    print("  Entitaeten je Pilotfall:")
    for c in sorted(pilot_je_fall):
        kollision = set(pilot_je_fall[c]) & mess_ent
        print(f"    {c}: {[x for x in pilot_je_fall[c] if not x.startswith('pfad=')]}"
              + (f"   !! KOLLISION {sorted(kollision)}" if kollision else ""))

    sauber = not schnitt and not code_schnitt
    print()
    print(f"  ERGEBNIS: {'ueberschneidungsfrei' if sauber else 'UEBERSCHNEIDUNG GEFUNDEN'}")

    ARCHIV.mkdir(parents=True, exist_ok=True)
    ziel = ARCHIV / "ueberschneidungsnachweis.json"
    ziel.write_text(json.dumps({
        "zweck": "AP-G2 Ueberschneidungsnachweis Pilot- gegen Messkatalog (Regel 5)",
        "zeitstempel_utc": datetime.now(timezone.utc).isoformat(),
        "quellen": {"mess_isoliert": str(MESS_ISO.relative_to(APP.parent)),
                    "mess_kombiniert": str(MESS_KOMB.relative_to(APP.parent)),
                    "pilot": str(PILOT.relative_to(APP.parent))},
        "mess_entitaeten": sorted(mess_ent),
        "pilot_entitaeten": sorted(pilot_ent),
        "gemeinsame_entitaeten": sorted(schnitt),
        "gemeinsame_fall_codes": sorted(code_schnitt),
        "gemeinsame_zielpfad_arten_absichtlich": sorted(gemeinsame_pfade),
        "entitaeten_je_pilotfall": pilot_je_fall,
        "entitaeten_je_messfall": mess_je_fall,
        "ueberschneidungsfrei": sauber,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Rohartefakt: {ziel}")
    return 0 if sauber else 1


if __name__ == "__main__":
    sys.exit(main())
