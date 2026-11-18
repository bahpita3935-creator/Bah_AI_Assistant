"""AI provider abstraction and Ollama implementation."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Iterator
from typing import Protocol


class AIProvider(Protocol):
    @property
    def name(self) -> str:
        """Name displayed in the interface."""

    def is_available(self) -> bool:
        """Return whether the provider can accept requests."""

    def stream(self, messages: list[dict[str, str]], model: str) -> Iterator[str]:
        """Stream generated text chunks."""


class OllamaProvider:
    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self.base_url = base_url.rstrip("/")

    @property
    def name(self) -> str:
        return "Ollama local"

    def is_available(self) -> bool:
        try:
            request = urllib.request.Request(
                f"{self.base_url}/api/tags",
                method="GET",
            )
            with urllib.request.urlopen(request, timeout=2) as response:
                return response.status == 200
        except (urllib.error.URLError, TimeoutError):
            return False

    def stream(
        self,
        messages: list[dict[str, str]],
        model: str = "llama3.2",
    ) -> Iterator[str]:
        payload = json.dumps(
            {
                "model": model,
                "messages": messages,
                "stream": True,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=60) as response:
            for raw_line in response:
                data = json.loads(raw_line.decode("utf-8"))
                if message := data.get("message"):
                    if text := message.get("content"):
                        yield text
