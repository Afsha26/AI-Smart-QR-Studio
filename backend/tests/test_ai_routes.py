from fastapi.testclient import TestClient

from backend.main import create_app


def test_ai_content_endpoint_returns_existing_service_response(monkeypatch):
    async def fake_generate_content(prompt, type_hint):
        return {
            "title": "Cafe",
            "tagline": "Fresh coffee",
            "cta": "View the menu",
            "content": f"{type_hint}: {prompt}",
        }

    monkeypatch.setattr("backend.routers.ai.generate_content_service", fake_generate_content)

    response = TestClient(create_app()).post(
        "/ai/content",
        json={"prompt": "Create cafe content", "type": "url"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "title": "Cafe",
        "tagline": "Fresh coffee",
        "cta": "View the menu",
        "content": "url: Create cafe content",
    }


def test_existing_ai_endpoints_keep_their_response_envelope(monkeypatch):
    class FakeGeminiService:
        async def generate_qr_configuration(self, prompt):
            return {"type": "text", "payload": prompt}

        async def suggest_theme(self, prompt):
            return {"theme": prompt}

        async def improve_qr(self, configuration):
            return {"recommendations": [configuration["payload"]]}

        async def explain_qr(self, payload):
            return {"explanation": payload}

    monkeypatch.setattr("backend.routers.ai.GeminiService", FakeGeminiService)
    client = TestClient(create_app())

    requests = [
        ("/ai/generate", {"prompt": "Create a QR"}, {"type": "text", "payload": "Create a QR"}),
        ("/ai/theme", {"prompt": "Suggest a theme"}, {"theme": "Suggest a theme"}),
        (
            "/ai/improve",
            {"payload": "https://example.com", "style": {}},
            {"recommendations": ["https://example.com"]},
        ),
        (
            "/ai/explain",
            {"payload": "https://example.com"},
            {"explanation": "https://example.com"},
        ),
    ]

    for path, request_body, data in requests:
        response = client.post(path, json=request_body)
        assert response.status_code == 200
        assert response.json() == {
            "success": True,
            "data": data,
            "error": None,
            "metadata": None,
        }
