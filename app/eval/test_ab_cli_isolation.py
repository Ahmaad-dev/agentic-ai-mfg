"""
R7a — Erreichbarkeitsnachweis: Können die Änderungen aus BA-043/BA-044 die Bedingungen A, B
oder den CLI-Pfad erreichen?

WARUM DAS DER KERN IST
----------------------
Bauregel B (CLAUDE.md): *Jede Fähigkeit, die es nur in C gibt — ein behobener Fehler, ein
besserer Retry, eine zusätzliche Prüfung — erscheint später als Architektureffekt, obwohl sie
keiner ist.* Der Umkehrschluss gilt genauso: Eine Reparatur, die versehentlich AUCH A und B
verändert, macht die Regressionsreferenz aus AP-B ungültig.

Deshalb wird hier **mechanisch** geprüft, nicht argumentiert. Grundlage ist der AST, nicht die
Textsuche — dieselbe Lehre wie beim Exit-Code-Zähler in BA-025 und beim Docstring-Zählfehler:
ein `grep` findet auch Vorkommen in Kommentaren und Docstrings.

WAS GEPRÜFT WIRD
----------------
  1. Alle in BA-044 geänderten Dateien liegen unter `graph/`. Kein Modul ausserhalb von
     `graph/` importiert sie — mit genau einer erlaubten Ausnahme: `sp_agent`, und dort nur
     im Zweig `SP_ARCHITECTURE_MODE == "graph"`.
  2. `run_technical_check()` — die EINZIGE gemeinsame Runtime-Funktion, deren Vertrag BA-043
     geändert hat — hat genau einen Aufrufer, und der liegt im Graphen.
  3. Der CLI-Pfad derselben Datei ruft `validate_with_retry` DIREKT und ist damit unberührt.
  4. `run_correction_generation()` und `run_apply()` behalten ihre Legacy-Defaults; die
     Guards liegen in den Graph-Knoten, nicht in der Runtime.

**Das ist ein statischer Nachweis.** Er zeigt Erreichbarkeit, nicht Laufzeitverhalten. Die
empirische Bestätigung ist ein echter Monolith-Lauf (R7b) — und der läuft ausdrücklich auf
einem PILOT-Snapshot, nicht auf einem der 17 Messfälle.

Aufruf:  .venv/Scripts/python.exe app/eval/test_ab_cli_isolation.py
"""
import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from graph_regression_harness import APP, Pruefung  # noqa: E402

SP = APP / "tools" / "smart-planning"
GRAPH = SP / "graph"
RUNTIME = SP / "runtime"

#: Was BA-044 angefasst hat. Alles unter `graph/` — das ist die zu belegende Behauptung.
GEAENDERT_BA044 = [
    GRAPH / "nodes" / "correction.py",
    GRAPH / "nodes" / "apply_revalidate.py",
    GRAPH / "nodes" / "evaluation.py",
    GRAPH / "trace_keys.py",
]

#: Die eine gemeinsame Runtime-Funktion, deren Vertrag BA-043 geändert hat.
GETEILTE_FUNKTION = "run_technical_check"

#: Module, die den Graphen importieren dürfen. `sp_agent` ist der EINZIGE Verzweigungspunkt
#: (CLAUDE.md, harte Regel 1).
#:
#: ABGRENZUNG (BA-045): Gefragt ist, ob PRODUKTCODE ausserhalb von `graph/` den Graphen
#: erreicht. `app/eval/` ist Mess- und Prüfwerkzeug, kein Produktcode — es läuft nie in A, B
#: oder im CLI-Pfad und wird deshalb getrennt ausgewiesen statt mitgezählt. Die Trennung wird
#: SICHTBAR gemacht, nicht stillschweigend vorgenommen: die Eval-Importeure werden gedruckt.
ERLAUBTE_GRAPH_IMPORTEURE = {"sp_agent"}


def _py_dateien():
    for wurzel in (APP,):
        for f in wurzel.rglob("*.py"):
            if "__pycache__" in f.parts or ".venv" in f.parts:
                continue
            yield f


def _baum(f: Path):
    try:
        return ast.parse(f.read_text(encoding="utf-8", errors="replace"), filename=str(f))
    except SyntaxError:
        return None


def _importiert_graph(baum) -> bool:
    for k in ast.walk(baum):
        if isinstance(k, ast.Import):
            if any(a.name == "graph" or a.name.startswith("graph.") for a in k.names):
                return True
        elif isinstance(k, ast.ImportFrom):
            m = k.module or ""
            if m == "graph" or m.startswith("graph."):
                return True
    return False


def _aufrufe(baum, name: str) -> list:
    """Zeilen, in denen `name` als Funktion GERUFEN wird — AST, nicht Text."""
    treffer = []
    for k in ast.walk(baum):
        if not isinstance(k, ast.Call):
            continue
        f = k.func
        if (isinstance(f, ast.Name) and f.id == name) or \
           (isinstance(f, ast.Attribute) and f.attr == name):
            treffer.append(k.lineno)
    return treffer


