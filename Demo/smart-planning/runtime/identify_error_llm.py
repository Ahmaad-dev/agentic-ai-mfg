"""
Identify Error with LLM Tool
Uses Azure OpenAI to analyze validation errors and automatically trigger the identify tool.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import AzureOpenAI

# Storage Manager (LOCAL / AZURE)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from runtime_storage import get_storage, get_iteration_folders

# AP7.0/AP7.5: rulebook loader + der Karten-Index (Agent waehlt selbst aus, siehe Prompt)
from rulebook_loader import load_rulebook, card_index as rb_card_index

# Load environment variables (aus demo-Verzeichnis)
# Lade .env aus dem demo-Verzeichnis (2 Ebenen höher)
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def load_validation_fix_rules():
    """
    Load the rulebook for error IDENTIFICATION (AP7.0).

    No error_type is passed: this step is what SELECTS the error in the first place, so the
    [validate_*] tag is not known yet. In "cards" mode that means _core.md alone — which is
    exactly what identification needs (prioritisation, search-mode selection, investigation
    decision, action catalogue). In "monolith" mode the full file is loaded as before.
    """
    return load_rulebook()


def derive_error_type_from_message(message: str):
    """
    AP3.6b-1: Derive a reliable error_type from the leading [validate_*] tag of a
    validation message.

    Every validator message starts with a tag like '[validate_<name>] <rest>'. That tag
    is the trustworthy error classifier — unlike the hit-count heuristic in
    identify_snapshot.py, which mislabels e.g. a missing-field error as DUPLICATE_ID
    (see AP3.6a). Example:
        '[validate_work_item_configs_completeness] Article ...' -> 'WORK_ITEM_CONFIGS_COMPLETENESS'

    Returns None (no exception) if no [validate_*] tag is present, so callers get a
    consistent, defensive fallback.
    """
    if not isinstance(message, str):
        return None
    match = re.match(r"\s*\[validate_([^\]]+)\]", message)
    if not match:
        return None
    return match.group(1).strip().upper()


def normalize_field_name(field_name):
    """Convert common field name variations to camelCase"""
    # Common field name mappings
    field_mappings = {
        "worker qualifications": "workerQualifications",
        "work plans": "workPlans",
        "customer order positions": "customerOrderPositions",
        "packaging equipment compatibility": "packagingEquipmentCompatibility",
        "demand id": "demandId",
        "article id": "articleId",
        "equipment key": "equipmentKey"
    }
    
    # Normalize: lowercase and trim
    normalized = field_name.lower().strip()
    
    # Check if we have a mapping
    if normalized in field_mappings:
        return field_mappings[normalized]
    
    # Fallback: remove spaces and convert to camelCase
    words = normalized.split()
    if len(words) > 1:
        return words[0] + ''.join(word.capitalize() for word in words[1:])
    
    return field_name


def load_current_snapshot_id(snapshot_id: str = None):
    """Load snapshot ID. Argument hat Priorität, Fallback auf current_snapshot.txt."""
    if snapshot_id:
        return snapshot_id
    runtime_files_dir = Path(__file__).parent / "runtime-files"
    current_snapshot_file = runtime_files_dir / "current_snapshot.txt"
    
    if not current_snapshot_file.exists():
        print(f"Error: {current_snapshot_file} not found")
        return None
    
    with open(current_snapshot_file, 'r') as f:
        content = f.read().strip()
        if "snapshot_id = " in content:
            return content.split("snapshot_id = ")[1].strip()
        else:
            print(f"Error: Invalid format in {current_snapshot_file}")
            return None


def load_validation_data(snapshot_id):
    """Load validation data from snapshot directory"""
    storage = get_storage()
    data = storage.load_json(f"{snapshot_id}/snapshot-validation.json")
    if data is None:
        print(f"Error: {snapshot_id}/snapshot-validation.json not found")
    return data


def get_next_iteration_number(snapshot_id):
    """Find the highest iteration number and return next number"""
    nums = get_iteration_folders(snapshot_id)
    return (max(nums) + 1) if nums else 1


def save_llm_response(snapshot_id, llm_response, first_error, llm_call_data):
    """Save LLM response and full call data to iteration folder"""
    iteration_number = get_next_iteration_number(snapshot_id)
    storage = get_storage()

    # Prepare data to save
    output_data = {
        "iteration": iteration_number,
        "original_error": first_error,
        "llm_analysis": llm_response
    }

    storage.save_json(f"{snapshot_id}/iteration-{iteration_number}/llm_identify_response.json", output_data)
    print(f"\nLLM response saved: {snapshot_id}/iteration-{iteration_number}/llm_identify_response.json")

    storage.save_json(f"{snapshot_id}/iteration-{iteration_number}/llm_identify_call.json", llm_call_data)
    print(f"Full LLM call saved: {snapshot_id}/iteration-{iteration_number}/llm_identify_call.json")

    # Return a local-compatible Path for the iteration dir (needed by caller)
    from pathlib import Path
    iteration_dir = storage._get_local_path(f"{snapshot_id}/iteration-{iteration_number}") if storage.mode == "LOCAL" else Path(snapshot_id) / f"iteration-{iteration_number}"
    return iteration_dir, iteration_number


def analyze_validation_with_llm(validation_data):
    """Use Azure OpenAI to analyze validation data and identify the first ERROR"""
    
    # Initialize Azure OpenAI client
    client = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION")
    )
    
    # Filter for ERROR messages only
    error_messages = [msg for msg in validation_data if msg.get('level') == 'ERROR']
    
    if not error_messages:
        print("No ERROR messages found in validation data")
        return None
    
    print(f"Found {len(error_messages)} ERROR message(s)")
    print(f"Analyzing ALL ERRORs with LLM to prioritize...")
    
    # Load validation fix rules
    try:
        fix_rules = load_validation_fix_rules()
    except Exception as e:
        print(f"Error loading validation fix rules: {e}")
        return None

    # AP7.5: der VOLLSTAENDIGE Regelbestand als Inhaltsverzeichnis (Datei + Klartext-
    # Beschreibung). Der Agent hat damit jederzeit Zugriff auf alles und waehlt selbst aus,
    # was er liest — ohne dass ein Fachanwender einen Validator-Tag kennen muss.
    try:
        card_index = rb_card_index()
    except Exception as e:
        print(f"WARN: Regelkarten-Index nicht ladbar: {e}")
        card_index = "(nicht verfuegbar)"
    
    # Create prompt for LLM with ALL errors
    prompt = f"""You are analyzing validation errors from a Smart Planning system. 
