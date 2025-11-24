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

See [webapp/README.md](webapp/README.md#api-endpoints) for complete API documentation including job management, discovery, and system endpoints.

## Storage Implementation

Thread-safe in-memory storage using `JobStore` class with `threading.Lock` for concurrent access. See [webapp/README.md](webapp/README.md#storage) for implementation details.

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

**23 comprehensive tests** covering all endpoints, error cases, and concurrent scenarios with ~9 second execution time. See [webapp/README.md](webapp/README.md#testing) for test suite details and running instructions.

## Configuration

Environment variables (`ECHO_MESSAGE`, `LOG_LEVEL`, `IMAGE_TAG`) and pipeline parameters are configured in code. See [webapp/README.md](webapp/README.md#configuration) for complete configuration reference.

## Deployment

Deployed as a Docker container on AWS ECS Fargate with Application Load Balancer. See [webapp/README.md](webapp/README.md#docker) for Docker build instructions and [infra/README.md](infra/README.md) for AWS deployment details.

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

Complete API usage examples with curl commands and responses are available in [webapp/README.md](webapp/README.md#usage).

## Additional Resources

- [webapp/README.md](webapp/README.md) - Developer documentation, local setup, API usage
- [README.md](README.md) - Project overview and quick start
- [infra/README.md](infra/README.md) - AWS deployment and infrastructure
