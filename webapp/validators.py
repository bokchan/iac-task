"""
Business Logic and Validation Layer

This module demonstrates FastAPI's value as an abstraction layer by implementing
domain-specific validation and business rules before submitting to Prefect.
"""

from typing import Dict, List, Optional
from fastapi import HTTPException


# Supported pipelines with their required parameters
PIPELINE_REGISTRY = {
    "gatk_variant_calling": {
        "required_params": ["sample_id", "reference_genome"],
        "optional_params": ["fastq_r1", "fastq_r2", "bam_file", "caller", "quality_threshold", "depth_threshold"],
        "valid_references": ["hg19", "hg38", "GRCh37", "GRCh38"],
        "description": "GATK variant calling pipeline for WGS/WES data",
    },
    "rnaseq_deseq2": {
        "required_params": ["sample_id", "reference"],
        "optional_params": ["fastq_files", "adapter_sequence", "min_quality", "quantification_method"],
        "valid_references": ["gencode_v38", "gencode_v44", "ensembl_110"],
        "description": "RNA-seq differential expression analysis with DESeq2",
    },
    "cross_lab_etl": {
        "required_params": ["source_group", "target_group", "data_types"],
        "optional_params": ["validation_level", "anonymize"],
        "description": "Cross-laboratory data integration and ETL",
    },
    "chip_seq_macs2": {
        "required_params": ["sample_id", "reference_genome", "antibody"],
        "optional_params": ["input_control", "peak_type", "fdr_threshold"],
        "valid_references": ["hg38", "mm10", "mm39"],
        "description": "ChIP-seq peak calling with MACS2",
    },
}


# Research group quotas (jobs per day)
RESEARCH_GROUP_QUOTAS = {
    "genomics_lab": 100,
    "transcriptomics_lab": 50,
    "cancer_genomics_lab": 100,
    "clinical_research": 30,
    "data_integration_team": 20,
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
            detail=f"Unknown pipeline '{pipeline_name}'. Available: {available}"
        )


def validate_pipeline_parameters(pipeline_name: str, parameters: Dict) -> None:
    """
    Validate that required parameters are present and valid.

    Args:
        pipeline_name: Name of the pipeline
        parameters: Pipeline parameters

    Raises:
        HTTPException: 400 if validation fails
    """
    config = PIPELINE_REGISTRY[pipeline_name]

    # Check required parameters
    required = config.get("required_params", [])
    missing = [param for param in required if param not in parameters]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required parameters for '{pipeline_name}': {missing}"
        )

    # Validate reference genome if applicable
    if "reference_genome" in parameters:
        valid_refs = config.get("valid_references", [])
        if valid_refs and parameters["reference_genome"] not in valid_refs:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid reference_genome. Valid options for {pipeline_name}: {valid_refs}"
            )

    # Validate reference transcriptome if applicable
    if "reference" in parameters:
        valid_refs = config.get("valid_references", [])
        if valid_refs and parameters["reference"] not in valid_refs:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid reference. Valid options for {pipeline_name}: {valid_refs}"
            )


def check_research_group_quota(research_group: Optional[str], job_count: int) -> None:
    """
    Check if research group has exceeded their quota.

    Args:
        research_group: Research group identifier
        job_count: Current number of jobs submitted today

    Raises:
        HTTPException: 429 if quota exceeded
    """
    if not research_group:
        return  # No quota enforcement for anonymous submissions

    quota = RESEARCH_GROUP_QUOTAS.get(research_group)
    if quota is None:
        # Unknown research group - allow but log warning
        return

    if job_count >= quota:
        raise HTTPException(
            status_code=429,
            detail=f"Research group '{research_group}' has exceeded daily quota of {quota} jobs"
        )


def validate_file_paths(parameters: Dict) -> None:
    """
    Validate that file paths follow expected patterns.

    Args:
        parameters: Pipeline parameters

    Raises:
        HTTPException: 400 if file paths are invalid
    """
    file_params = ["fastq_r1", "fastq_r2", "bam_file", "fastq_files"]

    for param in file_params:
        if param not in parameters:
            continue

        paths = parameters[param] if isinstance(parameters[param], list) else [parameters[param]]

        for path in paths:
            if not isinstance(path, str):
                continue

            # Check for valid path prefixes (s3://, /data/, etc.)
            valid_prefixes = ["s3://", "/data/", "/mnt/", "gs://", "https://"]
            if not any(path.startswith(prefix) for prefix in valid_prefixes):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file path '{path}'. Must start with: {valid_prefixes}"
                )


def get_pipeline_info(pipeline_name: Optional[str] = None) -> Dict:
    """
    Get information about available pipelines.

    Args:
        pipeline_name: Optional specific pipeline to query

    Returns:
        Pipeline configuration information
    """
    if pipeline_name:
        if pipeline_name not in PIPELINE_REGISTRY:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline '{pipeline_name}' not found"
            )
        return {
            "pipeline_name": pipeline_name,
            **PIPELINE_REGISTRY[pipeline_name]
        }

    return {
        "available_pipelines": [
            {
                "name": name,
                "description": config["description"],
                "required_params": config["required_params"],
            }
            for name, config in PIPELINE_REGISTRY.items()
        ]
    }


def sanitize_parameters(parameters: Dict) -> Dict:
    """
    Sanitize and normalize parameters before execution.

    Args:
        parameters: Raw pipeline parameters

    Returns:
        Sanitized parameters
    """
    sanitized = parameters.copy()

    # Normalize reference genome naming
    if "reference_genome" in sanitized:
        ref = sanitized["reference_genome"].lower()
        if ref in ["grch38", "hg38"]:
            sanitized["reference_genome"] = "hg38"
        elif ref in ["grch37", "hg19"]:
            sanitized["reference_genome"] = "hg19"

    # Ensure quality thresholds are integers
    for param in ["quality_threshold", "min_quality", "depth_threshold"]:
        if param in sanitized and isinstance(sanitized[param], (int, float)):
            sanitized[param] = int(sanitized[param])

    # Convert single file to list if needed
    if "fastq_files" in sanitized and isinstance(sanitized["fastq_files"], str):
        sanitized["fastq_files"] = [sanitized["fastq_files"]]

    return sanitized
