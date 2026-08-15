"""Prueft die vier Architektur-Optimierungen vom 15.08.2026."""
import sys
sys.path.insert(0, '.')

import web_server
web_server.initialize_system()
orch = web_server.orchestrator
from memory import short_term
from agents.sp_agent import SPAgent
import core.agent_config as cfg

SNAP = 'a810d470-45ca-4e5a-83bc-65246a045e58'
ok_alle = []


def sag(nr, titel, ok, detail=''):
    ok_alle.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'}  [{nr}] {titel}")
    for z in str(detail).splitlines():
        if z:
            print(f"           {z}")


# ═══════════════════════════════ 1) Herkunft im Verlauf
h = [{'role': 'user', 'content': 'welche fehler?', 'agent_name': None},
     {'role': 'assistant', 'content': '3 Fehler, 5 Warnungen', 'agent_name': 'sp'},
     {'role': 'assistant', 'content': 'alles bestens', 'agent_name': 'Chat'},
     {'role': 'assistant', 'content': 'ohne herkunft', 'agent_name': 'Unknown'}]
msgs = short_term.as_llm_messages(h)
sag(1, 'Werkzeug-Ergebnis und Gespräch sind im Verlauf unterscheidbar',
    msgs[1]['content'].startswith('[Werkzeug-Ergebnis]')
    and msgs[2]['content'].startswith('[Gespräch]')
    and msgs[0]['content'] == 'welche fehler?',
    '\n'.join(f"{m['role']:9} | {m['content']}" for m in msgs))
sag(1, 'Unbekannte Herkunft bekommt KEIN erfundenes Etikett',
    msgs[3]['content'] == 'ohne herkunft')
sag(1, 'Nur role/content — die Chat-Completions-Schnittstelle akzeptiert das',
    all(set(m) == {'role', 'content'} for m in msgs))

# ═══════════════════════════════ 2) Chat/RAG antworten direkt
quelle = __import__('pathlib').Path('agents/orchestration_agent.py').read_text(encoding='utf-8')
sag(2, 'Chat und RAG werden durchgereicht statt nachformuliert',
    'if agent_key in ("email", "chat", "rag"):' in quelle)
for name, p in [('Chat', cfg.DEFAULT_CHAT_SYSTEM_PROMPT), ('RAG', cfg.DEFAULT_RAG_SYSTEM_PROMPT)]:
    sag(2, f'{name}-Prompt trägt die Regeln, die vorher nur in der Schicht standen',
        all(r in p for r in ['DU ANTWORTEST DIREKT', 'HERKUNFT FRUEHERER',
                             'NUR BEHAUPTEN, WAS BELEGT', 'KEINE TECHNISCHEN PFADE'])
        and 'aufbereitet' not in p)
sag(2, 'SP behält die Schicht — dort entsteht die Antwort erst aus dem Werkzeugergebnis',
    'def _interpret_sp_result' in quelle and '"chat", "rag"' in quelle)

# ═══════════════════════════════ 3) Ein LLM-Aufruf weniger
faelle = [
    ({'agent': 'sp', 'action': 'download_snapshot'}, 'tool/download_snapshot'),
    ({'agent': 'sp', 'action': 'full_correction Pipeline'}, 'pipeline/full_correction'),
    ({'agent': 'sp', 'action': 'validiere und korrigiere'}, None),
    ({'agent': 'chat', 'action': 'download_snapshot'}, None),
    (None, None),
]
zeilen, alle_ok = [], True
for plan, erwartet in faelle:
    r = orch._intent_from_plan(plan, 'abc-123')
    ist = f"{r['action_type']}/{r['action_name']}" if r else None
    alle_ok &= (ist == erwartet)
    zeilen.append(f"{str((plan or {}).get('action', '—'))[:28]:30} -> {ist or 'Rückfall auf LLM-Analyse'}")
sag(3, 'Eindeutige Pläne kürzen den zweiten LLM-Aufruf ab, unklare fallen zurück',
    alle_ok, '\n'.join(zeilen))

# ═══════════════════════════════ 4) Zahlen aus dem Code
scope = SPAgent._describe_analysis_scope(type('X', (), {'name': 'SP'})(), SNAP)
block = orch._facts_block('pipeline', 'analyze_only', {'analysis_scope': scope})
# Erwartung aus den Daten ableiten, nicht festschreiben: der Snapshot-Zustand aendert
# sich durch jede Freigabe, feste Zahlen wuerden echte Regressionen verdecken.
_gefunden = str(scope['errors_found'])
_offen = str(len(scope['errors_not_addressed']))
sag(4, 'Fakten-Block nennt Fundzahl, Reichweite und dass nichts geschrieben wurde',
    _gefunden in block and _offen in block and 'nichts' in block.lower(),
    block + f"\n(erwartet: {_gefunden} gefunden, {_offen} unberuehrt)")

block2 = orch._facts_block('tool', 'validate_snapshot',
                           {'validation': {'errors': 2, 'warnings': 5, 'is_valid': False}})
sag(4, 'Validierungszahlen erscheinen unverändert', '2 Fehler' in block2 and '5 Warnungen' in block2, block2)
sag(4, 'Ohne belastbare Zahlen entfällt der Block ersatzlos',
    orch._facts_block('tool', 'irgendwas', {'success': True}) == '')

print()
print('ERGEBNIS:', 'alle vier Optimierungen wirksam' if all(ok_alle)
      else f'{ok_alle.count(False)} von {len(ok_alle)} Prüfungen offen')
