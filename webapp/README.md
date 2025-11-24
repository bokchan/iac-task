# Pipeline Orchestration Service - Web Application

A FastAPI-based REST API service for submitting and tracking Snakemake pipeline jobs with background task processing and thread-safe storage.

> **Documentation**: See [PROJECT.md](../PROJECT.md) for detailed architecture and technical specifications.

## Quick Start

### Local Development

```bash
# Install dependencies (requires Python 3.14+)
pip install uv
uv sync

# Run development server
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Access at http://localhost:8000 • Docs at http://localhost:8000/docs

### Docker

```bash
# From project root
docker compose up --build
```

### Usage

**Submit a GATK variant calling job:**
```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_name": "gatk_variant_calling",
    "parameters": {
      "sample_id": "WGS_001",
      "fastq_r1": "/data/WGS_001_R1.fastq.gz",
      "fastq_r2": "/data/WGS_001_R2.fastq.gz",
      "reference_genome": "hg38",
      "caller": "HaplotypeCaller",
      "quality_threshold": 30
    },
    "research_group": "genomics_lab",
    "description": "Whole genome sequencing variant calling"
  }'
```

**Submit an RNA-seq analysis job:**
```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_name": "rnaseq_deseq2",
    "parameters": {
      "sample_id": "RNA_001",
      "fastq_files": ["/data/RNA_001.fastq.gz"],
      "reference": "gencode_v38",
      "quantification_method": "salmon",
      "min_quality": 20
    },
    "research_group": "transcriptomics_lab",
    "description": "RNA-seq differential expression analysis"
  }'
```

**Check job status:**
```bash
curl http://localhost:8000/jobs/{job-id}
```

**List all jobs (with research group filter):**
```bash
curl http://localhost:8000/jobs

# Filter by research group (if implemented):
curl "http://localhost:8000/jobs?research_group=genomics_lab"
```

## API Endpoints

### Job Management

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/jobs` | POST | Submit new pipeline job | `JobResponse` (201) |
| `/jobs/{id}` | GET | Get job status by UUID | `JobResponse` (200/404) |
| `/jobs` | GET | List all jobs | `JobList` (200) |

**Job Lifecycle**: `PENDING` → `RUNNING` → `COMPLETED`/`FAILED`

### System

| Endpoint | Description |
|----------|-------------|
| `/` | Echo message (configurable via `ECHO_MESSAGE`) |
| `/health` | Health check for load balancers |
| `/version` | Application version (from `IMAGE_TAG`) |
| `/docs` | Interactive API documentation (Swagger UI) |
| `/redoc` | Alternative API documentation |

## Data Models

### JobStatus
```python
PENDING    # Awaiting execution
RUNNING    # Currently executing
COMPLETED  # Finished successfully
FAILED     # Finished with errors
```

### JobSubmission (Request)
```python
pipeline_name: PipelineName                                    # Pipeline to execute (enum)
parameters: GATKVariantCallingParams | RNASeqDESeq2Params     # Typed pipeline parameters
description: str | None                                        # Optional description
research_group: str | None                                     # Research group identifier
```

### JobResponse (Response)
```python
id: UUID                                                       # Unique identifier
status: JobStatus                                              # Current status
pipeline_name: PipelineName                                    # Pipeline name (enum)
parameters: GATKVariantCallingParams | RNASeqDESeq2Params     # Typed pipeline parameters
description: str | None                                        # Job description
research_group: str | None                                     # Research group identifier
created_at: datetime                                           # Creation time
updated_at: datetime                                           # Last update
started_at: datetime | None                                    # Start time
completed_at: datetime | None                                  # Completion time
error_message: str | None                                      # Error details
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ECHO_MESSAGE` | `"Hello World"` | Root endpoint message |
| `LOG_LEVEL` | `"INFO"` | Logging level |
| `IMAGE_TAG` | `"unknown"` | Application version |

### Supported Pipelines

Two pipelines with Pydantic validation:

1. **GATK Variant Calling** (`PipelineName.GATK_VARIANT_CALLING`)
   - Parameters: `GATKVariantCallingParams`
   - Fields: sample_id, fastq_r1, fastq_r2, reference_genome, caller, quality_threshold, depth_threshold

2. **RNA-seq DESeq2** (`PipelineName.RNASEQ_DESEQ2`)
   - Parameters: `RNASeqDESeq2Params`
   - Fields: sample_id, fastq_files, reference, adapter_sequence, min_quality, quantification_method

### Pipeline Execution Configuration

In `pipeline.py`:
```python
min_duration: float = 10      # Min execution time (seconds)
max_duration: float = 30      # Max execution time (seconds)
success_rate: float = 0.8     # Success probability
```

> **Note**: Tests use 0.1-0.5s durations for fast execution.

## Testing

### Run Tests

```bash
# All tests
uv run pytest

# Verbose output
uv run pytest -v

# Specific file
uv run pytest webapp/tests/test_jobs_api.py
```

### Test Suite

**23 tests** covering:

- **test_jobs_api.py** (15 tests): Job submission, retrieval, listing, validation, concurrent operations
- **test_pipeline.py** (3 tests): Background tasks, lifecycle, concurrent execution
- **test_app.py** (5 tests): System endpoints, configuration

