"""
Knoten 8 — Ergebnisbewertung.

**Bewusst ein KNOTEN, keine Kante** (BA_MASTERPLAN Kap. 9). Eine Kante hinterlaesst keinen
Zwischenzustand, auf den man zeigen kann; fuer eine Arbeit ueber Nachvollziehbarkeit ist das
die schlechtere Wahl. Als Knoten schreibt die Bewertung `decision` samt Begruendung in den
State — der Router danach liest nur noch `decision["action"]` und enthaelt KEINE Fachlogik.

Damit ist jede Verzweigung im `trace` begruendet nachlesbar. Ein Router mit eingebauter
if/else-Kette waere wieder genau der implizite Kontrollfluss, den die Arbeit dem Monolithen
vorwirft.

Beobachtungspunkt fuer das **UF2-Grenzfallverhalten**: `stop_uncertain` ist der positiv zu
wertende "ehrliches Nein statt halluzinierter Korrektur"-Pfad (Kap. 15.3).
"""
from datetime import datetime, timezone

#: Muss mit graph_state.DECISION_ACTIONS uebereinstimmen.
ACTIONS = ("continue", "stop_valid", "stop_max_iter", "stop_uncertain")


def node_evaluation(state: dict) -> dict:
    """
    Liest:    technical_check (K6), applied/errors_after (K7), correction_proposal (K5),
              iteration, max_iterations
    Schreibt: state["decision"], ggf. state["manual_intervention_required"],
              haengt einen trace-Eintrag an.

    DER ENTSCHEIDUNGSVERTRAG (umgekehrt am 21.08.2026, BA-044)
    ----------------------------------------------------------
    **Nur eine VOLLSTAENDIG POSITIV BELEGTE technische Verarbeitung darf zu `stop_valid`,
    `continue` oder `stop_max_iter` fuehren.** Alles andere ist `stop_uncertain`.

    Das ist die Umkehr der Beweislast, und sie ist der Kern der Korrektur. Vorher fragte
    dieser Knoten "ist Knoten 7 gelaufen UND hat er versagt?" — ueber `k7_gelaufen =
    bool(applied)`, an dem alle vier Unsicherheitszweige hingen. Fehlte `applied` GANZ, war
    die Vorbedingung falsch, saemtliche Zweige wurden uebersprungen und der Ablauf fiel
    durch bis auf `continue`. **Fehlende Evidenz wurde als Unbedenklichkeit gelesen.**
    Dieselbe Klasse Fehler wie das falsche Gruen aus BA-021, nur eine Ebene hoeher: dort
    galt eine VERALTETE Zahl als gueltig, hier eine FEHLENDE.

    Die erste zutreffende Regel gewinnt — auch wenn mehrere Bedingungen wahr sind:

      STUFE 1 — technische/operative Unsicherheit  -> stop_uncertain
        1a. `schema_valid is not True` — Knoten 6 hat seine Retries INTERN erschoepft
            (Kap. 11, es gibt keine Rueckkante 6->5). Steht VOR 1b, weil dies der
            legitime Pfad Knoten 6 -> Knoten 8 ist (bedingte Kante A): dort fehlt
            `applied` als FOLGE, nicht als Ursache — der Schemafehler ist die Ursache
            und gehoert in die Begruendung.
        1b. **kein `applied` im State** — Knoten 7 hat nichts hinterlassen. Ohne seinen
            Nachweis ist ueber Anwenden, Hochladen und Re-Validierung NICHTS bekannt.
        1c. kein Vorschlag / kein `target_path` (reale Faehigkeitsluecke, ehrliches Nein)
        1d. `applied_ok is not True`      — Anwenden nicht positiv belegt
        1e. `uploaded is not True`        — Hochladen nicht positiv belegt
        1f. `revalidation_ok is not True` — Re-Validierungsjob nicht positiv belegt
        1g. `errors_after is None`        — keine belastbare neue Fehlerzahl
      STUFE 2 — `errors_after == 0`                              -> stop_valid
      STUFE 3 — Fehler vorhanden UND Iterationslimit erreicht    -> stop_max_iter
      STUFE 4 — Fehler vorhanden                                 -> continue (Rueckkante 8->2)

    **`is not True` statt `not x`** in 1d-1f: `None` (nie gesetzt) und `False` (gescheitert)
    muessen beide blockieren, und ein fehlender Schluessel darf nicht als Erfolg gelten.

    **Stufe 1 schlaegt Stufe 2.** `applied_ok=False` zusammen mit `errors_after=0` ergibt
    `stop_uncertain`, nicht `stop_valid` — eine 0, die nach einem gescheiterten Anwenden
    gemessen wurde, belegt nichts.

    **`errors_after is None` ist NICHT dasselbe wie 0** (1g):
        None -> keine belastbare neue Validierung (Job offen, gescheitert, Timeout)
        0    -> Validierung nachweislich abgeschlossen UND fehlerfrei
    Ohne diese Unterscheidung waere jedes falsche Gruen ein `stop_valid`.

    **1f ist neu (BA-044).** `revalidation_ok` kam in dieser Kette bisher UEBERHAUPT nicht
    vor; 1g fing den Fall nur mit ab, solange Knoten 7 die Kopplung "Job nicht ok =>
    errors_after None" einhaelt. Das war eine unausgesprochene Abhaengigkeit zwischen zwei
    Knoten. Sie ist jetzt explizit — an den in BA-036 archivierten P04/P10-Verlaeufen
    aendert das nichts, weil dort in jedem `continue`-Durchgang `revalidation_ok=True` war.
    """
    begonnen = datetime.now(timezone.utc)

    tc = state.get("technical_check") or {}
    applied_roh = state.get("applied")
    applied = applied_roh or {}
    vorschlag = state.get("correction_proposal") or {}
    errors_after = state.get("errors_after")
    iteration = state.get("iteration", 0)
    max_iter = state.get("max_iterations", 5)
    # BA-044: `k7_gelaufen = bool(applied)` ist ERSATZLOS entfallen. Es war die falsche
    # Vorbedingung — nicht der einzelne Vergleich war falsch, sondern die Frage davor.
    # Statt "ist K7 gelaufen und hat versagt?" fragt der Knoten jetzt "ist positiv belegt,
    # dass K7 erfolgreich war?". Fehlt `applied`, ist die Antwort NEIN, nicht "egal".
    k7_hat_belegt = isinstance(applied_roh, dict) and bool(applied_roh)
    # Der Re-Validierungsjob. Knoten 7 legt ihn unter `applied["revalidation"]` ab; `None`
    # heisst "nie ausgeloest oder Exception", `{"ok": False}` heisst "ausgeloest, nicht ok".
    revalidation_ok = (applied.get("revalidation") or {}).get("ok")

    # ---- STUFE 1: technische und operative Unsicherheit ----
    if tc.get("schema_valid") is not True:
        action, grund = "stop_uncertain", (
            f"Schemapruefung nicht positiv belegt (schema_valid={tc.get('schema_valid')!r}) "
            f"nach {tc.get('retries', 0)} Retry(s). Knoten 6 hat seine Versuche intern "
            f"erschoepft; eine erneute Generierung fuer denselben Schemafehler ist nicht "
            f"vorgesehen.")
    elif not k7_hat_belegt:
        action, grund = "stop_uncertain", (
            "Knoten 7 hat keinen Verarbeitungsnachweis hinterlassen (`applied` fehlt). Ueber "
            "Anwenden, Hochladen und Re-Validierung ist damit NICHTS bekannt. Fehlende "
            "Evidenz gilt nicht als Erfolg (BA-044).")
    elif not vorschlag or not vorschlag.get("target_path"):
        action, grund = "stop_uncertain", (
            "Kein verwertbarer Korrekturvorschlag: target_path fehlt. Bekannte "
            "Faehigkeitsluecke — es wird bewusst KEINE Korrektur erzwungen.")
    elif applied.get("applied_ok") is not True:
        action, grund = "stop_uncertain", (
            f"Anwenden nicht positiv belegt (applied_ok={applied.get('applied_ok')!r}): "
            f"{applied.get('errors')}")
    elif applied.get("uploaded") is not True:
        action, grund = "stop_uncertain", (
            f"Hochladen nicht positiv belegt (uploaded={applied.get('uploaded')!r}): "
            f"{applied.get('errors')}")
    elif revalidation_ok is not True:
        action, grund = "stop_uncertain", (
            f"Re-Validierung nicht positiv belegt (revalidation_ok={revalidation_ok!r}). "
            f"Ohne erfolgreich abgeschlossenen Validierungsjob ist jede Fehlerzahl danach "
            f"unbelegt. Details: {applied.get('errors')}")
    elif errors_after is None:
        action, grund = "stop_uncertain", (
            "Keine belastbare Re-Validierung: `errors_after` bleibt unbelegt, obwohl der Job "
            "als erfolgreich gemeldet wurde — eine 0 waere hier ein falsches Gruen. "
            f"Details: {applied.get('errors')}")
    # ---- STUFE 2: nachweislich fehlerfrei ----
    elif errors_after == 0:
        neu = applied.get("errors_new")
        action, grund = "stop_valid", (
            f"Re-Validierung abgeschlossen und fehlerfrei (0 Fehler; "
            f"{applied.get('errors_resolved')} behoben, {neu} neu).")
    # ---- STUFE 3: Limit erreicht ----
    elif iteration >= max_iter:
        action, grund = "stop_max_iter", (
            f"Maximale Iterationen erreicht ({iteration}/{max_iter}), verbleibende Fehler: "
            f"{errors_after} (davon {applied.get('errors_new')} neu erzeugt).")
        state["manual_intervention_required"] = True
    # ---- STUFE 4: weiter ----
    else:
        action, grund = "continue", (
            f"Noch {errors_after} Fehler nach Iteration {iteration} "
            f"({applied.get('errors_resolved')} behoben, {applied.get('errors_new')} neu); "
            f"neue FACHLICHE Iteration ueber Knoten 2.")

    state["decision"] = {"action": action, "reasoning": grund,
                         "iteration": iteration, "errors_after": errors_after}
    if action.startswith("stop"):
        state["finished_at"] = datetime.now(timezone.utc).isoformat()

    dauer_ms = int((datetime.now(timezone.utc) - begonnen).total_seconds() * 1000)
    state.setdefault("trace", []).append({
        "node": "evaluation",
        "timestamp_utc": begonnen.isoformat(),
        "duration_ms": dauer_ms,
        "input_digest": {"schema_valid": tc.get("schema_valid"),
                         "hat_target_path": bool(vorschlag.get("target_path")),
                         # BA-044: beide neu - ohne sie liesse sich im Trace nicht
                         # nachlesen, WELCHE Stufe gegriffen hat.
                         "k7_hat_belegt": k7_hat_belegt,
                         "applied_ok": applied.get("applied_ok"),
                         "uploaded": applied.get("uploaded"),
                         "revalidation_ok": revalidation_ok,
                         "errors_after": errors_after,
                         "iteration": iteration, "max_iterations": max_iter},
        "output_digest": {"action": action, "reasoning": grund},
    })
    return state


def route_after_evaluation(state: dict) -> str:
    """
    Bedingte Kante B (Kap. 11). **Enthaelt keine Fachlogik** — sie liest nur das Feld, das
    Knoten 8 gesetzt hat. Genau darin liegt der Unterschied zum impliziten Kontrollfluss
    des Monolithen.
    """
    action = (state.get("decision") or {}).get("action", "stop_uncertain")
    return "classification" if action == "continue" else "answer"
