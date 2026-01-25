#!/usr/bin/env python3
"""
Erstellt einen neuen Test-Snapshot in der API
"""

from smart_planning_api import SmartPlanningAPI
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

api = SmartPlanningAPI(
    base_url='https://vm-t-weu-ccadmm-idp-test02.internal.idp.cca-dev.com/esarom-be/api/v1',
    bearer_token=os.getenv('BEARER_TOKEN'),
    verify_ssl=False
)

# Erstelle neuen Snapshot
snapshot_name = f'AI-Correction-Test-{datetime.now().strftime("%Y%m%d_%H%M%S")}'
comment = 'Auto-generated test snapshot with crawler for AI correction testing'

snapshot_metadata = api.create_snapshot(
    name=snapshot_name,
    comment=comment,
    run_crawler=True  # ← Crawler läuft automatisch und füllt Snapshot mit Daten
)

# Manueller Schritt, weil der Snapshot initial keine Errors beinhaltet
print(f"\n{'='*70}")
print(f"✓ Neuer Snapshot erstellt")
print(f"{'='*70}")
print(f"Snapshot ID: {snapshot_metadata['id']}")
print(f"Snapshot Name: {snapshot_metadata['name']}")
print(f"Comment: {snapshot_metadata.get('comment', 'N/A')}")
print(f"Validated: {snapshot_metadata.get('isSuccessfullyValidated', 'N/A')}")
print(f"Modified At: {snapshot_metadata.get('dataModifiedAt', 'N/A')}")
print(f"Modified By: {snapshot_metadata.get('dataModifiedBy', 'N/A')}")
print(f"\n🔧 NÄCHSTER SCHRITT:")
print(f"   Bitte baue jetzt Errors in den Snapshot ein!")
print(f"   Wenn fertig, starte: python main_correction.py {snapshot_metadata['id']}")
print(f"{'='*70}\n")
print(f"   Wenn fertig, starte: python main_correction.py {snapshot_id}")
print(f"{'='*70}\n")
