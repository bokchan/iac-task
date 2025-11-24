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
        ..., description="Name of the Snakemake pipeline to execute"
    )
    parameters: dict = Field(
        default_factory=dict, description="Pipeline parameters and configuration"
    )
    description: Optional[str] = Field(None, description="Optional job description")

    class Config:
        json_schema_extra = {
            "example": {
                "pipeline_name": "variant_calling",
                "parameters": {"sample_id": "S001", "genome": "hg38"},
                "description": "Run variant calling on sample S001",
            }
        }


class JobResponse(BaseModel):
    """Response model for job information."""

    id: UUID = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    pipeline_name: str = Field(..., description="Pipeline name")
    parameters: dict = Field(..., description="Pipeline parameters")
    description: Optional[str] = Field(None, description="Job description")
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
                "pipeline_name": "variant_calling",
                "parameters": {"sample_id": "S001", "genome": "hg38"},
                "description": "Run variant calling on sample S001",
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
                        "pipeline_name": "variant_calling",
                        "parameters": {"sample_id": "S001"},
                        "created_at": "2025-11-24T10:00:00Z",
                        "updated_at": "2025-11-24T10:00:30Z",
                    }
                ],
                "total": 1,
            }
        }
