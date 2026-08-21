"""
Permanente Regressionen zum Iterations-/Proposal-Handoff des Graph-Pfads (BA-044).

Sie sichern die vier Reparaturen aus BA-043 und die drei Nachbesserungen aus BA-044 ab.
**Ersatz für die verlorenen Scratchpad-Skripte** — ein bestandener Test, der sich nicht
wiederholen lässt, ist kein Nachweis.

    R1  Guard-Mismatch          State-Vorschlag != Platten-Vorschlag -> nichts wird angewandt
    R2  Missing-Artifact        `artifact_iteration_number` fehlt -> kein Latest-Resolver,
                                kein Disk-Fallback, K8 sagt stop_uncertain
    R3  Vier-Kombinationen      der Vertrag von `run_technical_check()` GEGEN DIE RUNTIME
    R4  Hash-Kette ohne Retry   H_before == H_after, `retry_hat_vorschlag_geaendert` False
    R5  Schema-Retry            H_before -> H_after, und K7 arbeitet mit H_after
    R6  Mehrfachiteration       D1->1, D2->2, D3->3; der Guard darf NICHT auslösen
    R9a Hülle valide            kein HANDOFF-bedingter Retry; K6-Eingang == K5-Hülle (SHA-256)
    R9b Hülle invalide          Retry löst aus, finale Hülle autoritativ, K7 bekommt sie

R9a/R9b sind das Paar aus BA-047. Sie schreiben ausdrücklich NICHT `retries=0` als
Systeminvariante fest — in echten Pilotläufen sind Schema-Retries legitim. Geprüft wird, dass
ein Retry nicht mehr **durch den Graph-Handoff** entsteht.

R3 ruft die **echte** Runtime-Funktion (kein LLM, kein Server — nur der Vertrag um sie herum).
R1, R2, R4, R5 und R6 laufen mit Attrappen an den Aussenkanten; begründet im Harness.

**Kein Messlauf.** Keine Regelkarte, kein Prompt, keiner der 17 Messfälle.
`generate_audit_report()` wird nicht aufgerufen.

Aufruf:  .venv/Scripts/python.exe app/eval/test_graph_handoff_regressions.py [--only R1,R2]
Exit 0 = alle gewählten Regressionen bestanden, 1 = mindestens eine FAIL.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from graph_regression_harness import (  # noqa: E402
    APP, Pruefung, Zaehler, basis_state, echtes_modul, knoten_laden, pfade_setzen,
    stub_modul, voll_huelle,
)

pfade_setzen()


# --------------------------------------------------------------------- Attrappen
def _storage(meldungen=None):
    """Fake-Storage. `load_json` liefert die Validierungsmeldungen, sonst nichts."""
    class S:
        def __init__(self):
            self.gelesen = []

        def load_json(self, pfad):
            self.gelesen.append(pfad)
            if pfad.endswith("snapshot-validation.json"):
                return meldungen if meldungen is not None else []
            return None

        def save_json(self, *a, **kw):
            return None

    return S()


def _k7_aussenkanten(*, huelle_auf_platte=None, apply_ok=True, upload_ok=True,
                     trigger_ok=True, meldungen_nachher=None):
    """
    Belegt sys.modules mit den Aussenkanten von Knoten 7 und gibt die Zähler zurück.
    Die Knoten importieren im Funktionsrumpf — deshalb genügt sys.modules, und der echte
    Runtime-Code wird gar nicht geladen (kein Netz, keine Platte).
    """
    laden = Zaehler("load_correction_proposal", rueckgabe=huelle_auf_platte)
    anwenden = Zaehler("run_apply", rueckgabe=lambda *a, **kw: {
        "applied_ok": apply_ok, "iteration_number": kw.get("iteration_number"),
        "proposal": kw.get("correction_proposal"),
        "error": None if apply_ok else "Attrappe: apply abgelehnt"})
    hochladen = Zaehler("run_upload", rueckgabe={
        "uploaded": upload_ok, "response": None,
        "error": None if upload_ok else "Attrappe: upload abgelehnt"})
    trigger = Zaehler("trigger_server_validation", rueckgabe={
        "ok": trigger_ok, "job_id": "job-0001", "status":
        "FINISHED" if trigger_ok else "FAILED", "waited_s": 0, "error": None})
    validieren = Zaehler("validate_snapshot", rueckgabe=None)
    st = _storage(meldungen_nachher)

    stub_modul("apply_correction", load_correction_proposal=laden, run_apply=anwenden)
    stub_modul("update_snapshot", run_upload=hochladen)
    stub_modul("validate_snapshot", validate_snapshot=validieren)
    routes = stub_modul("routes")
    sv = stub_modul("routes.server_validation", trigger_server_validation=trigger)
    routes.server_validation = sv
    stub_modul("runtime_storage", get_storage=lambda: st)

    return {"laden": laden, "anwenden": anwenden, "hochladen": hochladen,
            "trigger": trigger, "validieren": validieren, "storage": st}


def _k5_aussenkanten(iteration_vorhanden=None):
    """
    Aussenkanten von Knoten 5. `run_correction_generation` MODELLIERT den Legacy-Fallback
    der echten Runtime: `iteration_number is None` -> `get_latest_iteration_number_local()`
    (generate_correction_llm.py:913-914, Funktion definiert :94). Statisch verifiziert.
    Der Zähler `latest_local` macht den Fallback damit direkt beobachtbar.
    """
    latest = Zaehler("get_latest_iteration_number_local", rueckgabe=1)

    def erzeugen(snapshot_id, fix_rules=None, identify_response=None, search_results=None,
                 iteration_number=None, check_open_proposal=True):
        if iteration_number is None:
            iteration_number = latest(snapshot_id)
        return {"proposal": {"action": "modify", "target_path": "articles[0].relDensity",
                             "new_value": 1.049, "value_source": "llm"},
                "output_data": None, "llm_call": None,
                "iteration_number": iteration_number, "blocked_by": None, "error": None}

    erzeugen_z = Zaehler("run_correction_generation", rueckgabe=erzeugen)
    stub_modul("generate_correction_llm",
               run_correction_generation=erzeugen_z,
               get_latest_iteration_number_local=latest)
    stub_modul("identify_snapshot", context_sha256=lambda o: "ctxhash")
    stub_modul("identify_error_llm", identify_sha256=lambda o: "idhash")
    return {"erzeugen": erzeugen_z, "latest_local": latest}


def _k6_aussenkanten(schema_valid=True, retries=0, proposal_nach_retry=None):
    """
    Aussenkante von Knoten 6. `run_technical_check` MODELLIERT den Vertrag aus BA-043:
    fehlt die Nummer, wird `_load_latest_proposal()` gerufen. Der Zähler macht es sichtbar.
    """
    latest = Zaehler("_load_latest_proposal", rueckgabe=(1, None))

    def pruefen(snapshot_id, iteration_number=None, correction_proposal=None, max_retries=5):
        if iteration_number is None:
            latest(snapshot_id)
        endgueltig = proposal_nach_retry if proposal_nach_retry is not None else correction_proposal
        return {"schema_valid": schema_valid, "retries": retries, "errors": [],
                "proposal": endgueltig, "iteration_number": iteration_number,
                "proposal_sha256_before": "H_before",
                "proposal_sha256_after": "H_after" if proposal_nach_retry else "H_before"}

    pruefen_z = Zaehler("run_technical_check", rueckgabe=pruefen)
    stub_modul("validate_correction_schema_llm", run_technical_check=pruefen_z)
    return {"pruefen": pruefen_z, "latest_proposal": latest}


# ===================================================================== R1
def r1_guard_mismatch() -> Pruefung:
    """
    Der State trägt Vorschlag X, auf Platte liegt Y. Der Guard muss WIRKLICH blockieren —
    nicht nur melden. Vorher ging bei Mismatch `None` in `run_apply()`, und die Funktion
    lud sich Y selbst von Platte nach (`apply_correction.py:550-552`); angewandt wurde
    genau der Vorschlag, den der Guard verworfen hatte (BA-035, P04/P10).
    """
    p = Pruefung("R1 — Guard-Mismatch: State != Platte")

    im_state = {"action": "modify", "target_path": "articles[0].relDensity", "new_value": 1.049}
    auf_platte = {"action": "modify", "target_path": "articles[0].relDensity", "new_value": 9.999}
    z = _k7_aussenkanten(huelle_auf_platte=voll_huelle(auf_platte))

    k7 = knoten_laden("apply_revalidate")
    k8 = knoten_laden("evaluation")

    st = basis_state(correction_proposal=im_state,
                     technical_check={"schema_valid": True, "retries": 0, "errors": []})
    st = k7.node_apply_revalidate(st)
    st = k8.node_evaluation(st)

    ang = st["applied"]
    p.gleich("run_apply Aufrufe", 0, z["anwenden"].n)
    p.gleich("run_upload Aufrufe", 0, z["hochladen"].n)
    p.gleich("trigger_server_validation Aufrufe", 0, z["trigger"].n)
    p.gleich("validate_snapshot Aufrufe", 0, z["validieren"].n)
    p.gleich("proposal_identisch", False, ang["proposal_identisch"])
    p.gleich("applied_ok", False, ang["applied_ok"])
    p.gleich("uploaded", False, ang["uploaded"])
    p.gleich("revalidation_ok", None, (ang["revalidation"] or {}).get("ok"))
    p.gleich("errors_after", None, st["errors_after"])
    p.gleich("K8 decision", "stop_uncertain", st["decision"]["action"])
    return p


# ===================================================================== R2
def r2_missing_artifact_iteration() -> Pruefung:
    """
    `artifact_iteration_number` fehlt. K5, K6 und K7 werden EINZELN geprüft — sonst
    verdeckt ein früher Abbruch die Fallbacks der anderen (genau der Grund, warum BA-043
    drei Stellen übersah). Danach der Gesamtpfad.
    """
    p = Pruefung("R2 — fehlende artifact_iteration_number")

    # ---- K5 einzeln ----
    z5 = _k5_aussenkanten()
    k5 = knoten_laden("correction")
    s5 = k5.node_correction(basis_state(artifact_iteration_number=None,
                                        correction_proposal=None))
    p.gleich("K5: run_correction_generation Aufrufe", 0, z5["erzeugen"].n)
    p.gleich("K5: latest-Resolver Aufrufe", 0, z5["latest_local"].n)
    p.gleich("K5: correction_proposal", None, s5["correction_proposal"])
    tr5 = [t for t in s5["trace"] if t["node"] == "correction"][-1]
    p.wahr("K5: Trace nennt die fehlende Nummer",
           "artifact_iteration_number" in (tr5["output_digest"].get("fehler") or ""),
           tr5["output_digest"].get("fehler"))
    p.gleich("K5: Trace artifact_iteration_number", None,
             tr5["input_digest"]["artifact_iteration_number"])

    # ---- K6 einzeln ----
    z6 = _k6_aussenkanten()
    k6 = knoten_laden("technical_check")
    s6 = k6.node_technical_check(basis_state(artifact_iteration_number=None))
    p.gleich("K6: run_technical_check Aufrufe", 0, z6["pruefen"].n)
    p.gleich("K6: latest-Resolver Aufrufe", 0, z6["latest_proposal"].n)
    p.gleich("K6: schema_valid", False, s6["technical_check"]["schema_valid"])

    # ---- K7 einzeln ----
    z7 = _k7_aussenkanten(huelle_auf_platte=voll_huelle({"action": "modify"}))
    k7 = knoten_laden("apply_revalidate")
    s7 = k7.node_apply_revalidate(
        basis_state(artifact_iteration_number=None,
                    technical_check={"schema_valid": True, "retries": 0, "errors": []}))
    p.gleich("K7: load_correction_proposal Aufrufe", 0, z7["laden"].n)
    p.gleich("K7: run_apply Aufrufe", 0, z7["anwenden"].n)
    p.gleich("K7: run_upload Aufrufe", 0, z7["hochladen"].n)
    p.gleich("K7: trigger_server_validation Aufrufe", 0, z7["trigger"].n)
    p.gleich("K7: applied_ok", False, s7["applied"]["applied_ok"])
    p.gleich("K7: errors_after", None, s7["errors_after"])

    # ---- K8 auf dem K7-Ergebnis ----
    k8 = knoten_laden("evaluation")
    s8 = k8.node_evaluation(s7)
    p.gleich("K8: decision nach K7-Blockade", "stop_uncertain", s8["decision"]["action"])

    # ---- K8 mit VOLLSTÄNDIG fehlendem `applied` (der eigentliche BA-044-Befund) ----
    s8b = k8.node_evaluation(basis_state(
        artifact_iteration_number=None,
        technical_check={"schema_valid": True, "retries": 0, "errors": []}))
    p.gleich("K8: decision wenn `applied` ganz fehlt", "stop_uncertain",
             s8b["decision"]["action"])
    p.gleich("K8: k7_hat_belegt im Trace", False,
             [t for t in s8b["trace"] if t["node"] == "evaluation"][-1]
             ["input_digest"]["k7_hat_belegt"])

    # ---- Gesamtpfad K5 -> K6 -> K7 -> K8 ----
    z5 = _k5_aussenkanten()
    z6 = _k6_aussenkanten()
    z7 = _k7_aussenkanten(huelle_auf_platte=voll_huelle({"action": "modify"}))
    k5, k6, k7, k8 = (knoten_laden(n) for n in
                      ("correction", "technical_check", "apply_revalidate", "evaluation"))
    g = basis_state(artifact_iteration_number=None, correction_proposal=None)
    for fn in (k5.node_correction, k6.node_technical_check,
               k7.node_apply_revalidate, k8.node_evaluation):
        g = fn(g)
    resolver = z5["latest_local"].n + z6["latest_proposal"].n + z7["laden"].n
    p.gleich("Gesamtpfad: Resolver-/Disk-Zugriffe gesamt", 0, resolver)
    p.gleich("Gesamtpfad: run_apply", 0, z7["anwenden"].n)
    p.gleich("Gesamtpfad: run_upload", 0, z7["hochladen"].n)
    p.gleich("Gesamtpfad: errors_after", None, g["errors_after"])
    p.gleich("Gesamtpfad: decision", "stop_uncertain", g["decision"]["action"])
    return p


# ===================================================================== R3
def r3_vier_kombinationen() -> Pruefung:
    """
    Der Vier-Kombinationen-Vertrag von `run_technical_check()` — GEGEN DIE ECHTE RUNTIME,
    nicht gegen eine Attrappe. BA-043 hat hier `or` durch vier getrennte Fälle ersetzt;
    dieser Test hält fest, dass ein ÜBERGEBENER Wert nie überschrieben wird.

        beides fehlt   -> Legacy/CLI: Disk-Fallback (A/B/CLI-Verhalten, unverändert)
        nur Nummer     -> Proposal BEHALTEN, Nummer von Platte
        nur Proposal   -> Nummer BEHALTEN, Proposal von Platte
        beides da      -> nichts laden

    Geprüft wird über `_load_latest_proposal`, den einzigen Ladeweg der Funktion. Der
    eigentliche Schema-Check wird neutralisiert, damit kein LLM-Retry startet — Gegenstand
    ist die Kombinatorik davor, nicht die Schemaprüfung.
    """
    p = Pruefung("R3 — Vier-Kombinationen-Vertrag von run_technical_check (echte Runtime)")

    # ECHTE Runtime erzwingen - R2 hinterlaesst hier sonst seine Attrappe.
    schema = echtes_modul("validate_correction_schema_llm")

    platte_nr, platte_vorschlag = 7, {"action": "modify", "target_path": "von/platte"}
    uebergeben_nr, uebergeben_vorschlag = 3, {"action": "modify", "target_path": "aus/state"}

    orig_load = schema._load_latest_proposal
    orig_retry = schema.validate_with_retry
    try:
        for name, nr, vorschlag, erw_load, erw_nr, erw_ziel in [
            ("beides fehlt",  None,          None,                 1, platte_nr,    "von/platte"),
            ("nur Nummer",    None,          uebergeben_vorschlag, 1, platte_nr,    "aus/state"),
            ("nur Proposal",  uebergeben_nr, None,                 1, uebergeben_nr, "von/platte"),
            ("beides da",     uebergeben_nr, uebergeben_vorschlag, 0, uebergeben_nr, "aus/state"),
        ]:
            laden = Zaehler("_load_latest_proposal",
                            rueckgabe=(platte_nr, dict(platte_vorschlag)))
            schema._load_latest_proposal = laden
            schema.validate_with_retry = lambda sid, it, prop, **kw: prop  # neutral
            erg = schema.run_technical_check("TEST-SNAPSHOT-0000",
                                             iteration_number=nr,
                                             correction_proposal=(dict(vorschlag)
                                                                  if vorschlag else None))
            p.gleich(f"{name}: _load_latest_proposal Aufrufe", erw_load, laden.n)
            p.gleich(f"{name}: iteration_number", erw_nr, erg["iteration_number"])
            p.gleich(f"{name}: benutzter Vorschlag", erw_ziel,
                     (erg["proposal"] or {}).get("target_path"))
    finally:
        schema._load_latest_proposal = orig_load
        schema.validate_with_retry = orig_retry
    return p


# ===================================================================== R4
def r4_hashkette_ohne_retry() -> Pruefung:
    """
    Ohne Retry muss `H_before == H_after` gelten und `retry_hat_vorschlag_geaendert` False
    sein. Sonst wäre die Hash-Kette aus BA-043 als Nachweis wertlos: ein Term, der immer
    "verändert" meldet, unterscheidet nichts.

    Gegen die ECHTE Runtime — nur `validate_with_retry` ist neutralisiert (gibt den
    Vorschlag unverändert zurück, genau wie ein Lauf ohne Schemafehler).
    """
    p = Pruefung("R4 — Hash-Kette ohne Retry")

    schema = echtes_modul("validate_correction_schema_llm")
    vorschlag = {"action": "modify", "target_path": "articles[0].relDensity", "new_value": 1.049}

    orig_retry = schema.validate_with_retry
    try:
        schema.validate_with_retry = lambda sid, it, prop, **kw: prop
        erg = schema.run_technical_check("TEST-SNAPSHOT-0000", iteration_number=1,
                                         correction_proposal=dict(vorschlag))
    finally:
        schema.validate_with_retry = orig_retry

    p.gleich("schema_valid", True, erg["schema_valid"])
    p.gleich("retries", 0, erg["retries"])
    p.wahr("H_before ist gesetzt", erg["proposal_sha256_before"] is not None,
           erg["proposal_sha256_before"])
    p.gleich("H_before == H_after", erg["proposal_sha256_before"], erg["proposal_sha256_after"])

    # Und im Knoten: `retry_hat_vorschlag_geaendert` muss False sein.
    z6 = _k6_aussenkanten(schema_valid=True, retries=0)   # H_before == H_before
    k6 = knoten_laden("technical_check")
    s = k6.node_technical_check(basis_state(correction_proposal=dict(vorschlag)))
    tr = [t for t in s["trace"] if t["node"] == "technical_check"][-1]
    p.gleich("Knoten 6: retry_hat_vorschlag_geaendert",
             False, tr["provenienz"]["retry_hat_vorschlag_geaendert"])
    return p


# ===================================================================== R5
def r5_schema_retry() -> Pruefung:
    """
    Ein Retry verändert den Vorschlag LEGITIM: H_before -> H_after. Zwei Dinge müssen folgen:
      (a) `retry_hat_vorschlag_geaendert` ist True,
      (b) Knoten 7 arbeitet mit dem Stand NACH dem Retry — sonst meldete er zu Recht Drift.
    Punkt (b) ist Änderung 7 aus BA-043; ohne sie war die Rückkante ab Durchgang 2 blockiert.
    """
    p = Pruefung("R5 — gezielter Schema-Retry: H_before -> H_after, K7 nutzt H_after")

    vor_retry = {"action": "modify", "target_path": "articles[0].relDensity", "new_value": 1.049}
    nach_retry = {"action": "modify", "target_path": "articles[0].relDensity", "new_value": 1.063}

    _k6_aussenkanten(schema_valid=True, retries=1,
                     proposal_nach_retry=voll_huelle(dict(nach_retry)))
    k6 = knoten_laden("technical_check")
    s = k6.node_technical_check(basis_state(correction_proposal=dict(vor_retry)))

    tr = [t for t in s["trace"] if t["node"] == "technical_check"][-1]
    p.gleich("retries", 1, s["technical_check"]["retries"])
    p.gleich("retry_hat_vorschlag_geaendert", True,
             tr["provenienz"]["retry_hat_vorschlag_geaendert"])
    p.gleich("H_before != H_after", True,
             tr["provenienz"]["proposal_sha256_before"] != tr["provenienz"]["proposal_sha256_after"])
    p.gleich("State trägt den Stand NACH dem Retry", 1.063,
             s["correction_proposal"]["new_value"])

    # Knoten 7 auf demselben State: die Platte trägt ebenfalls den Retry-Stand -> kein Drift.
    z7 = _k7_aussenkanten(huelle_auf_platte=voll_huelle(dict(nach_retry)),
                          meldungen_nachher=[])
    k7 = knoten_laden("apply_revalidate")
    s = k7.node_apply_revalidate(s)
    p.gleich("K7: proposal_identisch nach Retry", True, s["applied"]["proposal_identisch"])
    p.gleich("K7: run_apply gerufen", 1, z7["anwenden"].n)
    p.gleich("K7: angewandter Wert", 1.063,
             z7["anwenden"].aufrufe[0]["kwargs"]["correction_proposal"]
             ["correction_proposal"]["new_value"])
    return p


# ===================================================================== R6
def r6_mehrfachiteration() -> Pruefung:
    """
    Die Invariante aus BA-042: Knoten 2 zählt 1 -> 2 -> 3, und K5, K6, K7 arbeiten in JEDEM
    Durchgang auf genau diesem Ordner. Vorher fror der Wert auf `1` ein, weil Knoten 6 ihn
    aus seiner EIGENEN vorigen Ausgabe las (Zirkelbezug, `technical_check.py:31`).

    Der Guard darf dabei NICHT auslösen — er ist für den Fehlerfall da, nicht für den
    Normalbetrieb. Ein Guard, der im gesunden Fall anschlägt, wäre die Blockade aus BA-035.
    """
    p = Pruefung("R6 — Mehrfachiteration: D1->1, D2->2, D3->3, Guard schweigt")

    beobachtet = {"k5": [], "k6": [], "k7": []}
    for durchgang, nr in enumerate((1, 2, 3), start=1):
        vorschlag = {"action": "modify", "target_path": f"articles[{nr}].relDensity",
                     "new_value": 1.0 + nr}
        z5 = _k5_aussenkanten()
        z6 = _k6_aussenkanten(schema_valid=True, retries=0)
        z7 = _k7_aussenkanten(huelle_auf_platte=voll_huelle(dict(vorschlag), iteration=nr),
                              meldungen_nachher=[])
        k5, k6, k7 = (knoten_laden(n) for n in
                      ("correction", "technical_check", "apply_revalidate"))

        st = basis_state(artifact_iteration_number=nr, iteration=durchgang,
                         correction_proposal=None)
        st = k5.node_correction(st)
        # Stand aus K5 dieses Durchgangs - innerer Vorschlag UND Huelle (BA-047)
        st["correction_proposal"] = dict(vorschlag)
        st["correction_response"] = voll_huelle(dict(vorschlag), iteration=nr,
                                                sid=st["snapshot_id"])
        st = k6.node_technical_check(st)
        st = k7.node_apply_revalidate(st)

        beobachtet["k5"].append(z5["erzeugen"].aufrufe[0]["kwargs"]["iteration_number"])
        beobachtet["k6"].append(z6["pruefen"].aufrufe[0]["kwargs"]["iteration_number"])
        beobachtet["k7"].append(z7["anwenden"].aufrufe[0]["kwargs"]["iteration_number"]
                                if z7["anwenden"].n else None)
        p.gleich(f"D{durchgang}: kein Latest-Resolver in K5", 0, z5["latest_local"].n)
        p.gleich(f"D{durchgang}: kein Latest-Resolver in K6", 0, z6["latest_proposal"].n)
        p.gleich(f"D{durchgang}: proposal_identisch (Guard schweigt)", True,
                 st["applied"]["proposal_identisch"])
        p.gleich(f"D{durchgang}: applied_ok", True, st["applied"]["applied_ok"])

    p.gleich("K5 sah die Iterationen", [1, 2, 3], beobachtet["k5"])
    p.gleich("K6 sah die Iterationen", [1, 2, 3], beobachtet["k6"])
    p.gleich("K7 sah die Iterationen", [1, 2, 3], beobachtet["k7"])
    return p



# ===================================================================== R9
def _echte_schema_pruefung(retry_liefert=None):
    """
    Aussenkante fuer die Huellen-Regressionen: die ECHTE `validate_with_retry`-Semantik,
    aber ohne LLM. Geprueft wird mit dem echten Pydantic-Modell `LLMCorrectionResponse`;
    nur der LLM-Reparaturaufruf ist eine Attrappe.

    Damit misst der Test, was er messen soll: ob der uebergebene Gegenstand die SCHEMAPRUEFUNG
    besteht - nicht, ob eine nachgebaute Attrappe ihn fuer gueltig haelt.
    """
    schema = echtes_modul("validate_correction_schema_llm")
    retry = Zaehler("retry_llm_with_schema_error", rueckgabe=lambda *a, **kw: retry_liefert)
    orig_retry = schema.retry_llm_with_schema_error
    orig_storage = schema.get_storage
    schema.retry_llm_with_schema_error = retry
    schema.get_storage = lambda: _storage()
    return schema, retry, (orig_retry, orig_storage)


def _echtheit_pruefen(p, schema):
    """
    Belegt IN JEDEM LAUF, dass der entscheidende Validator echt ist und nicht gestubbt.

    Ohne diese Prüfung wäre R9a wertlos: `retries=0` liesse sich auch dadurch erreichen, dass
    eine Attrappe alles durchwinkt. Genau dieser Fehler ist im Projekt schon zweimal passiert
    (BA-047: `voll_huelle()` war jahrelang schema-ungültig, gemerkt hat es niemand, weil der
    Prüfer gestubbt war). Eine Zusage im Text ist kein Nachweis — deshalb hier als Assertion.

    Gestubbt sind bewusst **nur** die beiden Aussenkanten: der LLM-Reparaturaufruf und der
    Plattenzugriff. Die Schemaprüfung selbst läuft echt.
    """
    import inspect
    p.gleich("ECHTHEIT: Modul ist die Runtime, nicht eine Attrappe",
             "validate_correction_schema_llm.py", Path(schema.__file__).name)
    for name in ("validate_correction_proposal", "validate_with_retry", "run_technical_check"):
        fn = getattr(schema, name)
        p.wahr(f"ECHTHEIT: {name} ist echt (keine Attrappe)",
               not isinstance(fn, Zaehler) and getattr(fn, "__module__", None)
               == "validate_correction_schema_llm",
               f"{type(fn).__name__} / {getattr(fn, '__module__', None)}")
    p.wahr("ECHTHEIT: geprueft wird das echte Pydantic-Modell",
           "LLMCorrectionResponse(**correction_proposal)"
           in inspect.getsource(schema.validate_correction_proposal),
           "validate_correction_proposal ruft LLMCorrectionResponse")
    p.wahr("ECHTHEIT: nur der LLM-Reparaturaufruf ist gestubbt",
           isinstance(schema.retry_llm_with_schema_error, Zaehler),
           type(schema.retry_llm_with_schema_error).__name__)


def r9a_huelle_valide_kein_retry() -> Pruefung:
    """
    R9a — kontrolliert SCHEMAVALIDE vollstaendige Huelle -> `retries=0`.

    WICHTIG, was hier NICHT behauptet wird: `retries=0` ist **keine Systeminvariante**. Ein
    echter Pilotlauf darf jederzeit einen Schema-Retry ausloesen — das Modell kann strukturell
    danebenliegen, und genau das ist Kategorie 2. Geprueft wird ausschliesslich, dass ein
    Retry **nicht mehr durch den Graph-Handoff** entsteht, also nicht wegen fehlender
    Huellenfelder (BA-046/BA-047).

    Zusaetzlich die harte Invariante: der Hash, den Knoten 6 als Eingang protokolliert, ist
    derselbe, den Knoten 5 als erzeugte Huelle protokolliert hat.
    """
    p = Pruefung("R9a — valide Huelle: kein handoff-bedingter Retry, Invariante haelt")

    schema, retry, orig = _echte_schema_pruefung()
    try:
        _echtheit_pruefen(p, schema)
        z5 = _k5_aussenkanten()
        k5 = knoten_laden("correction")
        k6 = knoten_laden("technical_check")

        st = k5.node_correction(basis_state(correction_proposal=None))
        # Die Attrappe von K5 liefert nur den inneren Vorschlag; die Huelle baut das
        # Testgeruest genauso, wie `run_correction_generation()` sie erzeugt.
        st["correction_response"] = voll_huelle(dict(st["correction_proposal"]),
                                                iteration=1, sid=st["snapshot_id"])
        tr5 = [t for t in st["trace"] if t["node"] == "correction"][-1]
        tr5["provenienz"]["response_sha256"] = k5._sha256(st["correction_response"])

        st = k6.node_technical_check(st)
        tr6 = [t for t in st["trace"] if t["node"] == "technical_check"][-1]

        p.gleich("schema_valid", True, st["technical_check"]["schema_valid"])
        p.gleich("retries", 0, st["technical_check"]["retries"])
        p.gleich("LLM-Reparaturaufrufe", 0, retry.n)
        p.gleich("INVARIANTE: K6-Eingangshash == K5-Huellenhash",
                 tr5["provenienz"]["response_sha256"],
                 tr6["input_digest"]["response_sha256_eingang"])
        p.gleich("H_before == H_after (kein Retry)",
                 tr6["provenienz"]["proposal_sha256_before"],
                 tr6["provenienz"]["proposal_sha256_after"])
        p.gleich("finale Huelle unveraendert",
                 tr5["provenienz"]["response_sha256"],
                 tr6["provenienz"]["response_sha256_final"])
        p.wahr("K7 bekommt den INNEREN Vorschlag, nicht die Huelle",
               "correction_proposal" not in (st["correction_proposal"] or {}),
               sorted(st["correction_proposal"] or {})[:4])
    finally:
        schema.retry_llm_with_schema_error, schema.get_storage = orig
    return p


def r9b_huelle_invalide_retry() -> Pruefung:
    """
    R9b — kontrolliert ECHT schema-invalide Huelle -> der Retry MUSS ausloesen, und danach
    muss die finale Huelle autoritativ sein.

    Der Gegenpol zu R9a. Ohne ihn liesse sich `retries=0` auch dadurch erreichen, dass die
    Pruefung gar nichts mehr prueft — ein Test, der nie anschlaegt, belegt nichts.

    Die Invaliditaet ist ECHT: `correction_proposal.action` fehlt, ein Pflichtfeld des
    inneren Modells. Kein kuenstlich entferntes Huellenfeld — sonst pruefte der Test wieder
    genau den Defekt, den BA-047 beseitigt hat.
    """
    p = Pruefung("R9b — invalide Huelle: Retry loest aus, finale Huelle ist autoritativ")

    kaputt = voll_huelle({"new_value": 1.0})
    del kaputt["correction_proposal"]["reasoning"]        # Pflichtfeld raus -> echt invalide
    repariert = voll_huelle({"action": "modify", "target_path": "articles[0].relDensity",
                             "new_value": 1.063, "reasoning": "nach Retry"})

    schema, retry, orig = _echte_schema_pruefung(retry_liefert=repariert)
    try:
        _echtheit_pruefen(p, schema)
        k6 = knoten_laden("technical_check")
        st = k6.node_technical_check(basis_state(
            correction_proposal=dict(kaputt["correction_proposal"]),
            correction_response=kaputt))
        tr6 = [t for t in st["trace"] if t["node"] == "technical_check"][-1]

        p.wahr("die Ausgangshuelle ist WIRKLICH schema-invalide",
               schema.validate_correction_proposal(kaputt)[0] is False,
               str(schema.validate_correction_proposal(kaputt)[2])[:120])
        p.gleich("LLM-Reparaturaufrufe", 1, retry.n)
        p.gleich("retries", 1, st["technical_check"]["retries"])
        p.gleich("schema_valid nach Retry", True, st["technical_check"]["schema_valid"])
        p.gleich("H_before != H_after", True,
                 tr6["provenienz"]["proposal_sha256_before"]
                 != tr6["provenienz"]["proposal_sha256_after"])
        p.gleich("retry_hat_vorschlag_geaendert", True,
                 tr6["provenienz"]["retry_hat_vorschlag_geaendert"])
        p.gleich("finale Huelle im State == Retry-Ergebnis", repariert,
                 st["correction_response"])
        p.gleich("finaler Huellen-Hash im Trace",
                 k6._sha256(repariert), tr6["provenienz"]["response_sha256_final"])
        p.gleich("K7 bekommt den FINALEN inneren Vorschlag", 1.063,
                 st["correction_proposal"]["new_value"])
        p.wahr("die Fehlermeldung nennt NICHT die Huellenfelder (kein Handoff-Artefakt)",
               all(f not in str(st["technical_check"]["errors"])
                   for f in ("iteration\n", "snapshot_id\n", "original_error\n")),
               str(st["technical_check"]["errors"])[:160])
    finally:
        schema.retry_llm_with_schema_error, schema.get_storage = orig
    return p


# --------------------------------------------------------------------- Runner
REGRESSIONEN = {
    "R1": r1_guard_mismatch,
    "R2": r2_missing_artifact_iteration,
    "R3": r3_vier_kombinationen,
    "R4": r4_hashkette_ohne_retry,
    "R5": r5_schema_retry,
    "R6": r6_mehrfachiteration,
    "R9A": r9a_huelle_valide_kein_retry,
    "R9B": r9b_huelle_invalide_retry,
}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None, help="Komma-Liste, z. B. R1,R2")
    ap.add_argument("--keine-umgebungspruefung", action="store_true",
                    help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    if not args.keine_umgebungspruefung:
        sys.path.insert(0, str(APP))
        from core.run_metadata import require_ba_env
        meta = require_ba_env("Graph-Handoff-Regressionen (BA-044)")
        u = meta["umgebung"]
        print(f"Umgebung: {u['sys_prefix']}  Pakete: {u['pakete']}")

    namen = list(REGRESSIONEN)
    if args.only:
        gewuenscht = {x.strip().upper() for x in args.only.split(",")}
        namen = [n for n in namen if n in gewuenscht]

    ergebnisse = []
    for n in namen:
        p = REGRESSIONEN[n]()
        p.drucken()
        ergebnisse.append((n, p.bestanden, p.anzahl))

    print("\n=== Zusammenfassung ===")
    for n, ok, (gut, alle) in ergebnisse:
        print(f"  {n}: {'PASS' if ok else 'FAIL'}  {gut}/{alle}")
    return 0 if all(ok for _, ok, _ in ergebnisse) else 1


if __name__ == "__main__":
    sys.exit(main())
