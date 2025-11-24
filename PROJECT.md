# Pipeline Orchestration Service

## Overview

A FastAPI-based REST API service for submitting and tracking bioinformatics pipeline jobs. This proof-of-concept implementation demonstrates a lightweight job orchestration system with in-memory storage and background task processing, designed for multi-research-group computational biology environments.

## Bioinformatics Applications

### Multi-Research-Group Data Processing

This architecture addresses common challenges in bioinformatics core facilities and computational biology departments:

#### Use Case 1: Variant Calling Pipeline Coordination

**Challenge**: Multiple research groups submit WGS/WES samples for variant calling, requiring standardized processing and transparent status tracking.

**Solution**:

- Standardized REST API ensures consistent job submission format across labs
- Research group tagging enables job tracking and organization
- Background processing handles long-running GATK workflows
- Real-time job status provides transparency across research groups
- Pydantic validation ensures data quality (reference genome versions, quality thresholds)

**Example Job Submission**:

```json
{
  "pipeline_name": "gatk_variant_calling",
  "parameters": {
    "sample_id": "WGS_001",
    "reference_genome": "hg38",
    "fastq_r1": "s3://input-data/WGS_001_R1.fastq.gz",
    "fastq_r2": "s3://input-data/WGS_001_R2.fastq.gz",
    "caller": "HaplotypeCaller",
    "quality_threshold": 30,
    "depth_threshold": 10
  },
  "research_group": "cancer_genomics_lab",
  "description": "Variant calling for tumor sample WGS_001"
}
```

#### Use Case 2: RNA-Seq Analysis Job Tracking

**Challenge**: Research groups submit RNA-seq samples requiring standardized processing and status visibility.

**Solution**:

- REST API provides consistent interface for RNA-seq job submission
- Background processing handles analysis workflows
- Status tracking shows job lifecycle (PENDING → RUNNING → COMPLETED/FAILED)
- Research group tagging enables job organization
- Pydantic validation ensures correct parameters and file paths

**Example Job Submission**:

```json
{
  "pipeline_name": "rnaseq_deseq2",
  "parameters": {
    "sample_id": "RNA_001",
    "reference": "gencode_v38",
    "fastq_files": ["s3://data/RNA_001.fastq.gz"],
    "adapter_sequence": "AGATCGGAAGAGC",
    "min_quality": 20,
    "quantification_method": "salmon"
  },
  "research_group": "systems_biology_lab",
  "description": "RNA-seq analysis for sample RNA_001"
}
```

**Benefits of Current Implementation**:

- **Transparency**: Research groups can track job status in real-time via API
- **Standardization**: Consistent REST API for all pipeline submissions
- **Validation**: Pydantic models ensure parameter correctness and data quality
- **Reproducibility**: Complete job parameters logged with timestamps
- **Flexibility**: Easy integration with external tools via REST API

### Current Implementation (Proof of Concept)

This is a **demonstration/PoC** system with mock pipeline execution. The architecture is designed to be extensible for future integration with workflow engines, but currently uses simulated execution.

**What's Implemented:**
- FastAPI REST API for job submission and tracking
- Mock pipeline execution (Python sleep with configurable duration)
- In-memory job storage with thread safety
- Pydantic validation for pipeline parameters

**Future Integration Possibilities:**
The abstraction layer in `orchestrator.py` is designed to support integration with:
- **Prefect**: Native Python orchestration
- **Snakemake**: Python-based bioinformatics workflows
- **Nextflow**: Production genomics pipelines (nf-core)
- **Dagster**: Data pipeline orchestration
- **Airflow**: Workflow scheduling

> **Note**: Currently all jobs use mock execution. See `webapp/orchestrator.py` where `ORCHESTRATOR_BACKEND = "mock"`.

## Features

- **REST API**: Submit, track, and list pipeline execution jobs
- **Background Processing**: Asynchronous job execution using FastAPI BackgroundTasks
- **Thread-Safe Storage**: Concurrent-safe in-memory job management
- **Mock Pipeline Execution**: Simulated pipeline runs with configurable duration (10-30s)
- **Parameter Validation**: Pydantic models for GATK and RNA-seq pipeline parameters
- **Comprehensive Testing**: Full test coverage with 23 automated tests
- **OpenAPI Documentation**: Auto-generated interactive API documentation
- **Extensible Architecture**: Abstraction layer ready for real orchestrator integration

