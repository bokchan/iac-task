"""Unit tests for pipeline execution and background tasks."""

import time
import uuid
from unittest.mock import AsyncMock, patch

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
MOCK_MAX_DURATION = 0.5


@pytest.fixture
def mock_pipeline_durations(monkeypatch):
    """Mock pipeline execution to use fast durations for testing."""
    original_execute = execute_mock_pipeline.__wrapped__ if hasattr(execute_mock_pipeline, '__wrapped__') else execute_mock_pipeline

    async def fast_execute(job_id, pipeline_name, parameters, min_duration=None, max_duration=None, success_rate=0.8):
        # Override durations with fast values
        return await original_execute(
            job_id=job_id,
            pipeline_name=pipeline_name,
            parameters=parameters,
            min_duration=MOCK_MIN_DURATION,
            max_duration=MOCK_MAX_DURATION,
            success_rate=success_rate,
        )

    monkeypatch.setattr('webapp.main.execute_mock_pipeline', fast_execute)
    monkeypatch.setattr('webapp.pipeline.execute_mock_pipeline', fast_execute)
    return fast_execute


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

        # Wait for background task to complete (with mocked fast duration)
        time.sleep(1.0)  # Max wait for MOCK_MAX_DURATION + buffer

        # Check job status - should have completed or failed (not pending)
        updated_job = job_store.get(uuid.UUID(job_id))
        assert updated_job.status in [JobStatus.COMPLETED, JobStatus.FAILED]

        # Verify timestamps are set
        assert updated_job.started_at is not None
        assert updated_job.completed_at is not None

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

        # Wait for all jobs to process with fast durations
        time.sleep(1.0)

        # Check that jobs have been processed
        statuses = [job_store.get(uuid.UUID(jid)).status for jid in job_ids]

        # All jobs should have completed (COMPLETED or FAILED)
        assert all(status in [JobStatus.COMPLETED, JobStatus.FAILED] for status in statuses)

    def test_job_lifecycle_through_api(self, client: TestClient):
        """Test complete job lifecycle through API endpoints with fast execution."""
        # 1. Submit job
        payload = {
            "pipeline_name": "lifecycle_test",
            "parameters": {"stage": "submit"},
        }
        submit_response = client.post("/jobs", json=payload)
        assert submit_response.status_code == 201
        job_id = submit_response.json()["id"]

        # 2. Wait for processing (background task with fast duration)
        time.sleep(1.0)  # Max wait time for MOCK_MAX_DURATION + buffer

        # 3. Check updated status (should be completed or failed)
        get_response = client.get(f"/jobs/{job_id}")
        final_status = get_response.json()["status"]
        assert final_status in [
            JobStatus.COMPLETED.value,
            JobStatus.FAILED.value,
        ]

        # 4. Job should appear in list
        list_response = client.get("/jobs")
        assert list_response.status_code == 200
        job_ids = [job["id"] for job in list_response.json()["jobs"]]
        assert job_id in job_ids

        # 5. Verify timestamps are set
        job_data = get_response.json()
        assert job_data["created_at"] is not None
        assert job_data["updated_at"] is not None
        assert job_data["started_at"] is not None
        assert job_data["completed_at"] is not None
