"""
LLM-based Correction Proposal Generator

Generates structured correction proposals for validation errors using Azure OpenAI.
Reads validation-fix-rules.md and last_search_results.json to create actionable corrections.
"""

import json
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load environment variables
load_dotenv()

def load_current_snapshot_id():
    """Load the current snapshot ID from runtime-files/current_snapshot.txt"""
    current_snapshot_file = Path("runtime-files/current_snapshot.txt")
    if not current_snapshot_file.exists():
        raise FileNotFoundError("runtime-files/current_snapshot.txt not found")
    
    snapshot_id = current_snapshot_file.read_text().strip()
    if not snapshot_id:
        raise ValueError("current_snapshot.txt is empty")
    
    # Remove "snapshot_id = " prefix if present
    if snapshot_id.startswith("snapshot_id = "):
        snapshot_id = snapshot_id.replace("snapshot_id = ", "").strip()
    
    return snapshot_id

def load_validation_fix_rules():
    """Load the validation fix rules document"""
    rules_file = Path("runtime-files/llm-validation-fix-rules.md")
    if not rules_file.exists():
        raise FileNotFoundError("llm-validation-fix-rules.md not found")
    
    return rules_file.read_text(encoding='utf-8')

def load_search_results(snapshot_id):
    """Load the last_search_results.json from the snapshot folder"""
    snapshot_folder = Path("..") / "Snapshots" / snapshot_id
    search_results_file = snapshot_folder / "last_search_results.json"
    
    if not search_results_file.exists():
        raise FileNotFoundError(f"last_search_results.json not found in {snapshot_folder}")
    
    with open(search_results_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_identify_response(snapshot_id):
    """Load llm_identify_response.json from the latest iteration folder"""
    snapshot_folder = Path("..") / "Snapshots" / snapshot_id
    
    # Find highest iteration folder
    iteration_folders = [
        d for d in snapshot_folder.iterdir()
        if d.is_dir() and re.match(r'^iteration-(\d+)$', d.name)
    ]
    
    if not iteration_folders:
        raise FileNotFoundError(f"No iteration folders found in {snapshot_folder}")
    
    # Get latest iteration
    latest_iteration = max(iteration_folders, 
                          key=lambda d: int(re.match(r'^iteration-(\d+)$', d.name).group(1)))
    
    identify_file = latest_iteration / "llm_identify_response.json"
    if not identify_file.exists():
        raise FileNotFoundError(f"llm_identify_response.json not found in {latest_iteration}")
    
    with open(identify_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_latest_iteration_number(snapshot_id):
    """Find the highest iteration folder that contains llm_identify_response.json"""
    snapshot_folder = Path("..") / "Snapshots" / snapshot_id
    
    if not snapshot_folder.exists():
        raise FileNotFoundError(f"Snapshot folder not found: {snapshot_folder}")
    
    iteration_folders = [
        d for d in snapshot_folder.iterdir()
        if d.is_dir() and re.match(r'^iteration-(\d+)$', d.name)
    ]
    
    if not iteration_folders:
        raise FileNotFoundError(f"No iteration folders found in {snapshot_folder}")
    
    # Filter for folders that contain llm_identify_response.json
    valid_iterations = [
        d for d in iteration_folders
        if (d / "llm_identify_response.json").exists()
    ]
    
    if not valid_iterations:
        raise FileNotFoundError(f"No iteration folders with llm_identify_response.json found")
    
    # Get highest valid iteration number
    iteration_numbers = [
        int(re.match(r'^iteration-(\d+)$', d.name).group(1))
        for d in valid_iterations
    ]
    
    return max(iteration_numbers)

def save_correction_proposal(snapshot_id, iteration_number, proposal_data, llm_call_data):
    """Save the correction proposal and LLM call details to iteration folder"""
    snapshot_folder = Path("..") / "Snapshots" / snapshot_id
    iteration_folder = snapshot_folder / f"iteration-{iteration_number}"
    iteration_folder.mkdir(exist_ok=True)
    
    # Save correction proposal
    proposal_file = iteration_folder / "llm_correction_proposal.json"
    with open(proposal_file, 'w', encoding='utf-8') as f:
        json.dump(proposal_data, f, indent=2, ensure_ascii=False)
    
    # Save full LLM call details
    call_file = iteration_folder / "llm_correction_call.json"
    with open(call_file, 'w', encoding='utf-8') as f:
        json.dump(llm_call_data, f, indent=2, ensure_ascii=False)
    
    print(f"Saved correction proposal to: {proposal_file}")
    print(f"Saved LLM call details to: {call_file}")

def generate_correction_with_llm(fix_rules, identify_response, search_results):
    """Generate correction proposal using Azure OpenAI"""
    
    # Initialize Azure OpenAI client
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    
    # Build prompt
    prompt = f"""You are a data correction expert for Smart Planning API snapshots.

INPUT DATA EXPLANATION:
1. VALIDATION FIX RULES: Mandatory correction strategies for different error types. Follow these rules exactly.
2. ORIGINAL ERROR: Raw validation message from the Smart Planning API validator showing what failed.
3. ERROR ANALYSIS: Interpreted error type and search parameters from the analysis tool.
4. SEARCH RESULTS: Located error with enriched context containing:
   - enriched_context.field_examples: Valid values for reference (use to understand correct formats)
   - enriched_context.format_patterns: Detected ID patterns with statistics (use to generate new IDs)
   - enriched_context.related_entities: Similar entries and all valid IDs (use to find gaps or duplicates)
   - reference_data_available: If true, reference data from a valid snapshot is available as fallback
   - reference_data: Sample entries (first 3) from reference snapshot
   - reference_data_count: Total number of entries available in reference
   - fallback_solution: If "reference_data", use reference snapshot to populate empty array

HOW TO USE THE DATA:
- PLAN A: Check field_examples to see what valid values look like (preferred)
- PLAN A: Use format_patterns to detect ID naming conventions (preferred)
- PLAN A: Use related_entities to find missing sequence numbers or similar entries (preferred)
- PLAN B: If reference_data_available=true AND fallback_solution="reference_data", propose to copy from reference
- Follow the pattern exactly when generating new values

---

VALIDATION FIX RULES:
{fix_rules}

ORIGINAL ERROR:
{json.dumps(identify_response.get('original_error', {}), indent=2, ensure_ascii=False)}

ERROR ANALYSIS:
{json.dumps(identify_response.get('llm_analysis', {}), indent=2, ensure_ascii=False)}

SEARCH RESULTS (Error Context):
{json.dumps(search_results, indent=2, ensure_ascii=False)}

---

TASK:
Analyze the error and generate a structured correction proposal following the fix rules.

CRITICAL DECISION RULES:

0. TARGET PATH EXTRACTION (MOST IMPORTANT):
   **ALWAYS extract target_path from the SEARCH RESULTS, NEVER construct it yourself!**
   - Search results contain "path" field like "articles[40].articleId" or "demands[165].demandId"
   - Use this EXACT path as base, then append the field that needs correction
   - Example: If error is about "rel_density_min" and path is "articles[40].articleId", use "articles[40].rel_density_min"
   - **NEVER use the search_value as array index** (e.g., WRONG: "articles[106270]" when search_value="106270")
   - The search_value might be an ID value (106270), but the array index is in the path field!

1. MANUAL INTERVENTION REQUIRED:
   If search_results contains "manual_intervention_required": true:
   - Use "action": "manual_intervention_required"
   - Set "target_path": to the problematic field path
   - Set "reasoning": Explain why automatic correction is not possible (include the "reason" from search_results)
   - Do NOT attempt any automatic correction
   - This happens when reference data fallback is disabled or no solution exists

2. REFERENCE DATA FALLBACK (when enabled):
   If search_results contains "fallback_solution": "reference_data":
   - Use "action": "update_field"
   - Set "new_value": "USE_REFERENCE_DATA" 
   - Add to reasoning: "Using reference snapshot as fallback (contains X entries). ⚠ Manual verification recommended."
   - This will copy all entries from the reference snapshot

OUTPUT FORMAT (JSON):
{{
  "action": "update_field" OR "manual_intervention_required",
  "target_path": "exact.path[index].field",
  "current_value": "current value",
  "new_value": "corrected value" OR null (for manual_intervention_required),
  "reasoning": "Explanation of why this correction is proposed OR why manual intervention is needed",
  "additional_updates": [
    {{
      "target_path": "path.to.reference",
      "current_value": "old",
      "new_value": "new"
    }}
  ]
}}
"""
    
    # Make API call
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        messages=[
            {"role": "system", "content": "You are a precise data correction expert. Always respond with valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        response_format={"type": "json_object"}
    )
    
    # Parse response
    correction_proposal = json.loads(response.choices[0].message.content)
    
    # Build LLM call log
    llm_call_data = {
        "request": {
            "model": os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            "temperature": 0.3,
            "messages": [
                {"role": "system", "content": "You are a precise data correction expert. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ]
        },
        "response": {
            "content": correction_proposal,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    }
    
    return correction_proposal, llm_call_data

def main():
    print("=== LLM Correction Proposal Generator ===\n")
    
    # Load snapshot ID
    snapshot_id = load_current_snapshot_id()
    print(f"Snapshot ID: {snapshot_id}\n")
    
    # Get latest iteration number (use existing, don't create new)
    iteration_number = get_latest_iteration_number(snapshot_id)
    print(f"Using existing iteration: {iteration_number}\n")
    
    # Load inputs
    print("Loading inputs...")
    fix_rules = load_validation_fix_rules()
    identify_response = load_identify_response(snapshot_id)
    search_results = load_search_results(snapshot_id)
    print(f"- Fix rules loaded ({len(fix_rules)} chars)")
    print(f"- Error analysis loaded (iteration {identify_response.get('iteration')})")
    print(f"- Search results loaded ({search_results['results_count']} results)\n")
    
    # Generate correction proposal
    print("Generating correction proposal with LLM...")
    correction_proposal, llm_call_data = generate_correction_with_llm(fix_rules, identify_response, search_results)
    
    print(f"\nProposal generated:")
    print(f"- Action: {correction_proposal.get('action')}")
    print(f"- Target: {correction_proposal.get('target_path')}")
    print(f"- New Value: {correction_proposal.get('new_value')}")
    print(f"- Additional Updates: {len(correction_proposal.get('additional_updates', []))}")
    
    # Build final output
    output_data = {
        "iteration": iteration_number,
        "snapshot_id": snapshot_id,
        "original_error": identify_response.get("original_error", {}),
        "error_analyzed": {
            "search_mode": search_results.get("search_mode"),
            "search_value": search_results.get("search_value"),
            "error_type": search_results.get("error_type"),
            "results_count": search_results.get("results_count")
        },
        "correction_proposal": correction_proposal
    }
    
    # Save output
    save_correction_proposal(snapshot_id, iteration_number, output_data, llm_call_data)
    
    print("\nToken Usage:")
    print(f"- Prompt: {llm_call_data['response']['usage']['prompt_tokens']}")
    print(f"- Completion: {llm_call_data['response']['usage']['completion_tokens']}")
    print(f"- Total: {llm_call_data['response']['usage']['total_tokens']}")
    
    print("\n=== Done ===")

if __name__ == "__main__":
    main()