Your task is to SELECT the MOST CRITICAL error to fix first and extract the relevant information.

ALL Validation Errors ({len(error_messages)} total):
{json.dumps(error_messages, indent=2)}

Please analyze ALL errors using the rules from Section 0 (Error Identification & Prioritization):
1. Identify dependencies - does one error cause others?
2. Determine severity - which error is most critical?
3. Select the BEST error to fix FIRST based on prioritization guidelines
4. Choose the correct search_mode (value vs empty_field) based on the rules
5. Extract the appropriate search_value

Respond in JSON format:
{{
    "selected_error_index": 0,
    "selected_error": {{"level": "ERROR", "message": "..."}},
    "search_mode": "value" or "empty_field",
    "search_value": "the ID value to search for (value mode) OR the field name (empty_field mode)",
    "error_type": "brief description of the selected error",
    "should_investigate": true or false,
    "prioritization_reasoning": "Why this error was selected as most critical (reference Section 0.1)",
    "relevant_cards": ["file.md", "..."],
    "relevant_cards_reasoning": "Warum genau diese Karten zu diesem Fehler passen"
}}

---

# VERFUEGBARE REGELKARTEN (Wissensbestand des Agenten)

Dies ist der VOLLSTAENDIGE Regelbestand. Waehle in "relevant_cards" JEDE Karte aus, deren
Beschreibung zum ausgewaehlten Fehler passt — auch mehrere. Die Beschreibungen stammen von
Fachanwendern und sind in normaler Sprache formuliert; entscheide inhaltlich, nicht nach
Schluesselwoertern. Passt keine, gib eine leere Liste zurueck.

{card_index}

---

# VALIDATION FIX RULES (use Section 0 for error identification):

