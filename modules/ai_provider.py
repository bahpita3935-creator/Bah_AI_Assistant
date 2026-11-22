"""AI provider abstraction and Ollama implementation."""

from __future__ import annotations

import http.client
import json
import os
import shutil
import subprocess
import time
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
    def __init__(self, base_url: str = "http://127.0.0.1:11434") -> None:
        self.base_url = base_url.rstrip("/")

    @property
    def name(self) -> str:
        return "Ollama local"

    def find_executable(self) -> str | None:
        """Find Ollama on PATH or in common Windows installation folders."""
        executable = shutil.which("ollama")
        if executable:
            return executable

        candidates = [
            os.environ.get("LOCALAPPDATA", "")
            + r"\Programs\Ollama\ollama.exe",
            os.environ.get("LOCALAPPDATA", "")
            + r"\Microsoft\WinGet\Links\ollama.exe",
            r"C:\Program Files\Ollama\ollama.exe",
            r"C:\Program Files (x86)\Ollama\ollama.exe",
            os.environ.get("USERPROFILE", "") + r"\.local\bin\ollama.exe",
        ]
        for candidate in candidates:
            if candidate and os.path.isfile(candidate):
                return candidate
        return None

    def ensure_running(self, timeout_seconds: float = 10) -> bool:
        """Start Ollama locally when an executable is available."""
        if self.is_available():
            return True

        executable = self.find_executable()
        if executable is None:
            return False

        try:
            flags = subprocess.DETACHED_PROCESS if os.name == "nt" else 0
            subprocess.Popen(
                [executable, "serve"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=flags,
                close_fds=True,
            )
        except (OSError, subprocess.SubprocessError):
            return False

        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if self.is_available():
                return True
            time.sleep(0.25)
        return False

    def list_models(self) -> list[str]:
        """Return the names of locally installed Ollama models."""
        try:
            request = urllib.request.Request(
                f"{self.base_url}/api/tags",
                method="GET",
            )
            with urllib.request.urlopen(request, timeout=3) as response:
                data = json.loads(response.read().decode("utf-8"))
            models = data.get("models", [])
            if not isinstance(models, list):
                return []
            names = [
                model.get("name")
                for model in models
                if isinstance(model, dict) and isinstance(model.get("name"), str)
            ]
            return sorted(set(names))
        except (
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
            OSError,
        ):
            return []

    def model_is_available(self, model: str) -> bool:
        """Return whether a model is present locally."""
        if not model.strip():
            return False
        model = model.strip()
        base_model = model.removesuffix(":latest")
        for installed in self.list_models():
            if installed == model:
                return True
            if installed.removesuffix(":latest") == base_model:
                return True
        return False

    def is_available(self) -> bool:
        try:
            request = urllib.request.Request(
                f"{self.base_url}/api/tags",
                method="GET",
            )
            with urllib.request.urlopen(request, timeout=2) as response:
                return response.status == 200
        except (
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
            OSError,
        ):
            return False

    def stream(
        self,
        messages: list[dict[str, str]],
        model: str = "phi3",
    ) -> Iterator[str]:
        payload = json.dumps(
            {
                "model": model,
                "messages": messages,
                "stream": True,
                "keep_alive": "10m",
                "options": {"num_predict": 256, "temperature": 0.7},
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        completed = False
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                for raw_line in response:
                    data = json.loads(raw_line.decode("utf-8"))
                    if error := data.get("error"):
                        raise RuntimeError(f"Erreur Ollama : {error}")
                    completed = data.get("done") is True
                    if message := data.get("message"):
                        if text := message.get("content"):
                            yield text
                    if completed:
                        break
                if not completed:
                    raise RuntimeError(
                        "La réponse Ollama est incomplète : flux terminé sans done=true."
                    )
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            try:
                error = json.loads(body).get("error", body)
            except json.JSONDecodeError:
                error = body or exc.reason
            raise RuntimeError(
                f"Erreur API Ollama HTTP {exc.code} sur /api/chat : {error}"
            ) from exc
        except (http.client.HTTPException, OSError) as exc:
            raise RuntimeError(f"Le flux Ollama a été interrompu : {exc}") from exc
