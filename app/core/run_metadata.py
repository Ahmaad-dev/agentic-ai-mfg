"""
Lauf-Metadaten fuer BA-Messlaeufe.

WARUM ES DIESE DATEI GIBT (BA-025, Befunde F1 und F2)
-----------------------------------------------------
F2: `B2-regressionsreferenz.json` war eine blanke Liste von Bewertungszeilen — ohne
Zeitstempel, Modell, Temperatur oder Schalterstellung. Damit wiederholte sie genau den
Defekt, den CLAUDE.md als bekannte Falle ueber `pt4-eval-results.json` fuehrt, und verletzte
die harte Regel 7 (*„Rohdaten vollstaendig ablegen"*).

F1: Im Repository liegen ZWEI virtuelle Umgebungen — `.venv/` (Wurzel, 19.08.2026) und
`app/.venv/` (04.01.2026). Sie unterscheiden sich in `pydantic` (2.13.4 gegen 2.12.5), und
`pydantic` liegt an drei Stellen im gemessenen Pfad:

    generate_correction_llm.py:29        CorrectionProposal
    validate_correction_schema_llm.py:24 LLMCorrectionResponse  (Knoten 6, Schemapruefung)
    apply_correction.py:23               LLMCorrectionResponse

`sp_agent.py:81` reicht `sys.executable` an alle Subprozesse weiter. Welcher Interpreter den
Lauf startet, entscheidet also still ueber die gesamte Messkette. Ein Versionsunterschied
koennte veraendern, WELCHER Vorschlag als schemagueltig gilt — das ist Kategorie 2.

ENTSCHEIDUNG (20.08.2026, vom Nutzer freigegeben)
--------------------------------------------------
**Verbindliche BA-Messumgebung ist die Wurzel-`.venv/`.** Geprueft wurde vorher
repositoryweit, ob etwas funktional an `app/.venv` haengt: Fundstellen sind ausschliesslich
Dokumentation (`app/README.md:30`, zwei Docstrings in `app/eval/`) und
Berechtigungseintraege in `.claude/settings.json`. Kein Startskript, keine CI, keine
VS-Code-Konfiguration. Die Produktion laeuft im Container unter Python 3.11 **ganz ohne
venv** und ist davon ohnehin unberuehrt.

`app/.venv` wird **nicht geloescht** — sie bleibt die historische PT4-Entwicklungsumgebung.
Stattdessen protokolliert jeder Messlauf, unter welchem Interpreter er tatsaechlich lief.

Diese Datei ist rein additiv: kein Produktionscode importiert sie.
"""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

#: Wurzel des Repositories (…/app/core/run_metadata.py -> drei Ebenen hoch).
REPO_ROOT = Path(__file__).resolve().parents[2]

#: Die verbindliche BA-Messumgebung. Laeuft ein Messlauf unter einem anderen Interpreter,
#: wird das NICHT blockiert — es wird protokolliert (`ba_env_ok: false`). Blockieren waere
#: falsch: ein Lauf soll nicht scheitern, weil er dokumentiert werden will.
BA_MEASUREMENT_VENV = REPO_ROOT / ".venv"

#: Pakete, die im gemessenen Pfad liegen oder ihn tragen. `pydantic` steht bewusst vorn.
TRACKED_PACKAGES = ("pydantic", "openai", "langgraph", "langchain-core", "requests")

#: Fest verdrahtet in `generate_correction_llm.py:753` und `identify_error_llm.py:239`.
#: Hier als Konstante mit Fundstelle, damit die Zahl im Protokoll nachpruefbar ist und nicht
#: aus dem Gedaechtnis stammt.
MEASURED_TEMPERATURE = 0.3
MEASURED_TEMPERATURE_SOURCE = ("generate_correction_llm.py:753", "identify_error_llm.py:239")


def _paketversionen() -> dict:
    import importlib.metadata as md
    aus = {}
    for name in TRACKED_PACKAGES:
        try:
            aus[name] = md.version(name)
        except Exception:
            aus[name] = None          # nicht installiert — auch das ist eine Information
    return aus


def _git_stand() -> dict:
    """Commit und Sauberkeit des Arbeitsbaums. Ohne das laesst sich ein Lauf spaeter keinem
    Codestand zuordnen (Regel 7)."""
    def lauf(*args):
        try:
            return subprocess.run(args, cwd=REPO_ROOT, capture_output=True, text=True,
                                  timeout=20).stdout.strip() or None
        except Exception:
            return None
    commit = lauf("git", "rev-parse", "HEAD")
    status = lauf("git", "status", "--porcelain")
    return {
        "commit": commit,
        "arbeitsbaum_sauber": (status == "" if status is not None else None),
        "geaenderte_dateien": (len(status.splitlines()) if status else 0),
    }


