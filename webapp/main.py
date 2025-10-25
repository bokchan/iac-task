from fastapi import FastAPI

app = FastAPI()


@app.get("/echo")
async def echo():
    """TODO Make configurable with ENV VAR"""
    return {"message": "Hello World"}


@app.get("/health")
async def health_check():
    """Healthcheck"""
    return "OK"
