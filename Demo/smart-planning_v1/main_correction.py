#!/usr/bin/env python3
"""
Smart Planning Snapshot Corrector - Main Entry Point

Workflow:
1. Hole Snapshot von Smart Planning API
2. Speichere lokal in snapshots-ai/snapshot-TIMESTAMP/
3. Validiere und hole Fehler
4. Korrigiere mit LLM in Schleife
5. Speichere korrigierten Snapshot
"""

import argparse
import json
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv

from smart_planning_api import SmartPlanningAPI
from context_extractor import ContextExtractor
from llm_corrector import LLMCorrector
from correction_applier import CorrectionApplier

# Load environment variables from .env
load_dotenv()

# Configure logging
log_dir = Path('system-logs')
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f'correction_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class SnapshotCorrectionOrchestrator:
    """
    Orchestrates the full correction workflow with LLM intelligence.
    """
    
    def __init__(
        self,
        api_client: SmartPlanningAPI,
        llm_corrector: LLMCorrector,
        work_dir: Path,
        original_snapshot_id: str,
        max_iterations: int = 10
    ):
        self.api = api_client
        self.llm = llm_corrector
        self.work_dir = work_dir
        self.original_snapshot_id = original_snapshot_id
        self.max_iterations = max_iterations
        self.applier = CorrectionApplier()
    
    def correct_snapshot(
        self,
        snapshot: Dict[str, Any],
        snapshot_name: str = None
    ) -> Dict[str, Any]:
        """
        Auto-correct snapshot until all errors are resolved.
        
        Returns:
            Final corrected snapshot
        """
        if not snapshot_name:
            snapshot_name = f"AutoCorrect_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        current_snapshot = snapshot.copy()
        iteration = 0
        
        logger.info(f"Starting auto-correction: {snapshot_name}")
        
        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"\n{'='*60}")
            logger.info(f"Iteration {iteration}/{self.max_iterations}")
            logger.info(f"{'='*60}")
            
            # Update snapshot and get validation
            logger.info("Updating snapshot in Smart Planning API...")
            self.api.update_snapshot(
                snapshot_id=self.original_snapshot_id,
                snapshot_data=current_snapshot,
                name=f"{snapshot_name}_iter{iteration}",
                comment=f"Auto-correction iteration {iteration}"
            )
            
            logger.info(f"Snapshot updated: {self.original_snapshot_id}")
            
            # Get validation messages
            validation = self.api.get_validation_messages(self.original_snapshot_id)
            errors = [msg for msg in validation if msg['level'] == 'ERROR']
            warnings = [msg for msg in validation if msg['level'] == 'WARNING']
            
            logger.info(f"Validation result: {len(errors)} errors, {len(warnings)} warnings")
            
            # Save validation for this iteration
            validation_file = self.work_dir / f"validation-iteration-{iteration}.json"
            with open(validation_file, 'w', encoding='utf-8') as f:
                json.dump(validation, f, indent=2, ensure_ascii=False)
            logger.info(f"✓ Validierung gespeichert: {validation_file.name}")
            
            # Check if done
            if len(errors) == 0:
                logger.info("✓ No errors remaining - snapshot is valid!")
                break
            
            # Process each error
            logger.info(f"Processing {len(errors)} errors...")
            extractor = ContextExtractor(current_snapshot)
            
            # Directory for this iteration's contexts
            context_dir = self.work_dir / "logs" / f"iteration-{iteration}"
            context_dir.mkdir(parents=True, exist_ok=True)
            
            for idx, error in enumerate(errors, 1):
                logger.info(f"\n--- Error {idx}/{len(errors)} ---")
                logger.info(f"Message: {error['message']}")
                
                try:
                    # Extract context
                    context = extractor.extract_for_error(error)
                    if not context:
                        logger.warning("Could not extract context - skipping")
                        continue
                    
                    # Save extracted context for inspection
                    context_file = context_dir / f"context-error-{idx}.json"
                    with open(context_file, 'w', encoding='utf-8') as f:
                        # Convert Pydantic model to dict for JSON serialization
                        json.dump(context.model_dump() if hasattr(context, 'model_dump') else context.dict(), 
                                  f, indent=2, ensure_ascii=False)
                    logger.info(f"✓ Context gespeichert: {context_file.name}")
                    
                    # Get LLM correction
                    correction = self._get_llm_correction(context)
                    if not correction:
                        logger.warning("Could not get LLM correction - skipping")
                        continue
                    
                    # Save LLM response for inspection
                    response_file = context_dir / f"llm-response-error-{idx}.json"
                    with open(response_file, 'w', encoding='utf-8') as f:
                        json.dump(correction.model_dump() if hasattr(correction, 'model_dump') else correction.dict(),
                                  f, indent=2, ensure_ascii=False)
                    logger.info(f"✓ LLM Response gespeichert: {response_file.name}")
                    
                    # Apply correction
                    current_snapshot = self._apply_correction(
                        current_snapshot,
                        context,
                        correction,
                        iteration=iteration,
                        error_message=error['message']
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to correct error: {e}", exc_info=True)
                    continue
            
            # Save snapshot after each iteration
            iter_snapshot_file = self.work_dir / f"snapshot-iteration-{iteration}.json"
            with open(iter_snapshot_file, 'w', encoding='utf-8') as f:
                json.dump(current_snapshot, f, indent=2, ensure_ascii=False)
            logger.info(f"✓ Snapshot nach Iteration {iteration} gespeichert")
            
            logger.info(f"Iteration {iteration} complete")
        
        if iteration >= self.max_iterations:
            logger.warning(f"Max iterations ({self.max_iterations}) reached - snapshot may still have errors")
        
        return current_snapshot
    
    def _get_llm_correction(self, context: Any) -> Any:
        """Route context to appropriate LLM corrector"""
        from correction_models import (
            DensityCorrectionRequest,
            DuplicateIDCorrectionRequest,
            EmptyIDCorrectionRequest,
            MissingReferenceRequest
        )
        
        if isinstance(context, DensityCorrectionRequest):
            return self.llm.correct_density_error(context)
        elif isinstance(context, DuplicateIDCorrectionRequest):
            return self.llm.correct_duplicate_id(context)
        elif isinstance(context, EmptyIDCorrectionRequest):
            return self.llm.correct_empty_id(context)
        elif isinstance(context, MissingReferenceRequest):
            return self.llm.correct_missing_reference(context)
        else:
            logger.warning(f"Unknown context type: {type(context)}")
            return None
    
    def _apply_correction(
        self,
        snapshot: Dict[str, Any],
        context: Any,
        correction: Any,
        iteration: int = 0,
        error_message: str = ""
    ) -> Dict[str, Any]:
        """Route correction to appropriate applier"""
        from correction_models import (
            DensityCorrectionResponse,
            DuplicateIDCorrectionResponse,
            EmptyIDCorrectionResponse,
            MissingReferenceResponse
        )
        
        if isinstance(correction, DensityCorrectionResponse):
            return self.applier.apply_density_correction(
                snapshot, 
                correction, 
                iteration=iteration, 
                error_message=error_message
            )
        elif isinstance(correction, DuplicateIDCorrectionResponse):
            return self.applier.apply_duplicate_id_correction(
                snapshot,
                context.collection,
                correction,
                iteration=iteration,
                error_message=error_message
            )
        elif isinstance(correction, EmptyIDCorrectionResponse):
            return self.applier.apply_empty_id_correction(
                snapshot,
                context.collection,
                correction,
                iteration=iteration,
                error_message=error_message
            )
        elif isinstance(correction, MissingReferenceResponse):
            ref_field = self._get_ref_field(context)
            return self.applier.apply_missing_reference_correction(
                snapshot,
                context.referencing_items[0].get('_collection', 'unknown'),
                ref_field,
                correction
            )
        else:
            logger.warning(f"Unknown correction type: {type(correction)}")
            return snapshot
    
    def _get_ref_field(self, context: Any) -> str:
        """Extract reference field from context"""
        return 'workPlanId'  # Default
    
    def export_correction_log(self, filepath: str):
        """Export detailed correction log"""
        self.applier.export_log_json(filepath)


def main():
    parser = argparse.ArgumentParser(
        description='Hole Snapshot von API und korrigiere mit LLM'
    )
    parser.add_argument(
        'snapshot_id',
        help='UUID des Snapshots in Smart Planning API'
    )
    parser.add_argument(
        '--api-url',
        default='https://vm-t-weu-ccadmm-idp-test02.internal.idp.cca-dev.com/esarom-be/api/v1',
        help='Smart Planning API base URL'
    )
    parser.add_argument(
        '--bearer-token',
        help='OAuth2 Bearer Token (or set BEARER_TOKEN in .env)'
    )
    parser.add_argument(
        '--verify-ssl',
        action='store_true',
        help='Verify SSL certificates (default: False)'
    )
    parser.add_argument(
        '--azure-endpoint',
        help='Azure OpenAI endpoint (or set AZURE_OPENAI_SP_ENDPOINT in .env)'
    )
    parser.add_argument(
        '--azure-key',
        help='Azure OpenAI API key (or set AZURE_OPENAI_SP_KEY in .env)'
    )
    parser.add_argument(
        '--openai-key',
        help='[DEPRECATED] Use --azure-key instead'
    )
    parser.add_argument(
        '--deployment-name',
        default='gpt-4o-mini',
        help='Azure OpenAI deployment name (default: gpt-4o-mini)'
    )
    parser.add_argument(
        '--model',
        help='[DEPRECATED] Use --deployment-name instead'
    )
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=10,
        help='Maximum correction iterations'
    )
    
    args = parser.parse_args()
    
    # Read from environment
    bearer_token = args.bearer_token or os.getenv('BEARER_TOKEN')
    azure_endpoint = args.azure_endpoint or os.getenv('AZURE_OPENAI_SP_ENDPOINT')
    azure_key = args.azure_key or os.getenv('AZURE_OPENAI_SP_KEY')
    deployment_name = args.deployment_name or os.getenv('AZURE_OPENAI_SP_DEPLOYMENT', 'gpt-4o-mini')
    api_version = os.getenv('AZURE_OPENAI_SP_API_VERSION', '2025-01-01-preview')
    
    if not bearer_token:
        logger.error("Bearer token required! Set BEARER_TOKEN in .env")
        return 1
    
    if not azure_endpoint:
        logger.error("Azure OpenAI endpoint required! Set AZURE_OPENAI_SP_ENDPOINT in .env")
        return 1
    
    if not azure_key:
        logger.error("Azure OpenAI API key required! Set AZURE_OPENAI_SP_KEY in .env")
        return 1
    
    try:
        # Initialize API client
        api_client = SmartPlanningAPI(
            base_url=args.api_url,
            bearer_token=bearer_token,
            verify_ssl=args.verify_ssl
        )
        
        # SCHRITT 1: Snapshot von API holen
        logger.info(f"\n{'='*70}")
        logger.info(f"SCHRITT 1: Hole Snapshot {args.snapshot_id} von API")
        logger.info(f"{'='*70}")
        
        snapshot_response = api_client.get_snapshot(args.snapshot_id)
        
        # Extract dataJson (it's a string!)
        snapshot_data_str = snapshot_response.get('dataJson')
        if not snapshot_data_str:
            logger.error("Snapshot hat kein dataJson!")
            return 1
        
        snapshot_data = json.loads(snapshot_data_str)
        snapshot_name = snapshot_response.get('name', 'UnknownSnapshot')
        
        logger.info(f"✓ Snapshot geladen: {snapshot_name}")
        logger.info(f"  - {len(snapshot_data.get('articles', []))} Articles")
        logger.info(f"  - {len(snapshot_data.get('demands', []))} Demands")
        logger.info(f"  - {len(snapshot_data.get('equipment', []))} Equipment")
        logger.info(f"  - {len(snapshot_data.get('workerQualifications', []))} WorkerQualifications")
        
        # SCHRITT 2: Lokal speichern
        # Verwende snapshot_id für Ordnernamen (nicht Timestamp!)
        output_dir = Path(f"snapshots-ai/snapshot-{args.snapshot_id}")
        
        # Bereinige alte Iterationsdateien falls Ordner schon existiert
        if output_dir.exists():
            # Lösche alte iteration snapshots und logs
            for old_file in output_dir.glob("snapshot-iteration-*.json"):
                old_file.unlink()
            for old_file in output_dir.glob("validation-iteration-*.json"):
                old_file.unlink()
            if (output_dir / "logs").exists():
                import shutil
                shutil.rmtree(output_dir / "logs")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"\n{'='*70}")
        logger.info(f"SCHRITT 2: Speichere lokal in {output_dir}")
        logger.info(f"{'='*70}")
        
        # Snapshot-Inhalt
        snapshot_file = output_dir / "snapshot-original.json"
        with open(snapshot_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot_data, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Snapshot: {snapshot_file.name}")
        
        # Metadaten - Hole vollständige Snapshot-Metadaten von API
        full_snapshot = api_client.get_snapshot(args.snapshot_id)
        metadata = {
            "original_snapshot_id": args.snapshot_id,
            "original_snapshot_name": snapshot_name,
            "timestamp": datetime.now().isoformat(),
            "api_url": args.api_url,
            "snapshot_size": {
                "articles": len(snapshot_data.get('articles', [])),
                "demands": len(snapshot_data.get('demands', [])),
                "equipment": len(snapshot_data.get('equipment', [])),
                "workerQualifications": len(snapshot_data.get('workerQualifications', []))
            },
            # API Metadaten
            "api_metadata": {
                "id": full_snapshot.get('id'),
                "name": full_snapshot.get('name'),
                "comment": full_snapshot.get('comment'),
                "parentId": full_snapshot.get('parentId'),
                "nrOfChildren": full_snapshot.get('nrOfChildren'),
                "isSuccessfullyValidated": full_snapshot.get('isSuccessfullyValidated'),
                "dataModifiedAt": full_snapshot.get('dataModifiedAt'),
                "dataModifiedBy": full_snapshot.get('dataModifiedBy'),
                "planningRun": full_snapshot.get('planningRun')
            }
        }
        with open(output_dir / "metadata.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Metadaten: metadata.json")
        
        # SCHRITT 3: Validierung holen
        logger.info(f"\n{'='*70}")
        logger.info(f"SCHRITT 3: Hole Validierung von API")
        logger.info(f"{'='*70}")
        
        validation = api_client.get_validation_messages(args.snapshot_id)
        
        with open(output_dir / "validation-original.json", 'w', encoding='utf-8') as f:
            json.dump(validation, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Validierung: validation-original.json")
        
        errors = [m for m in validation if m['level'] == 'ERROR']
        warnings = [m for m in validation if m['level'] == 'WARNING']
        logger.info(f"  - {len(errors)} ERRORs")
        logger.info(f"  - {len(warnings)} WARNINGs")
        
        if len(errors) == 0:
            logger.info("\n✓ Snapshot ist bereits valide!")
            return 0
        
        # SCHRITT 4: LLM-Korrekturen
        logger.info(f"\n{'='*70}")
        logger.info(f"SCHRITT 4: Starte LLM-Korrektur-Loop")
        logger.info(f"{'='*70}")
        
        llm_corrector = LLMCorrector(
            azure_endpoint=azure_endpoint,
            api_key=azure_key,
            api_version=api_version,
            deployment_name=deployment_name
        )
        
        orchestrator = SnapshotCorrectionOrchestrator(
            api_client=api_client,
            llm_corrector=llm_corrector,
            work_dir=output_dir,
            original_snapshot_id=args.snapshot_id,
            max_iterations=args.max_iterations
        )
        
        corrected_snapshot = orchestrator.correct_snapshot(
            snapshot_data,
            snapshot_name=f"{snapshot_name}_corrected"
        )
        
        # SCHRITT 5: Korrigierten Snapshot speichern
        logger.info(f"\n{'='*70}")
        logger.info(f"SCHRITT 5: Speichere korrigierten Snapshot")
        logger.info(f"{'='*70}")
        
        with open(output_dir / "snapshot-corrected.json", 'w', encoding='utf-8') as f:
            json.dump(corrected_snapshot, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Korrigiert: snapshot-corrected.json")
        
        orchestrator.export_correction_log(str(output_dir / "correction-log.json"))
        logger.info(f"✓ Log: correction-log.json")
        
        logger.info(f"\n{'='*70}")
        logger.info(f"✓ FERTIG! Alle Dateien in:")
        logger.info(f"  {output_dir.absolute()}")
        logger.info(f"{'='*70}")
        return 0
        
    except Exception as e:
        logger.error(f"\n✗ Fehler: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
