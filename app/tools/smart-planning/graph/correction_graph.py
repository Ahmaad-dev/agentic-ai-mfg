"""
AP-E — Der Korrekturgraph.

**Hier entsteht keine Fachlogik.** Diese Datei verdrahtet ausschliesslich, was in AP-D gebaut
und geprueft wurde: die neun Knotenfunktionen, den `GraphState` und die in
`BA_MASTERPLAN.md` Kap. 11 festgelegten Uebergaenge. Wer hier eine fachliche Entscheidung
sucht, sucht am falschen Ort — sie steht in den Knoten.

WAS LANGGRAPH HIER TUT UND WAS NICHT (Kap. 5.1, AP-A2-Kasten)
--------------------------------------------------------------
LangGraph ist **nur Orchestrator**. Ausdruecklich NICHT verwendet:
  * keine LangChain-LLM-Wrapper — die Knoten rufen den bestehenden Azure-Client der
    Runtime-Skripte, sonst waeren Modell, Temperatur und API-Version zwischen den Varianten
    nur dokumentiert statt strukturell identisch,
  * keine Prebuilt-Agenten — sie wuerden die Pipeline ersetzen statt sie zu orchestrieren,
  * **keine Retry-Policies auf Knotenebene** — die Schema-Wiederholung ist bestehende Logik
    (`validate_with_retry(..., max_retries=5)`) und bleibt unveraendert im Knoten 6.
  * kein Checkpointer (AP-A2.4) — der `trace` wird selbst geschrieben.

DIE KANTEN (Kap. 11)
---------------------
    START → 1 → 2 → 3 → 4 → 5 → 6
    6 ──schema_valid=True──▶ 7 ──▶ 8
      └─schema_valid=False─▶ 8
    8 ──decision.action == "continue"──▶ 2      (Rueckkante, FACHLICHE Iteration)
      └─sonst────────────────────────────▶ 9 ──▶ END

**Es gibt KEINE Rueckkante 6→5.** Technische Wiederholungen bleiben vollstaendig INNERHALB
von Knoten 6. Eine Graph-Kante waere eine zweite Retry-Schicht ueber der bestehenden und
wuerde die Zahl der Versuche zwischen den Bedingungen ungleich machen (Kap. 11,
korrigiert 19.08.2026).

**Beide Router enthalten keine Fachlogik.** Sie lesen genau ein Feld, das ein Knoten gesetzt
hat. Genau darin liegt der Unterschied zum impliziten Kontrollfluss des Monolithen — und
genau das macht Nachvollziehbarkeit (UF3) ueberhaupt messbar.
"""
from __future__ import annotations

import json
import sys
import typing
from datetime import datetime, timezone
from pathlib import Path

_HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(_HIER.parent))            # …/smart-planning
sys.path.insert(0, str(_HIER.parent / "runtime"))

from langgraph.graph import StateGraph, START, END          # noqa: E402

from graph.graph_state import GraphState, new_state         # noqa: E402
from graph.nodes.input_analysis import node_input_analysis   # noqa: E402
from graph.nodes.classification import node_classification   # noqa: E402
from graph.nodes.context_search import node_context_search   # noqa: E402
from graph.nodes.rule_matching import node_rule_matching     # noqa: E402
from graph.nodes.correction import node_correction           # noqa: E402
from graph.nodes.technical_check import node_technical_check  # noqa: E402
from graph.nodes.apply_revalidate import node_apply_revalidate  # noqa: E402
from graph.nodes.evaluation import node_evaluation, route_after_evaluation  # noqa: E402
from graph.nodes.answer import node_answer                   # noqa: E402

#: Knotennamen im Graphen = Namen im `trace`. Bewusst gleich, damit ein Trace-Eintrag ohne
#: Uebersetzungstabelle einer Graphposition zuzuordnen ist (Kap. 12.4).
KNOTEN = (
    ("input_analysis", node_input_analysis),
    ("classification", node_classification),
    ("context_search", node_context_search),
    ("rule_matching", node_rule_matching),
    ("correction", node_correction),
    ("technical_check", node_technical_check),
    ("apply_revalidate", node_apply_revalidate),
    ("evaluation", node_evaluation),
    ("answer", node_answer),
)

