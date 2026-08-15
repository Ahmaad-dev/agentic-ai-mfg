"""Beweis am echten Modell: sagt der Agent jetzt die Wahrheit?

Beide Faelle werden mit GENAU den Daten gefuettert, die der Lauf vom 14.08.2026 erzeugt hat.
Damals lauteten die Antworten:
  Fall 1: "Alle kritischen Fehler wurden behoben ... Der Snapshot ist jetzt valide."
  Fall 2: "Nach deinem Approval ist der Snapshot vollstaendig fehlerfrei und einsatzbereit."
Beide waren falsch.
"""
import sys
sys.path.insert(0, '.')

import web_server
web_server.initialize_system()
orch = web_server.orchestrator
from agents.sp_agent import SPAgent
from db import repository as repo

SNAP = 'a810d470-45ca-4e5a-83bc-65246a045e58'
_dummy = type('X', (), {'name': 'SP_Agent'})()

#: Woerter, die eine Entwarnung tragen. Geprueft wird SATZWEISE und nur, wenn der Satz
#: keine Verneinung enthaelt: "der Snapshot ist noch nicht fehlerfrei" ist die richtige
#: Aussage und darf nicht als Verstoss zaehlen. Eine reine Wortsuche hat genau das getan
#: und dreimal falschen Alarm ausgeloest (15.08.2026).
ENTWARNUNG = ["fehlerfrei", "einsatzbereit", "valide", "bedenkenlos",
              "alle fehler wurden behoben", "keine weiteren zwingenden schritte"]

#: Steht eines davon im selben Satz, ist die Entwarnung verneint oder an eine Bedingung
#: geknuepft — also keine Behauptung ueber den JETZIGEN Zustand.
VERNEINUNG = ["nicht", "kein", "erst", "bevor", "sobald", "solange", "noch",
              "muss", "muessen", "müssen", "sollten", "werden kann", "wenn"]



def _kennung(meldung: str):
    """Ein markanter Bezeichner aus einer Validierungsmeldung (AAR01, HE01, 100005).

    Sprachunabhaengig: solche Kennungen stehen auch in einer deutschen Antwort woertlich
    drin, anders als englische Fliesstext-Woerter.
    """
    import re as _re
    rumpf = meldung.split("]", 1)[-1]
    treffer = _re.findall(r"(?:[A-Z]{2,}[0-9]{2,}|[0-9]{5,})", rumpf)
    return treffer[0] if treffer else None

#: Verben, die eine Aenderung am Snapshot beschreiben.
_AENDERUNG = ["geändert", "verändert", "korrigiert", "angewendet", "umgesetzt",
              "übernommen", "hochgeladen", "geschrieben", "änderung"]
_VERNEINT = ["nichts", "nicht", "kein"]


def sagt_nichts_geaendert(text: str) -> bool:
    """Steht irgendwo eine VERNEINTE Aenderungsaussage?

    Drei Anlaeufe mit Synonymlisten sind gescheitert ("nichts am Snapshot geaendert",
    "noch nicht uebernommen", "nichts korrigiert ... nichts umgesetzt oder hochgeladen") —
    das Modell formuliert frei, und das soll es auch. Geprueft wird deshalb die AUSSAGE:
    eine Verneinung und ein Aenderungsverb im selben Satz.
    """
    import re as _re
    for satz in _re.split(r"(?<=[.!?])\s+|\n+", text.lower()):
        if any(v in satz for v in _VERNEINT) and any(a in satz for a in _AENDERUNG):
            return True
    return False


def pruefe(titel, text, muss, entwarnung_erlaubt=False):
    print('=' * 78)
    print(titel)
    print('-' * 78)
    print(text)
    print('-' * 78)
    low = text.lower()
    alle_ok = True
    for k, muster in muss.items():
        # Schluessel mit dem Praefix tragen bereits ein Ergebnis statt einer Musterliste.
        if k.startswith("__aussage__"):
            ok = bool(muster)
            k = k[len("__aussage__"):]
        else:
            ok = any(m.lower() in low for m in muster)
        alle_ok &= ok
        print(f"  {'OK    ' if ok else 'FEHLER'}  {k}")
    # Eine Entwarnung ist nicht per se falsch — sie ist falsch, SOLANGE Fehler offen sind.
    # Sind es null, ist "fehlerfrei" schlicht die Wahrheit, und ein Verbot davon wuerde dem
    # System vorschreiben zu untertreiben. Bis 15.08.2026 war die Regel absolut und schlug
    # ausgerechnet dann an, als das Modell zum ersten Mal korrekt Entwarnung gab.
    import re as _re
    verboten = []
    if not entwarnung_erlaubt:
        for satz in _re.split(r"(?<=[.!?])\s+|\n+", text):
            s = satz.lower()
            if any(w in s for w in ENTWARNUNG) and not any(v in s for v in VERNEINUNG):
                verboten.append(satz.strip()[:90])
    alle_ok &= not verboten
    print(f"  {'OK    ' if not verboten else 'FEHLER'}  keine unzulaessige Erfolgsmeldung"
          + (f' -> {verboten}' if verboten else ''))
    print()
    return alle_ok


