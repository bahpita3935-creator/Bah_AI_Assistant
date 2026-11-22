"""Tests for the Ollama provider without making real network requests."""

import io
import json
from unittest.mock import patch
from urllib.error import HTTPError

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


class FakeStreamingResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def __iter__(self):
        yield b'{"message":{"role":"assistant","content":"Bonjour"},"done":false}\n'
        yield b'{"message":{"role":"assistant","content":" phi3"},"done":true}\n'


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
    assert provider.stream.__defaults__ == ("phi3",)


def test_stream_uses_local_chat_endpoint_and_phi3_payload() -> None:
    provider = OllamaProvider()
    messages = [{"role": "user", "content": "Bonjour"}]

    with patch(
        "modules.ai_provider.urllib.request.urlopen",
        return_value=FakeStreamingResponse(),
    ) as urlopen:
        result = "".join(provider.stream(messages))

    request = urlopen.call_args.args[0]
    payload = json.loads(request.data.decode("utf-8"))
    assert request.full_url == "http://127.0.0.1:11434/api/chat"
    assert payload["model"] == "phi3"
    assert payload["messages"] == messages
    assert payload["stream"] is True
    assert payload["keep_alive"] == "10m"
    assert payload["options"] == {"num_predict": 256, "temperature": 0.7}
    assert result == "Bonjour phi3"


def test_chat_endpoint_404_has_actionable_error() -> None:
    provider = OllamaProvider()
    error_body = b'{"error":"model not found"}'

    with patch(
        "modules.ai_provider.urllib.request.urlopen",
        side_effect=HTTPError(
            "http://127.0.0.1:11434/api/chat",
            404,
            "Not Found",
            {},
            io.BytesIO(error_body),
        ),
    ):
        try:
            "".join(
                provider.stream(
                    [{"role": "user", "content": "Bonjour"}],
                    model="phi3",
                )
            )
        except RuntimeError as exc:
            assert "HTTP 404 sur /api/chat" in str(exc)
            assert "model not found" in str(exc)
        else:
            raise AssertionError("Expected an Ollama API error")
