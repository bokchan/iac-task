# Stage 1: Builder - Install dependencies and build the application
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

# Set environment variables for optimal uv behavior
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy webapp dependency files first for better layer caching
COPY ./pyproject.toml ./uv.lock ./

# Install dependencies into a virtual environment
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy application source code
COPY ./*.py ./__init__.py ./README.md ./

# Install the application
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Stage 2: Runtime - Create minimal production image
FROM python:3.14-slim-bookworm AS runtime

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd --system --gid 999 nonroot \
    && useradd --system --gid 999 --uid 999 --create-home --shell /bin/bash nonroot

# Set working directory to parent of webapp
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder --chown=nonroot:nonroot /app/.venv /app/.venv

# Copy application code into webapp subdirectory (exclude .venv to avoid duplication)
COPY --from=builder --chown=nonroot:nonroot /app/*.py /app/webapp/
COPY --from=builder --chown=nonroot:nonroot /app/__init__.py /app/webapp/
COPY --from=builder --chown=nonroot:nonroot /app/README.md /app/webapp/

# Switch to non-root user
USER nonroot

# Expose the port FastAPI will run on
EXPOSE 8000

# Use uvicorn to run the FastAPI application as a module
# Note: LOG_LEVEL environment variable will be used if set, otherwise defaults to "info"
CMD ["sh", "-c", "uvicorn webapp.main:app --host 0.0.0.0 --port 8000"]
