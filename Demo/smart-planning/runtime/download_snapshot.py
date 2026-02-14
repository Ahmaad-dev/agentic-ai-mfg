"""  
Skript zum Herunterladen und Speichern von existierenden Snapshots über die Smart Planning API.
Funktioniert mit Snapshot-ID oder Snapshot-Name.
"""
import sys
import requests
import json
import warnings
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

# UTF-8 Encoding für Windows-Terminal
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# .env Datei laden (aus demo-Verzeichnis)
try:
    from dotenv import load_dotenv
    from pathlib import Path
    # Lade .env aus dem demo-Verzeichnis (2 Ebenen höher)
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass  

# SSL-Warnungen deaktivieren (für Test-Umgebung)
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

class SmartPlanningAPI:
    """Client für die Smart Planning API."""
    
    def __init__(self, base_uri: str = "https://vm-t-weu-ccadmm-idp-test02.internal.idp.cca-dev.com"):
        self.base_uri = base_uri
        self.token_uri = f"{base_uri}/keycloak/realms/Esarom/protocol/openid-connect/token"
        self.api_base_uri = f"{base_uri}/esarom-be/api/v1"
        self.token: Optional[str] = None
        
    def authenticate(self, client_id: str = "apiClient-test", 
                    client_secret: Optional[str] = None) -> str:
        """
        Authentifiziert sich per OAuth und gibt das Access Token zurück.
        
        Args:
            client_id: OAuth Client ID
            client_secret: OAuth Client Secret (optional, wird aus Umgebungsvariable CLIENT_SECRET gelesen wenn nicht angegeben)
            
        Returns:
            Access Token
        """
        print("1. Authentifizierung...")
        
        # Client Secret aus Umgebungsvariable lesen
        if client_secret is None:
            client_secret = os.getenv("CLIENT_SECRET")
            if not client_secret:
                raise ValueError("CLIENT_SECRET Umgebungsvariable ist nicht gesetzt und kein client_secret wurde übergeben")
        
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials"
        }
        
        response = requests.post(
            self.token_uri,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=data,
            verify=False
        )
        response.raise_for_status()
        
        self.token = response.json()["access_token"]
        print("Token erfolgreich abgerufen")
        return self.token
    
    def list_snapshots(self) -> List[Dict[str, Any]]:
        """
        Listet alle verfügbaren Snapshots auf.
        
        Returns:
            Liste von Snapshot-Informationen
        """
        if not self.token:
            raise ValueError("Nicht authentifiziert. Bitte zuerst authenticate() aufrufen.")
        
        response = requests.get(
            f"{self.api_base_uri}/snapshots",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            },
            verify=False
        )
        response.raise_for_status()
        
        return response.json()
    
    def find_snapshot_by_name_or_id(self, identifier: str) -> Dict[str, Any]:
        """
        Findet einen Snapshot anhand von Name oder ID.
        
        Args:
            identifier: Snapshot-ID (UUID) oder Snapshot-Name
            
        Returns:
            Snapshot-Informationen mit ID
        """
        print(f"\n2. Suche nach Snapshot: {identifier}")
        
        # Prüfe ob identifier eine UUID ist (enthält Bindestriche und ist ca. 36 Zeichen)
        is_uuid = '-' in identifier and len(identifier) >= 32
        
        if is_uuid:
            # Direkt als ID verwenden
            print(f"Erkannt als Snapshot-ID")
            return {"id": identifier}
        else:
            # Nach Name suchen
            print(f"Suche nach Snapshot mit Name: {identifier}")
            snapshots_response = self.list_snapshots()
            
            # DEBUG: Prüfe was die API zurückgibt
            print(f"DEBUG: Type of response: {type(snapshots_response)}")
            if isinstance(snapshots_response, dict):
                print(f"DEBUG: Response keys: {list(snapshots_response.keys())}")
            
            # Die API verwendet eine paginierte Response-Struktur
            # Die Snapshots sind im 'content' oder 'elements' Key
            if isinstance(snapshots_response, dict):
                # Mögliche Keys für paginierte APIs: 'content', 'elements', 'snapshots', 'items', 'data'
                snapshots = (snapshots_response.get('content') or 
                           snapshots_response.get('elements') or
                           snapshots_response.get('snapshots') or 
                           snapshots_response.get('items') or 
                           snapshots_response.get('data'))
                
                if not snapshots:
                    # Vielleicht ist es ein Dict mit IDs als Keys?
                    if all(isinstance(v, dict) for v in snapshots_response.values()):
                        snapshots = list(snapshots_response.values())
                        print(f"DEBUG: Using dict values as snapshots")
                    elif 'id' in snapshots_response:
                        # Falls response ein einzelnes Snapshot ist
                        snapshots = [snapshots_response]
                    else:
                        snapshots = []
                
                print(f"DEBUG: Extracted {len(snapshots)} snapshots from response")
            elif isinstance(snapshots_response, list):
                snapshots = snapshots_response
            else:
                raise ValueError(f"Unexpected API response type: {type(snapshots_response)}")
            
            # Exakte Übereinstimmung
            for snapshot in snapshots:
                if isinstance(snapshot, dict) and snapshot.get('name') == identifier:
                    print(f"Snapshot gefunden: {snapshot['name']} (ID: {snapshot['id']})")
                    return snapshot
            
            # Teilübereinstimmung (case-insensitive)
            identifier_lower = identifier.lower()
            for snapshot in snapshots:
                if isinstance(snapshot, dict):
                    snapshot_name = snapshot.get('name', '')
                    if identifier_lower in snapshot_name.lower():
                        print(f"Snapshot gefunden (Teilübereinstimmung): {snapshot['name']} (ID: {snapshot['id']})")
                        return snapshot
            
            raise ValueError(f"Kein Snapshot mit Name '{identifier}' gefunden. Verfügbare Snapshots: {len(snapshots)}")
    
    def get_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        """
        Ruft die vollständigen Snapshot-Daten ab.
        
        Args:
            snapshot_id: UUID des Snapshots
            
        Returns:
            Vollständige Snapshot-Daten
        """
        if not self.token:
            raise ValueError("Nicht authentifiziert. Bitte zuerst authenticate() aufrufen.")
        
        print(f"\n3. Snapshot-Daten werden abgerufen...")
        
        response = requests.get(
            f"{self.api_base_uri}/snapshots/{snapshot_id}",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            },
            verify=False
        )
        response.raise_for_status()
        
        print("Snapshot-Daten erfolgreich abgerufen")
        return response.json()


