"""
Runtime Storage Helper

Provides snapshot-specific storage access for all runtime scripts.
Supports both LOCAL filesystem and AZURE Blob Storage.

Usage in runtime scripts:
    from runtime_storage import get_storage, get_iteration_folders, get_iteration_folders_with_file, get_latest_iteration_number

STORAGE_MODE is read from .env:
    STORAGE_MODE=LOCAL  → reads/writes from Snapshots/ folder (default)
    STORAGE_MODE=AZURE  → reads/writes from Azure Blob Storage
"""

import re
import sys
from pathlib import Path
from typing import List, Optional

# Add demo directory to sys.path so StorageManager can be imported
_demo_dir = str(Path(__file__).parent.parent.parent)
if _demo_dir not in sys.path:
    sys.path.insert(0, _demo_dir)

from storage_manager import StorageManager

# Singleton StorageManager instance (lazy-initialized)
_storage: Optional[StorageManager] = None


def get_storage() -> StorageManager:
    """
    Returns the singleton StorageManager configured for the Snapshots directory.
    Call this at the start of any function that needs to read/write snapshot files.
    """
    global _storage
    if _storage is None:
        # Base path: <runtime_dir>/../../Snapshots  =  smart-planning/Snapshots
        snapshots_base = str(Path(__file__).parent.parent / "Snapshots")
        _storage = StorageManager(base_path=snapshots_base)
    return _storage


def get_iteration_folders(snapshot_id: str) -> List[int]:
    """
    Returns a sorted list of all iteration numbers that exist for a snapshot.
    Works for both LOCAL and AZURE modes.

    Example: [1, 2, 3]
    """
    storage = get_storage()
    iteration_numbers = []

    if storage.mode == "LOCAL":
        local_path = storage._get_local_path(snapshot_id)
        if local_path.exists():
            for item in local_path.iterdir():
                m = re.match(r'^iteration-(\d+)$', item.name)
                if m and item.is_dir():
                    iteration_numbers.append(int(m.group(1)))
    else:
        # Azure: list blobs with prefix and extract iteration numbers
        blobs = storage.list_files(f"{snapshot_id}/")
        seen = set()
        for blob_path in blobs:
            # blob_path format: "snapshot_id/iteration-2/file.json"
            parts = blob_path.replace("\\", "/").split("/")
            if len(parts) >= 2:
                m = re.match(r'^iteration-(\d+)$', parts[1])
                if m:
                    seen.add(int(m.group(1)))
        iteration_numbers = list(seen)

    return sorted(iteration_numbers)


def get_iteration_folders_with_file(snapshot_id: str, filename: str) -> List[int]:
    """
    Returns a sorted list of iteration numbers where a specific file exists.
    Works for both LOCAL and AZURE modes.

    Example: get_iteration_folders_with_file(id, "llm_correction_proposal.json") → [1, 2]
    """
    storage = get_storage()
    iteration_numbers = []

    if storage.mode == "LOCAL":
        local_path = storage._get_local_path(snapshot_id)
        if local_path.exists():
            for item in local_path.iterdir():
                m = re.match(r'^iteration-(\d+)$', item.name)
                if m and item.is_dir() and (item / filename).exists():
                    iteration_numbers.append(int(m.group(1)))
    else:
        # Azure: check if blobs with the specific file exist per iteration
        blobs = storage.list_files(f"{snapshot_id}/")
        seen = set()
        for blob_path in blobs:
            # Looking for: snapshot_id/iteration-N/filename
            parts = blob_path.replace("\\", "/").split("/")
            if len(parts) >= 3 and parts[2] == filename:
                m = re.match(r'^iteration-(\d+)$', parts[1])
                if m:
                    seen.add(int(m.group(1)))
        iteration_numbers = list(seen)

    return sorted(iteration_numbers)


def get_latest_iteration_number(snapshot_id: str, require_file: str = None) -> Optional[int]:
    """
    Returns the highest iteration number for a snapshot.
    Optionally filter to only iterations that contain a specific file.
    Returns None if no iterations found.

    Examples:
        get_latest_iteration_number(id)                                    → 3
        get_latest_iteration_number(id, "llm_correction_proposal.json")   → 2
    """
    if require_file:
        nums = get_iteration_folders_with_file(snapshot_id, require_file)
    else:
        nums = get_iteration_folders(snapshot_id)

    return max(nums) if nums else None