## Architecture

### System Components

```
┌─────────────────┐
│   REST API      │  FastAPI application with job endpoints
│   (main.py)     │  - POST /jobs: Submit new job
└────────┬────────┘  - GET /jobs/{id}: Check status
         │           - GET /jobs: List all jobs
         ↓
┌─────────────────┐
│  Job Storage    │  Thread-safe in-memory store
│  (storage.py)   │  - JobStore with threading.Lock
└────────┬────────┘  - CRUD operations on job data
         │
         ↓
┌─────────────────┐
│ Mock Pipeline   │  Simulated execution
│ (pipeline.py)   │  - Random duration (10-30s)
└─────────────────┘  - 80% success rate
                     - Job status updates
```

> **Note**: The `orchestrator.py` module provides an abstraction layer for future integration with real workflow engines (Prefect, Dagster, Airflow), but currently routes all jobs to mock execution.

### Technology Stack

| Component            | Technology              | Purpose                              |
| -------------------- | ----------------------- | ------------------------------------ |
| **Web Framework**    | FastAPI                 | REST API with automatic OpenAPI docs |
| **Storage**          | In-memory dictionary    | Thread-safe job data persistence     |
| **Task Queue**       | FastAPI BackgroundTasks | Asynchronous job processing          |
| **Data Validation**  | Pydantic                | Request/response models              |
| **Testing**          | pytest                  | Automated test suite                 |
| **Containerization** | Docker                  | Multi-stage build for deployment     |

### File Structure

```
webapp/
├── main.py                   # FastAPI application and endpoints
├── models.py                 # Job management Pydantic models
├── pipeline_models.py        # Pipeline parameter models with validators
├── validators.py             # Pipeline registry and utility functions
├── storage.py                # Thread-safe in-memory storage
├── orchestrator.py           # Orchestration abstraction layer
├── run.py                    # Application entry point
├── pyproject.toml            # Dependencies and configuration
├── Dockerfile                # Container image definition
└── tests/                    # Test suite (23 tests)
    ├── conftest.py           # Test fixtures
    ├── test_app.py           # Application endpoint tests
    ├── test_jobs_api.py      # Job management tests
    └── test_pipeline.py      # Background task tests
```

## Data Models

### JobStatus (Enum)

```python
PENDING    # Job created, awaiting execution
RUNNING    # Job currently executing
COMPLETED  # Job finished successfully
FAILED     # Job finished with errors
```

### JobSubmission (Request)

```python
pipeline_name: PipelineName                                    # Pipeline to execute (enum)
parameters: GATKVariantCallingParams | RNASeqDESeq2Params     # Typed pipeline parameters
description: str | None                                        # Optional job description
research_group: str | None                                     # Research group identifier
```

**Validation**: Model validator ensures pipeline_name matches parameter type.

### JobResponse (Response)

```python
id: UUID                                                       # Unique job identifier
status: JobStatus                                              # Current execution status
pipeline_name: PipelineName                                    # Pipeline name (enum)
parameters: GATKVariantCallingParams | RNASeqDESeq2Params     # Typed pipeline parameters
description: str | None                                        # Job description
research_group: str | None                                     # Research group identifier
created_at: datetime                                           # Creation timestamp
updated_at: datetime                                           # Last update timestamp
started_at: datetime | None                                    # Execution start time
completed_at: datetime | None                                  # Execution completion time
error_message: str | None                                      # Error details if failed
```

### JobList (Response)

```python
jobs: List[JobResponse]         # Array of job objects
total: int                      # Total number of jobs
```

## API Endpoints

### Job Management

| Method | Endpoint     | Description             | Status Codes                      |
| ------ | ------------ | ----------------------- | --------------------------------- |
| POST   | `/jobs`      | Submit new pipeline job | 201 Created, 422 Validation Error |
| GET    | `/jobs/{id}` | Get job status by UUID  | 200 OK, 404 Not Found             |
| GET    | `/jobs`      | List all jobs           | 200 OK                            |

### System Endpoints

| Method | Endpoint   | Description                             |
| ------ | ---------- | --------------------------------------- |
| GET    | `/`        | Echo message (configurable)             |
| GET    | `/health`  | Health check for monitoring             |
| GET    | `/version` | Application version                     |
| GET    | `/docs`    | Interactive API documentation (Swagger) |
| GET    | `/redoc`   | Alternative API documentation           |

