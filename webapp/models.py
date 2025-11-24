"""Pydantic models for job management."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobSubmission(BaseModel):
    """Request model for job submission."""

    pipeline_name: str = Field(
        ..., description="Name of the bioinformatics pipeline to execute"
    )
    parameters: dict = Field(
        default_factory=dict, description="Pipeline parameters and configuration"
    )
    description: Optional[str] = Field(None, description="Optional job description")
    research_group: Optional[str] = Field(
        None, description="Research group or lab identifier submitting the job"
    )

    class Config:
        json_schema_extra = {
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


class JobResponse(BaseModel):
    """Response model for job information."""

    id: UUID = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    pipeline_name: str = Field(..., description="Pipeline name")
    parameters: dict = Field(..., description="Pipeline parameters")
    description: Optional[str] = Field(None, description="Job description")
    research_group: Optional[str] = Field(
        None, description="Research group or lab identifier"
    )
    created_at: datetime = Field(..., description="Job creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    started_at: Optional[datetime] = Field(None, description="Job start timestamp")
    completed_at: Optional[datetime] = Field(
        None, description="Job completion timestamp"
    )
    error_message: Optional[str] = Field(
        None, description="Error message if job failed"
    )

    class Config:
        json_schema_extra = {
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


class JobList(BaseModel):
    """Response model for listing jobs."""

    jobs: list[JobResponse] = Field(..., description="List of jobs")
    total: int = Field(..., description="Total number of jobs")

    class Config:
        json_schema_extra = {
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
