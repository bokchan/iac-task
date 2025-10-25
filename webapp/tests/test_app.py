import os
from unittest import mock

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_get_echo():
    response = client.get("/echo")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_echo_with_env_var() -> None:
    with mock.patch.dict(
        os.environ,
        {
            "ECHO_MESSAGE": "Mind the gap",
        },
    ):
        response = client.get("/echo")
        assert response.status_code == 200
        assert response.json() == {"message": "Mind the gap"}


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == "OK"
