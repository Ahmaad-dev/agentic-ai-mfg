"""
Update Snapshot Tool - Upload Corrected Data to Server

This tool uploads the corrected snapshot data back to the Smart Planning API server.
It reads the current snapshot ID, loads the corrected snapshot-data.json, and updates
the snapshot on the server using PUT /snapshots/{snapshotId}.

Usage:
    python update_snapshot.py

Requirements:
    - runtime-files/current_snapshot.txt must exist with snapshot ID
    - Snapshots/{uuid}/snapshot-data.json must exist (corrected version)
    - Snapshots/{uuid}/metadata.txt must exist (for name/comment)
    - CLIENT_SECRET environment variable must be set in .env file

Exit Codes:
    0 = Success - Snapshot updated on server
    1 = Failure - Error during update process

Output:
    - Prints upload status and server response
    - Creates upload-result.json in snapshot folder with timestamp and status
"""

import requests
import json
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import urllib3
import sys

# Disable SSL warnings for test environment
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
load_dotenv()


class SmartPlanningAPI:
    """Client for Smart Planning API"""
    
    def __init__(self):
        self.base_uri = "https://vm-t-weu-ccadmm-idp-test02.internal.idp.cca-dev.com"
        self.client_id = "apiClient-test"
        self.client_secret = os.getenv("CLIENT_SECRET")
        
        if not self.client_secret:
            raise ValueError("CLIENT_SECRET not found in environment variables")
        
        self.token = None
    
    def authenticate(self):
        """Get OAuth2 token"""
        token_url = f"{self.base_uri}/keycloak/realms/Esarom/protocol/openid-connect/token"
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        response = requests.post(token_url, data=data, verify=False)
        response.raise_for_status()
        
        self.token = response.json()["access_token"]
        print("✓ Authentication successful")
        return self.token
    
    def update_snapshot(self, snapshot_id: str, name: str, comment: str, data_json: str):
        """
        Update a snapshot on the server
        
        Args:
            snapshot_id: UUID of the snapshot to update
            name: Snapshot name
            comment: Snapshot comment (can be None)
            data_json: JSON string of the snapshot data
            
        Returns:
            Updated snapshot information (without data)
        """
        if not self.token:
            self.authenticate()
        
        url = f"{self.base_uri}/esarom-be/api/v1/snapshots/{snapshot_id}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Prepare request body according to SnapshotUpdateRequest schema
        body = {
            "name": name,
            "dataJson": data_json
        }
        
        # Only include comment if it's not None
        if comment is not None:
            body["comment"] = comment
        
        print(f"\n→ Uploading snapshot data to server...")
        print(f"  Snapshot ID: {snapshot_id}")
        print(f"  Name: {name}")
        print(f"  Data size: {len(data_json):,} characters")
        
        response = requests.put(url, headers=headers, json=body, verify=False)
        response.raise_for_status()
        
        return response.json()


def parse_metadata(metadata_file: Path) -> dict:
    """
    Parse metadata.txt to extract snapshot name and comment
    
    Args:
        metadata_file: Path to metadata.txt
        
    Returns:
        Dictionary with 'name' and 'comment'
    """
    with open(metadata_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the JSON block with snapshot information
    start_marker = "# SNAPSHOT INFORMATIONS\n\n```json\n"
    end_marker = "\n```"
    
    start_idx = content.find(start_marker)
    if start_idx == -1:
        raise ValueError("Could not find SNAPSHOT INFORMATIONS in metadata.txt")
    
    start_idx += len(start_marker)
    end_idx = content.find(end_marker, start_idx)
    
    if end_idx == -1:
        raise ValueError("Could not find end of JSON block in metadata.txt")
    
    json_str = content[start_idx:end_idx]
    snapshot_info = json.loads(json_str)
    
    return {
        "name": snapshot_info["name"],
        "comment": snapshot_info.get("comment")
    }


def append_upload_to_metadata(snapshot_dir: Path, response_data: dict):
    """
    Append upload status to metadata.txt for LLM context
    
    Args:
        snapshot_dir: Path to snapshot directory
        response_data: Server response with validation status
    """
    metadata_file = snapshot_dir / "metadata.txt"
    if not metadata_file.exists():
        return
    
    import re
    
    # Read existing content to find iteration number
    with open(metadata_file, 'r', encoding='utf-8') as f:
        existing_content = f.read()
    
    # Find highest upload iteration
    iteration_pattern = r'## UPLOAD Iteration (\d+)'
    iterations = re.findall(iteration_pattern, existing_content)
    
    if iterations:
        next_iteration = max([int(i) for i in iterations]) + 1
    else:
        next_iteration = 1
    
    # Extract important fields
    is_validated = response_data.get('isSuccessfullyValidated', False)
    modified_at = response_data.get('dataModifiedAt', 'Unknown')
    modified_by = response_data.get('dataModifiedBy', 'Unknown')
    
    # Status for LLM
    if is_validated:
        status_line = "**✓ SNAPSHOT IS VALID** - Server accepted the data without errors."
    else:
        status_line = "**✗ SNAPSHOT HAS ERRORS** - Server validation failed."
    
    with open(metadata_file, 'a', encoding='utf-8') as f:
        f.write(f"\n\n## UPLOAD Iteration {next_iteration}\n\n")
        f.write(f"**Uploaded at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Server validated:** {is_validated}\n")
        f.write(f"**Modified at (server):** {modified_at}\n")
        f.write(f"**Modified by:** {modified_by}\n")
        f.write(f"\n{status_line}\n")
    
    print(f"✓ Upload status appended to: {metadata_file}")


def save_upload_result(snapshot_dir: Path, success: bool, response_data: dict = None, error: str = None):
    """
    Save upload result to upload-result.json in snapshot folder
    
    Args:
        snapshot_dir: Path to snapshot directory
        success: Whether upload was successful
        response_data: Server response data (if success)
        error: Error message (if failure)
    """
    result = {
        "uploaded_at": datetime.now().isoformat(),
        "success": success
    }
    
    if success and response_data:
        result["server_response"] = response_data
    
    if not success and error:
        result["error"] = error
    
    result_file = snapshot_dir / "upload-result.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n→ Upload result saved to: {result_file}")


