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

import sys
import requests
import json
import os
from pathlib import Path
from datetime import datetime

# UTF-8 Encoding für Windows-Terminal
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
import urllib3
import sys

# Storage Manager (LOCAL / AZURE)
sys.path.insert(0, str(Path(__file__).parents[3]))
from runtime_storage import get_storage

# Disable SSL warnings for test environment
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables (aus dem Anwendungsverzeichnis app/)
# Lade .env aus dem Anwendungsverzeichnis app/ (drei Ebenen höher, siehe parents[3])
env_path = Path(__file__).parents[3] / ".env"
load_dotenv(dotenv_path=env_path)

# --- Smart-Planning-Endpunkt (2026-08-03 aus dem Code herausgezogen) -------------------
# Host, Client-ID und Realm standen hier fest verdrahtet — beide mit „test" im Namen. In
# Azure ausgerollt haette das Produktiv-Backend gegen die Testumgebung gesprochen. Die
# alten Werte sind weiterhin der Standard, es aendert sich also nichts, solange niemand
# die Variablen setzt.
SP_BASE_URI = os.getenv("SMART_PLANNING_BASE_URI", "https://vm-t-weu-ccadmm-idp-test02.internal.idp.cca-dev.com").rstrip("/")
SP_CLIENT_ID = os.getenv("SMART_PLANNING_CLIENT_ID", "apiClient-test")
SP_REALM = os.getenv("SMART_PLANNING_REALM", "Esarom")


class SmartPlanningAPI:
    """Client for Smart Planning API"""
    
    def __init__(self):
        self.base_uri = SP_BASE_URI
        self.client_id = SP_CLIENT_ID
        self.client_secret = os.getenv("CLIENT_SECRET")
        
        if not self.client_secret:
            raise ValueError("CLIENT_SECRET not found in environment variables")
        
        self.token = None
    
    def authenticate(self):
        """Get OAuth2 token"""
        token_url = f"{self.base_uri}/keycloak/realms/{SP_REALM}/protocol/openid-connect/token"
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        response = requests.post(token_url, data=data, verify=False, timeout=10)
        response.raise_for_status()
        
        self.token = response.json()["access_token"]
        print("Authentication successful")
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
        
        print(f"\nUploading snapshot data to server...")
        print(f"  Snapshot ID: {snapshot_id}")
        print(f"  Name: {name}")
        print(f"  Data size: {len(data_json):,} characters")
        
        response = requests.put(url, headers=headers, json=body, verify=False, timeout=60)
        response.raise_for_status()
        
        return response.json()


def parse_metadata(snapshot_id: str = None, content: str = None) -> dict:
    """
    Parse metadata content to extract snapshot name and comment.
    Accepts either a snapshot_id (loads via StorageManager) or raw content string.
    """
    if content is None:
        if snapshot_id is None:
            raise ValueError("Either snapshot_id or content must be provided")
        storage = get_storage()
        content = storage.load_text(f"{snapshot_id}/metadata.txt")
        if content is None:
            raise FileNotFoundError(f"metadata.txt not found for snapshot {snapshot_id}")
    
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


def append_upload_to_metadata(snapshot_id: str, response_data: dict):
    """
    Append upload status to metadata.txt for LLM context.
    """
    storage = get_storage()
    existing_content = storage.load_text(f"{snapshot_id}/metadata.txt")
    if existing_content is None:
        return

    import re
    iteration_pattern = r'## UPLOAD Iteration (\d+)'
    iterations = re.findall(iteration_pattern, existing_content)
    next_iteration = max([int(i) for i in iterations]) + 1 if iterations else 1
    
    # Extract important fields
    is_validated = response_data.get('isSuccessfullyValidated', False)
    modified_at = response_data.get('dataModifiedAt', 'Unknown')
    modified_by = response_data.get('dataModifiedBy', 'Unknown')
    
    # Status for LLM
    if is_validated:
        status_line = "**SNAPSHOT IS VALID** - Server accepted the data without errors."
    else:
        status_line = "**SNAPSHOT HAS ERRORS** - Server validation failed."
    
    upload_entry = (
        f"\n\n## UPLOAD Iteration {next_iteration}\n\n"
        f"**Uploaded at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"**Server validated:** {is_validated}\n"
        f"**Modified at (server):** {modified_at}\n"
        f"**Modified by:** {modified_by}\n"
        f"\n{status_line}\n"
    )
    storage.save_text(f"{snapshot_id}/metadata.txt", existing_content + upload_entry)
    print(f"Upload status appended to metadata ({storage.mode} mode)")


