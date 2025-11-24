"""
Pipeline Registry and Utility Functions

Provides:
- Pipeline registry with descriptions and parameter schemas
- get_pipeline_info() for API discovery endpoints

Note: Parameter validation is handled automatically by Pydantic models
in pipeline_models.py and models.py, not in this module.
"""

from typing import Any

from fastapi import HTTPException

from .pipeline_models import (
    GATKVariantCallingParams,
    PipelineName,
    RNASeqDESeq2Params,
)

# Pipeline descriptions for API documentation
PIPELINE_REGISTRY: dict[PipelineName, dict] = {
    PipelineName.GATK_VARIANT_CALLING: {
        "description": "GATK variant calling pipeline for WGS/WES data",
        "model": GATKVariantCallingParams,
    },
    PipelineName.RNASEQ_DESEQ2: {
        "description": "RNA-seq differential expression analysis with DESeq2",
        "model": RNASeqDESeq2Params,
    },
}


def get_pipeline_info(
    pipeline_name: str | PipelineName | None = None,
) -> dict[str, object]:
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
        config = PIPELINE_REGISTRY[pipeline_name]  # pyrefly: ignore[bad-index]
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
