import logging
import os
from datetime import datetime
from uuid import UUID, uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException

from .models import JobList, JobResponse, JobStatus, JobSubmission
from .storage import job_store

app = FastAPI(
    title="Pipeline Orchestration Service",
    description="REST API for submitting and tracking Snakemake pipeline jobs",
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


@app.post("/jobs", response_model=JobResponse, status_code=201)
async def submit_job(
    job_submission: JobSubmission, background_tasks: BackgroundTasks
) -> JobResponse:
    """
    Submit a new pipeline job for execution.

    Args:
        job_submission: Job submission details including pipeline name and parameters
        background_tasks: FastAPI background tasks for async execution

    Returns:
        JobResponse with the created job details
    """
    # Create job with unique ID and initial status
    job_id = uuid4()
    now = datetime.utcnow()

    job = JobResponse(
        id=job_id,
        status=JobStatus.PENDING,
        pipeline_name=job_submission.pipeline_name,
        parameters=job_submission.parameters,
        description=job_submission.description,
        created_at=now,
        updated_at=now,
    )

    # Store the job
    job_store.create(job)

    logger.info(
        f"Job {job_id} submitted: {job_submission.pipeline_name} "
        f"with parameters {job_submission.parameters}"
    )

    # TODO: Schedule background task to process the job
    # background_tasks.add_task(process_job, job_id)

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
async def list_jobs() -> JobList:
    """
    List all jobs.

    Returns:
        JobList containing all jobs and total count
    """
    jobs = job_store.list_all()
    total = job_store.count()

    logger.info(f"Listed {total} jobs")
    return JobList(jobs=jobs, total=total)

