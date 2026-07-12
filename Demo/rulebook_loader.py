"""
Rulebook loader (PT4 / AP7.0, drop-in cards seit AP7.5).

Entscheidet, WELCHE Regeln in einen LLM-Prompt gehen. Zwei Modi, geschaltet über
RULEBOOK_MODE in agent_config.py:

  "monolith" (default) — die vollständige llm-validation-fix-rules.md, exakt wie früher.
  "cards"              — skills/_core.md plus JEDE Karte, die für den [validate_*]-Tag
                         dieses Fehlers zuständig ist.

--- Karten sind SELBSTBESCHREIBEND (drop-in) ---
Es gibt keine zentrale Zuordnungsliste im Code. Der Ordner wird gescannt, jede Karte sagt
selbst, wofür sie gilt. Neue Regel = neue .md-Datei. Kein Code-Change, kein Entwickler.

--- Wo die Karten liegen (lokal UND Cloud) ---
Zugriff über den StorageManager, exakt wie die Snapshots. Damit gilt derselbe Code für:
  STORAGE_MODE=LOCAL  -> demo/skills/
  STORAGE_MODE=AZURE  -> Blob-Prefix `skills/` im konfigurierten Container
Ein Fachanwender kann die Regeln im Storage Account bearbeiten, ohne Redeployment.
Der Prefix ist über RULEBOOK_SKILLS_PREFIX überschreibbar.

--- Routing: der Schlüssel ist der VALIDATOR-TAG, nicht der Dateiname ---
Geladen wird über das `[validate_*]`-Tag aus der Fehlermeldung von Smart Planning:
    "[validate_density_values] Article 100005 has invalid rel_density_min: -2"
     ^^^^^^^^^^^^^^^^^^^^^^^^^  ->  DENSITY_VALUES
Eine Karte MUSS daher sagen, für welche(s) Tag(s) sie gilt — per Frontmatter `applies_to`.
Ohne Frontmatter gilt die Konvention Dateiname -> Tag (`work-plan-ids.md` -> WORK_PLAN_IDS);
passt der so abgeleitete Tag zu keinem bekannten Validator, WARNT der Loader laut. Eine Karte,
die still nie geladen wird, ist der schlimmste mögliche Ausgang — siehe `check_cards()`.
"""
import os
from pathlib import Path
from typing import Optional

from agent_config import RULEBOOK_MODE
from storage_manager import StorageManager

DEMO_ROOT = Path(__file__).resolve().parent
MONOLITH_FILE = DEMO_ROOT / "smart-planning" / "runtime" / "runtime-files" / "llm-validation-fix-rules.md"

#: Ordner (LOCAL) bzw. Blob-Prefix (AZURE), in dem die Karten liegen.
SKILLS_PREFIX = os.getenv("RULEBOOK_SKILLS_PREFIX", "skills").strip("/")
CORE_CARD = "_core.md"

#: Die Validator-Tags, die Smart Planning tatsächlich ausgibt. Nur diese können je ein
#: Routing auslösen. Eine Karte mit einem Tag AUSSERHALB dieser Liste wird niemals geladen.
KNOWN_VALIDATOR_TAGS = {
    "UNIQUE_IDS",
    "DEMAND_ARTICLE_IDS",
    "DEMAND_UNIQUENESS",
    "DENSITY_VALUES",
    "WORK_ITEM_CONFIGS_COMPLETENESS",
    "START_END_OPERATION_EXISTENCE",
    "WORK_PLAN_IDS",
    "EQUIPMENT_PREDECESSOR_REFERENCES",
    "EQUIPMENT_CONNECTIVITY",
    "EQUIPMENT_DEPARTMENT_PRESENCE",
    "EQUIPMENT_UNAVAILABILITY_CONSISTENCY",
    "EQUIPMENT_WORKER_QUALIFICATION_COMPATIBILITY",
    "WORKER_CONSISTENCY",
}


def _storage() -> StorageManager:
    """Storage mit demo/ als Basis, damit 'skills/x.md' lokal UND auf Azure identisch auflöst."""
    return StorageManager(base_path=str(DEMO_ROOT))


def _split_frontmatter(text: str) -> tuple[dict, str]:
    """
    Trennt eine optionale `---`-Frontmatter vom Kartentext.

    Bewusst ein Mini-Parser statt PyYAML: die Frontmatter kennt nur `key: value` und
    `key: [a, b]`. Dafür eine Abhängigkeit einzuführen wäre unangemessen.
    """
    if not text.startswith("---"):
        return {}, text

    lines = text.splitlines()
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return {}, text  # kein schliessendes ---: als normalen Text behandeln

    meta: dict = {}
    for line in lines[1:end]:
        if not line.strip() or ":" not in line:
            continue
        key, _, raw = line.partition(":")
        raw = raw.strip()
        if raw.startswith("[") and raw.endswith("]"):
            meta[key.strip()] = [v.strip() for v in raw[1:-1].split(",") if v.strip()]
        else:
            meta[key.strip()] = raw
    return meta, "\n".join(lines[end + 1:]).lstrip("\n")


