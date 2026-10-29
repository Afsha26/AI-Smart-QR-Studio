import pytest
from fastapi.testclient import TestClient

from backend.main import create_app


@pytest.mark.parametrize(
    ("path", "body"),
    [
        ("/validator/", {"type": "url", "value": "https://example.com"}),
        ("/analysis/quality", {"payload": "https://example.com", "options": {}}),
    ],
)
def test_frontend_loopback_preflight_and_post(monkeypatch, path, body):
    monkeypatch.setenv("BACKEND_ALLOWED_ORIGINS", "http://localhost:8001")
    client = TestClient(create_app())
    origin = "http://127.0.0.1:8001"

    preflight = client.options(
        path,
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert preflight.status_code == 200
    assert preflight.headers["access-control-allow-origin"] == origin
    assert preflight.headers["access-control-allow-methods"] == "GET, POST, OPTIONS"
    assert "content-type" in preflight.headers["access-control-allow-headers"].lower()
    assert "access-control-allow-credentials" not in preflight.headers

    response = client.post(path, json=body, headers={"Origin": origin})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


def test_cors_rejects_unconfigured_frontend_origin(monkeypatch):
    monkeypatch.setenv("BACKEND_ALLOWED_ORIGINS", "http://localhost:8001")
    client = TestClient(create_app())

    response = client.options(
        "/validator/",
        headers={
            "Origin": "http://127.0.0.1:5500",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
