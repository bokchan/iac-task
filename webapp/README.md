# FastAPI Web Application

The core FastAPI web service for the IaC Task project. This lightweight application provides REST API endpoints with health monitoring, version tracking, and cloud-ready configuration.

> **Note**: This README focuses on the FastAPI application. For infrastructure deployment and project overview, see the [project root README](../README.md) and [infrastructure documentation](../infra/README.md).

## 🚀 Features

- **RESTful API**: Built with FastAPI for high performance and automatic OpenAPI documentation
- **Health Monitoring**: Built-in health check endpoint for container orchestration
- **Version Tracking**: Dynamic version endpoint that displays the deployed image tag
- **Environment Configuration**: Configurable message and logging via environment variables
- **Production Ready**: Multi-stage Docker build with security best practices
- **Testing**: Test suite with pytest and test client

## 📋 API Endpoints

| Endpoint   | Method | Description                                | Response                     |
| ---------- | ------ | ------------------------------------------ | ---------------------------- |
| `/`        | GET    | Returns configurable echo message          | `{"message": "Hello World"}` |
| `/health`  | GET    | Health check for load balancers            | `"OK"`                       |
| `/version` | GET    | Returns deployed application version       | `{"version": "abc1234"}`     |
| `/docs`    | GET    | Interactive API documentation (Swagger UI) | HTML page                    |
| `/redoc`   | GET    | Alternative API documentation              | HTML page                    |

## 🔧 Configuration

The application is configured via environment variables:

| Variable       | Default         | Description                                             |
| -------------- | --------------- | ------------------------------------------------------- |
| `ECHO_MESSAGE` | `"Hello World"` | Message returned by the root endpoint                   |
| `LOG_LEVEL`    | `"INFO"`        | Application logging level (DEBUG, INFO, WARNING, ERROR) |
| `IMAGE_TAG`    | `"unknown"`     | Version/tag of the deployed image                       |

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

The test suite covers:

- ✅ Root endpoint with default and custom messages
- ✅ Health check endpoint functionality
- ✅ Version endpoint with and without environment variable
- ✅ Environment variable configuration handling

## 🏗️ Project Structure

```
webapp/
├── main.py             # FastAPI application and routes
├── pyproject.toml      # Project dependencies and configuration
├── Dockerfile          # Multi-stage Docker build configuration
├── README.md           # This file
├── uv.lock             # Dependency lock file
├── tests/              # Test suite
│   ├── __init__.py
│   ├── conftest.py     # Test configuration and fixtures
│   └── test_app.py     # Application tests
└── scripts/            # Build and deployment scripts (if present)
```

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

| Endpoint | Purpose | Usage |
|----------|---------|-------|
| `/health` | Load balancer checks | Returns `"OK"` for uptime monitoring |
| `/version` | Deployment tracking | Returns `{"version": "<image-tag>"}` |
| `/docs` | API documentation | Interactive Swagger UI |

**Logging Configuration**:
```bash
# Set log level via environment variable
export LOG_LEVEL="DEBUG"  # DEBUG, INFO, WARNING, ERROR
uv run uvicorn main:app --reload
```

## 📚 API Documentation

Once the application is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json
