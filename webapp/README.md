# Pipeline Orchestration Service

A FastAPI-based REST API service for submitting and tracking Snakemake pipeline jobs. This service provides job management capabilities with background task processing, thread-safe storage, and comprehensive monitoring.

> **Project Context**: This is a 6-hour Proof of Concept (PoC) demonstrating pipeline orchestration. See [PROJECT.md](../PROJECT.md) for implementation details and scope.

> **Infrastructure**: For deployment and cloud architecture, see the [project root README](../README.md) and [infrastructure documentation](../infra/README.md).

## 🚀 Features

- **Job Management API**: Submit, track, and list pipeline jobs via REST endpoints
- **Background Processing**: Asynchronous job execution using FastAPI BackgroundTasks
- **Thread-Safe Storage**: In-memory job store with concurrent access support
- **Mock Pipeline Execution**: Simulates Snakemake pipeline with configurable duration and success rate
- **RESTful API**: Built with FastAPI for high performance and automatic OpenAPI documentation
- **Health Monitoring**: Built-in health check endpoint for container orchestration
- **Version Tracking**: Dynamic version endpoint that displays the deployed image tag
- **Environment Configuration**: Configurable via environment variables
- **Production Ready**: Multi-stage Docker build with security best practices
- **Comprehensive Testing**: 23 tests covering all endpoints and edge cases

## 📋 API Endpoints

### Job Management

| Endpoint     | Method | Description                             | Response                               |
| ------------ | ------ | --------------------------------------- | -------------------------------------- |
| `/jobs`      | POST   | Submit a new pipeline job for execution | `JobResponse` (201 Created)            |
| `/jobs/{id}` | GET    | Get job status and details by UUID      | `JobResponse` (200 OK / 404 Not Found) |
| `/jobs`      | GET    | List all jobs with total count          | `JobList` (200 OK)                     |

**Job Lifecycle**: `PENDING` → `RUNNING` → `COMPLETED` or `FAILED`

**Example Request** (POST /jobs):

```json
{
  "pipeline_name": "variant_calling",
  "parameters": { "sample_id": "S001", "genome": "hg38" },
  "description": "Run variant calling on sample S001"
}
```

**Example Response**:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "pipeline_name": "variant_calling",
  "parameters": { "sample_id": "S001", "genome": "hg38" },
  "description": "Run variant calling on sample S001",
  "created_at": "2025-11-24T10:00:00Z",
  "updated_at": "2025-11-24T10:00:00Z",
  "started_at": null,
  "completed_at": null,
  "error_message": null
}
```

### System Endpoints

| Endpoint   | Method | Description                                | Response                     |
| ---------- | ------ | ------------------------------------------ | ---------------------------- |
| `/`        | GET    | Returns configurable echo message          | `{"message": "Hello World"}` |
| `/health`  | GET    | Health check for load balancers            | `"OK"`                       |
| `/version` | GET    | Returns deployed application version       | `{"version": "abc1234"}`     |
| `/docs`    | GET    | Interactive API documentation (Swagger UI) | HTML page                    |
| `/redoc`   | GET    | Alternative API documentation              | HTML page                    |

## 🔧 Configuration

The application is configured via environment variables:

### Application Settings

| Variable       | Default         | Description                                             |
| -------------- | --------------- | ------------------------------------------------------- |
| `ECHO_MESSAGE` | `"Hello World"` | Message returned by the root endpoint                   |
| `LOG_LEVEL`    | `"INFO"`        | Application logging level (DEBUG, INFO, WARNING, ERROR) |
| `IMAGE_TAG`    | `"unknown"`     | Version/tag of the deployed image                       |

### Pipeline Configuration

The mock pipeline execution can be configured programmatically:

```python
# In pipeline.py - execute_mock_pipeline function parameters
min_duration: float = 10      # Minimum execution time (seconds)
max_duration: float = 30      # Maximum execution time (seconds)
success_rate: float = 0.8     # Probability of success (0.0-1.0)
```

> **Note**: In tests, durations are automatically mocked to 0.1-0.5s for fast execution.

## 🏃‍♂️ Running the Application

### Local Development

1. **Install dependencies** (requires Python 3.14+):

   ```bash
   # cd into 'webapp' directory
   # Install UV package manager
   pip install uv

   # Install dependencies
   uv sync

   # Activate the virtual environment
   source .venv/bin/activate
   ```

2. **Run the development server**:

   ```bash
   # Using UV
   uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

   # Or directly with uvicorn
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Access the application**:
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

