"""Unit tests for pipeline execution and background tasks."""

import asyncio
import time
import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from webapp.models import JobStatus
from webapp.pipeline import execute_mock_pipeline
from webapp.storage import job_store


@pytest.fixture(autouse=True)
def clear_job_store():
    """Clear the job store before each test."""
    job_store._jobs.clear()
    yield
    job_store._jobs.clear()


# Mock pipeline duration for fast tests
MOCK_MIN_DURATION = 0.1
MOCK_MAX_DURATION = 1.0


class TestMockPipeline:
    """Tests for mock pipeline execution."""

    @pytest.mark.asyncio
    async def test_pipeline_successful_execution(self):
        """Test successful pipeline execution."""
        # Create a job
        job_id = uuid.uuid4()
        from webapp.models import JobResponse
        from datetime import datetime

        job = JobResponse(
            id=job_id,
            status=JobStatus.PENDING,
            pipeline_name="test_pipeline",
            parameters={"test": "data"},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        job_store.create(job)

        # Execute pipeline with guaranteed success
        await execute_mock_pipeline(
            job_id=job_id,
            pipeline_name="test_pipeline",
            parameters={"test": "data"},
            min_duration=0.1,
            max_duration=0.2,
            success_rate=1.0,  # 100% success
        )

        # Verify job status updated to COMPLETED
        updated_job = job_store.get(job_id)
        assert updated_job.status == JobStatus.COMPLETED
        assert updated_job.started_at is not None
        assert updated_job.completed_at is not None
        assert updated_job.error_message is None

    @pytest.mark.asyncio
    async def test_pipeline_failure_execution(self):
        """Test failed pipeline execution."""
        # Create a job
        job_id = uuid.uuid4()
        from webapp.models import JobResponse
        from datetime import datetime

        job = JobResponse(
            id=job_id,
            status=JobStatus.PENDING,
            pipeline_name="failing_pipeline",
            parameters={"fail": True},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        job_store.create(job)

        # Execute pipeline with guaranteed failure
        await execute_mock_pipeline(
            job_id=job_id,
            pipeline_name="failing_pipeline",
            parameters={"fail": True},
            min_duration=0.1,
            max_duration=0.2,
            success_rate=0.0,  # 0% success (guaranteed failure)
        )

        # Verify job status updated to FAILED
        updated_job = job_store.get(job_id)
        assert updated_job.status == JobStatus.FAILED
        assert updated_job.started_at is not None
        assert updated_job.completed_at is not None
        assert updated_job.error_message is not None
        assert len(updated_job.error_message) > 0

    @pytest.mark.asyncio
    async def test_pipeline_updates_running_status(self):
        """Test that pipeline updates status to RUNNING immediately."""
        # Create a job
        job_id = uuid.uuid4()
        from webapp.models import JobResponse
        from datetime import datetime

        job = JobResponse(
            id=job_id,
            status=JobStatus.PENDING,
            pipeline_name="test_pipeline",
            parameters={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        job_store.create(job)

        # Start pipeline execution but don't await completion
        task = asyncio.create_task(
            execute_mock_pipeline(
                job_id=job_id,
                pipeline_name="test_pipeline",
                parameters={},
                min_duration=1.0,
                max_duration=1.0,
                success_rate=1.0,
            )
        )

        # Give it a moment to update to RUNNING
        await asyncio.sleep(0.1)

        # Verify status changed to RUNNING
        running_job = job_store.get(job_id)
        assert running_job.status == JobStatus.RUNNING
        assert running_job.started_at is not None

        # Wait for completion
        await task

        # Verify final status
        completed_job = job_store.get(job_id)
        assert completed_job.status == JobStatus.COMPLETED


class TestBackgroundTaskIntegration:
    """Tests for background task integration with API endpoints."""

    def test_job_submission_triggers_background_task(self, client: TestClient):
        """Test that job submission triggers background task execution."""
        payload = {
            "pipeline_name": "background_test",
            "parameters": {"test": "background"},
        }

        # Submit job
        response = client.post("/jobs", json=payload)
        assert response.status_code == 201

        job_id = response.json()["id"]

        # Job should initially be PENDING
        job = job_store.get(uuid.UUID(job_id))
        assert job.status == JobStatus.PENDING

        # Wait for background task to start (give it time to update to RUNNING or complete)
        time.sleep(1)

        # Check job status again - should have progressed
        updated_job = job_store.get(uuid.UUID(job_id))
        assert updated_job.status in [JobStatus.RUNNING, JobStatus.COMPLETED, JobStatus.FAILED]

    def test_multiple_concurrent_background_tasks(self, client: TestClient):
        """Test multiple jobs can be processed concurrently."""
        job_ids = []

        # Submit multiple jobs
        for i in range(3):
            payload = {
                "pipeline_name": f"concurrent_pipeline_{i}",
                "parameters": {"index": i},
            }
            response = client.post("/jobs", json=payload)
            job_ids.append(response.json()["id"])

        # All jobs should be submitted successfully
        assert len(job_ids) == 3

        # Give background tasks time to start
        time.sleep(1)

        # Check that jobs are being processed
        statuses = [job_store.get(uuid.UUID(jid)).status for jid in job_ids]

        # At least some jobs should have progressed beyond PENDING
        assert any(status != JobStatus.PENDING for status in statuses)

    def test_job_lifecycle_through_api(self, client: TestClient):
        """Test complete job lifecycle through API endpoints."""
        # 1. Submit job
        payload = {
            "pipeline_name": "lifecycle_test",
            "parameters": {"stage": "submit"},
        }
        submit_response = client.post("/jobs", json=payload)
        assert submit_response.status_code == 201
        job_id = submit_response.json()["id"]

        # 2. Check initial status (PENDING)
        get_response = client.get(f"/jobs/{job_id}")
        assert get_response.status_code == 200
        assert get_response.json()["status"] == JobStatus.PENDING.value

        # 3. Wait for processing
        time.sleep(0.5)

        # 4. Check updated status (RUNNING or completed)
        get_response = client.get(f"/jobs/{job_id}")
        status = get_response.json()["status"]
        assert status in [
            JobStatus.RUNNING.value,
            JobStatus.COMPLETED.value,
            JobStatus.FAILED.value,
        ]

        # 5. Job should appear in list
        list_response = client.get("/jobs")
        assert list_response.status_code == 200
        job_ids = [job["id"] for job in list_response.json()["jobs"]]
        assert job_id in job_ids