def _tags_of(meta: dict) -> list[str]:
    """
    Für welche [validate_*]-Tags gilt diese Karte — falls sie das überhaupt sagt.

    OPTIONAL. Eine Karte ohne `applies_to` ist NICHT tot: der Agent waehlt sie ueber ihre
    Beschreibung aus (siehe card_index). Es gibt bewusst KEINE Ableitung aus dem Dateinamen
    mehr — das war eine Falle: wer seine Datei `umgang-mit-falschen-nummern.md` nennt, haette
    den Tag UMGANG_MIT_FALSCHEN_NUMMERN bekommen, den es nie gibt, und die Karte waere
    stillschweigend nie geladen worden.
    """
    declared = meta.get("applies_to")
    if isinstance(declared, str):
        declared = [declared]
    return [t.strip().upper() for t in (declared or []) if t.strip()]


def _summarize(body: str, limit: int = 160) -> str:
    """Notbeschreibung aus dem Text, wenn die Karte keine `description` hat."""
    for line in body.splitlines():
        line = line.strip().lstrip("#").strip()
        if line and not line.startswith("---"):
            return line[:limit]
    return "(keine Beschreibung)"


def list_cards() -> list[dict]:
    """Alle Karten aus dem Skills-Storage."""
    storage = _storage()
    cards = []
    for path in sorted(storage.list_files(f"{SKILLS_PREFIX}/")):
        name = Path(path).name
        if not name.endswith(".md") or name.startswith("_"):
            continue  # `_core.md` und alles mit _ sind keine Karten (Vorlage, Doku)
        raw = storage.load_text(f"{SKILLS_PREFIX}/{name}")
        if raw is None:
            continue
        meta, body = _split_frontmatter(raw)
        cards.append({
            "file": name,
            "tags": _tags_of(meta),
            "description": meta.get("description", ""),
            "summary": _summarize(body),
            "body": body,
        })
    return cards


def check_cards() -> list[dict]:
    """Diagnose: `applies_to` mit einem Tag, den es gar nicht gibt (Tippfehler)."""
    problems = []
    for card in list_cards():
        unknown = [t for t in card["tags"] if t not in KNOWN_VALIDATOR_TAGS]
        if unknown:
            problems.append({
                "file": card["file"],
                "unknown_tags": unknown,
                "hint": (
                    f"'{', '.join(unknown)}' ist kein bekannter Validator-Tag — vermutlich ein "
                    "Tippfehler. Die Karte kann trotzdem ueber ihre Beschreibung gewaehlt "
                    f"werden. Bekannte Tags: {', '.join(sorted(KNOWN_VALIDATOR_TAGS))}"
                ),
            })
    return problems


def card_index() -> str:
    """
    Das Inhaltsverzeichnis ALLER Karten — Dateiname plus Beschreibung in Klartext.

    Der Agent bekommt es bei der Fehler-Identifikation zu sehen und waehlt daraus die
    relevanten Karten aus. Damit hat er JEDERZEIT Zugriff auf alles, ohne dass alles in
    jeden Prompt muss: er kennt den gesamten Regelbestand, liest aber nur, was er braucht.

    Genau deshalb muss NIEMAND einen Validator-Tag kennen, um eine Regel zu ergaenzen —
    eine Beschreibung in normaler Sprache reicht.
    """
    lines = []
    for card in list_cards():
        desc = card["description"] or card["summary"]
        lines.append(f"- {card['file']}: {desc}")
    return "\n".join(lines) if lines else "(keine Regelkarten vorhanden)"


def load_rulebook(error_type: Optional[str] = None,
                  extra_cards: Optional[list] = None) -> str:
    """
    Der Regeltext für diesen Prompt.

    Drei Quellen, in dieser Reihenfolge:
      1. `_core.md` — immer.
      2. Karten, deren `applies_to` auf den Validator-Tag passt (deterministischer Schnellweg).
      3. Karten, die der Agent bei der Identifikation als relevant BENANNT hat (`extra_cards`).
         Das ist der Weg fuer jede Karte, die ein Fachanwender in seiner Sprache beschrieben
         hat, ohne einen Tag zu kennen.

    error_type: das [validate_*]-Tag (uppercase) oder None (bei der Identifikation ist der
    Fehler ja noch nicht gewaehlt).
    """
    if RULEBOOK_MODE != "cards":
        if not MONOLITH_FILE.exists():
            raise FileNotFoundError("llm-validation-fix-rules.md not found")
        return MONOLITH_FILE.read_text(encoding="utf-8")

    storage = _storage()
    core_raw = storage.load_text(f"{SKILLS_PREFIX}/{CORE_CARD}")
    if core_raw is None:
        raise FileNotFoundError(f"{SKILLS_PREFIX}/{CORE_CARD} not found")
    _, core_body = _split_frontmatter(core_raw)
    parts = [core_body]

    cards = list_cards()
    wanted = (error_type or "").strip().upper()
    named = {str(n).strip().lower() for n in (extra_cards or [])}

    chosen, reasons = [], []
    for card in cards:
        if wanted and wanted in card["tags"]:
            chosen.append(card)
            reasons.append(f"{card['file']} (Tag {wanted})")
        elif card["file"].lower() in named or card["file"].lower().removesuffix(".md") in named:
            chosen.append(card)
            reasons.append(f"{card['file']} (vom Agenten als relevant gewaehlt)")

    parts.extend(c["body"] for c in chosen)
    if chosen:
        print(f"- Regelkarten: {', '.join(reasons)}")
    else:
        print(f"INFO: keine Regelkarte passt zu '{wanted or '-'}' — nur {CORE_CARD}. "
              f"Kein Regelverlust: der Monolith hat fuer diesen Fall ebenfalls keine "
              f"eigenen Regeln.")

    return "\n\n---\n\n".join(parts)
