"""
Pydantic Models für LLM-basierte Snapshot-Korrekturen

Jeder Fehlertyp hat:
1. Request Model - Input für LLM (nur relevante Daten)
2. Response Model - Erzwungenes Output-Schema vom LLM
"""

from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional, List, Dict, Any
from datetime import datetime


# =============================================================================
# 1. DENSITY CORRECTION
# =============================================================================

class DensityCorrectionRequest(BaseModel):
    """Input für LLM bei invalid density errors"""
    error_message: str = Field(description="Original error message from validation")
    affected_article: Dict[str, Any] = Field(description="The article with invalid density")
    similar_articles: List[Dict[str, Any]] = Field(
        description="Up to 10 similar articles for reference",
        max_length=10
    )


class DensityCorrectionResponse(BaseModel):
    """Enforced output structure from LLM for density corrections"""
    article_id: str = Field(description="ID of the article being corrected")
    corrected_rel_density_min: float = Field(
        gt=0,
        description="Corrected relDensityMin value (must be > 0)"
    )
    corrected_rel_density_max: float = Field(
        gt=0,
        description="Corrected relDensityMax value (must be > 0)"
    )
    calculation_method: Literal["median", "average", "min_from_similar", "max_from_similar", "default"] = Field(
        description="Method used to calculate the values"
    )
    reasoning: str = Field(
        description="Detailed explanation of why these values were chosen"
    )

    @field_validator('corrected_rel_density_max')
    @classmethod
    def validate_max_ge_min(cls, v, info):
        """Ensure max >= min"""
        if 'corrected_rel_density_min' in info.data:
            if v < info.data['corrected_rel_density_min']:
                raise ValueError('relDensityMax must be >= relDensityMin')
        return v


# =============================================================================
# 2. DUPLICATE ID CORRECTION
# =============================================================================

class DuplicateIDCorrectionRequest(BaseModel):
    """Input für LLM bei duplicate ID errors"""
    error_message: str
    duplicate_id: str = Field(description="The ID that is duplicated")
    collection: Literal["demands", "articles", "workPlans", "equipment", "workers"]
    affected_items: List[Dict[str, Any]] = Field(
        description="All items with the duplicate ID"
    )


class RenamedItem(BaseModel):
    """Structure for a renamed item"""
    original_id: str
    new_id: str
    index_in_collection: int = Field(description="Array index of this item")
    reason: str = Field(description="Why this item was renamed (e.g., 'older dueDate', 'lower priority')")


class DuplicateIDCorrectionResponse(BaseModel):
    """Enforced output for duplicate ID corrections"""
    collection: Literal["demands", "articles", "workPlans", "equipment", "workers"]
    keep_original_id: str = Field(
        description="ID value that keeps the original (not renamed)"
    )
    renamed_items: List[RenamedItem] = Field(
        description="Items that need to be renamed with new IDs"
    )
    reasoning: str = Field(
        description="Overall strategy for deciding which to keep vs rename"
    )


# =============================================================================
# 3. EMPTY ID CORRECTION
# =============================================================================

class EmptyIDCorrectionRequest(BaseModel):
    """Input für LLM bei empty ID errors"""
    error_message: str
    collection: Literal["demands", "articles", "workPlans", "equipment", "workers"]
    empty_items: List[Dict[str, Any]] = Field(
        description="Items with empty/null IDs (with their array index)"
    )


class GeneratedID(BaseModel):
    """Structure for a generated ID"""
    index_in_collection: int
    generated_id: str = Field(
        pattern=r'^[A-Z0-9_-]{3,50}$',
        description="Generated ID (alphanumeric, underscore, dash)"
    )
    generation_strategy: Literal["uuid", "incremental", "derived_from_data", "timestamp"]
    reasoning: str


class EmptyIDCorrectionResponse(BaseModel):
    """Enforced output for empty ID corrections"""
    collection: Literal["demands", "articles", "workPlans", "equipment", "workers"]
    generated_ids: List[GeneratedID]
    reasoning: str


# =============================================================================
# 4. MISSING REFERENCE CORRECTION
# =============================================================================

class MissingReferenceRequest(BaseModel):
    """Input für LLM bei missing reference errors"""
    error_message: str
    reference_type: Literal[
        "work_plan_id",
        "article_id",
        "equipment_id",
        "packaging_id",
        "worker_id"
    ]
    referencing_items: List[Dict[str, Any]] = Field(
        description="Items that reference non-existent IDs"
    )
    available_targets: List[Dict[str, Any]] = Field(
        description="Valid items that could be referenced instead",
        max_length=20
    )


class ReferenceCorrection(BaseModel):
    """Structure for a single reference correction"""
    item_index: int
    old_reference_id: Optional[str]
    new_reference_id: str
    reasoning: str


class MissingReferenceResponse(BaseModel):
    """Enforced output for missing reference corrections"""
    reference_type: Literal[
        "work_plan_id",
        "article_id",
        "equipment_id",
        "packaging_id",
        "worker_id"
    ]
    corrections: List[ReferenceCorrection]
    strategy: Literal["map_to_similar", "map_to_default", "remove_reference", "create_dummy"]
    reasoning: str


# =============================================================================
# 5. GENERIC CORRECTION (for complex/unknown errors)
# =============================================================================

class GenericCorrectionRequest(BaseModel):
    """Fallback input for errors not matching specific patterns"""
    error_message: str
    error_type: str = Field(description="Validator name from error message")
    affected_data: Dict[str, Any] = Field(
        description="Relevant snapshot data related to error"
    )
    correction_rules: str = Field(
        description="Business rules for fixing this type of error"
    )


class GenericCorrectionResponse(BaseModel):
    """Generic correction output"""
    corrections: List[Dict[str, Any]] = Field(
        description="List of corrections to apply (path + value)"
    )
    reasoning: str
    confidence: Literal["high", "medium", "low"] = Field(
        description="LLM's confidence in this correction"
    )


# =============================================================================
# CORRECTION LOG ENTRY
# =============================================================================

class CorrectionLogEntry(BaseModel):
    """Logged entry for every correction made"""
    timestamp: datetime = Field(default_factory=datetime.now)
    iteration: int
    error_type: str
    error_message: str
    correction_type: str = Field(
        description="Type of correction applied"
    )
    affected_collection: Optional[str] = None
    affected_ids: List[str] = Field(default_factory=list)
    llm_reasoning: str
    changes_made: Dict[str, Any]
    llm_confidence: Optional[str] = None
