# Webapp

Build docker image

    docker build -f webapp/Dockerfile .

Run with uvicorn

    uvicorn webapp:main:app
