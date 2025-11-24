"""
Business Logic and Validation Layer

This module demonstrates FastAPI's value as an abstraction layer by implementing
domain-specific validation and business rules before submitting to Prefect.
"""

from typing import Any, Dict, Optional, Union

from fastapi import HTTPException
from pydantic import ValidationError

from .pipeline_models import (
    PIPELINE_MODELS,
    GATKVariantCallingParams,
    RNASeqDESeq2Params,
)

# Pipeline descriptions for API documentation
PIPELINE_REGISTRY = {
    "gatk_variant_calling": {
        "description": "GATK variant calling pipeline for WGS/WES data",
        "model": GATKVariantCallingParams,
    },
    "rnaseq_deseq2": {
        "description": "RNA-seq differential expression analysis with DESeq2",
        "model": RNASeqDESeq2Params,
    },
}


def validate_pipeline_exists(pipeline_name: str) -> None:
    """
    Validate that the requested pipeline is supported.

    Args:
        pipeline_name: Name of the pipeline

    Raises:
        HTTPException: 400 if pipeline not found
    """
    if pipeline_name not in PIPELINE_REGISTRY:
        available = list(PIPELINE_REGISTRY.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Unknown pipeline '{pipeline_name}'. Available: {available}",
        )


def validate_pipeline_parameters(
    pipeline_name: str, parameters: Dict[str, Any]
) -> Union[GATKVariantCallingParams, RNASeqDESeq2Params]:
    """
    Validate pipeline parameters using Pydantic models.

    Args:
        pipeline_name: Name of the pipeline
        parameters: Pipeline parameters dictionary

    Returns:
        Validated Pydantic model instance

    Raises:
        HTTPException: 400 if validation fails
    """
    if pipeline_name not in PIPELINE_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown pipeline '{pipeline_name}'",
        )

    model_class = PIPELINE_MODELS[pipeline_name]

    try:
        # Validate using Pydantic model
        validated_params = model_class(**parameters)
        return validated_params
    except ValidationError as e:
        # Format validation errors for API response
        errors = []
        for error in e.errors():
            field = " -> ".join(str(x) for x in error["loc"])
            errors.append(f"{field}: {error['msg']}")

        raise HTTPException(
            status_code=400,
            detail=f"Invalid parameters for '{pipeline_name}': {'; '.join(errors)}",
        )


def get_pipeline_info(pipeline_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Get information about available pipelines.

    Args:
        pipeline_name: Optional specific pipeline to query

    Returns:
        Pipeline configuration information including schema
    """
    if pipeline_name:
        if pipeline_name not in PIPELINE_REGISTRY:
            raise HTTPException(
                status_code=404, detail=f"Pipeline '{pipeline_name}' not found"
            )
        config = PIPELINE_REGISTRY[pipeline_name]
        model_class = config["model"]
        schema = model_class.model_json_schema()
        # Extract example from json_schema_extra in model_config
        example = model_class.model_config.get("json_schema_extra", {}).get(
            "example", {}
        )
        return {
            "pipeline_name": pipeline_name,
            "description": config["description"],
            "parameters_schema": schema,
            "example": example,
        }

    return {
        "available_pipelines": [
            {
                "name": name,
                "description": config["description"],
                "parameters_schema": config["model"].model_json_schema(),
            }
            for name, config in PIPELINE_REGISTRY.items()
        ]
    }


def sanitize_parameters(
    parameters: Union[
        GATKVariantCallingParams,
        RNASeqDESeq2Params,
        Dict[str, Any],
    ],
) -> Dict[str, Any]:
    """
    Convert validated Pydantic model to dictionary for storage.

    Args:
        parameters: Validated pipeline parameters (Pydantic model or dict)

    Returns:
        Dictionary of parameters
    """
    # If already a Pydantic model, convert to dict
    if hasattr(parameters, "model_dump"):
        return parameters.model_dump(exclude_none=True)

    # Legacy dict handling
    return parameters
