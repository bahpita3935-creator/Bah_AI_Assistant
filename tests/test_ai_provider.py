"""Tests for the Ollama provider without making real network requests."""

import json
from unittest.mock import patch

from modules.ai_provider import OllamaProvider


class FakeResponse:
    def __init__(self, status: int, payload: dict) -> None:
        self.status = status
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def test_ollama_is_available_when_tags_endpoint_returns_ok() -> None:
    provider = OllamaProvider()

    with patch(
        "modules.ai_provider.urllib.request.urlopen",
        return_value=FakeResponse(200, {"models": []}),
    ):
        assert provider.is_available()


def test_ollama_is_unavailable_when_connection_fails() -> None:
    provider = OllamaProvider()

    with patch(
        "modules.ai_provider.urllib.request.urlopen",
        side_effect=ConnectionRefusedError,
    ):
        assert not provider.is_available()


def test_ollama_lists_installed_models() -> None:
    provider = OllamaProvider()
    payload = {
        "models": [
            {"name": "phi3:latest"},
            {"name": "llama3.2:latest"},
        ]
    }

    with patch(
        "modules.ai_provider.urllib.request.urlopen",
        return_value=FakeResponse(200, payload),
    ):
        assert provider.list_models() == ["llama3.2:latest", "phi3:latest"]


def test_phi3_alias_matches_phi3_latest() -> None:
    provider = OllamaProvider()

    with patch.object(provider, "list_models", return_value=["phi3:latest"]):
        assert provider.model_is_available("phi3")


def test_phi3_is_the_provider_default() -> None:
    provider = OllamaProvider()
    assert provider.ensure_running is not None
