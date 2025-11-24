"""
Application Entry Point

Direct execution entry point for local development.
Runs the FastAPI application with uvicorn and hot-reload enabled.

Usage:
    python -m webapp.run

Note: In production, use uvicorn directly or via Docker.
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "webapp.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
