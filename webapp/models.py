"""Pydantic models for job management."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .pipeline_models import GATKVariantCallingParams, PipelineName, RNASeqDESeq2Params


class JobStatus(str, Enum):
    """Job execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobSubmission(BaseModel):
    """Request model for job submission."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pipeline_name": "gatk_variant_calling",
                "parameters": {
                    "sample_id": "WGS_001",
                    "reference_genome": "hg38",
                    "bam_file": "s3://input-data/WGS_001.bam",
                    "quality_threshold": 30,
                    "caller": "HaplotypeCaller",
                },
                "description": "GATK variant calling for tumor sample WGS_001",
                "research_group": "cancer_genomics_lab",
            }
        }
    )

    pipeline_name: PipelineName = Field(
        ..., description="Name of the bioinformatics pipeline to execute"
    )
    parameters: GATKVariantCallingParams | RNASeqDESeq2Params = Field(
        ..., description="Pipeline parameters and configuration"
    )
    description: str | None = Field(None, description="Optional job description")
    research_group: str | None = Field(
        None, description="Research group or lab identifier submitting the job"
    )

    @model_validator(mode="after")
    def validate_pipeline_parameters_match(self):
        """Ensure parameters match the pipeline_name."""
        pipeline_to_model = {
            PipelineName.GATK_VARIANT_CALLING: GATKVariantCallingParams,
            PipelineName.RNASEQ_DESEQ2: RNASeqDESeq2Params,
        }

        expected_model = pipeline_to_model.get(self.pipeline_name)
        if expected_model and not isinstance(self.parameters, expected_model):
            raise ValueError(
                f"Parameters for pipeline '{self.pipeline_name}' must be of type "
                f"{expected_model.__name__}, got {type(self.parameters).__name__}"
            )
        return self


class JobResponse(BaseModel):
    """Response model for job information."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "running",
                "pipeline_name": "gatk_variant_calling",
                "parameters": {
                    "sample_id": "WGS_001",
                    "reference_genome": "hg38",
                    "bam_file": "s3://input-data/WGS_001.bam",
                    "quality_threshold": 30,
                    "caller": "HaplotypeCaller",
                },
                "description": "GATK variant calling for tumor sample WGS_001",
                "research_group": "cancer_genomics_lab",
                "created_at": "2025-11-24T10:00:00Z",
                "updated_at": "2025-11-24T10:00:05Z",
                "started_at": "2025-11-24T10:00:05Z",
                "completed_at": None,
                "error_message": None,
            }
        }
    )

    id: UUID = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    pipeline_name: PipelineName = Field(..., description="Pipeline name")
    parameters: GATKVariantCallingParams | RNASeqDESeq2Params = Field(..., description="Pipeline parameters")
    description: str | None = Field(None, description="Job description")
    research_group: str | None = Field(
        None, description="Research group or lab identifier"
    )
    created_at: datetime = Field(..., description="Job creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    started_at: datetime | None = Field(None, description="Job start timestamp")
    completed_at: datetime | None = Field(
        None, description="Job completion timestamp"
    )
    error_message: str | None = Field(
        None, description="Error message if job failed"
    )


class JobList(BaseModel):
    """Response model for listing jobs."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "jobs": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "status": "completed",
                        "pipeline_name": "gatk_variant_calling",
                        "parameters": {
                            "sample_id": "WGS_001",
                            "reference_genome": "hg38",
                        },
                        "research_group": "cancer_genomics_lab",
                        "created_at": "2025-11-24T10:00:00Z",
                        "updated_at": "2025-11-24T10:00:30Z",
                    }
                ],
                "total": 1,
            }
        }
    )

    jobs: list[JobResponse] = Field(..., description="List of jobs")
    total: int = Field(..., description="Total number of jobs")