## Storage Implementation

### JobStore Class

Thread-safe in-memory storage using Python dictionary with `threading.Lock`:

```python
class JobStore:
    def __init__(self):
        self._jobs: dict[UUID, JobResponse] = {}
        self._lock = threading.Lock()

    def create(self, job: JobResponse) -> JobResponse
    def get(self, job_id: UUID) -> Optional[JobResponse]
    def update(self, job_id: UUID, **kwargs) -> Optional[JobResponse]
    def list_all(self) -> list[JobResponse]
    def count(self) -> int
```

**Characteristics:**

- ✅ Thread-safe concurrent access
- ✅ Fast read/write operations
- ✅ Zero external dependencies
- ⚠️ Data lost on restart (by design for PoC)
- ⚠️ Single-instance limitation

## Pipeline Execution

### Mock Pipeline Simulator

The `execute_mock_pipeline()` function simulates Snakemake pipeline execution:

**Configuration:**

- `min_duration`: Minimum execution time (default: 10s)
- `max_duration`: Maximum execution time (default: 30s)
- `success_rate`: Probability of success (default: 0.8)

**Behavior:**

1. Updates job status to `RUNNING`
2. Simulates execution with random duration
3. Randomly succeeds or fails based on success rate
4. Updates job status to `COMPLETED` or `FAILED`
5. Stores error messages on failure

**Example Error Messages:**

- "Pipeline step 'variant_calling' failed: insufficient memory"
- "Reference genome file not found"
- "Sample quality check failed: low coverage"
- "Workflow execution timeout"
- "Invalid parameter configuration"

## Job Lifecycle

```
1. Client submits job via POST /jobs
   ↓
2. Job created with status PENDING
   Job stored in-memory
   Background task scheduled
   ↓
3. Background worker picks up job
   Status updated to RUNNING
   ↓
4. Mock pipeline executes (10-30 seconds)
   ↓
5. Job completes:
   → Success: Status = COMPLETED
   → Failure: Status = FAILED (with error message)
   ↓
6. Client polls GET /jobs/{id} for status
```

## Testing

### Test Suite Overview

**23 comprehensive tests** organized in 3 files:

#### test_jobs_api.py (15 tests)

- Job submission (success, validation, concurrent)
- Job retrieval (by ID, not found, invalid UUID)
- Job listing (empty, populated, all fields)
- Storage integration and persistence
- Thread-safe concurrent operations

#### test_pipeline.py (3 tests)

- Background task execution
- Multiple concurrent background tasks
- Complete job lifecycle validation

#### test_app.py (5 tests)

- Root endpoint functionality
- Health check endpoint
- Version endpoint
- Environment variable configuration

### Test Performance

- **Execution time**: ~9 seconds (all 23 tests)
- **Optimization**: Mock pipeline durations set to 0.1-0.5s in tests
- **Coverage**: All endpoints, error cases, and concurrent scenarios

### Running Tests

```bash
# Install dependencies
uv sync --group dev

# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest webapp/tests/test_jobs_api.py
```

## Configuration

### Environment Variables

| Variable       | Default         | Description                              |
| -------------- | --------------- | ---------------------------------------- |
| `ECHO_MESSAGE` | `"Hello World"` | Message returned by root endpoint        |
| `LOG_LEVEL`    | `"INFO"`        | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `IMAGE_TAG`    | `"unknown"`     | Deployed image version                   |

### Pipeline Parameters

Configured in code (`pipeline.py`):

```python
min_duration: float = 10      # Minimum execution seconds
max_duration: float = 30      # Maximum execution seconds
success_rate: float = 0.8     # Success probability (0.0-1.0)
```

## Deployment

### Docker Container

Multi-stage build for optimal security and size:

**Build stage**: Installs dependencies using UV package manager
**Runtime stage**: Minimal Python 3.14 slim image with non-root user

```bash
# Build image
docker build -f webapp/Dockerfile -t webapp:latest ./webapp

# Run container
docker run -p 8000:8000 \
  -e LOG_LEVEL="INFO" \
  -e IMAGE_TAG="v1.0.0" \
  webapp:latest
```

