"""
Gemeinsames Gerüst für die Graph-Handoff-Regressionen (BA-044).

WARUM ES DIESES MODUL GIBT
--------------------------
Die Regressionen 1 und 2 lagen als Wegwerf-Skripte im Scratchpad und sind verloren gegangen
(BA-044). Ein bestandener Test, der sich nicht wiederholen lässt, ist kein Nachweis — deshalb
liegen sie ab jetzt permanent unter `app/eval/`.

WAS HIER GEPRÜFT WIRD — UND WAS NICHT
--------------------------------------
Gegenstand sind die **Knotenverträge des Graph-Pfads**: Was tut Knoten 5, 6, 7 oder 8, wenn
ein Eingang fehlt oder widersprüchlich ist? Das ist eine Frage an den Kontrollfluss, nicht an
das Modell. Die Knoten laufen deshalb mit **Attrappen an den Aussenkanten**: kein LLM-Aufruf,
kein Server, kein Dateisystem.

Das ist **kein Messlauf** und erzeugt keine Messwerte. Es berührt weder Regelkarten noch
Prompts noch die 17 Messfälle. `generate_audit_report()` wird nie aufgerufen.

WARUM ATTRAPPEN STATT ECHTER RUNTIME
-------------------------------------
Die gesuchten Defekte sind genau die Fälle, in denen ein Knoten **etwas tut, was er nicht tun
darf** — einen Latest-Resolver rufen, auf Platte greifen, anwenden. Ein echter Lauf würde das
Verbotene ausführen und danach höchstens am Ergebnis erahnen lassen, dass es passiert ist.
Eine zählende Attrappe **beweist es direkt**: `run_apply` 0× gerufen ist ein härterer Beleg
als `applied_ok=False`.

Die Attrappen sitzen ausschliesslich an den Aussenkanten, die der Knoten importiert. Die
geprüfte Logik — der gesamte Knotenrumpf — ist der **echte Produktionscode**.

UMGEBUNG
--------
`require_ba_env()` erzwingt die Wurzel-`.venv` hart. Auch wenn hier kein Messwert entsteht:
Ein Vertrag, der unter einer anderen `pydantic`-Version geprüft wurde, sagt nichts über den
Messlauf aus (BA-025, Befund F8).
"""
import importlib
import sys
import types
from pathlib import Path

APP = Path(__file__).resolve().parent.parent
SP = APP / "tools" / "smart-planning"


def pfade_setzen():
    """Damit `graph.nodes.*` und die Runtime-Module importierbar sind."""
    for p in (str(APP), str(SP), str(SP / "runtime")):
        if p not in sys.path:
            sys.path.insert(0, p)


class Zaehler:
    """
    Eine Attrappe, die zählt, ob und womit sie gerufen wurde.

    Der Zähler ist der eigentliche Messwert dieser Tests: `0` beweist, dass ein Guard
    wirklich blockiert hat — nicht nur, dass das Ergebnis hinterher richtig aussah.
    """

    def __init__(self, name, rueckgabe=None, wirft=None):
        self.name = name
        self.rueckgabe = rueckgabe
        self.wirft = wirft
        self.aufrufe = []

    def __call__(self, *a, **kw):
        self.aufrufe.append({"args": a, "kwargs": kw})
        if self.wirft is not None:
            raise self.wirft
        if callable(self.rueckgabe):
            return self.rueckgabe(*a, **kw)
        return self.rueckgabe

    @property
    def n(self):
        return len(self.aufrufe)

    def __repr__(self):
        return f"<Zaehler {self.name} n={self.n}>"


#: Namen aller aktuell gesetzten Attrappen. Wird gebraucht, um sie wieder VOLLSTAENDIG zu
#: entfernen — eine einzelne uebriggebliebene Attrappe reicht, um einen spaeteren Testfall
#: still auf das falsche Modul zeigen zu lassen (siehe `echtes_modul`).
_STUBS = set()


def stub_modul(name: str, **attribute) -> types.ModuleType:
    """
    Legt ein Attrappen-Modul in `sys.modules` ab, damit das `import X` INNERHALB der
    Knotenfunktion es findet.

    Die Knoten importieren ihre Aussenkanten bewusst im Funktionsrumpf (`import
    apply_correction as applier`). Genau deshalb genügt es, `sys.modules` vorzubelegen — der
    echte Runtime-Code wird dann gar nicht erst geladen, es kann also weder ein Netzaufruf
    noch ein Dateizugriff aus Versehen passieren.
    """
    m = types.ModuleType(name)
    for k, v in attribute.items():
        setattr(m, k, v)
    sys.modules[name] = m
    _STUBS.add(name)
    return m


def knoten_laden(modulname: str):
    """
    Lädt ein Knotenmodul FRISCH. Ohne `reload` behielte ein zweiter Testfall die Attrappen
    des ersten — derselbe Fehlerfall wie BA-021 (`importlib.reload()` schaltet einen bereits
    importierten Schalter nicht um).
    """
    voll = f"graph.nodes.{modulname}"
    if voll in sys.modules:
        return importlib.reload(sys.modules[voll])
    return importlib.import_module(voll)