def save_upload_result(snapshot_id: str, success: bool, response_data: dict = None, error: str = None):
    """
    Save upload result to upload-result.json in snapshot folder.
    """
    result = {"uploaded_at": datetime.now().isoformat(), "success": success}
    if success and response_data:
        result["server_response"] = response_data
    if not success and error:
        result["error"] = error

    storage = get_storage()
    storage.save_json(f"{snapshot_id}/upload-result.json", result)
    print(f"\nUpload result saved ({storage.mode} mode): {snapshot_id}/upload-result.json")


def run_upload(snapshot_id) -> dict:
    """
    KNOTEN 7, Teil 2 — Hochladen (BA / AP-D3, 2026-08-19).

    Kernlogik aus main(), aufrufbar. Laedt die korrigierten Daten, holt Name und Kommentar aus
    metadata.txt, schickt sie an den Server, sichert das Ergebnis und haengt es an metadata.txt.

    Returns: {"uploaded": bool, "response": dict|None, "error": str|None}

    Beendet den Prozess NIE. main() behaelt seine Exit-Codes und haengt sie an diese Rueckgabe.
    """
    try:
        storage = get_storage()
        snapshot_data = storage.load_json(f"{snapshot_id}/snapshot-data.json")
        if snapshot_data is None:
            return {"uploaded": False, "response": None, "fehler_art": "kein_snapshot",
                    "error": f"snapshot-data.json not found for snapshot {snapshot_id}"}

        data_json = json.dumps(snapshot_data, ensure_ascii=False)
        print(f"  Data loaded ({len(data_json):,} characters)")

        metadata = parse_metadata(snapshot_id=snapshot_id)
        print(f"  Name: {metadata['name']}")
        print(f"  Comment: {metadata['comment'] or '(none)'}")

        api = SmartPlanningAPI()
        response_data = api.update_snapshot(
            snapshot_id=snapshot_id,
            name=metadata['name'],
            comment=metadata['comment'],
            data_json=data_json,
        )

        save_upload_result(snapshot_id, success=True, response_data=response_data)
        append_upload_to_metadata(snapshot_id, response_data)
        return {"uploaded": True, "response": response_data, "fehler_art": None, "error": None}

    except requests.exceptions.HTTPError as exc:
        save_upload_result(snapshot_id, success=False, error=str(exc))
        status = exc.response.status_code if exc.response is not None else "?"
        return {"uploaded": False, "response": None, "fehler_art": "http",
                "http_status": status,
                "http_text": (exc.response.text if exc.response is not None else None),
                "error": f"HTTP {status}: {exc}"}
    except Exception as exc:
        save_upload_result(snapshot_id, success=False, error=str(exc))
        return {"uploaded": False, "response": None, "fehler_art": "sonstiges",
                "fehler_typ": type(exc).__name__, "fehler_text": str(exc),
                "error": f"{type(exc).__name__}: {exc}"}