def download_and_save_snapshot(identifier: str, snapshots_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Lädt einen existierenden Snapshot herunter und speichert ihn lokal.
    
    Args:
        identifier: Snapshot-ID (UUID) oder Snapshot-Name
        snapshots_dir: Verzeichnis für Snapshots (optional, Standard: ../Snapshots relativ zum Skript)
        
    Returns:
        Dictionary mit snapshot_id, name und file_path
    """
    # Standard-Verzeichnis bestimmen
    if snapshots_dir is None:
        script_dir = Path(__file__).parent
        snapshots_dir = script_dir.parent / "Snapshots"
    
    snapshots_dir = Path(snapshots_dir)
    snapshots_dir.mkdir(parents=True, exist_ok=True)
        
    # API-Client initialisieren
    api = SmartPlanningAPI()
    
    # Authentifizieren
    api.authenticate()
    
    # Snapshot finden (by Name oder ID)
    snapshot_info = api.find_snapshot_by_name_or_id(identifier)
    snapshot_id = snapshot_info['id']
    
    # Snapshot-Daten abrufen
    snapshot_data = api.get_snapshot(snapshot_id)
    
    # Speichern
    print("\n4. Snapshot wird gespeichert...")
    snapshot_folder = snapshots_dir / f"{snapshot_id}"
    snapshot_folder.mkdir(parents=True, exist_ok=True)
    
    # Trennung: Metadata und Snapshot-Data
    metadata = {k: v for k, v in snapshot_data.items() if k != 'dataJson'}
    data_json = snapshot_data.get('dataJson', {})
    
    # Ergänze Source-Information (eindeutig für LLM)
    metadata["snapshot_source"] = "downloaded_from_server"
    metadata["server_downloaded_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Metadata-Datei im Hybrid-Format speichern
    metadata_file = snapshot_folder / "metadata.txt"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        f.write("# SNAPSHOT INFORMATIONS\n\n")
        f.write("```json\n")
        f.write(json.dumps(metadata, ensure_ascii=False, indent=2))
        f.write("\n```\n")
    
    # Original-Data Ordner erstellen
    original_data_folder = snapshot_folder / "original-data"
    original_data_folder.mkdir(parents=True, exist_ok=True)
    
    # Snapshot-Data als reine JSON-Datei speichern (schön formatiert)
    # Parse data_json if it's a string
    if isinstance(data_json, str):
        parsed_data = json.loads(data_json)
    else:
        parsed_data = data_json
    
    # Save in original-data folder
    snapshot_data_file_original = original_data_folder / "snapshot-data.json"
    with open(snapshot_data_file_original, 'w', encoding='utf-8') as f:
        json.dump(parsed_data, f, ensure_ascii=False, indent=4)
    
    # Save copy in main folder
    snapshot_data_file_main = snapshot_folder / "snapshot-data.json"
    with open(snapshot_data_file_main, 'w', encoding='utf-8') as f:
        json.dump(parsed_data, f, ensure_ascii=False, indent=4)
    
    print(f"Snapshot erfolgreich gespeichert")
    print(f"Ordner: {snapshot_folder}")
    print(f"Dateien: metadata.txt, snapshot-data.json, original-data/snapshot-data.json")
    
    print(f"Snapshot-ID:     {snapshot_id}")
    print(f"Name:            {metadata.get('name', 'N/A')}")
    print(f"Gespeichert in:  {snapshot_folder}")
    
    # Runtime-Files aktualisieren
    runtime_files_dir = Path(__file__).parent / "runtime-files"
    runtime_files_dir.mkdir(parents=True, exist_ok=True)
    
    # Aktuelle Snapshot-ID speichern (überschreiben)
    current_snapshot_file = runtime_files_dir / "current_snapshot.txt"
    with open(current_snapshot_file, 'w', encoding='utf-8') as f:
        f.write(f"snapshot_id = {snapshot_id}\n")
    
    # History-Datei (append)
    history_file = runtime_files_dir / "runtime-files-history.txt"
    with open(history_file, 'a', encoding='utf-8') as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"{timestamp} | snapshot_id = {snapshot_id} (downloaded)\n")
    
    return {
        "snapshot_id": snapshot_id,
        "name": metadata.get('name', 'N/A'),
        "metadata_file": str(metadata_file),
        "snapshot_data_file": str(snapshot_data_file_main),
        "snapshot_data_file_original": str(snapshot_data_file_original),
        "folder": str(snapshot_folder)
    }


if __name__ == "__main__":
    # Als Skript ausgeführt
    if len(sys.argv) < 2:
        print("Usage: python download_snapshot.py <snapshot_id_or_name>")
        print("Example: python download_snapshot.py abc-123-def-456")
        print("Example: python download_snapshot.py 'Production Plan V2'")
        exit(1)
    
    identifier = sys.argv[1]
    
    try:
        result = download_and_save_snapshot(identifier)
        print(f"\n✓ Snapshot {result['snapshot_id']} erfolgreich heruntergeladen und gespeichert.")
    except Exception as e:
        print(f"\n✗ Fehler: {e}")
        import traceback
        traceback.print_exc()
        exit(1)