"""
Knoten 7 — Anwendung und Re-Validierung.

Beobachtungspunkt fuer **Kategorie 4: Folgefehlererzeugung** (BA_MASTERPLAN Kap. 15.1).

**Ohne diesen Knoten schliesst die Iterationsschleife nicht.** Er erzeugt `errors_after`; die
frueheren acht Knoten endeten beim Korrekturvorschlag, waehrend die bedingte Kante bereits nach
`errors_after` fragte — ein Loch, das bei AP-D3 geschlossen wurde (Kap. 9).

VIER SCHRITTE
-------------
    1. `apply_correction.run_apply()`          — anwenden, sichern, metadata.txt fortschreiben
    2. `update_snapshot.run_upload()`          — an den Server zurueckschreiben
    3. `trigger_server_validation()`           — neue Validierung AUSLOESEN **und abwarten**
    4. `validate_snapshot.validate_snapshot()` — Ergebnis abholen

Schritt 3 ist nicht optional und sein Rueckgabewert AUCH NICHT (Nachbesserung 19.08.2026):
`update_snapshot` LOESCHT die Meldungen auf dem Server, und der Server rechnet nicht von selbst
neu. `validate_snapshot` macht nur das GET. Ohne Trigger liest man eine leere Liste und meldet
`errors=0` — ein FALSCHES GRUEN (dokumentiert in `routes/server_validation.py`, AP3.3d).
`trigger_server_validation()` ist synchron: es pollt den Job bis `FINISHED` und liefert
`{"ok", "job_id", "status", "waited_s"}`. **Ist `ok` falsch, wird `errors_after` auf `None`
gesetzt — niemals auf 0.**

    errors_after = None -> keine belastbare neue Validierung (Job offen, gescheitert, Timeout)
    errors_after = 0    -> neue Validierung nachweislich abgeschlossen UND fehlerfrei

Derselbe Trigger sitzt seit dem 19.08. auch in `SPAgent._execute_pipeline()`, damit die
Bedingungen A, B und C dieselbe fachliche Re-Validierungssemantik haben (Kap. 7.1.1).
"""
import hashlib
import json
from datetime import datetime, timezone


def _fehler_identitaeten(meldungen):
    """
    Stabile Identitaet je Fehlermeldung, damit sich Fehlermengen VOR und NACH der Korrektur
    vergleichen lassen. Die Anzahl allein genuegt nicht: 1 -> 1 kann heissen "nichts passiert"
    oder "A behoben, B neu erzeugt" — fuer Kategorie 4 ist das ein Unterschied.

    Der Server liefert keine Fehler-ID. Als Ersatz: der `[validate_*]`-Tag plus die
    normalisierte Meldung. Das ist stabil genug fuer denselben Snapshot vor/nach einer
    Korrektur und wird als Naeherung ausgewiesen, nicht als echte ID.
    """
    ids = {}
    for m in meldungen or []:
        if str(m.get("level", "")).upper() != "ERROR":
            continue
        text = (m.get("message") or "").strip()
        tag = text.split("]")[0].lstrip("[") if text.startswith("[") else "OHNE_TAG"
        ids[hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]] = tag
    return ids


