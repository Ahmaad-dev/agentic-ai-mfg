"""
Correction Applier

Applies LLM-generated correction proposals to snapshot-data.json.
Backs up original files to iteration folder before applying changes.

NOTE: This tool expects llm_correction_proposal.json to be already validated!
      Run validate_correction_schema_llm.py BEFORE this tool.
"""

import json
import re
import shutil
import sys
from pathlib import Path

# UTF-8 Encoding für Windows-Terminal
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
from datetime import datetime
from pydantic import ValidationError

from correction_models import LLMCorrectionResponse

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

def get_latest_iteration_number(snapshot_id):
    """Find the highest iteration folder that contains llm_correction_proposal.json"""
    snapshot_folder = Path("..") / "Snapshots" / snapshot_id
    
    if not snapshot_folder.exists():
        raise FileNotFoundError(f"Snapshot folder not found: {snapshot_folder}")
    
    iteration_folders = [
        d for d in snapshot_folder.iterdir()
        if d.is_dir() and re.match(r'^iteration-(\d+)$', d.name)
    ]
    
    if not iteration_folders:
        raise FileNotFoundError(f"No iteration folders found in {snapshot_folder}")
    
    # Filter for folders that contain llm_correction_proposal.json
    valid_iterations = [
        d for d in iteration_folders
        if (d / "llm_correction_proposal.json").exists()
    ]
    
    if not valid_iterations:
        raise FileNotFoundError(f"No iteration folders with llm_correction_proposal.json found")
    
    # Get highest valid iteration number
    iteration_numbers = [
        int(re.match(r'^iteration-(\d+)$', d.name).group(1))
        for d in valid_iterations
    ]
    
    return max(iteration_numbers)

def backup_files_to_iteration(snapshot_id, iteration_number):
    """Copy snapshot-data.json and snapshot-validation.json to iteration folder"""
    snapshot_folder = Path("..") / "Snapshots" / snapshot_id
    iteration_folder = snapshot_folder / f"iteration-{iteration_number}"
    
    # Files to backup
    files_to_backup = [
        "snapshot-data.json",
        "snapshot-validation.json"
    ]
    
    print(f"Backing up files to iteration-{iteration_number}...")
    for filename in files_to_backup:
        source = snapshot_folder / filename
        destination = iteration_folder / filename
        
        if source.exists():
            shutil.copy2(source, destination)
            print(f"  ✓ Backed up: {filename}")
        else:
            print(f"  ⚠ Skipped (not found): {filename}")

