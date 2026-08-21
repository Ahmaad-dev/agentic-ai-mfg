"""
Gemeinsame Kategorie-4-Auswertung fuer A, B und C.

WARUM (BA-051)
---------------
Der Runner nahm `errors_resolved` / `errors_new` / `new_error_types` aus `graph_state.json` -
und das schreibt **nur C**. Fuer A und B standen sie auf `None`. Das ist eine
Ungleichbehandlung im MESSINSTRUMENT, kein UF3-Befund: Kategorie 4 ist eine fachliche Groesse
und laesst sich fuer alle drei Arme aus den Validierungsmeldungen berechnen. Sie nur dort zu
erheben, wo zufaellig ein `GraphState` existiert, wuerde C bevorzugen - ein Unterschied waere
dann teilweise ein Artefakt der Messung statt der Architektur.

**Abzugrenzen:** Karten, Regel-Hashes und Trace, die nur C persistiert, bleiben asymmetrisch.
Das ist Untersuchungsgegenstand von UF3 (Masterplan Kap. 16.3), keine Luecke.

EINE IMPLEMENTIERUNG, NICHT DREI
---------------------------------
Die Fehleridentitaet wird **direkt aus Knoten 7 importiert**
(`graph/nodes/apply_revalidate._fehler_identitaeten`). Geprueft: reine Funktion, das Modul
importiert auf Modulebene nur `hashlib`, `json`, `datetime` - **keine Nebenwirkungen**, kein
Produktcode musste geaendert werden. Damit rechnen Produkt und Auswertung nachweislich mit
derselben Definition.

DIE IDENTITAETSDEFINITION - UND IHRE GRENZE
--------------------------------------------
`[validate_*]`-Tag + Hash der normalisierten Meldung. Der Server liefert keine Fehler-ID.

    ⚠ NAEHERUNG: Aendert sich der TEXT einer Meldung, waehrend die zugrunde liegende Ursache
    dieselbe bleibt (z. B. weil eine Zahl in der Meldung steht, die sich durch die Korrektur
    veraendert hat), erscheint derselbe Fehler als `resolved` UND `new`. Kategorie 4 wird
    dadurch tendenziell UEBERschaetzt. Die Definition wird hier bewusst NICHT neu gestaltet -
    sie ist Kontrollbedingung; die Kennzahl ist als Naeherung auszuweisen.

KEINE FALSCHEN NULLEN
----------------------
Ohne abgeschlossene Re-Validierung gibt es keine autoritativen Nach-Meldungen. Dann ist
Kategorie 4 `None` / `nicht_bestimmbar` - **niemals 0**. Eine 0 wuerde behaupten, es sei
nachweislich kein Folgefehler entstanden.
"""
from __future__ import annotations

import sys
from pathlib import Path

_SP = Path(__file__).resolve().parent.parent / "tools" / "smart-planning"
for _p in (str(_SP), str(_SP / "runtime")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# DIESELBE Funktion, die Knoten 7 im Produktpfad benutzt - importiert, nicht nachgebaut.
from graph.nodes.apply_revalidate import _fehler_identitaeten  # noqa: E402

#: Was in die Messzeile geschrieben wird, wenn keine belastbare Nach-Validierung vorliegt.
NICHT_BESTIMMBAR = None

FELDER = ("errors_resolved", "errors_remaining", "errors_new", "new_error_types")


def kategorie4(vorher_meldungen, nachher_meldungen, revalidation_ok) -> dict:
    """
    Die gemeinsame Messfunktion. Fuer A, B und C identisch aufgerufen.

    `vorher_meldungen`  : snapshot-validation.json VOR der Korrektur
    `nachher_meldungen` : snapshot-validation.json NACH abgeschlossener Re-Validierung
    `revalidation_ok`   : True nur, wenn der Validierungsjob nachweislich terminal erfolgreich war

    Returns `{errors_resolved, errors_remaining, errors_new, new_error_types,
              basis, hinweis}`.
    """
    if revalidation_ok is not True or nachher_meldungen is None:
        return {f: NICHT_BESTIMMBAR for f in FELDER} | {
            "basis": "nicht_bestimmbar",
            "hinweis": ("Keine abgeschlossene Re-Validierung bzw. keine autoritativen "
                        "Nach-Meldungen. Kategorie 4 bleibt unbelegt - eine 0 waere hier "
                        "die Behauptung, es sei nachweislich nichts Neues entstanden.")}

    vor = _fehler_identitaeten(vorher_meldungen or [])
    nach = _fehler_identitaeten(nachher_meldungen or [])
    behoben = set(vor) - set(nach)
    geblieben = set(vor) & set(nach)
    neu = set(nach) - set(vor)

    # SEMANTIK EXAKT WIE KNOTEN 7 (apply_revalidate.py:207), nachgesehen statt angenommen:
    # `_fehler_identitaeten()` liefert ein Dict {hash16: validator_tag} - der SCHLUESSEL ist
    # der Hash, der WERT der Tag. Der Typ wird also per Nachschlagen im NACHHER-Dict bestimmt,
    # nicht aus der Identitaet zurueckgeparst.
    #
    # Mein erster Entwurf nahm ein Format "<tag>|<hash>" an und lieferte deshalb Hashes statt
    # Tags (BA-051/BA-052). Fuenfte Annahme dieser Art in Folge - der Cross-Check gegen den
    # GraphState hat sie gefangen, wofuer er gebaut ist.
    return {
        "errors_resolved": len(behoben),
        "errors_remaining": len(geblieben),
        "errors_new": len(neu),
        "new_error_types": sorted({nach[i] for i in neu}),
        "basis": "validierungsmeldungen_vorher_nachher",
        "hinweis": ("Naeherung: Identitaet = Validator-Tag + Meldungs-Hash. Eine textlich "
                    "veraenderte Meldung derselben Ursache erscheint als resolved + new."),
    }


def cross_check_graphstate(berechnet: dict, graph_state: dict | None) -> dict:
    """
    Nur fuer C: Vergleich der GEMEINSAMEN Berechnung mit den im `graph_state.json`
    persistierten Werten.

    **Die gemeinsame Berechnung ist die primaere Messung.** Der GraphState ist Gegenprobe.
    Eine Abweichung wird ausgewiesen, nicht stillschweigend ueberschrieben - sie waere ein
    harter Befund ueber das Messinstrument.
    """
    if not graph_state:
        return {"durchgefuehrt": False, "grund": "kein graph_state.json (A/B)"}
    ap = (graph_state.get("applied") or {})
    persistiert = {"errors_resolved": ap.get("errors_resolved"),
                   "errors_remaining": ap.get("errors_remaining"),
                   "errors_new": ap.get("errors_new"),
                   "new_error_types": sorted(ap.get("new_error_types") or [])}
    verglichen = {k: berechnet.get(k) for k in FELDER}
    verglichen["new_error_types"] = sorted(verglichen.get("new_error_types") or [])
    abweichungen = {k: {"berechnet": verglichen[k], "graph_state": persistiert[k]}
                    for k in FELDER if verglichen[k] != persistiert[k]}
    return {"durchgefuehrt": True, "identisch": not abweichungen,
            "abweichungen": abweichungen, "graph_state_werte": persistiert}
