"""
Skript zum Erstellen und Speichern von Snapshots über die Smart Planning API.
"""
import requests
import json
import time
import warnings
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# .env Datei laden
try:
    from dotenv import load_dotenv
    load_dotenv()
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
    
    def create_snapshot(self, name: Optional[str] = None, run_crawler: bool = True) -> Dict[str, Any]:
        """
        Erstellt einen neuen Snapshot.
        
        Args:
            name: Name des Snapshots (optional, wird automatisch generiert wenn nicht angegeben)
            run_crawler: Ob der Crawler direkt ausgeführt werden soll
            
        Returns:
            Snapshot-Informationen (enthält ID, Name, etc.)
        """
        if not self.token:
            raise ValueError("Nicht authentifiziert. Bitte zuerst authenticate() aufrufen.")
        
        print("\n2. Snapshot wird erstellt...")
        
        if not name:
            name = f"SP-Agent: Snapshot vom {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        response = requests.post(
            f"{self.api_base_uri}/snapshots",
            params={"runCrawler": str(run_crawler).lower()},
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            },
            json={"name": name},
            verify=False
        )
        response.raise_for_status()
        
        snapshot_info = response.json()
        print(f"Snapshot erfolgreich erstellt")
        print(f"Snapshot-ID: {snapshot_info['id']}")
        print(f"Name: {snapshot_info['name']}")
        
        return snapshot_info
    
    def get_snapshot(self, snapshot_id: str, max_retries: int = 5, retry_delay: int = 3) -> Dict[str, Any]:
        """
        Ruft die vollständigen Snapshot-Daten ab.
        
        Args:
            snapshot_id: UUID des Snapshots
            max_retries: Maximale Anzahl an Wiederholungsversuchen
            retry_delay: Wartezeit zwischen Versuchen in Sekunden
            
        Returns:
            Vollständige Snapshot-Daten
        """
        if not self.token:
            raise ValueError("Nicht authentifiziert. Bitte zuerst authenticate() aufrufen.")
        
        print(f"\n3. Warte {retry_delay} Sekunden auf Crawler-Completion...")
        time.sleep(retry_delay)
        
        print("\n4. Snapshot-Daten werden abgerufen...")
        
        for attempt in range(max_retries):
            try:
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
                
            except requests.exceptions.HTTPError as e:
                if attempt < max_retries - 1:
                    print(f"Versuch {attempt + 1}/{max_retries} fehlgeschlagen, warte {retry_delay} Sekunden...")
                    time.sleep(retry_delay)
                else:
                    print(f"Fehler beim Abrufen der Snapshot-Daten nach {max_retries} Versuchen")
                    raise


def create_and_save_snapshot(snapshots_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Erstellt einen Snapshot und speichert ihn lokal.
    
    Args:
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
    
    # Snapshot erstellen
    snapshot_info = api.create_snapshot()
    snapshot_id = snapshot_info['id']
    
    # Snapshot-Daten abrufen
    snapshot_data = api.get_snapshot(snapshot_id)
    
    # Speichern
    print("\n5. Snapshot wird gespeichert...")
    snapshot_folder = snapshots_dir / f"{snapshot_id}"
    snapshot_folder.mkdir(parents=True, exist_ok=True)
    
    # Trennung: Metadata und Snapshot-Data
    metadata = {k: v for k, v in snapshot_data.items() if k != 'dataJson'}
    data_json = snapshot_data.get('dataJson', {})
    
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
    print(f"Name:            {snapshot_info['name']}")
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
        f.write(f"{timestamp} | snapshot_id = {snapshot_id}\n")
    
    return {
        "snapshot_id": snapshot_id,
        "name": snapshot_info['name'],
        "metadata_file": str(metadata_file),
        "snapshot_data_file": str(snapshot_data_file_main),
        "snapshot_data_file_original": str(snapshot_data_file_original),
        "folder": str(snapshot_folder)
    }


if __name__ == "__main__":
    # Als Skript ausgeführt
    try:
        result = create_and_save_snapshot()
        print(f"\n✓ Snapshot {result['snapshot_id']} erfolgreich erstellt und gespeichert.")
    except Exception as e:
        print(f"\n✗ Fehler: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