{fix_rules}
"""
    
    system_message = "You are a helpful assistant that analyzes validation errors and extracts relevant information for investigation."
    
    # Call Azure OpenAI
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        response_format={"type": "json_object"}
    )
    
    # Parse response
    llm_response = json.loads(response.choices[0].message.content)
    
    # Extract the selected error
    selected_index = llm_response.get('selected_error_index', 0)
    selected_error = error_messages[selected_index] if selected_index < len(error_messages) else error_messages[0]

    # AP3.6b-1: additively attach the tag-derived error type (reliable classifier from the
    # [validate_*] tag). The existing free-text `error_type` stays untouched next to it;
    # nothing is overwritten. Always written (None if no tag) for a consistent structure.
    llm_response["tag_error_type"] = derive_error_type_from_message(selected_error.get("message", ""))

    # Prepare full LLM call data for logging
    llm_call_data = {
        "request": {
            "model": os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "response_format": {"type": "json_object"}
        },
        "response": {
            "content": llm_response,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    }
    
    print(f"\nLLM Analysis:")
    print(f"   Total Errors Analyzed: {len(error_messages)}")
    print(f"   Selected Error Index: {selected_index}")
    print(f"   Prioritization: {llm_response.get('prioritization_reasoning', 'N/A')}")
    print(f"   Search Mode: {llm_response.get('search_mode')}")
    print(f"   Search Value: {llm_response.get('search_value')}")
    print(f"   Error Type: {llm_response.get('error_type')}")
    print(f"   Should Investigate: {llm_response.get('should_investigate')}")
    
    return llm_response, selected_error, llm_call_data


def trigger_identify_tool(search_mode, search_value, snapshot_id: str = None):
    """Trigger the identify_snapshot.py tool with the given search mode and value"""
    
    # Normalize field names for empty_field mode
    if search_mode == "empty_field":
        search_value = normalize_field_name(search_value)
    
    identify_script = Path(__file__).parent / "identify_snapshot.py"
    
    if not identify_script.exists():
        print(f"Error: {identify_script} not found")
        return False
    
    # Build command based on search mode
    # Always pass --snapshot-id when available to avoid relying on current_snapshot.txt
    snapshot_args = ["--snapshot-id", snapshot_id] if snapshot_id else []
    if search_mode == "empty_field":
        command_args = [sys.executable, str(identify_script)] + snapshot_args + ["--empty", search_value]
        print(f"\nTriggering identify tool in EMPTY FIELD mode for: {search_value}")
    else:
        command_args = [sys.executable, str(identify_script)] + snapshot_args + [search_value]
        print(f"\nTriggering identify tool in VALUE mode with: {search_value}")
    
    print("=" * 80)
    
    # Run the identify_snapshot.py script
    try:
        result = subprocess.run(
            command_args,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print("Identify tool completed successfully")
            return True
        else:
            print(f"Identify tool exited with code {result.returncode}")
            return False
            
    except Exception as e:
        print(f"Error running identify tool: {e}")
        return False


def main():
    """Main function"""
    import argparse
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--snapshot-id", dest="snapshot_id", default=None,
                        help="Snapshot UUID (optional, Fallback auf current_snapshot.txt)")
    parser.add_argument("--demo", action="store_true", help="Demo-Modus")
    args, _ = parser.parse_known_args()

    print("Starting LLM-based Error Analysis\n")
    
    demo_mode = args.demo
    snapshot_id = args.snapshot_id
    
    if demo_mode:
        print("DEMO MODE: Using test validation data\n")
        validation_data = [
            {
                "level": "ERROR",
                "message": "[validate_demand_uniqueness] Duplicate demand IDs found: D830081_005 appears 2 times in demands list"
            }
        ]
        snapshot_id = "demo-snapshot"
    else:
        # Snapshot-ID bestimmen (Argument hat Priorität)
        if not snapshot_id:
            snapshot_id = load_current_snapshot_id()
            if not snapshot_id:
                print("ERROR: No snapshot ID provided")
                return
            print(f"Snapshot ID from current_snapshot.txt: {snapshot_id}\n")
        else:
            print(f"Using Snapshot ID from argument: {snapshot_id}\n")
    
    # Step 2: Load validation data
    if not demo_mode:
        validation_data = load_validation_data(snapshot_id)
        if validation_data is None:
            return
    
    print(f"Validation data loaded: {len(validation_data)} message(s)\n")
    
    # Step 3: Analyze with LLM
    result = analyze_validation_with_llm(validation_data)
    if result is None:
        return
    
    llm_analysis, first_error, llm_call_data = result
    
    # Step 4: Save LLM response to iteration folder
    if not demo_mode:
        iteration_dir, iteration_number = save_llm_response(snapshot_id, llm_analysis, first_error, llm_call_data)
        print(f"Created iteration folder: iteration-{iteration_number}")
    
    # Step 5: Trigger identify tool if LLM recommends it
    if llm_analysis.get('should_investigate', False):
        search_mode = llm_analysis.get('search_mode', 'value')
        search_value = llm_analysis.get('search_value')
        if search_value:
            if not demo_mode:
                trigger_identify_tool(search_mode, search_value, snapshot_id)
            else:
                print(f"\nDEMO MODE: Would trigger identify tool")
                print(f"   Mode: {search_mode}")
                print(f"   Value: {search_value}")
        else:
            print("LLM did not provide a search value")
    else:
        print("\nLLM analysis suggests no specific investigation needed")
        print(f"   Reason: {llm_analysis.get('error_type', 'No specific ID found')}")


if __name__ == "__main__":
    main()