**Performance**: ~9 seconds total execution time

## Architecture

### Components

**main.py**: FastAPI application with REST endpoints
**models.py**: Pydantic data models for job management (JobSubmission, JobResponse, JobStatus)
**pipeline_models.py**: Pydantic models for pipeline parameters with field validators
**validators.py**: Pipeline registry and utility functions
**storage.py**: Thread-safe in-memory job storage (`JobStore`)
**orchestrator.py**: Abstraction layer over orchestration engines (Prefect/Dagster)
**prefect_integration.py**: Example Prefect workflows
**pipeline.py**: Mock pipeline execution simulator

### Storage

Thread-safe in-memory dictionary with `threading.Lock`:

```python
class JobStore:
    def create(self, job: JobResponse) -> JobResponse
    def get(self, job_id: UUID) -> Optional[JobResponse]
    def update(self, job_id: UUID, **kwargs) -> Optional[JobResponse]
    def list_all(self) -> list[JobResponse]
    def count(self) -> int
```

**Characteristics**:
- ✅ Thread-safe concurrent access
- ✅ Fast operations
- ⚠️ Data lost on restart (by design)
- ⚠️ Single-instance only

### Background Processing

Uses FastAPI `BackgroundTasks` for async job execution:

1. POST /jobs creates job with `PENDING` status
2. Background task scheduled
3. Task updates status to `RUNNING`
4. Mock pipeline executes (10-30 seconds)
5. Status updated to `COMPLETED` or `FAILED`

## Docker

### Build

```bash
docker build -f webapp/Dockerfile -t webapp:latest ./webapp
```

### Run

```bash
docker run -p 8000:8000 \
  -e LOG_LEVEL="INFO" \
  -e IMAGE_TAG="v1.0.0" \
  webapp:latest
```

### Image Details

**Multi-stage build**:
- **Build stage**: UV package manager, dependency installation
- **Runtime stage**: Minimal Python 3.14 slim, non-root user

**Security features**:
- 🔒 Non-root execution
- 🧹 Minimal dependencies
- 📦 Optimized image size

## Project Structure

```
webapp/
├── main.py                   # FastAPI app + endpoints
├── models.py                 # Job management Pydantic models
├── pipeline_models.py        # Pipeline parameter models (GATK, RNASeq)
├── validators.py             # Pipeline registry and utilities
├── storage.py                # JobStore implementation
├── orchestrator.py           # Orchestration abstraction layer
├── prefect_integration.py    # Example Prefect workflows
├── pipeline.py               # Mock pipeline execution
├── run.py                    # Entry point
├── pyproject.toml            # Dependencies
├── Dockerfile                # Container image
└── tests/                    # Test suite (23 tests)
    ├── conftest.py           # Fixtures
    ├── test_app.py           # System endpoints (5)
    ├── test_jobs_api.py      # Job management (15)
    └── test_pipeline.py      # Background tasks (3)
```

## Limitations

This is a **proof-of-concept** implementation:

### Known Limitations

1. **Storage**: In-memory only, data lost on restart
2. **Scalability**: Single-instance, no distributed job processing
3. **Persistence**: No database integration
4. **Authentication**: Not implemented
5. **Pipeline**: Mock only, not real Snakemake

### Production Considerations

For production deployment:

- **Persistent storage**: PostgreSQL/DynamoDB (3-4 hours)
- **Message queue**: SQS/SNS for job distribution (2-3 hours)
- **Separate workers**: Dedicated worker service (4-6 hours)
- **Authentication**: JWT/OAuth2 (4-6 hours)
- **Real pipeline**: Snakemake integration (8-16 hours)
- **Monitoring**: CloudWatch metrics/alarms (2-4 hours)

## Deployment

### AWS ECS

Deployed via existing infrastructure:
- **Container**: ECS Fargate
- **Load Balancer**: ALB
- **Registry**: ECR
- **CI/CD**: GitHub Actions

See [infrastructure documentation](../infra/README.md) for details.

## API Examples

### Example Request

```json
POST /jobs

{
  "pipeline_name": "variant_calling",
  "parameters": {
    "sample_id": "S001",
    "genome": "hg38"
  },
  "description": "Run variant calling on sample S001"
}
```

### Example Response

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "pipeline_name": "variant_calling",
  "parameters": {
    "sample_id": "S001",
    "genome": "hg38"
  },
  "description": "Run variant calling on sample S001",
  "created_at": "2025-11-24T10:00:00Z",
  "updated_at": "2025-11-24T10:00:00Z",
  "started_at": null,
  "completed_at": null,
  "error_message": null
}
```

### Status Check Response

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "pipeline_name": "variant_calling",
  "started_at": "2025-11-24T10:00:05Z",
  "completed_at": "2025-11-24T10:00:25Z",
  ...
}
```

### List Response

```json
{
  "jobs": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "pipeline_name": "variant_calling",
      ...
    }
  ],
  "total": 1
}
```

## Interactive Documentation

Once running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Additional Resources

- **[PROJECT.md](../PROJECT.md)**: Detailed technical documentation
- **[Root README](../README.md)**: Project overview
- **[Infrastructure README](../infra/README.md)**: AWS deployment guide
