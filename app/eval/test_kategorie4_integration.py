"""
Integrationsnachweis für die Kategorie-4-Messlogik (BA-049, AP-G3b).

WARUM DIESER TEST STATT NEUER PILOTFÄLLE
-----------------------------------------
Kategorie 4 (Folgefehlererzeugung) ist real beobachtet — aber ausschliesslich in
`7a9a981d…` D2 (BA-036), einem Lauf von **vor** dem K5→K6-Fix. Dessen Artefakte sind als
Debugging-Material eingestuft (`WARNUNG-BESCHAEDIGTE-ARTEFAKTE.md`).

**Alle Post-Fix-Pilottraces wurden geprüft**: `b51c5b1c…` (2 Durchgänge) und `7f447c4e…`
(1 Durchgang) — je `errors_new = 0`, `new_error_types = []`. **Kein Post-Fix-Positivfall.**

Ein Folgefehler lässt sich nicht bestellen: er entsteht, wenn das Modell zufällig eine
Korrektur wählt, die eine neue Kollision erzeugt. Neue LLM-Pilotfälle zu würfeln, bis einer
eintritt, wäre teuer und methodisch beliebig — und es würde die **Messlogik** trotzdem nicht
prüfen, sondern nur ihr Auslösen abwarten.

Stattdessen wird hier die **Kette selbst** nachgewiesen, mit dem echten Knoten 7:

    Serverantwort nach der Korrektur
      -> `_fehler_identitaeten()`      (stabile Fehleridentitäten, echte Funktion)
      -> `errors_resolved / errors_remaining / errors_new / new_error_types`
      -> `kategorie4_folgefehler()`    (der Klassifikator)

Gestubbt sind nur die Aussenkanten (Apply, Upload, Trigger, Storage) — die gesamte
Auswertelogik ist Produktionscode. Kein LLM, kein Server, keiner der 17 Messfälle.

DIE VIER FÄLLE, DIE KATEGORIE 4 UNTERSCHEIDEN MUSS
---------------------------------------------------
    A behoben, nichts neu        -> NEIN   (die Korrektur hat gewirkt)
    A behoben, B NEU entstanden  -> JA     (der Folgefehler — die zu messende Kategorie)
    nichts behoben, nichts neu   -> NEIN   (wirkungslos, aber kein Folgefehler)
    Verarbeitung unvollständig   -> NICHT_BESTIMMBAR

Der dritte Fall ist der wichtige: `1 -> 1` kann „nichts passiert" heissen **oder**
„A behoben, B neu". Ohne stabile Fehleridentitäten wäre das nicht unterscheidbar — genau
deshalb zählt `errors_new` und nicht die blosse Fehlerzahl.

Aufruf:  .venv/Scripts/python.exe app/eval/test_kategorie4_integration.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from graph_regression_harness import (APP, Pruefung, Zaehler, basis_state,  # noqa: E402
                                      knoten_laden, pfade_setzen, stub_modul, voll_huelle)
from kategorien import JA, NEIN, UNKLAR, kategorie4_folgefehler  # noqa: E402

pfade_setzen()


def _meldung(tag: str, text: str) -> dict:
    return {"level": "ERROR", "message": f"[{tag}] {text}"}


def _lauf(vorher: list, nachher: list) -> dict:
    """
    Führt den ECHTEN Knoten 7 mit kontrollierten Server-Antworten aus.
    `vorher` und `nachher` sind die Validierungsmeldungen vor bzw. nach der Korrektur.
    """
    zustaende = {"n": 0}

    class S:
        def load_json(self, pfad):
            if pfad.endswith("snapshot-validation.json"):
                zustaende["n"] += 1
                return vorher if zustaende["n"] == 1 else nachher
            return None

        def save_json(self, *a, **kw):
            return None

    vorschlag = {"action": "update_field", "target_path": "demands[0].demandId",
                 "new_value": "X", "reasoning": "Testfall"}
    huelle = voll_huelle(dict(vorschlag))
    # Der innere Vorschlag wird AUS DER HUELLE abgeleitet, nicht daneben gebaut:
    # `voll_huelle()` ergaenzt Pflichtfelder (z. B. `status`), und Knoten 7 vergleicht
    # State gegen Platte. Zwei getrennt gebaute Objekte weichen ab, und der Guard aus
    # BA-043 blockiert zu Recht - beim ersten Versuch genau so passiert.
    innen = dict(huelle["correction_proposal"])

    stub_modul("apply_correction",
               load_correction_proposal=Zaehler("laden", rueckgabe=huelle),
               run_apply=Zaehler("apply", rueckgabe={"applied_ok": True, "error": None,
                                                     "iteration_number": 1,
                                                     "proposal": huelle}))
    stub_modul("update_snapshot", run_upload=Zaehler("upload", rueckgabe={
        "uploaded": True, "response": None, "error": None}))
    stub_modul("validate_snapshot", validate_snapshot=Zaehler("validate", rueckgabe=None))
    routes = stub_modul("routes")
    routes.server_validation = stub_modul(
        "routes.server_validation",
        trigger_server_validation=Zaehler("trigger", rueckgabe={
            "ok": True, "job_id": "job-1", "status": "FINISHED", "waited_s": 0, "error": None}))
    stub_modul("runtime_storage", get_storage=lambda: S())

    k7 = knoten_laden("apply_revalidate")
    st = k7.node_apply_revalidate(basis_state(
        correction_proposal=innen, correction_response=huelle,
        technical_check={"schema_valid": True, "retries": 0, "errors": []}))
    return st


def pruefen() -> Pruefung:
    p = Pruefung("Kategorie 4 — Integrationsnachweis der Messlogik")

    A = _meldung("validate_unique_ids", "Doppelte demandId D999_001")
    B = _meldung("validate_demand_article_ids", "Unbekannter Artikel 999999")
    C = _meldung("validate_density_values", "relDensityMin muss > 0 sein")

    def bewerte(st):
        a = st["applied"]
        return kategorie4_folgefehler(a["applied_ok"], a["uploaded"],
                                      (a["revalidation"] or {}).get("ok"),
                                      st["errors_after"], a["errors_new"],
                                      a["new_error_types"])

    # --- Fall 1: A behoben, nichts Neues -> NEIN ---
    st = _lauf([A], [])
    p.gleich("Fall 1 errors_after", 0, st["errors_after"])
    p.gleich("Fall 1 errors_resolved", 1, st["applied"]["errors_resolved"])
    p.gleich("Fall 1 errors_new", 0, st["applied"]["errors_new"])
    p.gleich("Fall 1 Kategorie 4", NEIN, bewerte(st)["befund"])

    # --- Fall 2: A behoben, B NEU -> JA. Der eigentliche Nachweis. ---
    # Die Fehlerzahl bleibt 1 -> 1. NUR ueber die Fehleridentitaeten ist erkennbar, dass die
    # Korrektur einen Fehler behoben UND einen neuen erzeugt hat.
    st = _lauf([A], [B])
    p.gleich("Fall 2 errors_after (unveraendert 1!)", 1, st["errors_after"])
    p.gleich("Fall 2 errors_resolved", 1, st["applied"]["errors_resolved"])
    p.gleich("Fall 2 errors_new", 1, st["applied"]["errors_new"])
    p.gleich("Fall 2 new_error_types", ["validate_demand_article_ids"],
             st["applied"]["new_error_types"])
    r = bewerte(st)
    p.gleich("Fall 2 Kategorie 4 = FOLGEFEHLER", JA, r["befund"])
    p.gleich("Fall 2 Beleg nennt den neuen Typ", ["validate_demand_article_ids"],
             r["belege"]["neue_typen"])

    # --- Fall 3: nichts behoben, nichts neu -> NEIN (wirkungslos, kein Folgefehler) ---
    st = _lauf([A], [A])
    p.gleich("Fall 3 errors_after", 1, st["errors_after"])
    p.gleich("Fall 3 errors_resolved", 0, st["applied"]["errors_resolved"])
    p.gleich("Fall 3 errors_new", 0, st["applied"]["errors_new"])
    p.gleich("Fall 3 Kategorie 4 (wirkungslos != Folgefehler)", NEIN, bewerte(st)["befund"])

    # --- Fall 4: mehrere neue Fehler ---
    st = _lauf([A], [B, C])
    p.gleich("Fall 4 errors_new", 2, st["applied"]["errors_new"])
    p.gleich("Fall 4 neue Typen",
             ["validate_demand_article_ids", "validate_density_values"],
             st["applied"]["new_error_types"])
    p.gleich("Fall 4 Kategorie 4", JA, bewerte(st)["befund"])

    # --- Fall 5: Abgrenzung — unvollstaendige Verarbeitung ist NICHT "kein Folgefehler" ---
    p.gleich("Fall 5 Revalidierung unbelegt -> nicht bestimmbar", UNKLAR,
             kategorie4_folgefehler(True, True, None, None, None)["befund"])
    p.gleich("Fall 5 Apply gescheitert -> nicht bestimmbar", UNKLAR,
             kategorie4_folgefehler(False, False, None, None, None)["befund"])
    return p


def main():
    sys.path.insert(0, str(APP))
    from core.run_metadata import require_ba_env
    meta = require_ba_env("Kategorie-4-Integrationsnachweis (BA-049)")
    print(f"Umgebung: {meta['umgebung']['sys_prefix']}")
    p = pruefen()
    p.drucken()
    return 0 if p.bestanden else 1


if __name__ == "__main__":
    sys.exit(main())
