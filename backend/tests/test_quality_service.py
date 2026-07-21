import asyncio

from backend.services.quality_service import analyze_quality


def test_analyze_quality_returns_structured_response():
    result = asyncio.run(
        analyze_quality(
            "https://example.com/qr",
            {
                "fg": "#000000",
                "bg": "#ffffff",
                "size": 512,
                "logo": b"logo",
            },
        )
    )

    assert result["score"] >= 0
    assert result["score"] <= 100
    assert result["contrast"]["status"] in {
        "Excellent",
        "Good",
        "Fair",
        "Poor",
        "Unknown",
    }
    assert result["module"]["status"] in {"Excellent", "Good", "Too Small"}
    assert result["logo"]["status"] in {"None", "Safe", "Medium Risk", "High Risk"}
    assert isinstance(result["recommendations"], list)
    assert result["recommendations"]
