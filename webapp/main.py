import logging
import os

from fastapi import FastAPI

app = FastAPI()

# Configure logging, setting with the loglevel set by the environment variable LOG_LEVEL
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger(__name__)


@app.get("/")
async def root():
    """Return the string configured by the environment variable: ECHO_MESSAGE"""
    msg = os.environ.get("ECHO_MESSAGE", "Hello World")
    return {"message": msg}


@app.get("/health")
async def health_check():
    """Healthcheck"""
    return "OK"


@app.get("/version")
async def version():
    """Return the deployed version (image tag)"""
    version = os.environ.get("IMAGE_TAG", "unknown")
    logger.info(f"Version endpoint called, returning version: {version}")
    return {"version": version}
