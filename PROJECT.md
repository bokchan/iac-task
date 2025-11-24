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
- Research group tracking enables quota management and billing allocation
- Background processing handles long-running GATK/FreeBayes/DeepVariant workflows
- Real-time job status provides transparency across research groups
- Job parameters validation ensures data quality (reference genome versions, quality thresholds)

**Example Job Submission**:
```json
{
  "pipeline_name": "gatk_variant_calling",
  "parameters": {
    "sample_id": "WGS_001",
    "reference_genome": "hg38",
    "bam_file": "s3://input-data/WGS_001.bam",
    "quality_threshold": 30,
    "caller": "HaplotypeCaller"
  },
  "research_group": "cancer_genomics_lab",
  "description": "Variant calling for tumor sample WGS_001"
}
```

#### Use Case 2: RNA-Seq Analysis Queue Management

**Challenge**: Research groups submit RNA-seq samples with varying experimental designs, requiring resource coordination and preventing computational bottlenecks.

**Solution**:
- Queue management prevents resource contention on shared HPC clusters
- Job prioritization based on research group quotas and deadlines
- Status tracking shows pipeline progress (QC → Alignment → Quantification → DE Analysis)
- Automatic notifications when analysis completes
- Integration with downstream visualization tools (IGV, R/Bioconductor)

**Example Job Submission**:
```json
{
  "pipeline_name": "rnaseq_deseq2",
  "parameters": {
    "sample_ids": ["CTRL_1", "CTRL_2", "TREAT_1", "TREAT_2"],
    "reference_genome": "hg38",
    "annotation": "gencode_v38",
    "contrasts": ["TREAT_vs_CTRL"],
    "normalization": "rlog"
  },
  "research_group": "systems_biology_lab",
  "description": "Differential expression analysis - drug treatment study"
}
```

#### Use Case 3: Cross-Lab Data Integration and ETL

**Challenge**: Consolidating sequencing data from multiple research groups with different LIMS systems and data formats.

**Solution**:
- Standardized job metadata enables data consolidation across diverse sources
- Research group tracking for compliance, billing, and audit trails
- API-first design integrates with existing LIMS systems (Benchling, LabKey, OpenSpecimen)
- Pydantic validation ensures data quality and schema consistency
- Job history provides reproducibility and provenance tracking

**Benefits for Core Facilities**:
- **Transparency**: Research groups see pipeline status in real-time
- **Accountability**: Track resource usage per lab for billing/chargeback
- **Reproducibility**: Complete job parameters logged for publication/validation
- **Integration**: REST API connects to sequencers, LIMS, analysis platforms
- **Scalability**: Queue management handles burst workloads during grant deadlines

### Pipeline Integration

Compatible with standard bioinformatics workflow engines:

| Workflow Engine | Integration Method | Use Case |
|----------------|-------------------|----------|
| **Snakemake** | Direct execution via subprocess | Python-based workflows, conda environments |
| **Nextflow** | REST API to Seqera Platform | Production genomics pipelines (nf-core) |
| **Prefect** | Native Python orchestration | Complex ETL, data validation, notifications |
| **CWL** | cwltool execution | Portable, standardized workflows |

**Recommended Architecture**:
```
Research Groups → FastAPI (this service) → Prefect → Snakemake/Nextflow → Results
                      ↓                        ↓
                  Job Tracking           Workflow DAG Management
```

## Features

- **REST API**: Submit, track, and list pipeline execution jobs
- **Background Processing**: Asynchronous job execution using FastAPI BackgroundTasks
- **Thread-Safe Storage**: Concurrent-safe in-memory job management
- **Mock Pipeline Execution**: Configurable simulation of Snakemake pipeline runs
- **Comprehensive Testing**: Full test coverage with 23 automated tests
- **OpenAPI Documentation**: Auto-generated interactive API documentation

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
│ Background      │  Async task execution
│ Tasks           │  - Job lifecycle management
│ (pipeline.py)   │  - Status updates
└─────────────────┘  - Error handling
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Web Framework** | FastAPI | REST API with automatic OpenAPI docs |
| **Storage** | In-memory dictionary | Thread-safe job data persistence |
| **Task Queue** | FastAPI BackgroundTasks | Asynchronous job processing |
| **Data Validation** | Pydantic | Request/response models |
| **Testing** | pytest | Automated test suite |
| **Containerization** | Docker | Multi-stage build for deployment |

