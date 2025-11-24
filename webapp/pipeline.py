"""Mock Snakemake pipeline execution."""

import asyncio
import logging
import random
from datetime import datetime
from uuid import UUID

from .models import JobStatus
from .storage import job_store

logger = logging.getLogger(__name__)


async def execute_mock_pipeline(
    job_id: UUID,
    pipeline_name: str,
    parameters: dict,
    min_duration: int = 10,
    max_duration: int = 30,
    success_rate: float = 0.8,
) -> None:
    """
    Execute a mock Snakemake pipeline with simulated processing time.

    Args:
        job_id: UUID of the job to execute
        pipeline_name: Name of the pipeline
        parameters: Pipeline parameters
        min_duration: Minimum execution time in seconds (default: 10)
        max_duration: Maximum execution time in seconds (default: 30)
        success_rate: Probability of successful execution (default: 0.8)
    """
    logger.info(f"Starting mock pipeline execution for job {job_id}: {pipeline_name}")

    # Update job status to RUNNING
    job_store.update(
        job_id=job_id,
        status=JobStatus.RUNNING,
        started_at=datetime.utcnow(),
    )
    logger.info(f"Job {job_id} status updated to RUNNING")

    try:
        # Simulate pipeline execution with random duration
        duration = random.uniform(min_duration, max_duration)
        logger.info(f"Job {job_id} will run for {duration:.2f} seconds")

        await asyncio.sleep(duration)

        # Randomly determine success or failure based on success_rate
        is_success = random.random() < success_rate

        if is_success:
            # Successful completion
            job_store.update(
                job_id=job_id,
                status=JobStatus.COMPLETED,
                completed_at=datetime.utcnow(),
            )
            logger.info(
                f"Job {job_id} completed successfully after {duration:.2f} seconds"
            )
        else:
            # Simulated failure
            error_messages = [
                "Pipeline step 'variant_calling' failed: insufficient memory",
                "Reference genome file not found",
                "Sample quality check failed: low coverage",
                "Workflow execution timeout",
                "Invalid parameter configuration",
            ]
            error_message = random.choice(error_messages)

            job_store.update(
                job_id=job_id,
                status=JobStatus.FAILED,
                completed_at=datetime.utcnow(),
                error_message=error_message,
            )
            logger.warning(
                f"Job {job_id} failed after {duration:.2f} seconds: {error_message}"
            )

    except Exception as e:
        # Handle unexpected errors
        error_message = f"Unexpected error during pipeline execution: {str(e)}"
        job_store.update(
            job_id=job_id,
            status=JobStatus.FAILED,
            completed_at=datetime.utcnow(),
            error_message=error_message,
        )
        logger.error(
            f"Job {job_id} encountered an error: {error_message}", exc_info=True
        )