def main():
    """
    CLI-Huelle. Enthaelt seit dem 20.08.2026 KEINE Uploadlogik mehr.

    BEFUND F3 (BA-025): main() hatte die Kernlogik von run_upload() nachgebaut - laden,
    parse_metadata(), SmartPlanningAPI, speichern. Zwei Wege durch dieselbe Aufgabe.
    Bedingung A und B laufen ueber diese CLI (Subprozess aus sp_agent), Bedingung C ueber
    run_upload(). Jede spaetere Aenderung an nur einem der beiden Wege haette einen
    Unterschied erzeugt, der in den Ergebnissen wie ein Architektureffekt aussieht, ohne
    einer zu sein (CLAUDE.md, Bauregel B; BA_MASTERPLAN Kap. 12.2 - "eine Implementierung,
    kein Drift").

    Hier bleibt ausschliesslich CLI-Semantik: Argumente, current_snapshot.txt-Fallback,
    Banner, Exit-Codes. Die stdout-Zeilen sind bewusst wortgleich zur Fassung davor.
    """
    import argparse
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--snapshot-id", dest="snapshot_id", default=None,
                        help="Snapshot UUID (optional, Fallback auf current_snapshot.txt)")
    args, _ = parser.parse_known_args()

    # 1. Snapshot-ID bestimmen - reine CLI-Zustaendigkeit, kein Knoten braucht das.
    snapshot_id = args.snapshot_id
    if not snapshot_id:
        runtime_files_dir = Path(__file__).parent / "runtime-files"
        current_snapshot_file = runtime_files_dir / "current_snapshot.txt"

        if not current_snapshot_file.exists():
            print(f"ERROR: {current_snapshot_file} not found")
            print("Please run create_snapshot.py first")
            sys.exit(1)

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
    print()
    print(f"Snapshot ID: {snapshot_id}")

    ergebnis = run_upload(snapshot_id)

    # BEKANNTE, FACHLICH FOLGENLOSE CLI-ABWEICHUNG (20.08.2026, Befund F3/BA-026).
    # Auf dem Fehlerpfad erscheint die Zeile "Upload result saved (...)" jetzt VOR dem
    # Fehlerbanner statt danach. Ursache: `save_upload_result()` liegt in `run_upload()` -
    # dort muss es liegen, damit Bedingung C (Knoten 7) dasselbe Artefakt schreibt wie A und B.
    # Die CLI besitzt die Reihenfolge deshalb nicht mehr.
    #
    # Bewusst NICHT wiederhergestellt: das ginge nur, indem entweder die Logik wieder
    # dupliziert wird (genau der Befund, der hier behoben wurde) oder ein gemeinsamer Helfer
    # einen Druckunterdrueckungs-Schalter bekommt - beides ein Eingriff aus rein kosmetischem
    # Grund. Geprueft, dass es folgenlos ist: Zeilenmenge, Exit-Code (1) und erzeugtes
    # Artefakt (`upload-result.json`) sind unveraendert, und niemand parst dieses stdout -
    # `sp_agent._read_snapshot_metadata_from_stdout()` gilt nur fuer `rename_snapshot` und
    # `identify_snapshot`, sonst wertet der Agent ausschliesslich `returncode` aus.
    if ergebnis["uploaded"]:
        print()
        print("=" * 70)
        print("SUCCESS - Snapshot updated on server!")
        print("=" * 70)
        print()
        print("Server response:")
        print(json.dumps(ergebnis["response"], indent=2))
        print()
        print("Next step: Run validate_snapshot.py to verify corrections")
        sys.exit(0)

    # Fehlerpfade - wortgleich zur Fassung vor F3.
    art = ergebnis.get("fehler_art")
    if art == "kein_snapshot":
        print(f"ERROR: {ergebnis['error']}")
    elif art == "http":
        print()
        print("=" * 70)
        print("ERROR: HTTP Error during upload")
        print("=" * 70)
        print(f"Status Code: {ergebnis.get('http_status')}")
        print(f"Response: {ergebnis.get('http_text')}")
    else:
        print()
        print("=" * 70)
        print("ERROR: Upload failed")
        print("=" * 70)
        print(f"{ergebnis.get('fehler_typ')}: {ergebnis.get('fehler_text')}")
    sys.exit(1)


if __name__ == "__main__":
    main()