### File Structure

```
webapp/
├── main.py              # FastAPI application and endpoints
├── models.py            # Pydantic data models
├── storage.py           # Thread-safe in-memory storage
├── pipeline.py          # Mock pipeline execution logic
├── run.py               # Application entry point
├── pyproject.toml       # Dependencies and configuration
├── Dockerfile           # Container image definition
└── tests/               # Test suite (23 tests)
    ├── conftest.py      # Test fixtures
    ├── test_app.py      # Application endpoint tests
    ├── test_jobs_api.py # Job management tests
    └── test_pipeline.py # Background task tests
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
pipeline_name: str              # Name of pipeline to execute
parameters: dict                # Pipeline configuration
description: Optional[str]      # Human-readable description
```

### JobResponse (Response)
```python
id: UUID                        # Unique job identifier
status: JobStatus               # Current execution status
pipeline_name: str              # Pipeline name
parameters: dict                # Pipeline parameters
description: Optional[str]      # Job description
created_at: datetime            # Creation timestamp
updated_at: datetime            # Last update timestamp
started_at: Optional[datetime]  # Execution start time
completed_at: Optional[datetime]# Execution completion time
error_message: Optional[str]    # Error details if failed
```

### JobList (Response)
```python
jobs: List[JobResponse]         # Array of job objects
total: int                      # Total number of jobs
```

## API Endpoints

### Job Management

| Method | Endpoint | Description | Status Codes |
|--------|----------|-------------|--------------|
| POST | `/jobs` | Submit new pipeline job | 201 Created, 422 Validation Error |
| GET | `/jobs/{id}` | Get job status by UUID | 200 OK, 404 Not Found |
| GET | `/jobs` | List all jobs | 200 OK |

### System Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Echo message (configurable) |
| GET | `/health` | Health check for monitoring |
| GET | `/version` | Application version |
| GET | `/docs` | Interactive API documentation (Swagger) |
| GET | `/redoc` | Alternative API documentation |

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
- ⚠️  Data lost on restart (by design for PoC)
- ⚠️  Single-instance limitation

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

| Variable | Default | Description |
|----------|---------|-------------|
| `ECHO_MESSAGE` | `"Hello World"` | Message returned by root endpoint |
| `LOG_LEVEL` | `"INFO"` | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `IMAGE_TAG` | `"unknown"` | Deployed image version |

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

| Enhancement | Effort | Description |
|-------------|--------|-------------|
| **Persistent Storage** | 3-4 hours | Migrate to PostgreSQL/DynamoDB |
| **Message Queue** | 2-3 hours | Add SQS/SNS for job distribution |
| **Separate Workers** | 4-6 hours | Dedicated worker service |
| **Authentication** | 4-6 hours | JWT/OAuth2 implementation |
| **Real Pipeline** | 8-16 hours | Snakemake integration |
| **Monitoring** | 2-4 hours | CloudWatch metrics/alarms |

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

### Submit a Cross-Lab ETL Job

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_name": "cross_lab_etl",
    "parameters": {
      "source_group": "genomics_lab",
      "target_group": "clinical_research",
      "data_types": ["vcf", "phenotype_data"],
      "validation_level": "strict",
      "anonymize": true
    },
    "research_group": "data_integration_team",
    "description": "Transfer variant data to clinical research group"
  }'
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
- [Root README](../README.md) - Project overview
- [Infrastructure README](../infra/README.md) - AWS deployment guide
- [Web App README](webapp/README.md) - Detailed application documentation
