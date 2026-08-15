"""Prueft, ob die Dokumentation noch stimmt.

Aufruf aus dem Verzeichnis app/:  .venv/Scripts/python.exe -X utf8 eval/check_doku_stimmt.py

Dokumentation veraltet lautlos — sie beschwert sich nicht, wenn eine Funktion umbenannt oder
entfernt wird.  und  nennen
Funktionsnamen, Konstanten und Bedingungen; dieser Lauf prueft, dass es sie noch gibt.

Bewusst KEINE Textpruefung der Dokumente selbst: Formulierungen duerfen sich aendern. Was
nicht wandern darf, sind die Belege, auf die sie sich stuetzen.
"""
import sys
import pathlib

sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def lies(p):
    return pathlib.Path(p).read_text(encoding='utf-8')

PRUEFUNGEN = [
    # (Beschreibung, Datei, gesuchter Text)
    ("_describe_analysis_scope",        'agents/sp_agent.py',            'def _describe_analysis_scope'),
    ("open_proposal_blocking (Werkzeug)", 'tools/smart-planning/runtime/generate_correction_llm.py', 'def open_proposal_blocking'),
    ("Sperre nur unter HitL (Werkzeug)", 'tools/smart-planning/runtime/generate_correction_llm.py', 'if not HUMAN_IN_THE_LOOP:'),
    ("Sperre nur unter HitL (Pipeline)", 'agents/sp_agent.py',           'and snapshot_id and HUMAN_IN_THE_LOOP'),
    ("UTF-8 fuer Werkzeuge",            'agents/sp_agent.py',            'PYTHONIOENCODING'),
    ("Rueckgabewert wird ausgewertet",  'tools/smart-planning/runtime/identify_error_llm.py', 'if not trigger_identify_tool('),
    ("Vorbedingung snapshot-data",      'tools/smart-planning/runtime/identify_error_llm.py', 'snapshot-data.json fehlt'),
    ("Recovery nennt Tatsache",         'agents/sp_agent.py',            'search_results_missing'),
    ("_facts_block",                    'agents/orchestration_agent.py', 'def _facts_block'),
    ("_intent_from_plan",               'agents/orchestration_agent.py', 'def _intent_from_plan'),
    ("aktuelle Nachricht hat Vorrang",  'agents/orchestration_agent.py', 'snapshot_gemeint = self._snapshot_in_focus'),
    ("Chat/RAG durchgereicht",          'agents/orchestration_agent.py', 'if agent_key in ("email", "chat", "rag")'),
    ("APP_BASE_URL im Deep-Link",       'agents/orchestration_agent.py', '{APP_BASE_URL}/review.html'),
    ("review_url an offenen Vorschlaegen", 'agents/orchestration_agent.py', '"review_url"'),
    ("Fokus-Snapshot je Sitzung",       'memory/short_term.py',          'def set_focus_snapshot'),
    ("Herkunfts-Etiketten",             'memory/short_term.py',          'def as_llm_messages'),
    ("revalidation im Repository",      'db/repository.py',              '_summarize_revalidation'),
    ("juengste Nachvalidierung markiert", 'db/repository.py',            'ist_aktueller_stand'),
    ("Anwendbarkeit im Review Board",   'routes/review.py',              'def _annotate_applicability'),
    ("Pfadzerlegung Review",            'routes/review.py',              'def _parse_target_path'),
    ("Pfadzerlegung Anwenden",          'tools/smart-planning/runtime/apply_correction.py', 'def resolve_deep_path'),
    ("Kollektiv-Statistik",             'tools/smart-planning/runtime/identify_snapshot.py', 'work_item_config_stats_same_department'),
    ("Hinweis zu Array-Nachbarn",       'tools/smart-planning/runtime/identify_snapshot.py', 'items_neighbours_note'),
    ("Beleg-Regel im Prompt",           'tools/smart-planning/runtime/generate_correction_llm.py', 'WORAUF DU EINEN WERT STUETZEN DARFST'),
    ("min-width fuer Belegt-Kasten",    'ui/css/styles.css',             '.rb-grounded > div { min-width: 0; }'),
    ("overflow-wrap",                   'ui/css/styles.css',             'overflow-wrap: anywhere'),
    ("ueberholt-Kennzeichnung",         'ui/scripts/review.js',          'rb-status-stale'),
    ("DEV_SERVER_HOST",                 'web_server.py',                 'DEV_SERVER_HOST'),
]

fehlt = []
for name, datei, text in PRUEFUNGEN:
    ok = text in lies(datei)
    if not ok:
        fehlt.append(name)
    print(f"  {'OK    ' if ok else 'FEHLT '} {name}")

print()
import core.agent_config as c
werte = [
    ("DEINE STIMME in Chat-Prompt",  'Er fragt knapp' in c.DEFAULT_CHAT_SYSTEM_PROMPT),
    ("DEINE STIMME in RAG-Prompt",   'Er fragt knapp' in c.DEFAULT_RAG_SYSTEM_PROMPT),
    ("DEINE STIMME in Auswertung",   'Er fragt knapp' in c.DEFAULT_ORCHESTRATOR_SP_RESULT_INTERPRETATION_PROMPT),
    ("keine Laengenvorgabe mehr",    '2-3 Sätze' not in c.DEFAULT_ORCHESTRATOR_SP_RESULT_INTERPRETATION_PROMPT),
    ("APP_BASE_URL vorhanden",       bool(getattr(c, 'APP_BASE_URL', None))),
    ("max_step_result_chars = 1200", c.CHAT_HISTORY_CONFIG.get('max_step_result_chars') == 1200),
]
for name, ok in werte:
    if not ok:
        fehlt.append(name)
    print(f"  {'OK    ' if ok else 'FEHLT '} {name}")

print()
print('ERGEBNIS:', 'alle Behauptungen belegt' if not fehlt else f'NICHT belegt: {fehlt}')