#: Sequenzielle Kanten 1→…→6.
_SEQUENZ = ("input_analysis", "classification", "context_search",
            "rule_matching", "correction", "technical_check")


def route_after_technical_check(state: dict) -> str:
    """
    Bedingte Kante A (Kap. 11). **Keine Fachlogik** — liest nur `technical_check.schema_valid`.

    `True`  → Knoten 7 (anwenden und re-validieren)
    `False` → Knoten 8, der daraus `stop_uncertain` macht.

    Es wird ausdruecklich NICHT nach uebrigen Retries gefragt: die sind in Knoten 6 bereits
    erschoepft, wenn er `False` zurueckgibt. `None` (Knoten 6 gar nicht gelaufen) wird wie
    `False` behandelt — lieber Knoten 8 entscheiden lassen als etwas anwenden, dessen
    Schemastatus unbekannt ist.
    """
    return "apply_revalidate" if (state.get("technical_check") or {}).get("schema_valid") is True \
        else "evaluation"


def build_graph() -> StateGraph:
    """Baut den Graphen. Getrennt von `compile()`, damit Tests die Struktur pruefen koennen."""
    g = StateGraph(GraphState)

    for name, fn in KNOTEN:
        g.add_node(name, fn)

    g.add_edge(START, _SEQUENZ[0])
    for vorher, nachher in zip(_SEQUENZ, _SEQUENZ[1:]):
        g.add_edge(vorher, nachher)

    # Bedingte Kante A nach Knoten 6.
    g.add_conditional_edges("technical_check", route_after_technical_check,
                            {"apply_revalidate": "apply_revalidate", "evaluation": "evaluation"})
    g.add_edge("apply_revalidate", "evaluation")

    # Bedingte Kante B nach Knoten 8 — inklusive Rueckkante 8→2.
    g.add_conditional_edges("evaluation", route_after_evaluation,
                            {"classification": "classification", "answer": "answer"})
    g.add_edge("answer", END)
    return g


#: Die deklarierten Zustandsfelder. Dient nur der Selbstbeschreibung der abgelegten Datei -
#: so laesst sich spaeter pruefen, ob sie vollstaendig ist, ohne den Code danebenzulegen.
_STATE_FELDER = tuple(typing.get_type_hints(GraphState))

_KOMPILIERT = None


def get_graph():
    """Kompilierter Graph, einmal gebaut. Ohne Checkpointer (AP-A2.4)."""
    global _KOMPILIERT
    if _KOMPILIERT is None:
        _KOMPILIERT = build_graph().compile()
    return _KOMPILIERT


def run_correction_graph(snapshot_id: str, errors_before: int = 0,
                         max_iterations: int = 5) -> dict:
    """
    Fuehrt den Graphen fuer einen Snapshot aus und legt den vollstaendigen Zustand ab (E5).

    Returns den End-`GraphState`. Beendet den Prozess NIE — die Knoten fangen ihre Fehler
    selbst und schreiben sie als Zustand.

    `recursion_limit`: Die Rueckkante 8→2 kann bis zu `max_iterations` fachliche Durchgaenge
    ausloesen, jeder ueber bis zu acht Knoten. Der LangGraph-Standardwert (25) wuerde dabei
    greifen und den Lauf mit einer Framework-Ausnahme abbrechen — das waere ein
    **Abbruchgrund, den es im Monolithen nicht gibt** und der als Architektureffekt erschiene.
    Deshalb grosszuegig bemessen; die fachliche Obergrenze bleibt allein `max_iterations`,
    durchgesetzt von Knoten 8 (`stop_max_iter`).
    """
    zustand = new_state(snapshot_id, errors_before=errors_before,
                        max_iterations=max_iterations)
    grenze = max_iterations * len(KNOTEN) + 10
    ergebnis = get_graph().invoke(zustand, config={"recursion_limit": grenze})
    ergebnis["finished_at"] = datetime.now(timezone.utc).isoformat()
    _trace_ablegen(ergebnis)
    return ergebnis