### AWS ECS Deployment

Deployed via existing infrastructure:

- **Container**: ECS Fargate task
- **Load Balancer**: Application Load Balancer
- **Registry**: Amazon ECR
- **CI/CD**: GitHub Actions with OIDC authentication

See [infrastructure documentation](../infra/README.md) for deployment details.

## Limitations and Scope

### Current Implementation

This is a **proof-of-concept** implementation optimized for:

- ✅ Rapid development and demonstration
- ✅ Single-container deployments
- ✅ Development and testing environments
- ✅ Short-lived demo scenarios

### Known Limitations

1. **Storage**: In-memory only, data lost on restart
2. **Scalability**: Single-instance only (no load balancing of jobs)
3. **Persistence**: No database integration
4. **Authentication**: No auth/authorization implemented
5. **Pipeline**: Mock execution only, not real Snakemake integration

### Production Considerations

For production deployment, consider:

| Enhancement            | Effort     | Description                      |
| ---------------------- | ---------- | -------------------------------- |
| **Persistent Storage** | 3-4 hours  | Migrate to PostgreSQL/DynamoDB   |
| **Message Queue**      | 2-3 hours  | Add SQS/SNS for job distribution |
| **Separate Workers**   | 4-6 hours  | Dedicated worker service         |
| **Authentication**     | 4-6 hours  | JWT/OAuth2 implementation        |
| **Real Pipeline**      | 8-16 hours | Snakemake integration            |
| **Monitoring**         | 2-4 hours  | CloudWatch metrics/alarms        |

## Usage Examples

### Submit a GATK Variant Calling Job

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
      "quality_threshold": 30,
      "depth_threshold": 10
    },
    "research_group": "genomics_lab",
    "description": "WGS variant calling for patient sample"
  }'
```

**Response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "pipeline_name": "gatk_variant_calling",
  "research_group": "genomics_lab",
  "parameters": {
    "sample_id": "WGS_001",
    "reference_genome": "hg38",
    "caller": "HaplotypeCaller"
  },
  "created_at": "2025-11-24T10:00:00Z",
  "updated_at": "2025-11-24T10:00:00Z"
}
```

### Submit an RNA-seq Analysis Job

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_name": "rnaseq_deseq2",
    "parameters": {
      "sample_id": "RNA_001",
      "fastq_files": ["/data/RNA_001.fastq.gz"],
      "reference": "gencode_v38",
      "adapter_sequence": "AGATCGGAAGAGC",
      "min_quality": 20,
      "quantification_method": "salmon"
    },
    "research_group": "transcriptomics_lab",
    "description": "RNA-seq differential expression analysis"
  }'
```

### List Jobs with Filters

```bash
# List all jobs
curl http://localhost:8000/jobs

# Filter by research group
curl "http://localhost:8000/jobs?research_group=genomics_lab"

# Filter by status
curl "http://localhost:8000/jobs?status=completed"
```

### Check Job Status

```bash
curl http://localhost:8000/jobs/550e8400-e29b-41d4-a716-446655440000
```

**Response (Running):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "pipeline_name": "gatk_variant_calling",
  "research_group": "genomics_lab",
  "started_at": "2025-11-24T10:00:05Z",
  "created_at": "2025-11-24T10:00:00Z",
  "updated_at": "2025-11-24T10:00:05Z"
}
```

**Response (Completed):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "pipeline_name": "gatk_variant_calling",
  "research_group": "genomics_lab",
  "started_at": "2025-11-24T10:00:05Z",
  "completed_at": "2025-11-24T10:00:25Z",
  "created_at": "2025-11-24T10:00:00Z",
  "updated_at": "2025-11-24T10:00:25Z"
}
```

### List All Jobs

```bash
curl http://localhost:8000/jobs
```

**Response:**

```json
{
  "jobs": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      ...
    }
  ],
  "total": 1
}
```

## Development

### Local Setup

```bash
# Install UV package manager
pip install uv

# Install dependencies
uv sync

# Run development server
uv run uvicorn main:app --reload
```

Access application at http://localhost:8000

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Additional Resources

For project information, infrastructure details, and deployment instructions, see:

- [Root README](README.md) - Project overview
- [Infrastructure README](infra/README.md) - AWS deployment guide
- [Web App README](webapp/README.md) - Detailed application documentation
