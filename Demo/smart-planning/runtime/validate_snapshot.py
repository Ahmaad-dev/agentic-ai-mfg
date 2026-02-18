"""
Validate Snapshot Tool
Reads the current snapshot ID from runtime-files/current_snapshot.txt,
validates it via API, and saves the validation results to snapshot-validation.json.
"""

import sys
import requests
import json
import os
from pathlib import Path
from dotenv import load_dotenv
import urllib3

# Storage Manager (LOCAL / AZURE)
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from runtime_storage import get_storage

# UTF-8 Encoding für Windows-Terminal
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables from .env file (aus demo-Verzeichnis)
# Lade .env aus dem demo-Verzeichnis (2 Ebenen höher)
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

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
        print("Authentication successful")
        return self.token
    
    def get_validation_messages(self, snapshot_id):
        """Get validation messages for a snapshot"""
        if not self.token:
            self.authenticate()
        
        url = f"{self.base_uri}/esarom-be/api/v1/snapshots/{snapshot_id}/validation-messages"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        
        return response.json()


def validate_snapshot(snapshot_id: str = None):
    """Main function to validate snapshot and save results"""
    
    # 1. Snapshot-ID bestimmen: Argument hat Priorität, Fallback auf Datei
    if not snapshot_id:
        runtime_files_dir = Path(__file__).parent / "runtime-files"
        current_snapshot_file = runtime_files_dir / "current_snapshot.txt"
        
        if not current_snapshot_file.exists():
            print(f"Error: {current_snapshot_file} not found")
            return
        
        with open(current_snapshot_file, 'r') as f:
            content = f.read().strip()
            if "snapshot_id = " in content:
                snapshot_id = content.split("snapshot_id = ")[1].strip()
            else:
                print(f"Error: Invalid format in {current_snapshot_file}")
                return
    
    print(f"Snapshot ID: {snapshot_id}")
    
    # Get validation messages from API
    api = SmartPlanningAPI()
    
    try:
        validation_data = api.get_validation_messages(snapshot_id)
        print(f"Validation data retrieved ({len(validation_data)} messages)")

        # Save validation data via StorageManager (LOCAL or AZURE)
        storage = get_storage()
        storage.save_json(f"{snapshot_id}/original-data/snapshot-validation.json", validation_data)
        storage.save_json(f"{snapshot_id}/snapshot-validation.json", validation_data)

        print(f"✓ Validation saved ({storage.mode} mode)")

        # Append validation data to metadata.txt
        existing_metadata = storage.load_text(f"{snapshot_id}/metadata.txt")
        if existing_metadata is not None:
            # Calculate summary
            from datetime import datetime
            import re
            levels = {}
            for msg in validation_data:
                level = msg.get('level', 'UNKNOWN')
                levels[level] = levels.get(level, 0) + 1
            
            summary_text = ", ".join([f"{count} {level}" for level, count in sorted(levels.items())])
            if not summary_text:
                summary_text = "No validation issues found"
            
            # Shorten WARNING messages with long lists (keep ERROR messages full)
            shortened_data = []
            for msg in validation_data:
                msg_copy = msg.copy()
                if msg.get('level') == 'WARNING':
                    message = msg.get('message', '')
                    # If message is longer than 300 chars and contains UUIDs or long lists
                    if len(message) > 300 and (': ' in message):
                        parts = message.split(': ', 1)
                        if len(parts) == 2:
                            prefix = parts[0]
                            items_part = parts[1]
                            # Count items (comma-separated)
                            items = [item.strip() for item in items_part.split(',')]
                            if len(items) > 5:
                                # Show first 5 items
                                shortened_items = ', '.join(items[:5])
                                msg_copy['message'] = f"{prefix}: {shortened_items}, ... and {len(items) - 5} more"
                shortened_data.append(msg_copy)
            
            # Check if INITIAL VALIDATION already exists
            existing_content = existing_metadata

            if "INITIAL VALIDATION" in existing_content:
                # Find highest iteration number
                iteration_pattern = r'## VALIDATION Iteration (\d+)'
                iterations = re.findall(iteration_pattern, existing_content)
                
                if iterations:
                    # Get highest iteration number and add 1
                    next_iteration = max([int(i) for i in iterations]) + 1
                else:
                    # First iteration after initial validation
                    next_iteration = 1
                
                validation_header = f"## VALIDATION Iteration {next_iteration}\n\n"
            else:
                # First validation ever
                validation_header = "## INITIAL VALIDATION (First Run)\n\n"
            
            with_validation_entry = (f"\n\n{validation_header}"
                f"**Validated at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"**Total messages:** {len(validation_data)}\n"
                f"**Summary:** {summary_text}\n"
                f"**Status:** {'Valid' if not validation_data or all(m.get('level') != 'ERROR' for m in validation_data) else 'Has Errors - Not Valid!'}\n"
                "\n### Detailed validation messages:\n\n"
                "```json\n"
                + json.dumps(shortened_data, indent=4, ensure_ascii=False)
                + "\n```\n")
            storage.save_text(f"{snapshot_id}/metadata.txt", existing_content + with_validation_entry)
            print(f"Validation appended to metadata ({storage.mode} mode)")
        
        # Print summary
        if validation_data:
            levels = {}
            for msg in validation_data:
                level = msg.get('level', 'UNKNOWN')
                levels[level] = levels.get(level, 0) + 1
            
            print("\nValidation Summary:")
            for level, count in sorted(levels.items()):
                print(f"   {level}: {count}")
        else:
            print("\nNo validation messages (snapshot is valid)")
        
    except requests.exceptions.HTTPError as e:
        print(f"API Error: {e}")
        if e.response is not None:
            print(f"   Response: {e.response.text}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--snapshot-id", dest="snapshot_id", default=None,
                        help="Snapshot UUID (optional, Fallback auf current_snapshot.txt)")
    args, _ = parser.parse_known_args()
    validate_snapshot(snapshot_id=args.snapshot_id)
    validate_snapshot()
