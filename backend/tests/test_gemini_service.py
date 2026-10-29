import asyncio
import logging
import unittest
from unittest.mock import Mock

from backend.services.gemini_service import (
    DEFAULT_MODEL,
    GeminiAPIError,
    GeminiAuthenticationError,
    GeminiModelError,
    GeminiQuotaError,
    GeminiResponseError,
    GeminiService,
    GeminiTimeoutError,
    GeminiUnavailableError,
)


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

    def test_default_model_is_current_recommended_model(self) -> None:
        self.assertEqual(DEFAULT_MODEL, "gemini-3.8-flash")

    def test_send_request_passes_model_name_to_google_genai_sdk(self) -> None:
        self.service._client = Mock()
        self.service._model = "gemini-3.8-flash"

        asyncio.run(self.service._send_request("test prompt"))

        self.service._client.models.generate_content.assert_called_once()
        kwargs = self.service._client.models.generate_content.call_args.kwargs
        self.assertEqual(kwargs["model"], "gemini-3.8-flash")
        self.assertEqual(kwargs["contents"], "test prompt")

    def test_api_errors_do_not_expose_provider_details(self) -> None:
        secret = "sensitive-provider-detail"
        error = self.service._wrap_api_error(Exception(f"404 NOT_FOUND {secret}"))

        self.assertIsInstance(error, GeminiAPIError)
        self.assertNotIsInstance(error, GeminiModelError)
        self.assertNotIn(secret, str(error))

    def test_api_statuses_are_classified(self) -> None:
        cases = (
            (401, "unauthorized", GeminiAuthenticationError),
            (429, "resource exhausted", GeminiQuotaError),
            (404, "model not found", GeminiModelError),
            (503, "service unavailable", GeminiUnavailableError),
            (502, "gateway error", GeminiAPIError),
        )
        for status, message, expected_type in cases:
            with self.subTest(status=status):
                provider_error = Exception(message)
                provider_error.code = status
                self.assertIsInstance(self.service._wrap_api_error(provider_error), expected_type)

    def test_timeouts_are_classified(self) -> None:
        self.assertIsInstance(
            self.service._wrap_api_error(TimeoutError("request timed out")),
            GeminiTimeoutError,
        )

    def test_provider_diagnostics_are_structured_and_redacted(self) -> None:
        secret = "AIza" + ("A" * 35)
        provider_error = Exception(
            f"503 SERVICE_UNAVAILABLE {{'api_key': '{secret}', 'token': 'private-token-value'}} "
            "Authorization: Bearer another-private-token"
        )
        provider_error.code = 503

        with self.assertLogs("backend.services.gemini_service", level=logging.ERROR) as captured:
            self.service._log_api_error(provider_error, "suggest_theme")

        log_entry = captured.output[0]
        self.assertIn("exception_class=Exception", log_entry)
        self.assertIn("http_status=503", log_entry)
        self.assertIn("operation=suggest_theme", log_entry)
        self.assertIn("[REDACTED]", log_entry)
        self.assertNotIn(secret, log_entry)
        self.assertNotIn("private-token-value", log_entry)
        self.assertNotIn("another-private-token", log_entry)

    def test_service_unavailability_does_not_expose_provider_details(self) -> None:
        secret = "sensitive-provider-detail"
        provider_error = Exception(f"503 SERVICE_UNAVAILABLE {secret}")
        provider_error.code = 503

        error = self.service._wrap_api_error(provider_error)

        self.assertIsInstance(error, GeminiUnavailableError)
        self.assertNotIn(secret, str(error))

    def test_provider_error_http_status_is_read_from_response(self) -> None:
        provider_error = Exception("API key rejected")
        provider_error.response = Mock(status_code=401)

        self.assertIsInstance(
            self.service._wrap_api_error(provider_error),
            GeminiAuthenticationError,
        )


if __name__ == "__main__":
    unittest.main()