def main():
    """Main function to upload corrected snapshot data to server"""
    
    try:
        # 1. Read current snapshot ID
        runtime_files_dir = Path(__file__).parent / "runtime-files"
        current_snapshot_file = runtime_files_dir / "current_snapshot.txt"
        
        if not current_snapshot_file.exists():
            print(f"ERROR: {current_snapshot_file} not found")
            print("Please run create_snapshot.py first")
            sys.exit(1)
        
        # Parse snapshot ID from file
        with open(current_snapshot_file, 'r') as f:
            content = f.read().strip()
            if "snapshot_id = " in content:
                snapshot_id = content.split("snapshot_id = ")[1].strip()
            else:
                print(f"ERROR: Invalid format in {current_snapshot_file}")
                sys.exit(1)
        
        print("=" * 70)
        print("UPDATE SNAPSHOT - Upload Corrected Data to Server")
        print("=" * 70)
        print(f"\nSnapshot ID: {snapshot_id}")
        
        # 2. Locate snapshot folder
        snapshots_base = Path(__file__).parent.parent / "Snapshots"
        snapshot_dir = snapshots_base / snapshot_id
        
        if not snapshot_dir.exists():
            print(f"ERROR: Snapshot directory not found: {snapshot_dir}")
            sys.exit(1)
        
        # 3. Load corrected snapshot data
        snapshot_data_file = snapshot_dir / "snapshot-data.json"
        if not snapshot_data_file.exists():
            print(f"ERROR: snapshot-data.json not found: {snapshot_data_file}")
            sys.exit(1)
        
        print(f"\n→ Loading corrected snapshot data from:")
        print(f"  {snapshot_data_file}")
        
        with open(snapshot_data_file, 'r', encoding='utf-8') as f:
            snapshot_data = json.load(f)
        
        # Convert to JSON string for API
        data_json = json.dumps(snapshot_data, ensure_ascii=False)
        print(f"  ✓ Data loaded ({len(data_json):,} characters)")
        
        # 4. Load metadata (name and comment)
        metadata_file = snapshot_dir / "metadata.txt"
        if not metadata_file.exists():
            print(f"ERROR: metadata.txt not found: {metadata_file}")
            sys.exit(1)
        
        print(f"\n→ Loading snapshot metadata from:")
        print(f"  {metadata_file}")
        
        metadata = parse_metadata(metadata_file)
        print(f"  ✓ Name: {metadata['name']}")
        print(f"  ✓ Comment: {metadata['comment'] or '(none)'}")
        
        # 5. Upload to server
        api = SmartPlanningAPI()
        
        response_data = api.update_snapshot(
            snapshot_id=snapshot_id,
            name=metadata['name'],
            comment=metadata['comment'],
            data_json=data_json
        )
        
        print("\n" + "=" * 70)
        print("✓ SUCCESS - Snapshot updated on server!")
        print("=" * 70)
        print(f"\nServer response:")
        print(json.dumps(response_data, indent=2))
        
        # Save upload result
        save_upload_result(snapshot_dir, success=True, response_data=response_data)
        
        # Append to metadata.txt for LLM context
        append_upload_to_metadata(snapshot_dir, response_data)
        
        print("\n→ Next step: Run validate_snapshot.py to verify corrections")
        
        sys.exit(0)
        
    except requests.exceptions.HTTPError as e:
        print("\n" + "=" * 70)
        print("ERROR: HTTP Error during upload")
        print("=" * 70)
        print(f"Status Code: {e.response.status_code}")
        print(f"Response: {e.response.text}")
        
        # Save error result
        if 'snapshot_dir' in locals():
            save_upload_result(snapshot_dir, success=False, error=str(e))
        
        sys.exit(1)
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("ERROR: Upload failed")
        print("=" * 70)
        print(f"{type(e).__name__}: {str(e)}")
        
        # Save error result
        if 'snapshot_dir' in locals():
            save_upload_result(snapshot_dir, success=False, error=str(e))
        
        sys.exit(1)


if __name__ == "__main__":
    main()
