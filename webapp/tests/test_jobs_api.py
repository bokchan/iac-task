"""Unit tests for job management API endpoints."""

import uuid

import pytest
from fastapi.testclient import TestClient

from webapp.models import JobStatus
from webapp.storage import job_store


@pytest.fixture(autouse=True)
def clear_job_store():
    """Clear the job store before each test."""
    job_store._jobs.clear()
    yield
    job_store._jobs.clear()


class TestJobSubmission:
    """Tests for POST /jobs endpoint."""

    def test_submit_job_success(self, client: TestClient):
        """Test successful job submission."""
        payload = {
            "pipeline_name": "gatk_variant_calling",
            "parameters": {
                "sample_id": "WGS_001",
                "reference_genome": "hg38",
                "quality_threshold": 30,
            },
            "description": "GATK variant calling for sample WGS_001",
            "research_group": "genomics_lab",
        }

        response = client.post("/jobs", json=payload)

        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert data["status"] == JobStatus.PENDING.value
        assert data["pipeline_name"] == "gatk_variant_calling"
        assert data["parameters"]["sample_id"] == "WGS_001"
        assert data["parameters"]["reference_genome"] == "hg38"
        assert data["description"] == "GATK variant calling for sample WGS_001"
        assert data["research_group"] == "genomics_lab"
        assert "created_at" in data
        assert "updated_at" in data
        assert data["started_at"] is None
        assert data["completed_at"] is None
        assert data["error_message"] is None

        # Verify job is stored
        job_id = uuid.UUID(data["id"])
        stored_job = job_store.get(job_id)
        assert stored_job is not None
        assert stored_job.pipeline_name == "gatk_variant_calling"
        assert stored_job.research_group == "genomics_lab"

    def test_submit_job_minimal(self, client: TestClient):
        """Test job submission with minimal required fields."""
        payload = {
            "pipeline_name": "rnaseq_deseq2",
            "parameters": {
                "sample_id": "RNA_001",
                "reference": "gencode_v38",
            },
        }

        response = client.post("/jobs", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["pipeline_name"] == "rnaseq_deseq2"
        assert data["parameters"]["sample_id"] == "RNA_001"
        assert data["description"] is None

    def test_submit_job_missing_pipeline_name(self, client: TestClient):
        """Test job submission fails without pipeline_name."""
        payload = {
            "parameters": {"sample_id": "S001"},
        }

        response = client.post("/jobs", json=payload)

        assert response.status_code == 422  # Validation error

    def test_submit_multiple_jobs(self, client: TestClient):
        """Test submitting multiple jobs."""
        pipelines = [
            (
                "gatk_variant_calling",
                {"sample_id": "WGS_001", "reference_genome": "hg38"},
            ),
            ("rnaseq_deseq2", {"sample_id": "RNA_001", "reference": "gencode_v38"}),
        ]

        for pipeline_name, params in pipelines:
            payload = {
                "pipeline_name": pipeline_name,
                "parameters": params,
            }
            response = client.post("/jobs", json=payload)
            assert response.status_code == 201

        # Verify all jobs stored
        assert job_store.count() == 2


class TestGetJob:
    """Tests for GET /jobs/{job_id} endpoint."""

    def test_get_job_success(self, client: TestClient):
        """Test retrieving an existing job."""
        # First, create a job
        payload = {
            "pipeline_name": "gatk_variant_calling",
            "parameters": {"sample_id": "WGS_001", "reference_genome": "hg38"},
        }
        create_response = client.post("/jobs", json=payload)
        job_id = create_response.json()["id"]

        # Get the job (may complete quickly with mocked fast duration)
        response = client.get(f"/jobs/{job_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == job_id
        assert data["pipeline_name"] == "gatk_variant_calling"
        # With fast execution, job may already be completed
        assert data["status"] in [
            JobStatus.PENDING.value,
            JobStatus.RUNNING.value,
            JobStatus.COMPLETED.value,
            JobStatus.FAILED.value,
        ]

    def test_get_job_not_found(self, client: TestClient):
        """Test getting a non-existent job returns 404."""
        random_uuid = str(uuid.uuid4())
        response = client.get(f"/jobs/{random_uuid}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_job_invalid_uuid(self, client: TestClient):
        """Test getting a job with invalid UUID format."""
        response = client.get("/jobs/not-a-uuid")

        assert response.status_code == 422  # Validation error


class TestListJobs:
    """Tests for GET /jobs endpoint."""

    def test_list_jobs_empty(self, client: TestClient):
        """Test listing jobs when none exist."""
        response = client.get("/jobs")

        assert response.status_code == 200
        data = response.json()
        assert data["jobs"] == []
        assert data["total"] == 0

    def test_list_jobs_with_data(self, client: TestClient):
        """Test listing multiple jobs."""
        # Create several jobs
        job_ids = []
        pipelines = [
            (
                "gatk_variant_calling",
                {"sample_id": "WGS_001", "reference_genome": "hg38"},
            ),
            ("rnaseq_deseq2", {"sample_id": "RNA_001", "reference": "gencode_v38"}),
        ]

        for pipeline_name, params in pipelines:
            payload = {
                "pipeline_name": pipeline_name,
                "parameters": params,
            }
            response = client.post("/jobs", json=payload)
            job_ids.append(response.json()["id"])

        # List all jobs
        response = client.get("/jobs")

        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) == 2
        assert data["total"] == 2

        # Verify jobs are sorted by created_at (newest first)
        job_ids_in_response = [job["id"] for job in data["jobs"]]
        assert job_ids_in_response == list(reversed(job_ids))

    def test_list_jobs_returns_all_fields(self, client: TestClient):
        """Test that list returns complete job information."""
        payload = {
            "pipeline_name": "rnaseq_deseq2",
            "parameters": {"sample_id": "RNA_001", "reference": "gencode_v38"},
            "description": "Full test job",
        }
        client.post("/jobs", json=payload)

        response = client.get("/jobs")
        jobs = response.json()["jobs"]

        assert len(jobs) == 1
        job = jobs[0]
        assert "id" in job
        assert "status" in job
        assert "pipeline_name" in job
        assert "parameters" in job
        assert "description" in job
        assert "created_at" in job
        assert "updated_at" in job


class TestJobStorageIntegration:
    """Tests for job storage integration."""

    def test_job_persists_in_storage(self, client: TestClient):
        """Test that submitted job persists in storage."""
        payload = {
            "pipeline_name": "gatk_variant_calling",
            "parameters": {"sample_id": "WGS_001", "reference_genome": "hg38"},
        }

        response = client.post("/jobs", json=payload)
        job_id = uuid.UUID(response.json()["id"])

        # Verify direct access to storage (may complete quickly with mocked fast duration)
        stored_job = job_store.get(job_id)
        assert stored_job is not None
        assert stored_job.pipeline_name == "gatk_variant_calling"
        # With fast execution, job may already be completed
        assert stored_job.status in [
            JobStatus.PENDING,
            JobStatus.RUNNING,
            JobStatus.COMPLETED,
            JobStatus.FAILED,
        ]

    def test_concurrent_job_submissions(self, client: TestClient):
        """Test thread-safety with multiple job submissions."""
        import concurrent.futures

        pipelines = [
            "gatk_variant_calling",
            "rnaseq_deseq2",
        ]

        def submit_job(index: int):
            pipeline = pipelines[index % len(pipelines)]
            if pipeline == "gatk_variant_calling":
                params = {"sample_id": f"WGS_{index:03d}", "reference_genome": "hg38"}
            else:  # rnaseq_deseq2
                params = {"sample_id": f"RNA_{index:03d}", "reference": "gencode_v38"}

            payload = {
                "pipeline_name": pipeline,
                "parameters": params,
            }
            response = client.post("/jobs", json=payload)
            return response.status_code

        # Submit 10 jobs concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(submit_job, i) for i in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All should succeed
        assert all(status == 201 for status in results)
        assert job_store.count() == 10


class TestExistingEndpoints:
    """Tests for existing endpoints to ensure they still work."""

    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint still works."""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()

    def test_health_endpoint(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == "OK"

    def test_version_endpoint(self, client: TestClient):
        """Test version endpoint."""
        response = client.get("/version")
        assert response.status_code == 200
        assert "version" in response.json()