def _trace_ablegen(zustand: dict) -> str | None:
    """
    E5 — den vollstaendigen Zustand je Lauf ablegen (harte Regel 7).

    Ohne diese Datei ist keine Aussage ueber UF3 belastbar; sie ist der Anhang der Arbeit.
    Der Suchkontext (`extracted_context.results_object`) und die Meldungslisten werden dabei
    **durch ihre Hashes ersetzt** — sie koennen sechsstellig viele Zeichen umfassen und wuerden
    die Datei unlesbar machen (Kap. 12.5). Die Hashes stehen ohnehin schon im Zustand, die
    Rohdaten liegen als Artefakte im Snapshot-Ordner.
    """
    from runtime_storage import get_storage, get_latest_iteration_number
    try:
        schlank = dict(zustand)
        ec = dict(schlank.get("extracted_context") or {})
        if "results_object" in ec:
            ec["results_object"] = f"<ausgelagert, sha256={ec.get('results_hash')}>"
        if ec:
            schlank["extracted_context"] = ec
        mr = dict(schlank.get("matched_rules") or {})
        if "rule_text" in mr:
            mr["rule_text"] = f"<ausgelagert, {mr.get('chars')} Zeichen, sha256={mr.get('rule_text_hash')}>"
        if mr:
            schlank["matched_rules"] = mr
        ke = dict(schlank.get("classified_error") or {})
        if "identify_response" in ke:
            ke["identify_response"] = f"<ausgelagert, sha256={ke.get('identify_response_sha256')}>"
        if ke:
            schlank["classified_error"] = ke
        iv = dict(schlank.get("initial_validation") or {})
        if iv.get("meldungen") is not None:
            iv["meldungen"] = f"<{len(iv['meldungen'])} Meldungen, siehe snapshot-validation.json>"
        if iv:
            schlank["initial_validation"] = iv
        # ABLAGE-ANMERKUNGEN, KEINE ZUSTANDSFELDER (klargestellt 20.08.2026, BA-030).
        # Frueher stand `final_validation_anzahl` auf derselben Ebene wie die Zustandsfelder -
        # die Datei hatte dadurch 20 Schluessel, waehrend `GraphState` 19 Felder deklariert.
        # Das sah nach einem undokumentierten Feld aus. Alles, was erst BEIM ABLEGEN entsteht,
        # steht jetzt unter `_ablage`; die uebrigen Schluessel sind exakt die 19 Zustandsfelder.
        ablage = {"graph_state_felder": len(_STATE_FELDER),
                  "ausgelagert": [k for k in ("extracted_context.results_object",
                                              "matched_rules.rule_text",
                                              "classified_error.identify_response",
                                              "initial_validation.meldungen",
                                              "final_validation")]}
        if isinstance(schlank.get("final_validation"), list):
            ablage["final_validation_anzahl"] = len(schlank["final_validation"])
            schlank["final_validation"] = "<siehe snapshot-validation.json nach der Re-Validierung>"
        schlank["_ablage"] = ablage

        sid = zustand["snapshot_id"]
        storage = get_storage()
        n = get_latest_iteration_number(sid) or 1
        pfad = f"{sid}/iteration-{n}/graph_state.json"
        storage.save_json(pfad, json.loads(json.dumps(schlank, ensure_ascii=False, default=str)))
        return pfad
    except Exception as exc:
        # Das Ablegen darf einen Lauf nicht kippen - aber es muss auffallen.
        print(f"WARNUNG: graph_state.json konnte nicht abgelegt werden: {type(exc).__name__}: {exc}")
        return None


def mermaid() -> str:
    """E6 — Ablaufdiagramm fuer Kapitel 4, direkt aus dem kompilierten Graphen."""
    return get_graph().get_graph().draw_mermaid()
