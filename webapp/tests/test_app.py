import os
from unittest import mock

from fastapi.testclient import TestClient


def test_get_root(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_get_root_with_env_var(client: TestClient) -> None:
    with mock.patch.dict(os.environ, {"ECHO_MESSAGE": "Mind the gap"}):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Mind the gap"}


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == "OK"


def test_get_version(client: TestClient) -> None:
    with mock.patch.dict(os.environ, {"IMAGE_TAG": "v1.2.3"}):
        response = client.get("/version")
        assert response.status_code == 200
        assert response.json() == {"version": "v1.2.3"}


def test_get_version_without_env_var(client: TestClient) -> None:
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json() == {"version": "unknown"}
