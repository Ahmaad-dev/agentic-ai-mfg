"""
Schema Validator for LLM Correction Proposals

Validates llm_correction_proposal.json against Pydantic schema.
If validation fails, calls LLM again to fix schema errors (max 3 retries).
"""

import json
import os
import sys
from pathlib import Path
from pydantic import ValidationError
from openai import AzureOpenAI
from dotenv import load_dotenv

# Storage Manager (LOCAL / AZURE)
import sys
sys.path.insert(0, str(Path(__file__).parents[3]))
from runtime_storage import get_storage, get_iteration_folders_with_file

# AP7.0: rulebook loader (monolith vs. error-type cards, switched via RULEBOOK_MODE)
from core.rulebook_loader import load_rulebook

from correction_models import LLMCorrectionResponse

# Load environment variables (aus dem Anwendungsverzeichnis app/)
# Lade .env aus dem Anwendungsverzeichnis app/ (drei Ebenen höher, siehe parents[3])
env_path = Path(__file__).parents[3] / ".env"
load_dotenv(dotenv_path=env_path)


def validate_correction_proposal(correction_proposal):
    """Validate correction proposal against Pydantic schema"""
    try:
        validated = LLMCorrectionResponse(**correction_proposal)
        return True, validated, None
    except ValidationError as e:
        return False, None, e


def retry_llm_with_schema_error(snapshot_id, iteration_number, validation_error, correction_proposal):
    """Call LLM again with schema validation error"""
    print(f"\nWARNING Schema validation failed. Requesting LLM to fix the schema...")
    
    # Load original inputs
    storage = get_storage()

    # Load identify response
    identify_response = storage.load_json(f"{snapshot_id}/iteration-{iteration_number}/llm_identify_response.json")
    if identify_response is None:
        raise FileNotFoundError(f"llm_identify_response.json not found in iteration-{iteration_number}")

    # Load search results
    search_results = storage.load_json(f"{snapshot_id}/last_search_results.json")
    if search_results is None:
        raise FileNotFoundError(f"last_search_results.json not found for snapshot {snapshot_id}")
    
    # Load fix rules (AP7.0: monolith, or _core.md + the card for this error's [validate_*] tag)
    fix_rules = load_rulebook((identify_response.get("llm_analysis") or {}).get("tag_error_type"))
    
    # Build retry prompt
    retry_prompt = f"""Your previous response had JSON schema validation errors.

**VALIDATION ERRORS:**
{validation_error.json()}

**YOUR INVALID RESPONSE:**
```json
{json.dumps(correction_proposal, indent=2)}
```

**REQUIRED JSON SCHEMA:**
{{
  "iteration": int,
  "snapshot_id": str,
  "original_error": {{
    "level": str,
    "message": str
  }},
  "error_analyzed": {{
    "search_mode": str,
    "search_value": str (optional),
    "error_type": str,
    "results_count": int
  }},
  "correction_proposal": {{
    "action": str,
    "target_path": str,
    "current_value": str,
    "new_value": str,
    "reasoning": str,
    "additional_updates": [
      {{
        "target_path": str,
        "current_value": str,
        "new_value": str
      }}
    ] (optional)
  }}
}}

**ORIGINAL INPUTS:**

**Validation Fix Rules:**
{fix_rules}

**Original Error:**
{json.dumps(identify_response['original_error'], indent=2)}

**Error Analysis:**
{json.dumps(identify_response.get('llm_analysis', identify_response.get('error_analyzed', {})), indent=2)}

**Search Results:**
{json.dumps(search_results, indent=2)}

Please provide a corrected JSON response that matches the schema exactly.
"""
    
    # Call LLM
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    
    print(f"  Calling Azure OpenAI...")
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        messages=[
            {"role": "system", "content": "You are a data correction expert. Fix your JSON schema errors."},
            {"role": "user", "content": retry_prompt}
        ],
        temperature=0.3,
        response_format={"type": "json_object"}
    )
    
    # Parse response
    response_data = json.loads(response.choices[0].message.content)
    
    return response_data