### Quick Usage Examples

**Submit a job**:

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_name": "variant_calling",
    "parameters": {"sample_id": "S001", "genome": "hg38"},
    "description": "Run variant calling on sample S001"
  }'
# Returns: Job ID and initial status (PENDING)
```

**Check job status**:

```bash
curl http://localhost:8000/jobs/{job-id}
# Returns: Current job status (PENDING/RUNNING/COMPLETED/FAILED)
```

**List all jobs**:

```bash
curl http://localhost:8000/jobs
# Returns: Array of all jobs with total count
```

### Docker Deployment

#### Using Docker Compose (Recommended)

The project root includes `docker-compose.yml` for integrated development:

```bash
# From the project root directory
docker compose up --build
# → Starts webapp with hot reload and health checks
```

> **Full Docker Compose details**: See [project root README](../README.md#getting-started)

#### Manual Docker Commands

1. **Build the Docker image**:

   ```bash
   # From the project root directory
   docker build -f webapp/Dockerfile -t webapp:latest ./webapp
   ```

2. **Run the container**:

   ```bash
   docker run -p 8000:8000 \
     -e ECHO_MESSAGE="Hello from Docker!" \
     -e LOG_LEVEL="DEBUG" \
     -e IMAGE_TAG="docker-latest" \
     webapp:latest
   ```

3. **Run with custom configuration**:
   ```bash
   docker run -p 8000:8000 \
     --env-file .env \
     webapp:latest
   ```

## 🧪 Testing

The application includes a basic test suite covering all endpoints.

### Run Tests

```bash
# Install development dependencies
uv sync --group dev

# Run all tests
uv run pytest

# Run tests with verbose output
uv run pytest -v

```

### Test Coverage

The test suite includes **23 comprehensive tests** covering:

#### Job Management API (`test_jobs_api.py` - 15 tests)

- ✅ Job submission (success, minimal, validation, multiple concurrent)
- ✅ Job retrieval (by ID, not found, invalid UUID)
- ✅ Job listing (empty, with data, all fields)
- ✅ Storage integration and persistence
- ✅ Concurrent job submissions (thread-safe operations)
- ✅ Existing endpoints (root, health, version)

#### Background Task Integration (`test_pipeline.py` - 3 tests)

- ✅ Background task triggering
- ✅ Multiple concurrent background tasks
- ✅ Complete job lifecycle (PENDING → RUNNING → COMPLETED/FAILED)

#### Existing Functionality (`test_app.py` - 5 tests)

- ✅ Root endpoint with default and custom messages
- ✅ Health check endpoint functionality
- ✅ Version endpoint with and without environment variable
- ✅ Environment variable configuration handling

**Performance**: All tests execute in ~9 seconds (optimized from 86+ seconds)

## 🏗️ Project Structure

```
webapp/
├── main.py             # FastAPI app with job management endpoints
├── models.py            # Pydantic models (JobStatus, JobSubmission, JobResponse, JobList)
├── storage.py           # Thread-safe in-memory job storage (JobStore)
├── pipeline.py          # Mock pipeline execution with background tasks
├── run.py               # Application entry point
├── pyproject.toml       # Project dependencies and configuration
├── Dockerfile           # Multi-stage Docker build configuration
├── README.md            # This file
├── uv.lock              # Dependency lock file
└── tests/               # Test suite (23 tests)
    ├── __init__.py
    ├── conftest.py      # Test configuration and fixtures
    ├── test_app.py      # Existing endpoint tests (5 tests)
    ├── test_jobs_api.py # Job management API tests (15 tests)
    └── test_pipeline.py # Background task tests (3 tests)
