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

from correction_models import LLMCorrectionResponse

# Load environment variables
load_dotenv()


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
    iteration_folder = Path("..") / "Snapshots" / snapshot_id / f"iteration-{iteration_number}"
    
    # Load identify response
    identify_file = iteration_folder / "llm_identify_response.json"
    with open(identify_file, 'r', encoding='utf-8') as f:
        identify_response = json.load(f)
    
    # Load search results
    snapshot_folder = Path("..") / "Snapshots" / snapshot_id
    search_results_file = snapshot_folder / "last_search_results.json"
    with open(search_results_file, 'r', encoding='utf-8') as f:
        search_results = json.load(f)
    
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
    iteration_folder = Path("..") / "Snapshots" / snapshot_id / f"iteration-{iteration_number}"
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
                proposal_file = iteration_folder / "llm_correction_proposal.json"
                with open(proposal_file, 'w', encoding='utf-8') as f:
                    json.dump(current_proposal, f, indent=2, ensure_ascii=False)
                print(f"OK Retry successful - llm_correction_proposal.json OVERWRITTEN with corrected version")
            else:
                print(f"OK Schema validation passed")
            return current_proposal
        else:
            print(f"ERROR Schema validation failed:")
            print(f"   {validation_error}")
            
            # Save original as retry_0.json (only once)
            if not original_saved:
                retry_0_file = iteration_folder / "llm_correction_proposal_retry_0.json"
                with open(retry_0_file, 'w', encoding='utf-8') as f:
                    json.dump(correction_proposal, f, indent=2, ensure_ascii=False)
                print(f"   Saved original invalid JSON as: {retry_0_file.name}")
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
                retry_file = iteration_folder / f"llm_correction_proposal_retry_{retry_count}.json"
                with open(retry_file, 'w', encoding='utf-8') as f:
                    json.dump(current_proposal, f, indent=2, ensure_ascii=False)
                print(f"   Saved as: {retry_file.name}")
            else:
                print(f"\nERROR Max retries ({max_retries}) reached. Schema validation failed.")
                print(f"Please check llm_correction_proposal.json manually.")
                sys.exit(1)
    
    return current_proposal


def main():
    """Main entry point for standalone execution"""
    print("=== Correction Proposal Schema Validator ===\n")
    
    # Load snapshot ID
    current_snapshot_file = Path("runtime-files/current_snapshot.txt")
    if not current_snapshot_file.exists():
        print("ERROR runtime-files/current_snapshot.txt not found")
        sys.exit(1)
    
    snapshot_id = current_snapshot_file.read_text().strip()
    if snapshot_id.startswith("snapshot_id = "):
        snapshot_id = snapshot_id.replace("snapshot_id = ", "").strip()
    
    print(f"Snapshot ID: {snapshot_id}")
    
    # Get latest iteration number
    snapshot_folder = Path("..") / "Snapshots" / snapshot_id
    iteration_folders = [
        d for d in snapshot_folder.iterdir()
        if d.is_dir() and d.name.startswith("iteration-")
    ]
    
    valid_iterations = [
        d for d in iteration_folders
        if (d / "llm_correction_proposal.json").exists()
    ]
    
    if not valid_iterations:
        print("ERROR No iteration folders with llm_correction_proposal.json found")
        sys.exit(1)
    
    import re
    iteration_numbers = [
        int(re.match(r'^iteration-(\d+)$', d.name).group(1))
        for d in valid_iterations
    ]
    iteration_number = max(iteration_numbers)
    
    print(f"Using iteration: {iteration_number}\n")
    
    # Load correction proposal
    proposal_file = Path("..") / "Snapshots" / snapshot_id / f"iteration-{iteration_number}" / "llm_correction_proposal.json"
    with open(proposal_file, 'r', encoding='utf-8') as f:
        correction_proposal = json.load(f)
    
    # Validate with retry
    validated_proposal = validate_with_retry(snapshot_id, iteration_number, correction_proposal)
    
    print("\n=== Validation Complete ===")
    print("Correction proposal is valid and ready to apply.")


if __name__ == "__main__":
    main()
