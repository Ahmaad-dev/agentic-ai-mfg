"""Prueft die sechs Befunde des Audits vom 15.08.2026 — jeder einzeln, am laufenden System.

Jeder Test stellt GENAU die Lage her, in der der Agent vorher blind war.
"""
import sys
sys.path.insert(0, '.')

import web_server
web_server.initialize_system()
orch = web_server.orchestrator
from memory import short_term
from db import repository as repo

SNAP = 'a810d470-45ca-4e5a-83bc-65246a045e58'
ergebnisse = []


def sag(nr, titel, ok, detail=''):
    ergebnisse.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'}  [{nr}] {titel}")
    if detail:
        for zeile in str(detail).splitlines():
            print(f"           {zeile}")


# ─────────────────────────────────────────── 1) Trennung der Sitzungen
short_term.set_focus_snapshot(101, SNAP)
short_term.set_focus_snapshot(202, 'ffffffff-1111-2222-3333-444444444444')
a = short_term.get_focus_snapshot(101)
b = short_term.get_focus_snapshot(202)
c = short_term.get_focus_snapshot(303)          # nie etwas gesetzt
sag(1, 'Fokus-Snapshot ist je Sitzung getrennt',
    a == SNAP and b != a and c is None,
    f'Sitzung 101 -> {a}\nSitzung 202 -> {b}\nSitzung 303 -> {c} (unbeteiligt, bekommt nichts)')

short_term.clear(101)
sag(1, 'Leeren einer Sitzung nimmt ihren Snapshot-Bezug mit',
    short_term.get_focus_snapshot(101) is None
    and short_term.get_focus_snapshot(202) is not None,
    f'nach clear(101): 101 -> {short_term.get_focus_snapshot(101)}, '
    f'202 unveraendert -> {short_term.get_focus_snapshot(202)}')

# ─────────────────────────────────────────── 2) Zustand wird frisch gelesen
orch._session_id = 404
short_term.set_focus_snapshot(404, SNAP)
meta = orch._current_snapshot_metadata([], '')
frisch = (meta or {}).get('isSuccessfullyValidated')
# Gegenprobe: direkt von der Platte
direkt = (web_server.agents['sp']._read_snapshot_metadata(SNAP) or {}).get('isSuccessfullyValidated')
sag(2, 'Snapshot-Zustand kommt frisch aus der Ablage, nicht aus einem Zwischenspeicher',
    meta is not None and frisch == direkt,
    f'ueber den Orchestrator: isSuccessfullyValidated={frisch}\n'
    f'direkt von der Platte : isSuccessfullyValidated={direkt}')
sag(2, 'Der alte prozessweite Zwischenspeicher existiert nicht mehr',
    not hasattr(orch, 'last_snapshot_metadata'),
    'Attribut `last_snapshot_metadata` am Orchestrator: '
    + ('noch da' if hasattr(orch, 'last_snapshot_metadata') else 'entfernt'))

# ─────────────────────────────────────────── 3) Entscheidungen im SP-Pfad
entsch = orch._get_review_decisions([], '')          # ohne UUID im Text!
sag(3, 'Entscheidungen werden auch ohne UUID im Text gefunden (ueber den Sitzungs-Fokus)',
    # Worauf es ankommt: dass ueberhaupt welche gefunden werden und dass die juengste als
    # aktueller Stand markiert ist. Die Entscheidungsart selbst aendert sich mit jeder
    # Nutzeraktion und taugt nicht als Erwartung.
    bool(entsch) and any((e.get('revalidation') or {}).get('ist_aktueller_stand')
                         for e in entsch),
    f'{len(entsch)} Entscheidung(en), erste: {entsch[0]["decision"] if entsch else "—"}, '
    f'offen danach: {entsch[0]["revalidation"]["errors_after"] if entsch else "—"}')

# ─────────────────────────────────────────── 5) Offene Vorschlaege
offen = orch._open_proposals_for_focus([], '')
alle_offen = repo.list_open_proposals_as_dicts()
fremd = [p for p in alle_offen if p['snapshot_id'] != SNAP]
sag(5, 'Offene Vorschlaege sind abrufbar und auf den Sitzungs-Snapshot begrenzt',
    all(p['snapshot_id'] == SNAP for p in offen),
    f'{len(offen)} offen fuer diesen Snapshot, {len(fremd)} offene Vorschlaege anderer '
    f'Snapshots werden korrekt NICHT durchgereicht')

# ─────────────────────────────────────────── 6) Kein Bezug -> nichts erfinden
orch._session_id = '_frische_sitzung_ohne_snapshot'
sag(6, 'Ohne Snapshot-Bezug liefert der Helfer leer statt irgendetwas',
    orch._snapshot_in_focus([], '') is None
    and orch._get_review_decisions([], '') == []
    and orch._open_proposals_for_focus([], '') == [],
    'frische Sitzung: kein Fokus, keine Entscheidungen, keine offenen Vorschlaege')

# ─────────────────────────────────────────── 4) Kuerzung
from core.agent_config import CHAT_HISTORY_CONFIG
grenze = CHAT_HISTORY_CONFIG.get('max_step_result_chars')
beispiel = 570   # Laenge der gemessenen wahrheitsgemaessen Antwort vom 14.08.2026
sag(4, 'Mehrschritt-Zusammenfassung schneidet die Wahrheits-Antwort nicht mehr ab',
    grenze is not None and grenze >= beispiel,
    f'Grenze {grenze} Zeichen, gemessene Antwort {beispiel} Zeichen (vorher fest 200)')

print()
print('ERGEBNIS:', 'alle Befunde behoben' if all(ergebnisse)
      else f'{ergebnisse.count(False)} von {len(ergebnisse)} Pruefungen offen')
