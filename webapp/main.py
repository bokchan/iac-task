import os

from fastapi import FastAPI

app = FastAPI()


@app.get("/echo")
async def echo():
    """Return the string configured by the environment variable: ECHO_MESSAGE"""
    msg = os.environ.get("ECHO_MESSAGE", "Hello World")
    return {"message": msg}


@app.get("/health")
async def health_check():
    """Healthcheck"""
    return "OK"
