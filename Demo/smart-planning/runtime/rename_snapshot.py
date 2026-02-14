"""
Skript zum Umbenennen eines Snapshots über die Smart Planning API.
"""
import sys
import requests
import json
import warnings
import os
import argparse
from pathlib import Path
from typing import Optional

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
        """Authentifiziert sich per OAuth und gibt das Access Token zurück."""
        print("1. Authentifizierung...")
        
        if client_secret is None:
            client_secret = os.getenv("CLIENT_SECRET")
            if not client_secret:
                raise ValueError("CLIENT_SECRET Umgebungsvariable ist nicht gesetzt")
        
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
        print("   ✓ Token erfolgreich abgerufen")
        return self.token
    
    def rename_snapshot(self, snapshot_id: str, new_name: str) -> dict:
        """
        Ändert den Namen eines existierenden Snapshots.
        
        Args:
            snapshot_id: UUID des Snapshots
            new_name: Neuer Name für den Snapshot
            
        Returns:
            API-Response als Dictionary
        """
        if not self.token:
            raise ValueError("Nicht authentifiziert. Bitte zuerst authenticate() aufrufen.")
        
        print(f"\n2. Hole aktuelle Snapshot-Daten...")
        print(f"   Snapshot-ID: {snapshot_id}")
        
        # Zuerst aktuellen Snapshot abrufen (um dataJson zu bekommen)
        get_url = f"{self.api_base_uri}/snapshots/{snapshot_id}"
        response = requests.get(
            get_url,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            },
            verify=False
        )
        
        if response.status_code != 200:
            print(f"   ✗ Fehler beim Abrufen: HTTP {response.status_code}")
            response.raise_for_status()
        
        current_snapshot = response.json()
        current_data_json = current_snapshot.get("dataJson")
        current_comment = current_snapshot.get("comment")
        
        print(f"   ✓ Snapshot abgerufen (aktueller Name: '{current_snapshot.get('name')}')")
        
        print(f"\n3. Ändere Snapshot-Namen...")
        print(f"   Neuer Name: '{new_name}'")
        
        # API-Endpoint zum Snapshot updaten
        # Format: PUT /api/v1/snapshots/{snapshotId}
        url = f"{self.api_base_uri}/snapshots/{snapshot_id}"
        
        # Body muss name UND dataJson enthalten
        payload = {
            "name": new_name,
            "dataJson": current_data_json
        }
        
        # Comment nur wenn vorhanden
        if current_comment:
            payload["comment"] = current_comment
        
        response = requests.put(
            url,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            },
            json=payload,
            verify=False
        )
        
        if response.status_code == 200:
            print(f"   ✓ Snapshot erfolgreich umbenannt!")
            result = response.json()
            
            # WICHTIG: Aktualisiere auch lokale metadata.txt!
            snapshot_dir = Path(__file__).parent.parent / "Snapshots" / snapshot_id
            metadata_file = snapshot_dir / "metadata.txt"
            
            if metadata_file.exists():
                print(f"\n4. Aktualisiere lokale metadata.txt...")
                try:
                    # Lese metadata.txt
                    content = metadata_file.read_text(encoding='utf-8')
                    
                    # Finde JSON-Block und aktualisiere Name
                    import re
                    # Suche nach "name": "alter Name" und ersetze
                    pattern = r'"name":\s*"[^"]*"'
                    replacement = f'"name": "{new_name}"'
                    updated_content = re.sub(pattern, replacement, content, count=1)
                    
                    # Schreibe zurück
                    metadata_file.write_text(updated_content, encoding='utf-8')
                    print(f"   ✓ Lokale metadata.txt aktualisiert")
                except Exception as e:
                    print(f"   ⚠ Warnung: Konnte metadata.txt nicht aktualisieren: {e}")
            
            return result
        else:
            print(f"   ✗ Fehler beim Umbenennen: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            response.raise_for_status()


def main():
    """Hauptfunktion mit Kommandozeilen-Argumenten."""
    parser = argparse.ArgumentParser(
        description="Ändert den Namen eines Snapshots über die Smart Planning API"
    )
    parser.add_argument(
        "snapshot_id",
        help="UUID des Snapshots"
    )
    parser.add_argument(
        "new_name",
        help="Neuer Name für den Snapshot"
    )
    parser.add_argument(
        "--client-id",
        default="apiClient-test",
        help="OAuth Client ID (default: apiClient-test)"
    )
    
    args = parser.parse_args()
    
    try:
        # API-Client initialisieren
        api = SmartPlanningAPI()
        
        # Authentifizieren
        api.authenticate(client_id=args.client_id)
        
        # Snapshot umbenennen
        result = api.rename_snapshot(args.snapshot_id, args.new_name)
        
        print("\n" + "="*60)
        print("ZUSAMMENFASSUNG")
        print("="*60)
        print(f"✓ Snapshot-ID:  {result.get('id', args.snapshot_id)}")
        print(f"✓ Neuer Name:   {result.get('name', args.new_name)}")
        print(f"✓ Status:       Erfolgreich umbenannt")
        print("="*60)
        
        # Erfolg-Signal für SP_Agent
        print("\nRENAME_SUCCESS")
        
    except Exception as e:
        print(f"\n✗ FEHLER: {str(e)}")
        print("\nRENAME_FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