def collect_run_metadata(extra: dict | None = None) -> dict:
    """
    Vollstaendige Lauf-Metadaten fuer eine Ergebnisdatei.

    Enthaelt KEINE Geheimnisse: Deployment-Name und API-Version sind unkritisch, Endpunkt
    und Schluessel werden bewusst nicht aufgenommen (CLAUDE.md, Abschnitt Daten und
    Sicherheit).

    `extra` wird flach angehaengt — dort gehoert hinein, was nur der jeweilige Lauf weiss
    (Bedingung A/B/C, Fallmenge, Zweck).
    """
    from core.agent_config import (RULEBOOK_MODE, MEMORY_MODE, SP_ARCHITECTURE_MODE,
                                   HUMAN_IN_THE_LOOP)

    # Dieselbe .env wie die Runtime-Skripte (`generate_correction_llm.py:44`), sonst stuenden
    # Deployment und API-Version als null in den Metadaten, obwohl der Lauf sie benutzt hat.
    # `override=False`: eine bereits gesetzte Umgebungsvariable gewinnt - so wie im Messlauf.
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=REPO_ROOT / "app" / ".env", override=False)
    except Exception:
        pass

    prefix = Path(sys.prefix).resolve()
    meta = {
        "zeitstempel_utc": datetime.now(timezone.utc).isoformat(),

        # --- F1: welcher Interpreter, und war es der vereinbarte? ---
        "umgebung": {
            "sys_executable": sys.executable,
            "sys_prefix": str(prefix),
            "sys_base_prefix": sys.base_prefix,
            "in_venv": sys.prefix != sys.base_prefix,
            "python_version": sys.version.split()[0],
            "python_version_voll": sys.version.replace("\n", " "),
            "ba_env_erwartet": str(BA_MEASUREMENT_VENV),
            "ba_env_ok": prefix == BA_MEASUREMENT_VENV.resolve(),
            "pakete": _paketversionen(),
        },

        # --- Schalter: die Kontrollbedingungen, unter denen der Lauf entstand ---
        "schalter": {
            "RULEBOOK_MODE": RULEBOOK_MODE,
            "MEMORY_MODE": MEMORY_MODE,
            "SP_ARCHITECTURE_MODE": SP_ARCHITECTURE_MODE,
            "HUMAN_IN_THE_LOOP": HUMAN_IN_THE_LOOP,
        },

        # --- Modell: ohne Endpunkt und ohne Schluessel ---
        "modell": {
            "deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION"),
            "temperature": MEASURED_TEMPERATURE,
            "temperature_quelle": list(MEASURED_TEMPERATURE_SOURCE),
            # Die exakte Modellversion liefert erst die API-Antwort (`response.model`).
            # Sie gehoert je Lauf aus dem Artefakt nachgetragen, nicht hier geraten.
            "version_hinweis": "exakte Version steht in llm_*_call.json -> response.model",
        },

        "git": _git_stand(),
    }
    if extra:
        meta.update(extra)
    return meta


class FalscheUmgebung(RuntimeError):
    """Der Lauf laeuft nicht in der eingefrorenen BA-Messumgebung."""


def require_ba_env(zweck: str = "finaler BA-Messlauf") -> dict:
    """
    HARTER ABBRUCH, wenn nicht die Wurzel-`.venv` laeuft. Fuer **finale Messlaeufe** (AP-H4a).

    Abgrenzung zu `warn_if_wrong_env()`: Warnen ist richtig fuer Entwicklungs- und
    Pilotlaeufe - dort soll ein Lauf nicht daran scheitern, dass er dokumentiert werden will.
    Fuer einen *finalen* Messlauf ist es falsch: `pydantic` liegt an drei Stellen im
    gemessenen Pfad (`generate_correction_llm.py:29`, `validate_correction_schema_llm.py:24`,
    `apply_correction.py:23`) und entscheidet in Knoten 6 mit, welcher Vorschlag als
    schemagueltig gilt. Ein unter der falschen Umgebung erhobener Wert ist nicht
    unbrauchbar-mit-Vermerk, sondern schlicht nicht vergleichbar.

    Deshalb **vor dem ersten Fall** pruefen, nicht mittendrin: ein halb gelaufener Messsatz
    unter gemischten Umgebungen waere schlimmer als gar keiner.

    Raises: FalscheUmgebung. Returns die Metadaten, wenn alles stimmt.
    """
    meta = collect_run_metadata({"zweck": zweck})
    u = meta["umgebung"]
    if not u["ba_env_ok"]:
        zeilen = [
            f"{zweck} abgebrochen: nicht die eingefrorene BA-Messumgebung.",
            f"  erwartet:    {u['ba_env_erwartet']}",
            f"  laeuft in:   {u['sys_prefix']}",
            f"  Interpreter: {u['sys_executable']}",
            f"  Pakete:      {u['pakete']}",
            "Kein Fall wurde ausgefuehrt.",
        ]
        raise FalscheUmgebung("\n".join(zeilen))
    return meta


def warn_if_wrong_env(zweck: str = "BA-Messlauf") -> bool:
    """
    Gibt eine deutliche Warnung aus, wenn nicht die Wurzel-`.venv` laeuft. Blockiert NICHT.
    Rueckgabe: True, wenn die Umgebung stimmt.
    """
    ok = Path(sys.prefix).resolve() == BA_MEASUREMENT_VENV.resolve()
    if not ok:
        print("!" * 78)
        print(f"WARNUNG: {zweck} laeuft NICHT in der vereinbarten BA-Messumgebung.")
        print(f"  erwartet: {BA_MEASUREMENT_VENV}")
        print(f"  laeuft in: {sys.prefix}")
        print("  Der Lauf wird fortgesetzt und als ba_env_ok=false protokolliert.")
        print("!" * 78)
    return ok