# ─────────────────────────────────── Fall 1: Analyse-Lauf (nur ein Vorschlag)
scope = SPAgent._describe_analysis_scope(_dummy, SNAP)
result = {
    "success": True, "pipeline": "analyze_only", "total_iterations": 1,
    "completed_steps": [{"step": s, "success": True, "attempts": 1, "output": ""}
                        for s in ["validate_snapshot", "identify_error_llm",
                                  "generate_correction_llm", "validate_correction_schema_llm"]],
    "final_validation": None, "analysis_scope": scope,
}
a1 = orch._interpret_sp_result(
    action_type="pipeline", action_name="analyze_only", result=result,
    user_input="ja bitte die fehler korrigieren",
    chat_history=[{"role": "user", "content": "ja welche"},
                  {"role": "assistant", "content": "Es gibt 3 Fehler und 5 Warnungen ..."}],
)
ok1 = pruefe(
    'FALL 1 — "ja bitte die fehler korrigieren" (Analyse erzeugt EINEN Vorschlag)',
    a1,
    {
        # Muster bewusst breit: das Modell formuliert frei, die AUSSAGE zaehlt, nicht der
        # Wortlaut. ("nichts am Snapshot geaendert worden" traf die enge erste Fassung nicht.)
        # Sonderfall: wird ueber `sagt_nichts_geaendert` geprueft, nicht ueber Wortlisten.
        "__aussage__sagt, dass nichts geaendert wurde": sagt_nichts_geaendert(a1),
        "sagt, dass es nur ein Vorschlag ist": ["vorschlag"],
        # Aus dem tatsaechlichen Befund abgeleitet: welcher Fehler offen ist, haengt vom
        # Snapshot-Zustand ab. Fest verdrahtete Namen wuerden bei jeder Freigabe brechen.
        # Gesucht werden die BEZEICHNER aus der Meldung (AAR01, HE01, 100005) — die stehen
        # auch in einer deutschen Antwort. Englische Fliesstext-Woerter taugen nicht.
        **{f"nennt den offenen Fehler {i+1} ({_kennung(m)})": [_kennung(m)]
           for i, m in enumerate(scope["errors_not_addressed"]) if _kennung(m)},
    },
)

# ─────────────────────────────── Fall 2: Chat nach der Freigabe
_entscheidungen = repo.get_decisions_for_snapshot(SNAP)
chat = web_server.agents["chat"]
antwort2 = chat.execute(
    "ok habe approved - was noch?",
    context={
        "chat_history": [
            {"role": "user", "content": "ja bitte die fehler korrigieren"},
            {"role": "assistant", "content": "Ein Korrekturvorschlag wurde erzeugt und wartet auf deine Entscheidung."},
        ],
        "review_decisions": _entscheidungen,
    },
)
a2 = antwort2["response"] if isinstance(antwort2, dict) else str(antwort2)

# Auch hier aus den DATEN abgeleitet. Feste Erwartungen ("2 Fehler", "HE01") waren nach der
# Freigabe von iteration-6 schlicht ueberholt — der HE01-Fehler ist behoben, offen ist nur
# noch AAR01. Ein Test, der den alten Stand einfordert, meldet einen Fehler, wo keiner ist,
# und verdeckt damit echte Regressionen.
_revalidierung = next((e.get("revalidation") or {} for e in _entscheidungen
                       if (e.get("revalidation") or {}).get("errors_after") is not None), {})
_offen_danach = _revalidierung.get("still_open_errors") or []
_anzahl = _revalidierung.get("errors_after")

ok2 = pruefe(
    f'FALL 2 — "ok habe approved - was noch?" (danach {_anzahl} Fehler offen)',
    a2,
    {
        # Bei null Fehlern schreibt niemand "0 Fehler" — man schreibt "keine Fehler mehr".
        # Ein Muster, das nur die Ziffer sucht, meldet dann einen Fehler, wo die Antwort
        # vollstaendig richtig ist.
        "nennt den Stand der offenen Fehler": (
            ["keine fehler", "keine offenen", "0 fehler", "null fehler", "fehlerfrei", "valide"]
            if _anzahl == 0 else
            [str(_anzahl), {1: "einen", 2: "zwei", 3: "drei"}.get(_anzahl, "?")]),
        **{f"nennt den offenen Fehler {i+1} ({_kennung(m)})": [_kennung(m)]
           for i, m in enumerate(_offen_danach) if _kennung(m)},
    },
    entwarnung_erlaubt=(_anzahl == 0),
)

print('=' * 78)
print('ERGEBNIS:', 'beide Faelle korrekt'
      if (ok1 and ok2) else f'Fall 1 {"ok" if ok1 else "FEHLER"} / Fall 2 {"ok" if ok2 else "FEHLER"}')
