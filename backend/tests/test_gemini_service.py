import asyncio
import unittest
from unittest.mock import Mock

from backend.services.gemini_service import GeminiResponseError, GeminiService


class GeminiServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = GeminiService(api_key="test-key")

    def test_generate_qr_configuration_parses_json(self) -> None:
        fake_response = Mock()
        fake_response.text = '{"type": "url", "payload": "https://example.com"}'
        self.service._client = Mock()
        self.service._client.models.generate_content.return_value = fake_response

        result = asyncio.run(self.service.generate_qr_configuration("Create a premium QR"))

        self.assertEqual(result["type"], "url")
        self.assertEqual(result["payload"], "https://example.com")

    def test_generate_qr_configuration_strips_markdown_fences(self) -> None:
        fake_response = Mock()
        fake_response.text = "```json\n{\"type\": \"text\", \"payload\": \"hello\"}\n```"
        self.service._client = Mock()
        self.service._client.models.generate_content.return_value = fake_response

        result = asyncio.run(self.service.generate_qr_configuration("Create a simple text QR"))

        self.assertEqual(result["type"], "text")
        self.assertEqual(result["payload"], "hello")

    def test_generate_qr_configuration_raises_for_invalid_json(self) -> None:
        fake_response = Mock()
        fake_response.text = "not valid json"
        self.service._client = Mock()
        self.service._client.models.generate_content.return_value = fake_response

        with self.assertRaises(GeminiResponseError):
            asyncio.run(self.service.generate_qr_configuration("Create a QR"))


if __name__ == "__main__":
    unittest.main()
