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
    Parse a target path like 'demands[3].demandId' into components.
    Returns: (array_name, index, field_name)
    Example: 'demands[3].demandId' -> ('demands', 3, 'demandId')
    """
    # Pattern: arrayName[index].fieldName
    match = re.match(r'^(\w+)\[(\d+)\]\.(\w+)$', path)
    if not match:
        raise ValueError(f"Invalid target path format: {path}")
    
    array_name = match.group(1)
    index = int(match.group(2))
    field_name = match.group(3)
    
    return array_name, index, field_name

def apply_single_update(data, target_path, new_value):
    """Apply a single field update to the data"""
    array_name, index, field_name = parse_target_path(target_path)
    
    # Validate array exists
    if array_name not in data:
        raise KeyError(f"Array '{array_name}' not found in snapshot data")
    
    # Validate index
    if index >= len(data[array_name]):
        raise IndexError(f"Index {index} out of range for array '{array_name}' (length: {len(data[array_name])})")
    
    # Apply update
    old_value = data[array_name][index].get(field_name)
    data[array_name][index][field_name] = new_value
    
    return old_value, new_value

def apply_correction(snapshot_id, correction_proposal):
    """Apply correction proposal to snapshot-data.json"""
    snapshot_folder = Path("..") / "Snapshots" / snapshot_id
    snapshot_file = snapshot_folder / "snapshot-data.json"
    
    # Load snapshot data
    print("\nLoading snapshot data...")
    with open(snapshot_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    proposal = correction_proposal.get("correction_proposal", {})
    
    # Apply main update
    target_path = proposal.get("target_path")
    new_value = proposal.get("new_value")
    
    print(f"\nApplying main correction:")
    print(f"  Path: {target_path}")
    print(f"  New Value: {new_value}")
    
    old_value, applied_value = apply_single_update(data, target_path, new_value)
    print(f"  Old Value: {old_value}")
    print(f"  ✓ Applied")
    
    # Apply additional updates if present
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
    
    # Save updated snapshot data
    print(f"\nSaving corrected snapshot data...")
    with open(snapshot_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved to: {snapshot_file}")
    
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
    correction_entry += f"- Old Value: `{proposal.get('current_value')}`\n"
    correction_entry += f"- New Value: `{proposal.get('new_value')}`\n"
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
