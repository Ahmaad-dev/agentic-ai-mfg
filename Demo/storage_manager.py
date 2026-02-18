import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Try to import azure-storage-blob, but don't crash if not installed (for pure local dev)
try:
    from azure.storage.blob import BlobServiceClient
    AZURE_STORAGE_AVAILABLE = True
except ImportError:
    AZURE_STORAGE_AVAILABLE = False

logger = logging.getLogger(__name__)

class StorageManager:
    """
    Abstraktionsschicht für Dateizugriff.
    Unterstützt lokalen Dateisystemzugriff und Azure Blob Storage.
    Konfiguration erfolgt über Umgebungsvariablen:
    - STORAGE_MODE: 'LOCAL' (default) oder 'AZURE'
    - AZURE_STORAGE_CONNECTION_STRING: Benötigt für 'AZURE' Mode
    - AZURE_STORAGE_CONTAINER: Name des Containers (default: 'snapshots')
    - LOCAL_STORAGE_PATH: Basispfad für lokale Dateien (default: './smart-planning/Snapshots')
    """

    def __init__(self, base_path: Optional[str] = None):
        from dotenv import load_dotenv
        load_dotenv()

        self.mode = os.getenv("STORAGE_MODE", "LOCAL").upper()
        
        # Lokaler Basispfad konfigurieren
        if base_path:
             self.local_base_path = Path(base_path)
        else:
             # Default path relative to this file or project root
             # Assuming this file is in demo/utils/ or demo/
             # Adjust based on where this file is placed.
             # If placed in demo/, then smart-planning is in ./smart-planning
             self.local_base_path = Path(os.getenv("LOCAL_STORAGE_PATH", "./smart-planning/Snapshots")).resolve()

        # Azure Konfiguration
        self.container_name = os.getenv("AZURE_STORAGE_CONTAINER", "snapshots")
        self.connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.blob_service_client = None
        self.container_client = None

        if self.mode == "AZURE":
            if not AZURE_STORAGE_AVAILABLE:
                logger.warning("azure-storage-blob nicht installiert. Fallback auf LOCAL Modus.")
                self.mode = "LOCAL"
            elif not self.connection_string:
                logger.warning("AZURE_STORAGE_CONNECTION_STRING nicht gesetzt. Fallback auf LOCAL Modus.")
                self.mode = "LOCAL"
            else:
                try:
                    self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
                    self.container_client = self.blob_service_client.get_container_client(self.container_name)
                    if not self.container_client.exists():
                        self.container_client.create_container()
                    logger.info(f"StorageManager initialisiert im AZURE Modus (Container: {self.container_name})")
                except Exception as e:
                    logger.error(f"Fehler bei Azure Storage Initialisierung: {e}. Fallback auf LOCAL.")
                    self.mode = "LOCAL"

        if self.mode == "LOCAL":
            logger.info(f"StorageManager initialisiert im LOCAL Modus (Pfad: {self.local_base_path})")
            self.local_base_path.mkdir(parents=True, exist_ok=True)

    def _get_local_path(self, path: str) -> Path:
        """Konvertiert relativen Pfad in absoluten lokalen Pfad"""
        return self.local_base_path / path

    def save_json(self, path: str, data: Union[Dict, List]) -> str:
        """Speichert Daten als JSON Datei"""
        try:
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            
            if self.mode == "AZURE":
                blob_client = self.container_client.get_blob_client(path)
                blob_client.upload_blob(json_str, overwrite=True)
                return blob_client.url
            else:
                full_path = self._get_local_path(path)
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(json_str)
                return str(full_path)
        except Exception as e:
            logger.error(f"Fehler beim Speichern von {path}: {e}")
            raise

    def load_json(self, path: str) -> Union[Dict, List, None]:
        """Lädt Daten aus einer JSON Datei"""
        try:
            if self.mode == "AZURE":
                blob_client = self.container_client.get_blob_client(path)
                if not blob_client.exists():
                    return None
                download_stream = blob_client.download_blob()
                return json.loads(download_stream.readall())
            else:
                full_path = self._get_local_path(path)
                if not full_path.exists():
                    return None
                with open(full_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Fehler beim Laden von {path}: {e}")
            return None

    def save_text(self, path: str, content: str) -> str:
        """Speichert Text in eine Datei"""
        try:
            if self.mode == "AZURE":
                blob_client = self.container_client.get_blob_client(path)
                blob_client.upload_blob(content, overwrite=True)
                return blob_client.url
            else:
                full_path = self._get_local_path(path)
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return str(full_path)
        except Exception as e:
            logger.error(f"Fehler beim Speichern von {path}: {e}")
            raise

    def load_text(self, path: str) -> Optional[str]:
        """Lädt Text aus einer Datei"""
        try:
            if self.mode == "AZURE":
                blob_client = self.container_client.get_blob_client(path)
                if not blob_client.exists():
                    return None
                return blob_client.download_blob().readall().decode('utf-8')
            else:
                full_path = self._get_local_path(path)
                if not full_path.exists():
                    return None
                with open(full_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            logger.error(f"Fehler beim Laden von {path}: {e}")
            return None

    def list_files(self, prefix: str = "") -> List[str]:
        """Listet Dateien in einem Verzeichnis (oder mit Prefix) auf"""
        files = []
        try:
            if self.mode == "AZURE":
                # Azure Blob Storage lists recursively by default if prefix is a folder
                blob_list = self.container_client.list_blobs(name_starts_with=prefix)
                for blob in blob_list:
                    files.append(blob.name)
            else:
                # Local lists recursively? No, pathlib glob needed.
                # Here implementation might differ. Let's do a simple recursive walk for consistency
                full_path = self._get_local_path(prefix)
                if full_path.exists() and full_path.is_dir():
                    for p in full_path.rglob("*"):
                        if p.is_file():
                            # Return relative path from base
                            files.append(str(p.relative_to(self.local_base_path)).replace("\\", "/"))
        except Exception as e:
            logger.error(f"Fehler beim Listen von Dateien mit Prefix {prefix}: {e}")
        return files

    def exists(self, path: str) -> bool:
        """Prüft ob eine Datei existiert"""
        try:
            if self.mode == "AZURE":
                blob_client = self.container_client.get_blob_client(path)
                return blob_client.exists()
            else:
                return self._get_local_path(path).exists()
        except Exception:
            return False