def _load_latest_proposal(snapshot_id):
    """
    Neueste Iteration mit `llm_correction_proposal.json` und den Vorschlag selbst.

    Additiv ergaenzt (BA / AP-D1, 2026-08-19): main() und der Graph-Knoten brauchen beide
    genau diesen Schritt. Eine Implementierung, damit die beiden Pfade nicht auseinanderlaufen
    koennen — main() haengt seine CLI-Semantik (Meldung + sys.exit) selbst daran.

    Returns: (iteration_number, correction_proposal) oder (None, None).
    """
    valid_nums = get_iteration_folders_with_file(snapshot_id, "llm_correction_proposal.json")
    if not valid_nums:
        return None, None
    n = max(valid_nums)
    return n, get_storage().load_json(f"{snapshot_id}/iteration-{n}/llm_correction_proposal.json")


def validate_with_retry(snapshot_id, iteration_number, correction_proposal, max_retries=5,
                        exit_on_failure=True, stats=None):
    """
    Validate correction proposal with retry logic.
    On successful retry: OVERWRITES llm_correction_proposal.json
    Returns validated proposal or exits with error.

    ZWEI ADDITIVE PARAMETER (BA / AP-D1, 2026-08-19) — Defaults = bisheriges Verhalten:

      exit_on_failure  True  (Default, CLI): bei erschoepften Retries `sys.exit(1)` wie bisher.
                       False (Graph-Knoten): gibt `None` zurueck. Ein Knoten darf den Prozess
                       NICHT beenden — sonst kann die bedingte Kante nicht mehr auf
                       `stop_uncertain` entscheiden (BA_MASTERPLAN Kap. 11).
      stats            dict, das mit {"retries": int, "errors": list[str]} gefuellt wird.
                       `retries` = ZUSATZVERSUCHE NACH DEM ERSTEN, also die Zahl der
                       tatsaechlich ausgefuehrten LLM-Retries. 0 = beim ersten Versuch gueltig.
                       Obergrenze ist `max_retries`; mehr als `max_retries` kann nicht
                       herauskommen. Der Graph braucht die Zahl fuer
                       `GraphState["technical_check"]`; ohne den Parameter aendert sich nichts.
    """
    retry_count = 0
    valid = False
    validated_proposal = None
    current_proposal = correction_proposal
    storage = get_storage()
    original_saved = False
    seen_errors = []
    # AP-D1-Nachbesserung (19.08.): `retry_count` wird VOR der Schranke erhoeht und ist damit
    # bei erschoepften Versuchen um eins zu hoch (max_retries=5 -> 6). Dieser Zaehler zaehlt
    # die TATSAECHLICH ausgefuehrten LLM-Retries und ist das, was in `stats["retries"]` geht.
    llm_retries_done = 0

    while not valid and retry_count <= max_retries:
        if retry_count > 0:
            print(f"\n--- Retry {retry_count}/{max_retries} ---")
        
        print(f"Validating correction proposal schema...")
        valid, validated_proposal, validation_error = validate_correction_proposal(current_proposal)
        
        if valid:
            # Success!
            if stats is not None:
                stats["retries"] = llm_retries_done
                stats["errors"] = seen_errors
            if retry_count > 0:
                # Retry was successful - OVERWRITE original file
                storage.save_json(f"{snapshot_id}/iteration-{iteration_number}/llm_correction_proposal.json", current_proposal)
                print(f"OK Retry successful - llm_correction_proposal.json OVERWRITTEN with corrected version")
            else:
                print(f"OK Schema validation passed")
            return current_proposal
        else:
            print(f"ERROR Schema validation failed:")
            print(f"   {validation_error}")
            seen_errors.append(str(validation_error))

            # Save original as retry_0.json (only once)
            if not original_saved:
                storage.save_json(f"{snapshot_id}/iteration-{iteration_number}/llm_correction_proposal_retry_0.json", correction_proposal)
                print(f"   Saved original invalid JSON as: llm_correction_proposal_retry_0.json")
                original_saved = True
            
            retry_count += 1
            
            if retry_count <= max_retries:
                # Retry with LLM
                current_proposal = retry_llm_with_schema_error(
                    snapshot_id, 
                    iteration_number, 
                    validation_error,
                    current_proposal
                )
                
                llm_retries_done += 1
                # Save retry attempt
                storage.save_json(f"{snapshot_id}/iteration-{iteration_number}/llm_correction_proposal_retry_{retry_count}.json", current_proposal)
                print(f"   Saved as: llm_correction_proposal_retry_{retry_count}.json")
            else:
                print(f"\nERROR Max retries ({max_retries}) reached. Schema validation failed.")
                if stats is not None:
                    stats["retries"] = llm_retries_done
                    stats["errors"] = seen_errors
                if exit_on_failure:
                    print(f"Please check llm_correction_proposal.json manually.")
                    sys.exit(1)
                # Graph-Pfad (AP-D1): strukturiert scheitern statt den Prozess beenden.
                return None
    
    return current_proposal


