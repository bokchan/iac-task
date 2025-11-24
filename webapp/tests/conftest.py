from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from webapp.main import app
from webapp.pipeline import execute_mock_pipeline


# Mock pipeline duration for fast tests (globally applied)
MOCK_MIN_DURATION = 0.1
MOCK_MAX_DURATION = 0.5


@pytest.fixture()
def client() -> Iterator[TestClient]:
    yield TestClient(app)


@pytest.fixture(autouse=True)
def fast_pipeline_execution(monkeypatch):
    """Automatically mock pipeline execution to use fast durations for all tests."""
    original_execute = (
        execute_mock_pipeline.__wrapped__
        if hasattr(execute_mock_pipeline, "__wrapped__")
        else execute_mock_pipeline
    )

    async def fast_execute(
        job_id,
        pipeline_name,
        parameters,
        min_duration=None,
        max_duration=None,
        success_rate=0.8,
    ):
        # Override durations with fast values
        return await original_execute(
            job_id=job_id,
            pipeline_name=pipeline_name,
            parameters=parameters,
            min_duration=MOCK_MIN_DURATION,
            max_duration=MOCK_MAX_DURATION,
            success_rate=success_rate,
        )

    monkeypatch.setattr("webapp.main.execute_mock_pipeline", fast_execute)
    monkeypatch.setattr("webapp.pipeline.execute_mock_pipeline", fast_execute)
