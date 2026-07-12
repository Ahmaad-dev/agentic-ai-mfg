"""
AP-E — Testkatalog: Snapshots mit gezielt injizierten, bekannten Fehlern.

Warum das nötig ist: Über alle vorhandenen Snapshots hinweg existieren nur 3 erreichbare
Fehler, und zwei unserer vier Regelkarten (UNIQUE_IDS, DENSITY_VALUES) kommen darin gar nicht
vor. Mehr Pipeline-Läufe erzeugen kein neues Wissen — es fehlt Fehler-MATERIAL. Der Plan sieht
den Katalog in AP-E ohnehin vor.

Abgrenzung, die zählt:
    Der INPUT darf konstruiert sein — die GROUND TRUTH bleibt beim Menschen.
Wir injizieren Fehler in Snapshot-Kopien. Wir erfinden KEINE Review-Entscheidungen:
`memory_items` ist per Definition die menschliche Wahrheit (siehe Fall #7 im PROJECT_LOG —
ein fabriziertes `reject` hat dort einen korrekten Vorschlag dauerhaft unterdrückt).

Ablauf je Katalogeintrag:
    1. Snapshot auf der Smart-Planning-TESTINSTANZ anlegen (Crawler holt echte Plandaten)
    2. Snapshot herunterladen
    3. EINEN bekannten Fehler injizieren; der ursprüngliche Wert wird als Ground Truth
       in metadata.txt festgehalten
    4. hochladen
    5. **Validierungs-Job TRIGGERN**, dann erst die Meldungen holen

Schritt 5 ist nicht optional: `validate_snapshot.py` holt nur die Nachrichtenliste und stösst
den Job NICHT an — ohne Trigger meldet der Server "0 Fehler, Snapshot ist valide", obwohl der
Fehler nachweislich drinsteht. Das ist der `REVALIDATION_PRE_AP33D`-Fehlgrün aus dem
PROJECT_LOG; ein Katalog, der darauf hereinfällt, evaluiert leere Snapshots.

Umgebung: TESTINSTANZ (vm-t-...-test02..., cca-dev.com) — vom Nutzer ausdrücklich freigegeben.
Die Einträge sind an ihrem Namen "PT4-TEST-*" erkennbar.

Aufruf:  python eval/build_test_catalog.py            (alle offenen Einträge)
         python eval/build_test_catalog.py --only 02  (nur einen)
"""
import argparse
import json
import sys
from pathlib import Path

DEMO = Path(__file__).resolve().parent.parent
RUNTIME = DEMO / "smart-planning" / "runtime"
sys.path.insert(0, str(DEMO))
sys.path.insert(0, str(RUNTIME))

import create_snapshot as cs  # noqa: E402
import update_snapshot as us  # noqa: E402
from runtime_storage import get_storage  # noqa: E402
from routes.server_validation import trigger_server_validation  # noqa: E402


# --------------------------------------------------------------------------- #
# Die Injektionen. Jede gibt (beschreibung, pfad, ground_truth) zurueck und
# veraendert `data` in place.
# --------------------------------------------------------------------------- #
def inject_empty_demand_id(data):
    """UNIQUE_IDS — leere Pflicht-ID. Der vertikale Slice von PT4."""
    d = data["demands"][5]
    original = d["demandId"]
    d["demandId"] = ""
    return "Leere demandId", "demands[5].demandId", original


def inject_duplicate_demand_id(data):
    """UNIQUE_IDS — doppelte ID. Ground Truth: demands[7] hatte eine eigene, eindeutige ID."""
    original = data["demands"][7]["demandId"]
    data["demands"][7]["demandId"] = data["demands"][6]["demandId"]
    return "Doppelte demandId", "demands[7].demandId", original


def inject_invalid_article_ref(data):
    """DEMAND_ARTICLE_IDS — Referenz auf einen Artikel, den es nicht gibt (Typo)."""
    d = data["demands"][11]
    original = d["articleId"]
    d["articleId"] = f"{original}X"  # ein Zeichen zu viel -> Levenshtein-Distanz 1
    return "Ungueltige articleId-Referenz (Typo)", "demands[11].articleId", original


