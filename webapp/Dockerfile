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

# Copy application source code (excluding unnecessary files)
COPY ./*.py ./README.md ./

# Install the application
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Stage 2: Runtime - Create minimal production image
FROM python:3.14-slim-bookworm AS runtime

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/app/.venv/bin:$PATH"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd --system --gid 999 nonroot \
    && useradd --system --gid 999 --uid 999 --create-home --shell /bin/bash nonroot

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder --chown=nonroot:nonroot /app/.venv /app/.venv

# Copy application code
COPY --from=builder --chown=nonroot:nonroot /app /app

# Switch to non-root user
USER nonroot

# Expose the port FastAPI will run on
EXPOSE 8000

# Add security and metadata labels
LABEL org.opencontainers.image.title="FastAPI WebApp" \
      org.opencontainers.image.description="A FastAPI application for the IaC task" \
      org.opencontainers.image.vendor="Andreas" \
      org.opencontainers.image.source="https://github.com/bokchan/devops-project"

# Use uvicorn to run the FastAPI application in production
# Note: LOG_LEVEL environment variable will be used if set, otherwise defaults to "info"
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 --access-log --log-level ${LOG_LEVEL:-info}"]