def _default_von(baum, funktion: str, parameter: str):
    """Der Default-Wert eines Parameters — belegt, dass der Legacy-Weg erhalten ist."""
    for k in ast.walk(baum):
        if isinstance(k, ast.FunctionDef) and k.name == funktion:
            args = k.args.args
            defaults = k.args.defaults
            versatz = len(args) - len(defaults)
            for i, a in enumerate(args):
                if a.arg == parameter and i >= versatz:
                    return ast.unparse(defaults[i - versatz])
    return "<nicht gefunden>"


def pruefen() -> Pruefung:
    p = Pruefung("R7a — Erreichbarkeit von A, B und CLI (statisch, AST)")

    # --- 1. Alle BA-044-Änderungen liegen unter graph/ ---
    p.wahr("alle BA-044-Dateien liegen unter graph/",
           all(GRAPH in f.parents or f.parent == GRAPH for f in GEAENDERT_BA044),
           [str(f.relative_to(APP)) for f in GEAENDERT_BA044])

    # --- 2. Wer importiert den Graphen? ---
    produkt, werkzeug = [], []
    for f in _py_dateien():
        if GRAPH in f.parents or f.parent == GRAPH:
            continue
        b = _baum(f)
        if b is not None and _importiert_graph(b):
            (werkzeug if f.parent.name == "eval" else produkt).append(f.stem)
    print(f"  (informativ) Graph-Importeure in app/eval/ — Werkzeug, kein Produktcode: "
          f"{sorted(set(werkzeug))}")
    p.gleich("Graph-Importeure im Produktcode ausserhalb von graph/",
             sorted(ERLAUBTE_GRAPH_IMPORTEURE), sorted(set(produkt)))

    # --- 3. run_technical_check: genau ein Aufrufer, und der liegt im Graphen ---
    ruft = {}
    for f in _py_dateien():
        b = _baum(f)
        if b is None:
            continue
        # Die Definition selbst und Testcode zählen nicht als Aufrufer.
        if f.name == "validate_correction_schema_llm.py" or f.parent.name == "eval":
            continue
        zeilen = _aufrufe(b, GETEILTE_FUNKTION)
        if zeilen:
            ruft[str(f.relative_to(APP))] = zeilen
    p.gleich(f"{GETEILTE_FUNKTION}: Aufrufer im Produktcode",
             ["tools/smart-planning/graph/nodes/technical_check.py"],
             sorted(k.replace("\\", "/") for k in ruft))

    # --- 4. Der CLI-Pfad ruft validate_with_retry DIREKT ---
    schema = _baum(RUNTIME / "validate_correction_schema_llm.py")
    in_main = []
    for k in ast.walk(schema):
        if isinstance(k, ast.FunctionDef) and k.name == "main":
            in_main = [n for n in _aufrufe(k, "validate_with_retry")]
    p.wahr("CLI main() ruft validate_with_retry direkt", bool(in_main), in_main)
    p.gleich("CLI main() ruft run_technical_check NICHT", [],
             [n for k in ast.walk(schema) if isinstance(k, ast.FunctionDef) and k.name == "main"
              for n in _aufrufe(k, GETEILTE_FUNKTION)])

    # --- 5. Legacy-Defaults der Runtime unangetastet ---
    gen = _baum(RUNTIME / "generate_correction_llm.py")
    app_ = _baum(RUNTIME / "apply_correction.py")
    p.gleich("run_correction_generation(iteration_number=…) Default", "None",
             _default_von(gen, "run_correction_generation", "iteration_number"))
    p.gleich("run_apply(iteration_number=…) Default", "None",
             _default_von(app_, "run_apply", "iteration_number"))
    p.gleich("run_technical_check(iteration_number=…) Default", "None",
             _default_von(schema, GETEILTE_FUNKTION, "iteration_number"))

    # --- 6. Die Guards liegen in den Knoten, nicht in der Runtime ---
    for datei, name in ((RUNTIME / "generate_correction_llm.py", "generate_correction_llm"),
                        (RUNTIME / "apply_correction.py", "apply_correction")):
        text = datei.read_text(encoding="utf-8", errors="replace")
        p.gleich(f"{name}: kein BA-044-Guard in der Runtime", 0,
                 text.count("artifact_iteration_number"))
    return p


def main():
    sys.path.insert(0, str(APP))
    from core.run_metadata import require_ba_env
    meta = require_ba_env("A/B/CLI-Erreichbarkeitsnachweis (BA-044)")
    print(f"Umgebung: {meta['umgebung']['sys_prefix']}")
    p = pruefen()
    p.drucken()
    return 0 if p.bestanden else 1


if __name__ == "__main__":
    sys.exit(main())