def inject_invalid_density(data):
    """DENSITY_VALUES — negativer Dichtewert (muss > 0 sein)."""
    for i, a in enumerate(data.get("articles", [])):
        if isinstance(a.get("relDensityMin"), (int, float)) and a["relDensityMin"] > 0:
            original = a["relDensityMin"]
            a["relDensityMin"] = -2
            return "Negative relDensityMin", f"articles[{i}].relDensityMin", original
    raise RuntimeError("Kein Artikel mit positiver relDensityMin gefunden")


CATALOG = [
    ("02", "duplicate demandId", inject_duplicate_demand_id),
    ("03", "invalid articleId ref", inject_invalid_article_ref),
    ("04", "invalid relDensityMin", inject_invalid_density),
]


def build(entry_id, title, inject):
    name = f"PT4-TEST-{entry_id} {title} (AP-E Katalog)"
    print(f"\n{'='*78}\n{name}\n{'='*78}")

    api = cs.SmartPlanningAPI()
    api.authenticate()
    info = api.create_snapshot(name=name)
    snapshot_id = info["id"]

    full = api.get_snapshot(snapshot_id)
    data = full.get("dataJson")
    if isinstance(data, str):
        data = json.loads(data)

    desc, path, ground_truth = inject(data)
    print(f">>> INJEKTION: {path}  {ground_truth!r} -> manipuliert  ({desc})")

    storage = get_storage()
    storage.save_json(f"{snapshot_id}/snapshot-data.json", data)
    storage.save_json(f"{snapshot_id}/original-data/snapshot-data.json", data)

    meta = {k: v for k, v in full.items() if k != "dataJson"}
    meta["snapshot_source"] = "AP-E test catalog (injected error)"
    meta["injected_error"] = {
        "catalog_id": entry_id,
        "description": desc,
        "path": path,
        "ground_truth": ground_truth,
    }
    storage.save_text(
        f"{snapshot_id}/metadata.txt",
        "# SNAPSHOT INFORMATIONS\n\n```json\n"
        + json.dumps(meta, ensure_ascii=False, indent=2)
        + "\n```\n",
    )

    upd = us.SmartPlanningAPI()
    upd.authenticate()
    upd.update_snapshot(
        snapshot_id=snapshot_id,
        name=name,
        comment=f"AP-E Testkatalog: {desc} (Ground Truth in metadata.txt)",
        data_json=json.dumps(data, ensure_ascii=False),
    )

    # PFLICHT: erst triggern, dann holen — sonst "0 Fehler" (falsches Gruen).
    trig = trigger_server_validation(snapshot_id)
    print(f">>> Validierungs-Job: {trig.get('status')} (job {str(trig.get('job_id'))[:8]}…)")

    import subprocess

    subprocess.run(
        [sys.executable, "validate_snapshot.py", "--snapshot-id", snapshot_id],
        cwd=RUNTIME, capture_output=True, text=True, timeout=300,
    )
    messages = storage.load_json(f"{snapshot_id}/snapshot-validation.json") or []
    errors = [m for m in messages if m.get("level") == "ERROR"]
    print(f">>> Validator meldet {len(errors)} ERROR(s):")
    for m in errors:
        print(f"      {m['message'][:92]}")

    return {"catalog_id": entry_id, "snapshot_id": snapshot_id, "name": name,
            "injected": desc, "path": path, "ground_truth": ground_truth,
            "errors": [m["message"] for m in errors]}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None, help="nur diesen Katalog-Eintrag bauen (z.B. 02)")
    args = ap.parse_args()

    built = []
    for entry_id, title, inject in CATALOG:
        if args.only and entry_id != args.only:
            continue
        try:
            built.append(build(entry_id, title, inject))
        except Exception as exc:  # ein fehlgeschlagener Eintrag darf den Rest nicht kippen
            print(f"!!! Eintrag {entry_id} fehlgeschlagen: {exc}")

    print(f"\n{'='*78}\nKATALOG\n{'='*78}")
    for b in built:
        print(f"  {b['catalog_id']}  {b['snapshot_id']}  {b['injected']:34} "
              f"{len(b['errors'])} ERROR(s)  Ground Truth: {b['ground_truth']!r}")
