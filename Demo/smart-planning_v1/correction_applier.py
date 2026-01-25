"""
Correction Applier - Applies LLM corrections to snapshot

Applies validated LLM corrections and maintains audit log.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime
from correction_models import (
    DensityCorrectionResponse,
    DuplicateIDCorrectionResponse,
    EmptyIDCorrectionResponse,
    MissingReferenceResponse,
    GenericCorrectionResponse,
    CorrectionLogEntry
)

logger = logging.getLogger(__name__)


class CorrectionApplier:
    """
    Applies LLM-generated corrections to snapshot with audit logging.
    """
    
    def __init__(self):
        self.log: List[CorrectionLogEntry] = []
    
    def apply_density_correction(
        self,
        snapshot: Dict[str, Any],
        response: DensityCorrectionResponse,
        iteration: int = 0,
        error_message: str = ""
    ) -> Dict[str, Any]:
        """
        Apply density correction to snapshot.
        
        Args:
            snapshot: Full snapshot dict
            response: LLM correction response
            iteration: Current iteration number
            error_message: Original error message
            
        Returns:
            Updated snapshot
        """
        articles = snapshot.get('articles', [])
        
        # Find and update article
        updated = False
        for article in articles:
            if article.get('articleId') == response.article_id:
                old_min = article.get('relDensityMin')
                old_max = article.get('relDensityMax')
                
                article['relDensityMin'] = response.corrected_rel_density_min
                article['relDensityMax'] = response.corrected_rel_density_max
                
                logger.info(
                    f"Applied density correction for {response.article_id}: "
                    f"min {old_min} → {response.corrected_rel_density_min}, "
                    f"max {old_max} → {response.corrected_rel_density_max}"
                )
                
                # Log correction
                self.log.append(CorrectionLogEntry(
                    timestamp=datetime.utcnow(),
                    iteration=iteration,
                    error_type="density_validation",
                    error_message=error_message,
                    correction_type="density_correction",
                    affected_collection="articles",
                    affected_ids=[response.article_id],
                    changes_made={
                        "article_id": response.article_id,
                        "relDensityMin": response.corrected_rel_density_min,
                        "relDensityMax": response.corrected_rel_density_max,
                        "method": response.calculation_method
                    },
                    llm_reasoning=response.reasoning
                ))
                
                updated = True
                break
        
        if not updated:
            logger.warning(f"Article {response.article_id} not found for density correction")
        
        return snapshot
    
    def apply_duplicate_id_correction(
        self,
        snapshot: Dict[str, Any],
        collection: str,
        response: DuplicateIDCorrectionResponse,
        iteration: int = 0,
        error_message: str = ""
    ) -> Dict[str, Any]:
        """
        Apply duplicate ID correction to snapshot.
        
        Keeps one item with original ID, renames duplicates.
        """
        items = snapshot.get(collection, [])
        
        # Determine ID field
        id_field = self._get_id_field(collection)
        
        # Apply renames
        renamed_count = 0
        for rename in response.renamed_items:
            item_index = rename.index_in_collection
            
            if item_index < len(items):
                old_id = items[item_index].get(id_field)
                items[item_index][id_field] = rename.new_id
                
                logger.info(
                    f"Renamed {collection}[{item_index}] ID: {old_id} → {rename.new_id}"
                )
                renamed_count += 1
        
        # Log correction
        self.log.append(CorrectionLogEntry(
            timestamp=datetime.utcnow(),
            iteration=iteration,
            error_type="duplicate_id",
            error_message=error_message,
            correction_type="duplicate_id_correction",
            affected_collection=collection,
            affected_ids=[response.keep_original_id] + [r.new_id for r in response.renamed_items],
            changes_made={
                "kept_original": response.keep_original_id,
                "renamed": [r.dict() for r in response.renamed_items]
            },
            llm_reasoning=response.reasoning
        ))
        
        logger.info(
            f"Applied duplicate ID correction: kept {response.keep_original_id}, "
            f"renamed {renamed_count} items"
        )
        
        return snapshot
    
    def apply_empty_id_correction(
        self,
        snapshot: Dict[str, Any],
        collection: str,
        response: EmptyIDCorrectionResponse,
        iteration: int = 0,
        error_message: str = ""
    ) -> Dict[str, Any]:
        """
        Apply empty ID correction to snapshot.
        
        Assigns generated IDs to items with empty/null IDs.
        """
        items = snapshot.get(collection, [])
        id_field = self._get_id_field(collection)
        
        # Apply generated IDs
        assigned_count = 0
        for gen_id in response.generated_ids:
            item_index = gen_id.index_in_collection
            
            if item_index < len(items):
                items[item_index][id_field] = gen_id.generated_id
                
                logger.info(
                    f"Assigned {collection}[{item_index}] ID: {gen_id.generated_id}"
                )
                assigned_count += 1
        
        # Log correction
        generated_ids = [g.generated_id for g in response.generated_ids]
        self.log.append(CorrectionLogEntry(
            timestamp=datetime.utcnow(),
            iteration=iteration,
            error_type="empty_id",
            error_message=error_message,
            correction_type="empty_id_correction",
            affected_collection=collection,
            affected_ids=generated_ids,
            changes_made={
                "generated_ids": [g.dict() for g in response.generated_ids]
            },
            llm_reasoning=response.reasoning
        ))
        
        logger.info(f"Applied empty ID correction: assigned {assigned_count} IDs")
        
        return snapshot
    
    def apply_missing_reference_correction(
        self,
        snapshot: Dict[str, Any],
        collection: str,
        ref_field: str,
        response: MissingReferenceResponse
    ) -> Dict[str, Any]:
        """
        Apply missing reference correction to snapshot.
        
        Updates invalid references to valid targets.
        """
        items = snapshot.get(collection, [])
        
        # Apply reference corrections
        corrected_count = 0
        for correction in response.corrections:
            item_index = correction.item_index
            
            if item_index < len(items):
                old_ref = items[item_index].get(ref_field)
                
                if correction.new_reference_id:
                    items[item_index][ref_field] = correction.new_reference_id
                    logger.info(
                        f"Updated {collection}[{item_index}] ref: "
                        f"{old_ref} → {correction.new_reference_id}"
                    )
                else:
                    # Remove invalid reference
                    items[item_index][ref_field] = None
                    logger.info(f"Removed invalid ref from {collection}[{item_index}]")
                
                corrected_count += 1
        
        # Log correction
        self.log.append(CorrectionLogEntry(
            timestamp=datetime.utcnow(),
            error_type="missing_reference",
            affected_id=f"{collection}_refs",
            correction_applied={
                "collection": collection,
                "ref_field": ref_field,
                "strategy": response.strategy,
                "corrections": [c.dict() for c in response.corrections]
            },
            llm_reasoning=response.reasoning
        ))
        
        logger.info(
            f"Applied reference correction: fixed {corrected_count} refs "
            f"using {response.strategy}"
        )
        
        return snapshot
    
    def apply_generic_correction(
        self,
        snapshot: Dict[str, Any],
        response: GenericCorrectionResponse
    ) -> Dict[str, Any]:
        """
        Apply generic correction steps.
        
        WARNING: Generic corrections may require manual verification.
        """
        logger.warning(
            "Applying generic correction - requires manual verification. "
            f"Steps: {response.correction_steps}"
        )
        
        # Log for audit (actual changes need manual implementation)
        self.log.append(CorrectionLogEntry(
            timestamp=datetime.utcnow(),
            error_type="generic",
            affected_id="unknown",
            correction_applied={
                "steps": response.correction_steps,
                "requires_manual_verification": True
            },
            llm_reasoning=response.rationale
        ))
        
        return snapshot
    
    def get_correction_log(self) -> List[Dict[str, Any]]:
        """
        Get audit log of all applied corrections.
        
        Returns:
            List of correction log entries as dicts
        """
        return [entry.dict() for entry in self.log]
    
    def export_log_json(self, filepath: str):
        """Export correction log to JSON file"""
        import json
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.get_correction_log(), f, indent=2, default=str)
        
        logger.info(f"Exported correction log to {filepath}")
    
    # Helper methods
    
    def _get_id_field(self, collection: str) -> str:
        """Get ID field name for collection"""
        mapping = {
            'demands': 'demandId',
            'articles': 'articleId',
            'workPlans': 'workPlanId',
            'equipment': 'equipmentId',
            'workerQualifications': 'workerId',
            'workerAvailability': 'workerId'
        }
        return mapping.get(collection, 'id')