# --------------------------------------------------------------------- Zustände
def voll_huelle(vorschlag: dict, iteration: int = 1, sid: str = "TEST-SNAPSHOT-0000") -> dict:
    """
    Eine WIRKLICH schema-gültige `LLMCorrectionResponse`-Hülle, wie sie auf Platte liegt.

    KORRIGIERT 21.08.2026 (BA-047). Die erste Fassung setzte `original_error` und
    `error_analyzed` auf Strings ("…"). Das ist **keine gültige Hülle**: das Modell verlangt
    dort `OriginalError` bzw. `ErrorAnalyzed`, also Objekte
    (`correction_models.py:51-62`). Aufgefallen ist es erst, als R9a/R9b die **echte**
    Pydantic-Prüfung benutzten — R1, R5 und R6 hatten den Prüfer gestubbt und konnten es
    nicht merken.

    **Das ist die Lehre in Kurzform:** eine Attrappe, die alles akzeptiert, prüft nichts.
    Wo der Gegenstand des Tests die Gültigkeit selbst ist, muss der echte Prüfer laufen.

    Die vier Pflichtfelder der Hülle sind zugleich der Grund, warum Knoten 7 die Hülle lädt
    statt sie selbst zu bauen, und warum Knoten 6 sie prüfen muss statt des inneren
    Vorschlags (BA-046).
    """
    innen = {"action": "update_field", "target_path": "articles[0].relDensity",
             "reasoning": "Testfall", "status": "pending_review"}
    innen.update(vorschlag or {})
    return {
        "iteration": iteration,
        "snapshot_id": sid,
        "original_error": {"level": "ERROR", "message": "[validate_test] Testmeldung"},
        "error_analyzed": {"search_mode": "value", "search_value": "100000",
                           "error_type": "TESTFALL", "results_count": 1},
        "correction_proposal": innen,
    }


def basis_state(**extra) -> dict:
    """
    Ein Zustand, der ALLE Vorbedingungen erfüllt. Jeder Testfall bricht davon genau EINE —
    sonst liesse sich ein Befund nicht zuordnen.
    """
    st = {
        "snapshot_id": "TEST-SNAPSHOT-0000",
        "iteration": 1,
        "max_iterations": 5,
        "artifact_iteration_number": 1,
        "architecture_mode": "graph",
        "errors_before": 2,
        "errors_after": None,
        "trace": [],
        "matched_rules": {"rule_text": "REGELTEXT", "cards_loaded": ["k1.md"],
                          "rulebook_mode": "cards"},
        "extracted_context": {"results_object": {"results_count": 3}, "results_hash": None,
                              "results_count": 3},
        "classified_error": {"identify_response": {"tag": "validate_x"},
                             "identify_response_sha256": None},
        "correction_proposal": {"action": "modify", "target_path": "articles[0].relDensity",
                                "new_value": 1.0},
    }
    st.update(extra)
    # BA-047: Die vollstaendige Huelle gehoert zum gesunden Zustand dazu - Knoten 6 prueft
    # sie, nicht den inneren Vorschlag. Wer `correction_proposal` ueberschreibt, bekommt die
    # passende Huelle automatisch; wer `correction_response` ausdruecklich setzt (auch auf
    # None, fuer den Guard-Test), behaelt seinen Wert.
    if "correction_response" not in extra:
        innen = st.get("correction_proposal")
        st["correction_response"] = (voll_huelle(innen,
                                                 iteration=st.get("artifact_iteration_number") or 1,
                                                 sid=st["snapshot_id"])
                                     if innen is not None else None)
    return st


# --------------------------------------------------------------------- Berichte
class Pruefung:
    """Sammelt Einzelprüfungen und liefert am Ende PASS/FAIL plus Belege."""

    def __init__(self, name: str):
        self.name = name
        self.zeilen = []

    def gleich(self, was: str, erwartet, beobachtet):
        ok = erwartet == beobachtet
        self.zeilen.append({"pruefung": was, "erwartet": erwartet,
                            "beobachtet": beobachtet, "ok": ok})
        return ok

    def wahr(self, was: str, bedingung: bool, beleg=None):
        self.zeilen.append({"pruefung": was, "erwartet": True,
                            "beobachtet": bool(bedingung), "beleg": beleg,
                            "ok": bool(bedingung)})
        return bool(bedingung)

    @property
    def bestanden(self) -> bool:
        return all(z["ok"] for z in self.zeilen)

    @property
    def anzahl(self):
        return sum(1 for z in self.zeilen if z["ok"]), len(self.zeilen)

    def drucken(self):
        gut, alle = self.anzahl
        print(f"\n--- {self.name}: {'PASS' if self.bestanden else 'FAIL'} {gut}/{alle} ---")
        for z in self.zeilen:
            mark = "ok  " if z["ok"] else "FAIL"
            print(f"  [{mark}] {z['pruefung']}: erwartet={z['erwartet']!r} "
                  f"beobachtet={z['beobachtet']!r}")
        return self.bestanden


def echtes_modul(name: str):
    """
    Erzwingt das ECHTE Runtime-Modul — und raeumt dafuer ALLE Attrappen ab.

    Gefunden beim ersten Suite-Lauf (BA-044), in zwei Stufen:
      1. R2 stubbt `validate_correction_schema_llm`; R3 bekam danach die Attrappe statt der
         Runtime und brach mit `AttributeError` ab.
      2. Nur diese eine Attrappe zu entfernen genuegte NICHT: das echte Modul importiert beim
         Laden `runtime_storage`, das ebenfalls noch als Attrappe in `sys.modules` stand ->
         `ImportError: cannot import name 'get_iteration_folders_with_file'`.

    **Einzeln gruen, in der Suite kaputt** — dieselbe Klasse Fehler wie in BA-021, wo
    `importlib.reload()` einen bereits importierten Schalter nicht umschaltete. Ein Test, der
    nur isoliert besteht, ist keine Regression.

    Deshalb wird hier nicht selektiv repariert, sondern der gesamte Attrappen-Satz entfernt.
    Wer danach wieder Attrappen braucht, setzt sie neu — das ist billig und eindeutig.
    """
    for gestubbt in list(_STUBS):
        sys.modules.pop(gestubbt, None)
    _STUBS.clear()
    return importlib.import_module(name)
