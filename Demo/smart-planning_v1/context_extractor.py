"""
Context Extractor - Isolates relevant data for LLM

Extracts only the affected objects + context from the full snapshot,
reducing token usage from MB to KB.
"""

import re
import logging
from typing import Dict, List, Any, Optional
from correction_models import (
    DensityCorrectionRequest,
    DuplicateIDCorrectionRequest,
    EmptyIDCorrectionRequest,
    MissingReferenceRequest
)

logger = logging.getLogger(__name__)


class ContextExtractor:
    """
    Extracts minimal relevant context from snapshot for each error.
    
    Instead of sending 1.6 MB snapshot to LLM,
    sends only 2-10 KB of relevant data.
    """
    
    def __init__(self, snapshot: Dict[str, Any]):
        self.snapshot = snapshot
        
    def extract_for_error(self, error: Dict[str, str]) -> Optional[Any]:
        """
        Routes error to appropriate extraction method based on message pattern.
        
        Args:
            error: Validation error dict with 'level' and 'message'
            
        Returns:
            Appropriate CorrectionRequest model or None
        """
        message = error.get('message', '')
        
        # Parse validator name
        validator_match = re.search(r'\[(\w+)\]', message)
        if not validator_match:
            logger.warning(f"Could not parse validator from: {message}")
            return None
        
        validator = validator_match.group(1)
        
        # Route to specific extractor
        if validator == 'validate_density_values':
            return self.extract_density_error(message)
        elif validator == 'validate_unique_ids':
            if 'Duplicate' in message:
                return self.extract_duplicate_id_error(message)
            elif 'empty' in message.lower():
                return self.extract_empty_id_error(message)
        elif validator in ['validate_work_plan_ids', 'validate_demand_article_ids',
                          'validate_equipment_predecessor_references']:
            return self.extract_missing_reference_error(message, validator)
        
        logger.warning(f"No extraction handler for validator: {validator}")
        return None
    
    def extract_density_error(self, error_message: str) -> DensityCorrectionRequest:
        """
        Extracts context for density validation errors.
        
        Error format: "[validate_density_values] Article 106270 has invalid rel_density_min: 0.0"
        """
        # Parse article ID
        article_id = self._parse_article_id(error_message)
        if not article_id:
            raise ValueError(f"Could not parse article ID from: {error_message}")
        
        # Find affected article
        articles = self.snapshot.get('articles', [])
        affected = next(
            (a for a in articles if a.get('articleId') == article_id),
            None
        )
        
        if not affected:
            raise ValueError(f"Article {article_id} not found in snapshot")
        
        # Find similar articles (same type, valid density)
        similar = [
            a for a in articles
            if (a.get('articleId') != article_id and
                a.get('articleType') == affected.get('articleType') and
                a.get('relDensityMin', 0) > 0)
        ][:10]  # Max 10 for context
        
        logger.debug(f"Extracted density error context: {article_id}, {len(similar)} similar articles")
        
        return DensityCorrectionRequest(
            error_message=error_message,
            affected_article=affected,
            similar_articles=similar
        )
    
    def extract_duplicate_id_error(self, error_message: str) -> DuplicateIDCorrectionRequest:
        """
        Extracts context for duplicate ID errors.
        
        Error format: "[validate_unique_ids] Demand IDs must be unique. Duplicates found: D830081_005."
        """
        # Parse duplicate ID
        duplicate_id_match = re.search(r'Duplicates found: ([A-Z0-9_-]+)', error_message)
        if not duplicate_id_match:
            raise ValueError(f"Could not parse duplicate ID from: {error_message}")
        
        duplicate_id = duplicate_id_match.group(1)
        
        # Determine collection
        if 'Demand IDs' in error_message:
            collection = 'demands'
            id_field = 'demandId'
        elif 'Article IDs' in error_message:
            collection = 'articles'
            id_field = 'articleId'
        elif 'Work Plan' in error_message:
            collection = 'workPlans'
            id_field = 'workPlanId'
        elif 'Equipment' in error_message:
            collection = 'equipment'
            id_field = 'equipmentId'
        elif 'Worker' in error_message:
            collection = 'workerQualifications'  # or workerAvailability
            id_field = 'workerId'
        else:
            raise ValueError(f"Unknown collection type in: {error_message}")
        
        # Find all items with this ID
        items = self.snapshot.get(collection, [])
        duplicates = [
            {**item, '_index': idx}  # Add index for reference
            for idx, item in enumerate(items)
            if item.get(id_field) == duplicate_id
        ]
        
        logger.debug(f"Extracted duplicate ID: {duplicate_id} ({len(duplicates)} occurrences)")
        
        return DuplicateIDCorrectionRequest(
            error_message=error_message,
            duplicate_id=duplicate_id,
            collection=collection,
            affected_items=duplicates
        )
    
    def extract_empty_id_error(self, error_message: str) -> EmptyIDCorrectionRequest:
        """
        Extracts context for empty ID errors.
        
        Error format: "[validate_unique_ids] Demand IDs must not be empty. Empty IDs found: ."
        """
        # Determine collection
        if 'Demand IDs' in error_message:
            collection = 'demands'
            id_field = 'demandId'
        elif 'Article IDs' in error_message:
            collection = 'articles'
            id_field = 'articleId'
        elif 'Work Plan' in error_message:
            collection = 'workPlans'
            id_field = 'workPlanId'
        elif 'Equipment' in error_message:
            collection = 'equipment'
            id_field = 'equipmentId'
        else:
            raise ValueError(f"Unknown collection in: {error_message}")
        
        # Find items with empty/null IDs
        items = self.snapshot.get(collection, [])
        empty_items = [
            {**item, '_index': idx}
            for idx, item in enumerate(items)
            if not item.get(id_field)
        ]
        
        logger.debug(f"Extracted empty ID errors: {len(empty_items)} items in {collection}")
        
        return EmptyIDCorrectionRequest(
            error_message=error_message,
            collection=collection,
            empty_items=empty_items
        )
    
    def extract_missing_reference_error(
        self, 
        error_message: str,
        validator: str
    ) -> MissingReferenceRequest:
        """
        Extracts context for missing reference errors.
        
        Examples:
        - "Work Plan IDs in Articles do not exist in Work Plans"
        - "Article IDs in Demands do not exist in Articles"
        """
        # Determine reference type and collections
        if validator == 'validate_work_plan_ids':
            ref_type = 'work_plan_id'
            referencing_collection = 'articles'
            ref_field = 'workPlanId'
            target_collection = 'workPlans'
            target_id_field = 'workPlanId'
            
        elif validator == 'validate_demand_article_ids':
            ref_type = 'article_id'
            referencing_collection = 'demands'
            ref_field = 'articleId'
            target_collection = 'articles'
            target_id_field = 'articleId'
            
        elif validator == 'validate_equipment_predecessor_references':
            ref_type = 'equipment_id'
            referencing_collection = 'equipment'
            ref_field = 'predecessorKey'  # May vary
            target_collection = 'equipment'
            target_id_field = 'equipmentId'
        else:
            raise ValueError(f"Unknown reference validator: {validator}")
        
        # Get valid target IDs
        targets = self.snapshot.get(target_collection, [])
        valid_ids = {t.get(target_id_field) for t in targets if t.get(target_id_field)}
        
        # Find items with invalid references
        items = self.snapshot.get(referencing_collection, [])
        invalid_refs = [
            {**item, '_index': idx}
            for idx, item in enumerate(items)
            if item.get(ref_field) and item.get(ref_field) not in valid_ids
        ]
        
        # Get sample of available targets (max 20)
        available_targets = targets[:20]
        
        logger.debug(f"Extracted missing ref: {len(invalid_refs)} invalid, {len(targets)} available")
        
        return MissingReferenceRequest(
            error_message=error_message,
            reference_type=ref_type,
            referencing_items=invalid_refs,
            available_targets=available_targets
        )
    
    # Helper methods
    
    def _parse_article_id(self, message: str) -> Optional[str]:
        """Extract article ID from error message"""
        match = re.search(r'Article (\d+)', message)
        return match.group(1) if match else None
    
    def _parse_demand_id(self, message: str) -> Optional[str]:
        """Extract demand ID from error message"""
        match = re.search(r'Demand ([A-Z0-9_-]+)', message)
        return match.group(1) if match else None