def node_apply_revalidate(state: dict) -> dict:
    """
    Liest:    state["snapshot_id"], state["correction_proposal"] (K5), state["technical_check"] (K6)
    Schreibt: state["applied"], state["errors_after"], state["final_validation"],
              haengt einen trace-Eintrag an.

    Beendet den Prozess NIE. Ein gescheitertes Anwenden, Hochladen oder Validieren ist ein
    Zustand; Knoten 8 entscheidet darueber.
    """
    import apply_correction as applier
    import update_snapshot as uploader
    import validate_snapshot as validator
    from routes.server_validation import trigger_server_validation
    from runtime_storage import get_storage

    begonnen = datetime.now(timezone.utc)
    sid = state["snapshot_id"]
    tc = state.get("technical_check") or {}
    storage = get_storage()
    fehler = []

    # --- Fehlermenge VOR der Korrektur festhalten (fuer Kategorie 4) ---
    vorher_meldungen = storage.load_json(f"{sid}/snapshot-validation.json") or []
    vorher_ids = _fehler_identitaeten(vorher_meldungen)

    # --- Proposal-Identitaet: der State ist die Wahrheit, nicht die Platte ---
    # `run_apply()` wuerde ohne Uebergabe den "neuesten" Vorschlag von Platte laden. Dann
    # koennte der State Vorschlag X tragen, angewendet wuerde aber Y.
    #
    # KORRIGIERT 20.08.2026 (gefunden im AP-D Gesamtsmoke).
    # Vorher baute dieser Knoten die Huelle selbst: {"correction_proposal": vorschlag}.
    # Das ist KEINE gueltige `LLMCorrectionResponse` - der Huelle fehlen vier Pflichtfelder
    # (`iteration`, `snapshot_id`, `original_error`, `error_analyzed`).
    # `apply_correction.validate_proposal_schema()` (`:83`) prueft aber genau dieses Modell und
    # ruft bei Verstoss `sys.exit(1)`. Ergebnis: Knoten 7 brach IMMER mit
    # "Schemapruefung abgebrochen (exit 1)" ab - der Graph-Pfad konnte nie anwenden, obwohl
    # Knoten 6 unmittelbar davor `schema_valid=True` meldete. Zwei Schemapruefungen, zwei
    # Urteile ueber denselben Vorschlag.
    #
    # In A und B laedt `apply_correction` die VOLLSTAENDIGE Huelle von Platte. Genau die wird
    # jetzt auch hier benutzt - gleiche Quelle, gleiches Schema, kein Sonderweg fuer C
    # (CLAUDE.md, Bauregel B). Die Staleness-Sorge von oben bleibt beantwortet, weil der
    # innere Vorschlag der Platte gegen den State geprueft und das Ergebnis protokolliert
    # wird: `proposal_identisch`. Weichen sie ab, wird NICHT angewendet.
    vorschlag = state.get("correction_proposal")
    # BA-043: die Artefaktnummer kommt aus dem State (Knoten 2), nicht aus der Rueckgabe
    # von Knoten 6 - die trug den eingefrorenen Wert des ersten Durchgangs (BA-042).
    iteration = state.get("artifact_iteration_number")
    proposal_hash = None
    proposal_identisch = None
    uebergeben = None

    # BA-044: DER GUARD STEHT VOR JEDEM DISK-ZUGRIFF, nicht dahinter.
    # BA-043 hat ihn erst unmittelbar vor `run_apply()` gesetzt - zwanzig Zeilen zu spaet.
    # Bei fehlender Artefaktnummer griff `load_correction_proposal(sid, None)` unten trotzdem
    # auf Platte zu (Pfad `iteration-None/...`). Auch `run_apply()` selbst wuerde bei
    # `iteration_number=None` die neueste Iteration aufloesen (apply_correction.py:544-545)
    # und einen fehlenden Vorschlag von Platte nachladen (:550-552). Beide Wege sind fuer
    # CLI/A/B richtig und bleiben dort unveraendert; im Graph-Pfad sind sie der stille
    # Fallback, den BA-043 ausschliessen wollte.
    #
    # Fehlt die Nummer: kein Disk-Fallback, kein Apply, kein Upload, keine Revalidierung.
    nummer_fehlt = iteration is None
    if nummer_fehlt:
        fehler.append(
            "apply: artifact_iteration_number fehlt - kein Disk-Zugriff, kein Apply. "
            "Im Graph-Pfad ist das ein Fehlerzustand, kein latest-Fallback (BA-044).")
    elif vorschlag is not None:
        if "correction_proposal" in vorschlag:
            uebergeben = vorschlag                      # schon eine vollstaendige Huelle
            proposal_identisch = True
        else:
            huelle = applier.load_correction_proposal(sid, iteration)
            innen = (huelle or {}).get("correction_proposal")
            proposal_identisch = (innen == vorschlag)
            if proposal_identisch:
                uebergeben = huelle
            else:
                fehler.append(
                    "apply: Vorschlag auf Platte weicht vom autoritativen State ab - "
                    "NICHT angewendet (BA-043)")
        if uebergeben is not None:
            proposal_hash = hashlib.sha256(
                json.dumps(uebergeben, sort_keys=True, ensure_ascii=False).encode("utf-8")
            ).hexdigest()

    # --- 1. Anwenden ---
    # BA-043: Der Guard muss WIRKLICH blockieren. Vorher wurde bei einem Mismatch `None`
    # weitergereicht - und `run_apply(None)` laedt dann selbst von Platte nach. Der Guard
    # meldete also nur und verhinderte nichts; in P04/P10 wurde genau der Vorschlag
    # angewendet, den er verworfen hatte. Im Graph-Pfad ist `None` ab jetzt KEIN
    # versteckter Ladebefehl: kein Vorschlag heisst kein Apply.
    #
    # BA-044: Die vier Vorabzuweisungen von `hochladen`, `trigger` und `errors_after`, die
    # BA-043 hier gesetzt hatte, sind ERSATZLOS entfallen. Sie waren wirkungslos - die
    # Bloecke 2 und 3 setzen dieselben Namen unmittelbar danach ohnehin neu. Regression 1
    # hat das bestaetigt (uploaded=False, revalidation_ok=None, errors_after=None), aber
    # toter Code, der zufaellig richtig liegt, ist kein Guard. Die Blockade traegt allein
    # `uebergeben is None`.
    if uebergeben is None:
        # Grund steht bereits in `fehler` (Nummer fehlt ODER Drift ODER kein Vorschlag) -
        # er wird NICHT ein zweites Mal angehaengt.
        anwenden = {"applied_ok": False, "error": (fehler[-1] if fehler else
                    "apply: kein autoritativer Vorschlag im State - nicht angewendet")}
    else:
        anwenden = applier.run_apply(sid, iteration_number=iteration,
                                     correction_proposal=uebergeben)
        if not anwenden["applied_ok"]:
            fehler.append(f"apply: {anwenden['error']}")

    # --- 2. Hochladen ---
    hochladen = {"uploaded": False, "response": None,
                 "error": "uebersprungen (apply fehlgeschlagen)"}
    if anwenden["applied_ok"]:
        hochladen = uploader.run_upload(sid)
        if not hochladen["uploaded"]:
            fehler.append(f"upload: {hochladen['error']}")

    # --- 3./4. Ausloesen, ABWARTEN, abholen ---
    errors_after, nachher_meldungen, trigger = None, [], None
    if hochladen["uploaded"]:
        try:
            trigger = trigger_server_validation(sid)
            if trigger.get("ok"):
                validator.validate_snapshot(sid)
                nachher_meldungen = storage.load_json(f"{sid}/snapshot-validation.json") or []
                errors_after = sum(1 for m in nachher_meldungen
                                   if str(m.get("level", "")).upper() == "ERROR")
            else:
                # KEIN falsches Gruen: lieber keine Zahl als eine veraltete.
                fehler.append(f"revalidate: Job nicht erfolgreich "
                              f"(status={trigger.get('status')}, {trigger.get('error')})")
        except Exception as exc:
            fehler.append(f"revalidate: {type(exc).__name__}: {exc}")

    # --- Fehlermengen vergleichen (Kategorie 4) ---
    nachher_ids = _fehler_identitaeten(nachher_meldungen) if errors_after is not None else {}
    behoben = sorted(set(vorher_ids) - set(nachher_ids)) if errors_after is not None else None
    verblieben = sorted(set(vorher_ids) & set(nachher_ids)) if errors_after is not None else None
    neu = sorted(set(nachher_ids) - set(vorher_ids)) if errors_after is not None else None

    state["applied"] = {
        "applied_ok": anwenden["applied_ok"],
        "uploaded": hochladen["uploaded"],
        "proposal_sha256": proposal_hash,
                         "proposal_identisch": proposal_identisch,
        "proposal_aus_state": vorschlag is not None,
        "revalidation": trigger,
        "errors_resolved": len(behoben) if behoben is not None else None,
        "errors_remaining": len(verblieben) if verblieben is not None else None,
        "errors_new": len(neu) if neu is not None else None,
        "new_error_types": sorted({nachher_ids[i] for i in (neu or [])}),
        "errors": fehler,
    }
    state["errors_after"] = errors_after
    # Getrennt von `initial_validation` aus Knoten 1 - siehe graph_state.py.
    state["final_validation"] = nachher_meldungen

    dauer_ms = int((datetime.now(timezone.utc) - begonnen).total_seconds() * 1000)
    state.setdefault("trace", []).append({
        "node": "apply_revalidate",
        "timestamp_utc": begonnen.isoformat(),
        "duration_ms": dauer_ms,
        "input_digest": {"schema_valid": tc.get("schema_valid"),
                         "iteration": iteration,
                         "proposal_sha256": proposal_hash,
                         "proposal_identisch": proposal_identisch,
                         "proposal_aus_state": vorschlag is not None},
        "output_digest": {"applied_ok": anwenden["applied_ok"],
                          "uploaded": hochladen["uploaded"],
                          "revalidation_ok": (trigger or {}).get("ok"),
                          "revalidation_job": str((trigger or {}).get("job_id"))[:8],
                          "revalidation_waited_s": (trigger or {}).get("waited_s"),
                          "errors_before": len(vorher_ids),
                          "errors_after": errors_after,
                          "errors_resolved": state["applied"]["errors_resolved"],
                          "errors_remaining": state["applied"]["errors_remaining"],
                          "errors_new": state["applied"]["errors_new"],
                          "new_error_types": state["applied"]["new_error_types"],
                          "fehler": fehler},
    })
    return state