def _proposal_sha256(obj):
    """Kanonischer Hash eines Vorschlags. Eine Definition fuer H_before und H_after."""
    if obj is None:
        return None
    import hashlib as _h, json as _j
    return _h.sha256(_j.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def run_technical_check(snapshot_id, iteration_number=None, correction_proposal=None,
                        max_retries=5) -> dict:
    """
    KNOTEN 6 — Technische Pruefung (BA / AP-D1, 2026-08-19).

    Aufrufbar aus dem Graphen; ruft dieselbe `validate_with_retry()` wie die CLI, nur ohne
    `sys.exit`. Es gibt weiterhin GENAU EINE Implementierung der Retry-Logik — dieser Wrapper
    ergaenzt nur Laden und Zustandsformung (BA_MASTERPLAN Kap. 12.2).

    Beobachtungspunkt fuer **Kategorie 2, strukturelle Halluzination** (Kap. 15.1). Erzeugt
    wird sie in Knoten 5; hier wird sie nur ERKANNT.

    Args:
        iteration_number / correction_proposal: optional. Fehlen sie, wird die neueste
        Iteration geladen — derselbe Weg, den die CLI nimmt.

    Returns: dict fuer `GraphState["technical_check"]`:
        {schema_valid: bool, retries: int, errors: list[str],
         proposal: dict|None, iteration_number: int|None}

    Wirft NICHT und beendet den Prozess NICHT. Ein fehlgeschlagener Schema-Check ist ein
    ZUSTAND, ueber den die bedingte Kante entscheidet (Kap. 11) — kein Programmabbruch.
    """
    # VERTRAG, explizit gemacht (BA-043). Vorher stand hier `or`, und ein uebergebenes
    # Proposal wurde allein deshalb verworfen, weil die Iterationsnummer fehlte - der State
    # von Knoten 5 ging verloren und geprueft wurde die Platte (BA-042).
    # Die drei Faelle werden jetzt GETRENNT behandelt; ein vorhandener Wert wird nie
    # ueberschrieben:
    #   beides fehlt   -> Legacy/CLI: bisheriger Disk-Fallback, unveraendert
    #   nur Nummer     -> Proposal behalten, Nummer aus der Platte ergaenzen
    #   nur Proposal   -> Nummer behalten, Proposal aus der Platte ergaenzen
    #   beides da      -> nichts laden
    if iteration_number is None and correction_proposal is None:
        iteration_number, correction_proposal = _load_latest_proposal(snapshot_id)
    elif iteration_number is None:
        iteration_number, _ = _load_latest_proposal(snapshot_id)
    elif correction_proposal is None:
        _, correction_proposal = _load_latest_proposal(snapshot_id)

    # Hash VOR der Pruefung - Gegenstueck zu `proposal_sha256_after`. Ein technischer Retry
    # darf den Vorschlag legitim veraendern; sichtbar sein muss es trotzdem.
    _vorher_hash = _proposal_sha256(correction_proposal)

    if correction_proposal is None:
        return {"schema_valid": False, "retries": 0,
                "errors": ["llm_correction_proposal.json nicht gefunden — "
                           "Knoten 5 hat keinen Vorschlag hinterlassen."],
                "proposal": None, "iteration_number": iteration_number,
                "proposal_sha256_before": _vorher_hash, "proposal_sha256_after": None}

    stats = {"retries": 0, "errors": []}
    try:
        validated = validate_with_retry(snapshot_id, iteration_number, correction_proposal,
                                        max_retries=max_retries, exit_on_failure=False,
                                        stats=stats)
    except Exception as exc:
        # Defensiv: auch ein unerwarteter Fehler (z. B. LLM-Timeout im Retry) darf den Graphen
        # nicht toeten, sondern muss als Zustand sichtbar werden.
        return {"schema_valid": False, "retries": stats.get("retries", 0),
                "errors": stats.get("errors", []) + [f"{type(exc).__name__}: {exc}"],
                "proposal": None, "iteration_number": iteration_number,
                "proposal_sha256_before": _vorher_hash, "proposal_sha256_after": None}

    return {"schema_valid": validated is not None,
            "retries": stats.get("retries", 0),
            "errors": stats.get("errors", []),
            # DER AUTORITATIVE VORSCHLAG nach der Pruefung. Bei einem Retry ist das eine
            # ANDERE Version als die von Knoten 5 - genau deshalb muss sie zurueck in den
            # State, sonst haelt Knoten 7 den alten Stand fuer massgeblich (BA-042).
            "proposal": validated,
            "iteration_number": iteration_number,
            "proposal_sha256_before": _vorher_hash,
            "proposal_sha256_after": _proposal_sha256(validated)}


def main():
    """Main entry point for standalone execution"""
    import argparse
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--snapshot-id", dest="snapshot_id", default=None,
                        help="Snapshot UUID (optional, Fallback auf current_snapshot.txt)")
    args, _ = parser.parse_known_args()

    print("=== Correction Proposal Schema Validator ===\n")
    
    # Snapshot-ID bestimmen: Argument hat Priorität, Fallback auf Datei
    snapshot_id = args.snapshot_id
    if not snapshot_id:
        current_snapshot_file = Path("runtime-files/current_snapshot.txt")
        if not current_snapshot_file.exists():
            print("ERROR runtime-files/current_snapshot.txt not found")
            sys.exit(1)
        snapshot_id = current_snapshot_file.read_text().strip()
        if snapshot_id.startswith("snapshot_id = "):
            snapshot_id = snapshot_id.replace("snapshot_id = ", "").strip()
    
    print(f"Snapshot ID: {snapshot_id}")

    # Get latest iteration + proposal (AP-D1: gemeinsamer Helfer mit dem Graph-Knoten, damit
    # die beiden Pfade nicht auseinanderlaufen. Die CLI-Semantik — Meldung und Exit-Code —
    # bleibt hier und ist unveraendert.)
    iteration_number, correction_proposal = _load_latest_proposal(snapshot_id)
    if iteration_number is None:
        print("ERROR No iteration folders with llm_correction_proposal.json found")
        sys.exit(1)

    print(f"Using iteration: {iteration_number}\n")

    if correction_proposal is None:
        print("ERROR Could not load llm_correction_proposal.json")
        sys.exit(1)

    # Validate with retry
    validated_proposal = validate_with_retry(snapshot_id, iteration_number, correction_proposal)
    
    print("\n=== Validation Complete ===")
    print("Correction proposal is valid and ready to apply.")


if __name__ == "__main__":
    main()
