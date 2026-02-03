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

# Load environment variables
load_dotenv()


def load_current_snapshot_id():
    """Load snapshot ID from current_snapshot.txt"""
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
    snapshot_dir = Path(__file__).parent.parent / "Snapshots" / snapshot_id
    validation_file = snapshot_dir / "snapshot-validation.json"
    
    if not validation_file.exists():
        print(f"Error: {validation_file} not found")
        return None
    
    with open(validation_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_next_iteration_number(snapshot_id):
    """Find the highest iteration number and return next number"""
    snapshot_dir = Path(__file__).parent.parent / "Snapshots" / snapshot_id
    
    if not snapshot_dir.exists():
        return 1
    
    # Find all iteration folders
    iteration_pattern = re.compile(r'^iteration-(\d+)$')
    max_iteration = 0
    
    for item in snapshot_dir.iterdir():
        if item.is_dir():
            match = iteration_pattern.match(item.name)
            if match:
                iteration_num = int(match.group(1))
                max_iteration = max(max_iteration, iteration_num)
    
    return max_iteration + 1


def save_llm_response(snapshot_id, llm_response, first_error, llm_call_data):
    """Save LLM response and full call data to iteration folder"""
    iteration_number = get_next_iteration_number(snapshot_id)
    
    snapshot_dir = Path(__file__).parent.parent / "Snapshots" / snapshot_id
    iteration_dir = snapshot_dir / f"iteration-{iteration_number}"
    iteration_dir.mkdir(parents=True, exist_ok=True)
    
    # Prepare data to save
    output_data = {
        "iteration": iteration_number,
        "original_error": first_error,
        "llm_analysis": llm_response
    }
    
    # Save to JSON file
    output_file = iteration_dir / "llm_identify_response.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nLLM response saved to: {output_file}")
    
    # Save full LLM call data
    llm_call_file = iteration_dir / "llm_identify_call.json"
    with open(llm_call_file, 'w', encoding='utf-8') as f:
        json.dump(llm_call_data, f, indent=2, ensure_ascii=False)
    
    print(f"Full LLM call saved to: {llm_call_file}")
    
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
    print(f"Analyzing first ERROR with LLM...")
    
    # Get the first error
    first_error = error_messages[0]
    
    # Create prompt for LLM
    prompt = f"""You are analyzing a validation error from a Smart Planning system. 
Your task is to extract the relevant ID or value that needs to be investigated.

Validation Error:
{json.dumps(first_error, indent=2)}

Please analyze this error and determine the search strategy:
1. If the error mentions a specific ID value (e.g., "D830081_005"), use "value" mode to search for that value
2. If the error mentions EMPTY or MISSING field values, use "empty_field" mode and specify the field name (e.g., "demandId")
3. A brief explanation of what the error is about

Respond in JSON format:
{{
    "search_mode": "value" or "empty_field",
    "search_value": "the ID value to search for (value mode) OR the field name (empty_field mode)",
    "error_type": "brief description of the error",
    "should_investigate": true or false
}}

Examples:
- For "Duplicate demand IDs found: D830081_005" → {{"search_mode": "value", "search_value": "D830081_005", "should_investigate": true}}
- For "Demand IDs must not be empty" → {{"search_mode": "empty_field", "search_value": "demandId", "should_investigate": true}}
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
    
    # Parse LLM response
    llm_response = json.loads(response.choices[0].message.content)
    
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
    print(f"   Search Mode: {llm_response.get('search_mode')}")
    print(f"   Search Value: {llm_response.get('search_value')}")
    print(f"   Error Type: {llm_response.get('error_type')}")
    print(f"   Should Investigate: {llm_response.get('should_investigate')}")
    
    return llm_response, first_error, llm_call_data


def trigger_identify_tool(search_mode, search_value):
    """Trigger the identify_snapshot.py tool with the given search mode and value"""
    
    identify_script = Path(__file__).parent / "identify_snapshot.py"
    
    if not identify_script.exists():
        print(f"Error: {identify_script} not found")
        return False
    
    # Build command based on search mode
    if search_mode == "empty_field":
        command_args = [sys.executable, str(identify_script), "--empty", search_value]
        print(f"\nTriggering identify tool in EMPTY FIELD mode for: {search_value}")
    else:
        command_args = [sys.executable, str(identify_script), search_value]
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
    print("Starting LLM-based Error Analysis\n")
    
    # Check for demo mode
    demo_mode = len(sys.argv) > 1 and sys.argv[1] == "--demo"
    
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
        # Step 1: Load snapshot ID
        snapshot_id = load_current_snapshot_id()
        if not snapshot_id:
            return
        
        print(f"Snapshot ID: {snapshot_id}\n")
        
        # Step 2: Load validation data
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
                trigger_identify_tool(search_mode, search_value)
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
