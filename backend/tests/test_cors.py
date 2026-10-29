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
@pytest.mark.parametrize("origin", ["http://127.0.0.1:5500", "http://localhost:5500"])
def test_live_server_preflight_and_post(monkeypatch, path, body, origin):
    monkeypatch.setenv("BACKEND_ALLOWED_ORIGINS", "http://localhost:8001")
    client = TestClient(create_app())

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


def test_cors_rejects_unconfigured_origin(monkeypatch):
    monkeypatch.setenv("BACKEND_ALLOWED_ORIGINS", "http://localhost:8001")
    client = TestClient(create_app())

    response = client.options(
        "/validator/",
        headers={
            "Origin": "http://localhost:5501",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
