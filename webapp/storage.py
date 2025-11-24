"""Thread-safe in-memory job storage."""

import threading
from datetime import datetime, timezone
from uuid import UUID

from .models import JobResponse, JobStatus


class JobStore:
    """Thread-safe in-memory storage for job data."""

    def __init__(self):
        """Initialize the job store with an empty dictionary and lock."""
        self._jobs: dict[UUID, JobResponse] = {}
        self._lock = threading.Lock()

    def create(self, job: JobResponse) -> JobResponse:
        """
        Create a new job in the store.

        Args:
            job: JobResponse object to store

        Returns:
            The stored JobResponse object
        """
        with self._lock:
            self._jobs[job.id] = job
            return job

    def get(self, job_id: UUID) -> JobResponse | None:
        """
        Retrieve a job by ID.

        Args:
            job_id: UUID of the job to retrieve

        Returns:
            JobResponse if found, None otherwise
        """
        with self._lock:
            return self._jobs.get(job_id)

    def update(
        self,
        job_id: UUID,
        status: JobStatus | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        error_message: str | None = None,
    ) -> JobResponse | None:
        """
        Update job status and timestamps.

        Args:
            job_id: UUID of the job to update
            status: New job status
            started_at: Job start timestamp
            completed_at: Job completion timestamp
            error_message: Error message if job failed

        Returns:
            Updated JobResponse if found, None otherwise
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None

            # Update fields if provided
            if status is not None:
                job.status = status
            if started_at is not None:
                job.started_at = started_at
            if completed_at is not None:
                job.completed_at = completed_at
            if error_message is not None:
                job.error_message = error_message

            # Always update the updated_at timestamp
            job.updated_at = datetime.now(tz=timezone.utc)

            return job

    def list_all(self) -> list[JobResponse]:
        """
        List all jobs in the store.

        Returns:
            List of all JobResponse objects, sorted by creation time (newest first)
        """
        with self._lock:
            return sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)

    def count(self) -> int:
        """
        Get the total number of jobs in the store.

        Returns:
            Total number of jobs
        """
        with self._lock:
            return len(self._jobs)


# Global singleton instance
job_store = JobStore()
