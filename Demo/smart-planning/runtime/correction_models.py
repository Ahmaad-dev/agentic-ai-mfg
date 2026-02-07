"""
Pydantic models for LLM correction proposal validation
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Union, Any


class AdditionalUpdate(BaseModel):
    """Model for additional updates in correction proposal"""
    target_path: str = Field(..., description="Path to the field to update (e.g., demands[166].demandId)")
    current_value: Union[str, int, float, bool, None] = Field(..., description="Current value of the field (supports all JSON types)")
    new_value: Union[str, int, float, bool, None] = Field(..., description="New value to set (supports all JSON types)")


class CorrectionProposal(BaseModel):
    """Model for the correction proposal from LLM"""
    action: str = Field(..., description="Action to perform: update_field, add_to_array, remove_from_array")
    target_path: str = Field(..., description="Path to the field/array (e.g., demands[165].demandId or demands)")
    current_value: Optional[Union[str, int, float, bool, None, dict]] = Field(None, description="Current value (for update_field) or item to remove (for remove_from_array)")
    new_value: Optional[Union[str, int, float, bool, None, dict]] = Field(None, description="New value (for update_field) or item to add (for add_to_array)")
    reasoning: str = Field(..., description="Explanation why this correction is needed")
    additional_updates: Optional[List[AdditionalUpdate]] = Field(
        default_factory=list,
        description="Optional list of additional updates to apply"
    )


class OriginalError(BaseModel):
    """Model for original validation error"""
    level: str = Field(..., description="Error level (ERROR, WARNING)")
    message: str = Field(..., description="Error message from validation API")


class ErrorAnalyzed(BaseModel):
    """Model for analyzed error from identify_error_llm.py"""
    search_mode: str = Field(..., description="Search mode used (value, empty, field)")
    search_value: Optional[Union[str, int]] = Field(None, description="Value searched for (string or integer)")
    error_type: str = Field(..., description="Type of error (DUPLICATE_ID, EMPTY_FIELD, etc.)")
    results_count: int = Field(..., description="Number of results found")


class LLMCorrectionResponse(BaseModel):
    """Complete model for LLM correction response"""
    iteration: int = Field(..., description="Iteration number")
    snapshot_id: str = Field(..., description="Snapshot UUID")
    original_error: OriginalError = Field(..., description="Original validation error")
    error_analyzed: ErrorAnalyzed = Field(..., description="Analyzed error information")
    correction_proposal: CorrectionProposal = Field(..., description="The correction proposal")
