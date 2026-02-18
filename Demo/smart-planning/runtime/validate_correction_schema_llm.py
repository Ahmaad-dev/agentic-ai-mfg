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
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from runtime_storage import get_storage, get_iteration_folders_with_file

from correction_models import LLMCorrectionResponse

# Load environment variables (aus demo-Verzeichnis)
# Lade .env aus dem demo-Verzeichnis (2 Ebenen höher)
env_path = Path(__file__).parent.parent.parent / ".env"
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
    
    # Load fix rules
    fix_rules_file = Path("runtime-files/llm-validation-fix-rules.md")
    fix_rules = fix_rules_file.read_text(encoding='utf-8')
    
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


def validate_with_retry(snapshot_id, iteration_number, correction_proposal, max_retries=5):
    """
    Validate correction proposal with retry logic.
    On successful retry: OVERWRITES llm_correction_proposal.json
    Returns validated proposal or exits with error.
    """
    retry_count = 0
    valid = False
    validated_proposal = None
    current_proposal = correction_proposal
    storage = get_storage()
    original_saved = False

    while not valid and retry_count <= max_retries:
        if retry_count > 0:
            print(f"\n--- Retry {retry_count}/{max_retries} ---")
        
        print(f"Validating correction proposal schema...")
        valid, validated_proposal, validation_error = validate_correction_proposal(current_proposal)
        
        if valid:
            # Success!
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
                
                # Save retry attempt
                storage.save_json(f"{snapshot_id}/iteration-{iteration_number}/llm_correction_proposal_retry_{retry_count}.json", current_proposal)
                print(f"   Saved as: llm_correction_proposal_retry_{retry_count}.json")
            else:
                print(f"\nERROR Max retries ({max_retries}) reached. Schema validation failed.")
                print(f"Please check llm_correction_proposal.json manually.")
                sys.exit(1)
    
    return current_proposal


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

    # Get latest iteration number using storage helper
    storage = get_storage()
    valid_nums = get_iteration_folders_with_file(snapshot_id, "llm_correction_proposal.json")
    if not valid_nums:
        print("ERROR No iteration folders with llm_correction_proposal.json found")
        sys.exit(1)
    iteration_number = max(valid_nums)

    print(f"Using iteration: {iteration_number}\n")

    # Load correction proposal
    correction_proposal = storage.load_json(f"{snapshot_id}/iteration-{iteration_number}/llm_correction_proposal.json")
    if correction_proposal is None:
        print("ERROR Could not load llm_correction_proposal.json")
        sys.exit(1)
    
    # Validate with retry
    validated_proposal = validate_with_retry(snapshot_id, iteration_number, correction_proposal)
    
    print("\n=== Validation Complete ===")
    print("Correction proposal is valid and ready to apply.")


if __name__ == "__main__":
    main()