```

### Key Components

**`models.py`**: Pydantic models for request/response validation

- `JobStatus`: Enum (PENDING, RUNNING, COMPLETED, FAILED)
- `JobSubmission`: Request model for job creation
- `JobResponse`: Response model with full job details
- `JobList`: Collection response with total count

**`storage.py`**: Thread-safe in-memory job storage

- `JobStore`: Dictionary-based storage with `threading.Lock`
- Methods: `create()`, `get()`, `update()`, `list_all()`, `count()`
- Global singleton instance for application-wide access

**`pipeline.py`**: Mock Snakemake pipeline execution

- `execute_mock_pipeline()`: Async function simulating pipeline runs
- Configurable duration (10-30s default) and success rate (80%)
- Updates job status throughout lifecycle
- Realistic error messages on failure

**`main.py`**: FastAPI application with endpoints

- Job management: POST /jobs, GET /jobs/{id}, GET /jobs
- System: /, /health, /version
- Background task integration
- OpenAPI documentation

## 🐳 Docker Image Details

The Dockerfile uses a **multi-stage build** approach for optimal security and performance:

### Build Stage

- Uses `ghcr.io/astral-sh/uv:python3.14-bookworm-slim` as base
- Installs build dependencies and application dependencies
- Leverages UV's caching for faster builds

### Runtime Stage

- Uses minimal `python:3.14-slim-bookworm` runtime image
- Runs as non-root user for security
- Optimized for production deployment
- Exposes port 8000

### Security Features

- 🔒 Non-root user execution
- 🧹 Minimal runtime dependencies
- 📦 Multi-stage build reduces image size
- 🔐 Security-focused base images

## 🔍 Application Monitoring

| Endpoint   | Purpose              | Usage                                |
| ---------- | -------------------- | ------------------------------------ |
| `/health`  | Load balancer checks | Returns `"OK"` for uptime monitoring |
| `/version` | Deployment tracking  | Returns `{"version": "<image-tag>"}` |
| `/docs`    | API documentation    | Interactive Swagger UI               |

**Logging Configuration**:

```bash
# Set log level via environment variable
export LOG_LEVEL="DEBUG"  # DEBUG, INFO, WARNING, ERROR
uv run uvicorn main:app --reload
```

## 🏗️ Architecture Notes

### Proof of Concept Scope

This is a **6-hour PoC implementation** focused on demonstrating core functionality. Design decisions prioritize rapid development and demonstration over production scalability.

#### Storage Implementation

**In-Memory Storage with Thread-Safe Operations**

- Uses Python dictionary with `threading.Lock` for concurrent access
- Jobs persist during application runtime only
- Data is lost on container restart/redeploy
- **Suitable for**: Single-container PoC, demos, development
- **Not suitable for**: Multi-instance deployments, long-term data retention

```python
# Thread-safe operations ensure correctness
with self._lock:
    self._jobs[job_id] = job_data
```

**Why This Works for PoC**:

- ✅ Real functional storage (not mocked)
- ✅ Correct concurrent access handling
- ✅ Fast read/write operations
- ✅ Zero infrastructure dependencies
- ✅ Easy to test and demonstrate
- ⚠️ Single container limitation (acceptable for PoC)
- ⚠️ Data loss on restart (acceptable for demos)

#### Background Task Processing

**FastAPI BackgroundTasks**

- Jobs execute asynchronously in the same process
- Suitable for lightweight, short-running tasks
- Simple implementation without external dependencies
- **Limitation**: Tied to web worker process lifecycle

**Job Lifecycle**:

```
POST /jobs → PENDING → Background worker → RUNNING → COMPLETED/FAILED
                           ↓
                    Updates in-memory store
```

### Production Considerations (Out of Scope)

For production deployment beyond PoC, consider:

1. **Persistent Storage**: PostgreSQL/DynamoDB (see PROJECT.md "Future Enhancements")
2. **Message Queue**: AWS SQS/SNS for job distribution
3. **Separate Workers**: Dedicated worker services for better scaling
4. **State Management**: Redis for distributed locking/caching
5. **Multi-Instance**: Load balancer with multiple containers
6. **Monitoring**: CloudWatch metrics, distributed tracing

**Estimated effort for production upgrade**: +3-4 hours (primarily database integration)

## 📚 API Documentation

Once the application is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json
