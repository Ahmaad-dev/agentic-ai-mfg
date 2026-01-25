"""
LLM Corrector - Intelligent error correction with structured outputs

Uses OpenAI's structured output feature to guarantee valid responses.
"""

import logging
from typing import Optional, Any
from openai import AzureOpenAI
from correction_models import (
    DensityCorrectionRequest, DensityCorrectionResponse,
    DuplicateIDCorrectionRequest, DuplicateIDCorrectionResponse,
    EmptyIDCorrectionRequest, EmptyIDCorrectionResponse,
    MissingReferenceRequest, MissingReferenceResponse,
    GenericCorrectionRequest, GenericCorrectionResponse
)

logger = logging.getLogger(__name__)


class LLMCorrector:
    """
    Corrects snapshot errors using LLM with enforced structured outputs.
    
    Uses OpenAI's beta.chat.completions.parse() with response_format
    to guarantee schema-compliant responses.
    """
    
    def __init__(
        self,
        azure_endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        api_version: str = "2024-08-01-preview",
        deployment_name: str = "gpt-4o-mini",
        temperature: float = 0.2
    ):
        """
        Initialize LLM corrector with Azure OpenAI.
        
        Args:
            azure_endpoint: Azure OpenAI endpoint URL
            api_key: Azure OpenAI API key
            api_version: API version
            deployment_name: Deployment name (e.g., gpt-4o-mini)
            temperature: Sampling temperature (lower = more deterministic)
        """
        self.client = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=api_key,
            api_version=api_version
        )
        self.model = deployment_name
        self.temperature = temperature
        
        # Verify model supports structured outputs
        if deployment_name not in ["gpt-4o", "gpt-4o-mini"]:
            logger.warning(
                f"Model {deployment_name} may not support structured outputs. "
                "Recommended: gpt-4o or gpt-4o-mini"
            )
    
    def correct_density_error(
        self, 
        request: DensityCorrectionRequest
    ) -> DensityCorrectionResponse:
        """
        Correct invalid density using LLM with structured output.
        
        LLM analyzes similar articles and suggests intelligent correction
        (median, mode, or domain-specific logic).
        """
        system_prompt = """You are an expert in manufacturing planning data correction.
Your task is to fix invalid density values by analyzing similar articles.

Guidelines:
- Calculate median of similar articles' relDensityMin/Max
- If no similar articles, use manufacturing domain knowledge (typical: 1.0-2.0)
- Ensure relDensityMax >= relDensityMin
- Explain your reasoning clearly"""

        user_prompt = f"""Fix the following density error:

Error: {request.error_message}

Affected Article:
{request.affected_article}

Similar Articles (for reference):
{request.similar_articles}

Provide corrected relDensityMin and relDensityMax values."""

        logger.info(f"Requesting LLM correction for density error: {request.affected_article.get('articleId')}")
        
        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=DensityCorrectionResponse,
            temperature=self.temperature
        )
        
        response = completion.choices[0].message.parsed
        logger.debug(f"LLM response: {response.calculation_method}, {response.reasoning}")
        
        return response
    
    def correct_duplicate_id(
        self,
        request: DuplicateIDCorrectionRequest
    ) -> DuplicateIDCorrectionResponse:
        """
        Correct duplicate IDs using LLM decision logic.
        
        LLM analyzes which duplicate to keep (original ID) and generates
        new IDs for the others.
        """
        system_prompt = """You are an expert in manufacturing planning data correction.
Your task is to resolve duplicate IDs by keeping one original and renaming others.

Guidelines:
- Keep the ID for the item that appears most "complete" or referenced elsewhere
- Generate new IDs following pattern: ORIGINAL_ID_2, ORIGINAL_ID_3, etc.
- Explain your decision clearly"""

        user_prompt = f"""Fix the following duplicate ID error:

Error: {request.error_message}

Duplicate ID: {request.duplicate_id}
Collection: {request.collection}

Items with this ID:
{request.affected_items}

Decide which item keeps the original ID and what new IDs to assign to others."""

        logger.info(f"Requesting LLM correction for duplicate ID: {request.duplicate_id}")
        
        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=DuplicateIDCorrectionResponse,
            temperature=self.temperature
        )
        
        response = completion.choices[0].message.parsed
        logger.debug(f"LLM response: keep original={response.keep_original_id}, renamed {len(response.renamed_items)}")
        
        return response
    
    def correct_empty_id(
        self,
        request: EmptyIDCorrectionRequest
    ) -> EmptyIDCorrectionResponse:
        """
        Generate valid IDs for empty/null IDs.
        
        LLM generates unique, meaningful IDs based on item context.
        """
        system_prompt = """You are an expert in manufacturing planning data correction.
Your task is to generate valid IDs for items with empty/null IDs.

Guidelines:
- Generate unique IDs in format: AUTO_<UUID> or context-based like EQUIP_<type>_<number>
- IDs must match pattern: ^[A-Z0-9_-]+$
- Ensure no duplicates in generated IDs
- Use item context to create meaningful IDs when possible"""

        user_prompt = f"""Fix the following empty ID error:

Error: {request.error_message}

Collection: {request.collection}
Items with empty IDs: {len(request.empty_items)}

Items:
{request.empty_items}

Generate unique valid IDs for each item."""

        logger.info(f"Requesting LLM correction for {len(request.empty_items)} empty IDs")
        
        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=EmptyIDCorrectionResponse,
            temperature=self.temperature
        )
        
        response = completion.choices[0].message.parsed
        logger.debug(f"LLM generated {len(response.generated_ids)} IDs")
        
        return response
    
    def correct_missing_reference(
        self,
        request: MissingReferenceRequest
    ) -> MissingReferenceResponse:
        """
        Fix missing reference errors with intelligent mapping.
        
        LLM maps invalid references to valid targets based on similarity.
        """
        system_prompt = """You are an expert in manufacturing planning data correction.
Your task is to fix broken references by mapping to valid targets.

Guidelines:
- Map each invalid reference to the most similar valid target
- Use context like names, types, or other attributes for matching
- Strategy options: exact_match, fuzzy_match, fallback_default, remove_reference
- Explain your mapping logic clearly"""

        user_prompt = f"""Fix the following missing reference error:

Error: {request.error_message}

Reference Type: {request.reference_type}
Items with invalid references: {len(request.referencing_items)}

Invalid References:
{request.referencing_items}

Available Valid Targets:
{request.available_targets}

Map each invalid reference to a valid target."""

        logger.info(f"Requesting LLM correction for {len(request.referencing_items)} missing refs")
        
        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=MissingReferenceResponse,
            temperature=self.temperature
        )
        
        response = completion.choices[0].message.parsed
        logger.debug(f"LLM mapped {len(response.corrections)} references using {response.strategy}")
        
        return response
    
    def correct_generic_error(
        self,
        request: GenericCorrectionRequest
    ) -> GenericCorrectionResponse:
        """
        Handle unknown error types with generic LLM correction.
        
        Fallback for errors not covered by specific handlers.
        """
        system_prompt = """You are an expert in manufacturing planning data correction.
Your task is to fix validation errors in snapshot data.

Provide specific correction steps with clear reasoning."""

        user_prompt = f"""Fix the following validation error:

Error: {request.error_message}

Affected Data:
{request.affected_data}

Provide correction steps and rationale."""

        logger.info(f"Requesting generic LLM correction for: {request.error_message[:100]}")
        
        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=GenericCorrectionResponse,
            temperature=self.temperature
        )
        
        response = completion.choices[0].message.parsed
        logger.debug(f"LLM generic correction: {len(response.correction_steps)} steps")
        
        return response