def load_correction_proposal(snapshot_id, iteration_number):
    """Load the correction proposal from iteration folder"""
    snapshot_folder = Path("..") / "Snapshots" / snapshot_id
    iteration_folder = snapshot_folder / f"iteration-{iteration_number}"
    
    proposal_file = iteration_folder / "llm_correction_proposal.json"
    if not proposal_file.exists():
        raise FileNotFoundError(f"llm_correction_proposal.json not found in iteration-{iteration_number}")
    
    with open(proposal_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_proposal_schema(correction_proposal):
    """
    Validate correction proposal schema (without retry).
    Returns True if valid, exits with clear error message if invalid.
    """
    try:
        LLMCorrectionResponse(**correction_proposal)
        return True
    except ValidationError as e:
        print("\n" + "="*80)
        print("ERROR: INVALID JSON SCHEMA DETECTED")
        print("="*80)
        print("\nThe llm_correction_proposal.json has schema validation errors.")
        print("\nPLEASE RUN THIS TOOL FIRST:")
        print("  python validate_correction_schema_llm.py")
        print(e)
        print("="*80)
        sys.exit(1)
        return json.load(f)

def parse_target_path(path):
    """
    Parse a target path like 'demands[3].demandId' or 'demands' into components.
    Returns: (array_name, index, field_name) or (array_name, None, None) for array paths
    Examples: 
      - 'demands[3].demandId' -> ('demands', 3, 'demandId')
      - 'equipment[0].predecessors[0]' -> ('equipment', 0, 'nested:predecessors[0]')
      - 'demands' -> ('demands', None, None)
    """
    # Pattern for nested array access: arrayName[index].nestedField[nestedIndex]
    # Example: equipment[0].predecessors[0]
    match_nested = re.match(r'^(\w+)\[(\d+)\]\.(\w+)\[(\d+)\]$', path)
    if match_nested:
        array_name = match_nested.group(1)
        index = int(match_nested.group(2))
        nested_field = match_nested.group(3)
        nested_index = int(match_nested.group(4))
        # Return special format: (array_name, index, "nested:field[idx]")
        return array_name, index, f"nested:{nested_field}[{nested_index}]"
    
    # Pattern for array element field: arrayName[index].fieldName
    match_field = re.match(r'^(\w+)\[(\d+)\]\.(\w+)$', path)
    if match_field:
        array_name = match_field.group(1)
        index = int(match_field.group(2))
        field_name = match_field.group(3)
        return array_name, index, field_name
    
    # Pattern for array with index only: arrayName[index]
    match_array_index = re.match(r'^(\w+)\[(\d+)\]$', path)
    if match_array_index:
        array_name = match_array_index.group(1)
        index = int(match_array_index.group(2))
        return array_name, index, None
    
    # Pattern for array itself: arrayName
    match_array = re.match(r'^(\w+)$', path)
    if match_array:
        array_name = match_array.group(1)
        return array_name, None, None
    
    raise ValueError(f"Invalid target path format: {path}. Expected 'arrayName[index].fieldName', 'arrayName[index].nestedArray[index]', 'arrayName[index]', or 'arrayName'")

def apply_single_update(data, target_path, new_value):
    """Apply a single field update to the data"""
    array_name, index, field_name = parse_target_path(target_path)
    
    if index is None or field_name is None:
        raise ValueError(f"update_field action requires full path with index and field: {target_path}")
    
    # Validate array exists
    if array_name not in data:
        raise KeyError(f"Array '{array_name}' not found in snapshot data")
    
    # Validate index
    if index >= len(data[array_name]):
        raise IndexError(f"Index {index} out of range for array '{array_name}' (length: {len(data[array_name])})")
    
    # FIX: Parse JSON strings to proper structures if needed
    # Sometimes LLM returns arrays/objects as JSON strings
    if isinstance(new_value, str) and (new_value.startswith('[') or new_value.startswith('{')):
        try:
            parsed_value = json.loads(new_value)
            print(f"  ⚠ Parsed JSON string to proper structure: {type(parsed_value).__name__}")
            new_value = parsed_value
        except json.JSONDecodeError:
            # Not a valid JSON string, keep as-is
            pass
    
    # Handle nested array access (e.g., equipment[0].predecessors[0])
    if field_name.startswith("nested:"):
        # Extract nested field and index: "nested:predecessors[0]" -> "predecessors", 0
        nested_match = re.match(r'^nested:(\w+)\[(\d+)\]$', field_name)
        if not nested_match:
            raise ValueError(f"Invalid nested field format: {field_name}")
        
        nested_field = nested_match.group(1)
        nested_index = int(nested_match.group(2))
        
        # Validate nested field exists
        if nested_field not in data[array_name][index]:
            raise KeyError(f"Nested field '{nested_field}' not found in {array_name}[{index}]")
        
        # Validate nested field is an array
        if not isinstance(data[array_name][index][nested_field], list):
            raise TypeError(f"Nested field '{nested_field}' in {array_name}[{index}] is not an array")
        
        # Validate nested index
        if nested_index >= len(data[array_name][index][nested_field]):
            raise IndexError(f"Nested index {nested_index} out of range for {array_name}[{index}].{nested_field} (length: {len(data[array_name][index][nested_field])})")
        
        # Apply nested update
        old_value = data[array_name][index][nested_field][nested_index]
        data[array_name][index][nested_field][nested_index] = new_value
        
        return old_value, new_value
    
    # Apply regular update
    old_value = data[array_name][index].get(field_name)
    data[array_name][index][field_name] = new_value
    
    return old_value, new_value


def add_to_array(data, target_path, new_item):
    """Add a new item to an array"""
    array_name, index, field_name = parse_target_path(target_path)
    
    if index is not None or field_name is not None:
        raise ValueError(f"add_to_array action requires array path only (e.g., 'demands'), got: {target_path}")
    
    # Validate array exists
    if array_name not in data:
        raise KeyError(f"Array '{array_name}' not found in snapshot data")
    
    if not isinstance(data[array_name], list):
        raise TypeError(f"'{array_name}' is not an array")
    
    # Add item to array
    data[array_name].append(new_item)
    new_index = len(data[array_name]) - 1
    
    print(f"  ✓ Added item at index {new_index}")
    return new_index


def load_reference_data(field_name):
    """Load reference data from reference snapshot"""
    identify_tool_files_dir = Path(__file__).parent / "identify-tool-files"
    reference_file = identify_tool_files_dir / "reference-snapshot.json"
    
    if not reference_file.exists():
        raise FileNotFoundError(f"Reference snapshot not found: {reference_file}")
    
    print(f"  ℹ Loading reference data from: {reference_file}")
    
    with open(reference_file, 'r', encoding='utf-8') as f:
        reference_data = json.load(f)
    
    if field_name not in reference_data:
        raise KeyError(f"Field '{field_name}' not found in reference snapshot")
    
    return reference_data[field_name]


def replace_with_reference_data(data, target_path, new_value):
    """Replace an empty array with data from reference snapshot"""
    # Special case: new_value is "USE_REFERENCE_DATA"
    if new_value != "USE_REFERENCE_DATA":
        raise ValueError(f"replace_with_reference_data expects 'USE_REFERENCE_DATA', got: {new_value}")
    
    # Parse target path (should be just field name for root-level arrays)
    field_name = target_path
    
    # Validate field exists and is an array
    if field_name not in data:
        raise KeyError(f"Field '{field_name}' not found in snapshot data")
    
    if not isinstance(data[field_name], list):
        raise TypeError(f"Field '{field_name}' is not an array")
    
    # Load reference data
    reference_data = load_reference_data(field_name)
    
    # Replace empty array with reference data
    old_count = len(data[field_name])
    data[field_name] = reference_data
    new_count = len(data[field_name])
    
    print(f"  ✓ Replaced empty array with {new_count} entries from reference snapshot")
    return old_count, new_count


def remove_from_array(data, target_path, item_to_remove):
    """Remove an item from an array by matching a field value"""
    array_name, index, field_name = parse_target_path(target_path)
    
    # If index specified, remove that specific index
    if index is not None:
        if array_name not in data:
            raise KeyError(f"Array '{array_name}' not found in snapshot data")
        
        if index >= len(data[array_name]):
            raise IndexError(f"Index {index} out of range for array '{array_name}' (length: {len(data[array_name])})")
        
        removed_item = data[array_name].pop(index)
        print(f"  ✓ Removed item at index {index}")
        return removed_item
    
    # Otherwise, remove by matching item_to_remove dict
    if array_name not in data:
        raise KeyError(f"Array '{array_name}' not found in snapshot data")
    
    if not isinstance(data[array_name], list):
        raise TypeError(f"'{array_name}' is not an array")
    
    if not isinstance(item_to_remove, dict):
        raise TypeError(f"item_to_remove must be a dict when index not specified")
    
    # Find and remove matching item
    for i, item in enumerate(data[array_name]):
        if isinstance(item, dict):
            # Check if all keys in item_to_remove match
            match = all(
                item.get(k) == v
                for k, v in item_to_remove.items()
            )
            if match:
                removed_item = data[array_name].pop(i)
                print(f"  ✓ Removed item at index {i}")
                return removed_item
    
    raise ValueError(f"No matching item found to remove from '{array_name}'")

def apply_correction(snapshot_id, correction_proposal):
    """Apply correction proposal to snapshot-data.json"""
    snapshot_folder = Path("..") / "Snapshots" / snapshot_id
    snapshot_file = snapshot_folder / "snapshot-data.json"
    
    # Load snapshot data
    print("\nLoading snapshot data...")
    with open(snapshot_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    proposal = correction_proposal.get("correction_proposal", {})
    action = proposal.get("action")
    target_path = proposal.get("target_path")
    
    print(f"\nApplying main correction:")
    print(f"  Action: {action}")
    print(f"  Path: {target_path}")
    
    # Execute based on action type
    if action == "manual_intervention_required":
        # No automatic correction - just log to metadata
        print(f"Important: MANUAL INTERVENTION REQUIRED")
        print(f"  Reasoning: {proposal.get('reasoning')}")
        print(f"\n  No automatic changes applied")
        print(f"  This correction requires manual review and action")
        
        # Don't modify snapshot data, but continue to log in metadata
        
    elif action == "update_field":
        new_value = proposal.get("new_value")
        
        # Special case: USE_REFERENCE_DATA for empty arrays
        if new_value == "USE_REFERENCE_DATA":
            print(f"  New Value: USE_REFERENCE_DATA (will load from reference snapshot)")
            old_count, new_count = replace_with_reference_data(data, target_path, new_value)
            print(f"  Applied")
        else:
            print(f"  New Value: {new_value}")
            old_value, applied_value = apply_single_update(data, target_path, new_value)
            print(f"  Old Value: {old_value}")
            print(f"  Applied")
        
    elif action == "add_to_array":
        new_item = proposal.get("new_value")
        if not isinstance(new_item, dict):
            raise TypeError(f"new_value for add_to_array must be a dict (object), got: {type(new_item)}")
        print(f"  New Item: {json.dumps(new_item, indent=2)[:200]}...")
        new_index = add_to_array(data, target_path, new_item)
        
    elif action == "remove_from_array":
        item_to_remove = proposal.get("current_value")
        print(f"  Item to Remove: {json.dumps(item_to_remove, indent=2)[:200]}...")
        removed_item = remove_from_array(data, target_path, item_to_remove)
        print(f"  Removed: {json.dumps(removed_item, indent=2)[:200]}...")
        
    else:
        raise ValueError(f"Unknown action: {action}. Supported: update_field, add_to_array, remove_from_array, manual_intervention_required")
    
    # Apply additional updates if present (only if not manual intervention)
    if action != "manual_intervention_required":
        additional_updates = proposal.get("additional_updates", [])
        if additional_updates:
            print(f"\nApplying {len(additional_updates)} additional update(s):")
            for i, update in enumerate(additional_updates, 1):
                update_path = update.get("target_path")
                update_value = update.get("new_value")
                
                print(f"\n  Update {i}:")
                print(f"    Path: {update_path}")
                print(f"    New Value: {update_value}")
                
                old_val, new_val = apply_single_update(data, update_path, update_value)
                print(f"    Old Value: {old_val}")
                print(f"    ✓ Applied")
    
    # Save updated snapshot data (only if not manual intervention)
    if action != "manual_intervention_required":
        print(f"\nSaving corrected snapshot data...")
        with open(snapshot_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Saved to: {snapshot_file}")
    else:
        print(f"\nSnapshot data NOT modified (manual intervention required)")
    
    return data

def append_correction_to_metadata(snapshot_id, correction_proposal):
    """Append LLM correction proposal to metadata.txt"""
    snapshot_folder = Path("..") / "Snapshots" / snapshot_id
    metadata_file = snapshot_folder / "metadata.txt"
    
    if not metadata_file.exists():
        print(f"\n⚠ metadata.txt not found, skipping metadata update")
        return
    
    # Build correction entry
    proposal = correction_proposal.get("correction_proposal", {})
    original_error = correction_proposal.get("original_error", {})
    error_analyzed = correction_proposal.get("error_analyzed", {})
    iteration_num = correction_proposal.get("iteration", "?")
    
    correction_entry = f"\n### LLM Correction Applied (Iteration {iteration_num})\n\n"
    
    # Original Error
    correction_entry += f"**Original Error:**\n"
    correction_entry += f"- Level: {original_error.get('level')}\n"
    correction_entry += f"- Message: {original_error.get('message')}\n\n"
    
    # Error Analysis
    correction_entry += f"**Error Analysis:**\n"
    correction_entry += f"- Error Type: {error_analyzed.get('error_type')}\n"
    correction_entry += f"- Search Mode: {error_analyzed.get('search_mode')}\n"
    correction_entry += f"- Search Value: `{error_analyzed.get('search_value')}`\n"
    correction_entry += f"- Results Found: {error_analyzed.get('results_count')}\n\n"
    
    # Correction Proposal
    correction_entry += f"**Correction Applied:**\n"
    correction_entry += f"- Action: {proposal.get('action')}\n"
    correction_entry += f"- Target Path: `{proposal.get('target_path')}`\n"
    
    # Check if manual intervention is required
    if proposal.get('action') == "manual_intervention_required":
        correction_entry += f"\n⚠⚠⚠ **MANUAL INTERVENTION REQUIRED** ⚠⚠⚠\n"
        correction_entry += f"- Status: NO AUTOMATIC CORRECTION APPLIED\n"
        correction_entry += f"- Reason: {proposal.get('reasoning')}\n"
        correction_entry += f"- Action Required: User must manually review and fix this error\n"
        correction_entry += f"- Current Value: `{proposal.get('current_value')}`\n\n"
    else:
        correction_entry += f"- Old Value: `{proposal.get('current_value')}`\n"
        correction_entry += f"- New Value: `{proposal.get('new_value')}`\n"
        
        # Check if reference data was used
        if proposal.get('new_value') == "USE_REFERENCE_DATA":
            correction_entry += f"\n**IMPORTANT: Reference Data Fallback Used**\n"
            correction_entry += f"- Source: Reference snapshot (runtime/identify-tool-files/reference-snapshot.json)\n"
            correction_entry += f"- Operation: Copied array data from reference snapshot\n"
            correction_entry += f"- Manual Verification: RECOMMENDED - verify that copied data is appropriate for this snapshot\n\n"
        
        correction_entry += f"- Reasoning: {proposal.get('reasoning')}\n"
    
    additional_updates = proposal.get('additional_updates', [])
    if additional_updates:
        correction_entry += f"\n**Additional Updates:**\n"
        for i, update in enumerate(additional_updates, 1):
            correction_entry += f"- Path: `{update.get('target_path')}` → `{update.get('new_value')}`\n"
    
    # Add original LLM correction proposal JSON
    correction_entry += f"\n**Original llm_correction_proposal:**\n\n"
    correction_entry += "```json\n"
    correction_entry += json.dumps(correction_proposal, indent=2, ensure_ascii=False)
    correction_entry += "\n```\n\n"
    
    # Append to metadata.txt
    with open(metadata_file, 'a', encoding='utf-8') as f:
        f.write(correction_entry)
    
    print(f"\n✓ Correction entry added to metadata.txt")

def main():
    print("=== Correction Applier ===\n")
    
    # Load snapshot ID
    snapshot_id = load_current_snapshot_id()
    print(f"Snapshot ID: {snapshot_id}")
    
    # Get latest iteration number
    iteration_number = get_latest_iteration_number(snapshot_id)
    print(f"Using iteration: {iteration_number}\n")
    
    # Backup files to iteration folder
    backup_files_to_iteration(snapshot_id, iteration_number)
    
    # Load correction proposal (must be validated beforehand!)
    print(f"\nLoading correction proposal...")
    correction_proposal = load_correction_proposal(snapshot_id, iteration_number)
    
    # Validate schema (exits with clear message if invalid)
    print(f"Checking JSON schema...")
    validate_proposal_schema(correction_proposal)
    print(f"  ✓ Schema is valid")
    
    proposal = correction_proposal.get("correction_proposal", {})
    print(f"\nProposal details:")
    print(f"  Action: {proposal.get('action')}")
    print(f"  Target: {proposal.get('target_path')}")
    print(f"  Reasoning: {proposal.get('reasoning')}")
    
    # Apply correction
    apply_correction(snapshot_id, correction_proposal)
    
    # Append correction to metadata.txt
    append_correction_to_metadata(snapshot_id, correction_proposal)
    
    print("\n=== Done ===")

if __name__ == "__main__":
    main()
