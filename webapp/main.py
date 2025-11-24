import logging
import os
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query

from webapp.models import JobList, JobResponse, JobStatus, JobSubmission
from .storage import job_store
from .validators import (
    validate_pipeline_exists,
    validate_pipeline_parameters,
    sanitize_parameters,
    get_pipeline_info,
)
from .orchestrator import submit_to_orchestrator, get_orchestrator_status

app = FastAPI(
    title="Pipeline Orchestration Service",
    description="""Domain-specific REST API for bioinformatics pipeline orchestration.

    Provides an abstraction layer over workflow engines (Prefect, Dagster, etc.) with:
    - Simplified job submission interface
    - Pipeline validation and business logic
    - Multi-tenant research group tracking
    - Unified job state management
    """,
    version="1.0.0",
)

# Configure logging, with the log level set by the environment variable LOG_LEVEL
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger(__name__)


@app.get("/")
async def root():
    """Return the string configured by the environment variable: ECHO_MESSAGE"""
    msg = os.environ.get("ECHO_MESSAGE", "Hello World")
    return {"message": msg}


@app.get("/health")
async def health_check():
    """Healthcheck"""
    return "OK"


@app.get("/version")
async def version():
    """Return the deployed version (image tag)"""
    version = os.environ.get("IMAGE_TAG", "unknown")
    logger.info(f"Version endpoint called, returning version: {version}")
    return {"version": version}


@app.get("/pipelines")
async def list_pipelines():
    """
    List available pipelines with their requirements.

    This endpoint demonstrates domain-specific API design - clients don't need
    to know about Prefect deployments, Dagster jobs, or Airflow DAGs.
    """
    return get_pipeline_info()


@app.get("/pipelines/{pipeline_name}")
async def get_pipeline(pipeline_name: str):
    """
    Get detailed information about a specific pipeline.

    Args:
        pipeline_name: Name of the pipeline

    Returns:
        Pipeline configuration and requirements
    """
    return get_pipeline_info(pipeline_name)


@app.get("/orchestrator/status")
async def orchestrator_status():
    """
    Get status of the underlying orchestration backend.

    Demonstrates abstraction - you can check backend health without
    exposing Prefect/Dagster/etc. directly to clients.
    """
    return get_orchestrator_status()


@app.post("/jobs", response_model=JobResponse, status_code=201)
async def submit_job(
    job_submission: JobSubmission, background_tasks: BackgroundTasks
) -> JobResponse:
    """
    Submit a new pipeline job for execution.

    This endpoint demonstrates FastAPI's value as an abstraction layer:
    1. Validates pipeline exists and parameters are correct
    2. Sanitizes and normalizes parameters
    3. Abstracts the underlying orchestration engine (Prefect/Dagster/etc.)
    4. Provides unified job tracking across all pipelines

    Args:
        job_submission: Job submission details including pipeline name and parameters
        background_tasks: FastAPI background tasks for async execution

    Returns:
        JobResponse with the created job details

    Raises:
        HTTPException: 400 for validation errors
    """
    # Business Logic Layer: Validate pipeline and parameters using Pydantic models
    validate_pipeline_exists(job_submission.pipeline_name)
    validated_params = validate_pipeline_parameters(
        job_submission.pipeline_name, job_submission.parameters
    )

    # Business Logic Layer: Convert validated model to dict for storage
    sanitized_params = sanitize_parameters(validated_params)

    # Create job with unique ID and initial status
    job_id = uuid4()
    now = datetime.now(tz=timezone.utc)

    job = JobResponse(
        id=job_id,
        status=JobStatus.PENDING,
        pipeline_name=job_submission.pipeline_name,
        parameters=sanitized_params,
        description=job_submission.description,
        research_group=job_submission.research_group,
        created_at=now,
        updated_at=now,
    )

    # Store the job in our persistent layer
    job_store.create(job)

    logger.info(
        f"Job {job_id} submitted by {job_submission.research_group or 'anonymous'}: "
        f"{job_submission.pipeline_name} with parameters {sanitized_params}"
    )

    # Orchestration Abstraction: Submit to configured backend (Prefect/Dagster/etc.)
    background_tasks.add_task(
        submit_to_orchestrator,
        job_id=job_id,
        pipeline_name=job_submission.pipeline_name,
        parameters=sanitized_params,
        research_group=job_submission.research_group,
    )
    logger.info(f"Job {job_id} submitted to orchestration backend")

    return job


@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: UUID) -> JobResponse:
    """
    Get job status and details by ID.

    Args:
        job_id: UUID of the job to retrieve

    Returns:
        JobResponse with current job details

    Raises:
        HTTPException: 404 if job not found
    """
    job = job_store.get(job_id)
    if job is None:
        logger.warning(f"Job {job_id} not found")
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    logger.info(f"Retrieved job {job_id} with status {job.status}")
    return job


@app.get("/jobs", response_model=JobList)
async def list_jobs(
    research_group: Optional[str] = Query(None, description="Filter by research group"),
    status: Optional[JobStatus] = Query(None, description="Filter by job status"),
) -> JobList:
    """
    List all jobs with optional filtering.

    Demonstrates multi-tenant isolation - research groups can filter their jobs.

    Args:
        research_group: Optional filter by research group
        status: Optional filter by job status

    Returns:
        JobList containing filtered jobs and total count
    """
    jobs = job_store.list_all()

    # Business Logic Layer: Filter by research group (multi-tenant isolation)
    if research_group:
        jobs = [j for j in jobs if j.research_group == research_group]

    # Business Logic Layer: Filter by status
    if status:
        jobs = [j for j in jobs if j.status == status]

    total = len(jobs)
    logger.info(
        f"Listed {total} jobs (research_group={research_group}, status={status})"
    )
    return JobList(jobs=jobs, total=total)
