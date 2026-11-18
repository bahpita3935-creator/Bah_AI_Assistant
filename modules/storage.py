"""Local JSON repositories for conversations and assistant memory."""

from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock
from typing import Iterable

from modules.models import Conversation


class JsonConversationStore:
    """Persist conversations in a local JSON file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._lock = Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({"conversations": []})

    def _read(self) -> dict:
        with self._lock:
            if not self.path.exists():
                return {"conversations": []}
            try:
                with self.path.open("r", encoding="utf-8") as file:
                    data = json.load(file)
            except (json.JSONDecodeError, OSError):
                return {"conversations": []}
            return data if isinstance(data, dict) else {"conversations": []}

    def _write(self, data: dict) -> None:
        with self._lock:
            temporary_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
            with temporary_path.open("w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            os.replace(temporary_path, self.path)

    def create(self, title: str = "Nouvelle conversation") -> Conversation:
        conversation = Conversation.create(title)
        data = self._read()
        conversations = data.setdefault("conversations", [])
        conversations.insert(0, conversation.to_dict())
        self._write(data)
        return conversation

    def list(self) -> list[Conversation]:
        data = self._read()
        items = data.get("conversations", [])
        if not isinstance(items, list):
            return []
        return [Conversation.from_dict(item) for item in items]

    def get(self, conversation_id: str) -> Conversation | None:
        for conversation in self.list():
            if conversation.id == conversation_id:
                return conversation
        return None

    def save(self, conversation: Conversation) -> None:
        data = self._read()
        conversations = data.setdefault("conversations", [])
        replaced = False
        for index, item in enumerate(conversations):
            if isinstance(item, dict) and item.get("id") == conversation.id:
                conversations[index] = conversation.to_dict()
                replaced = True
                break
        if not replaced:
            conversations.insert(0, conversation.to_dict())
        self._write(data)

    def delete(self, conversation_id: str) -> bool:
        data = self._read()
        conversations = data.setdefault("conversations", [])
        filtered = [
            item
            for item in conversations
            if not (isinstance(item, dict) and item.get("id") == conversation_id)
        ]
        if len(filtered) == len(conversations):
            return False
        data["conversations"] = filtered
        self._write(data)
        return True


class JsonMemoryStore:
    """Persist small local facts in a JSON file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        if not self.path.exists():
            self._write({"facts": []})

    def _read(self) -> dict:
        with self._lock:
            if not self.path.exists():
                return {"facts": []}
            try:
                with self.path.open("r", encoding="utf-8") as file:
                    data = json.load(file)
            except (json.JSONDecodeError, OSError):
                return {"facts": []}
            facts = data.get("facts", []) if isinstance(data, dict) else []
            return {"facts": facts if isinstance(facts, list) else []}

    def _write(self, data: dict) -> None:
        with self._lock:
            temporary_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
            with temporary_path.open("w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            os.replace(temporary_path, self.path)

    def list(self) -> list[str]:
        facts = self._read()["facts"]
        return [fact for fact in facts if isinstance(fact, str)]

    def add(self, fact: str) -> bool:
        fact = fact.strip()
        if not fact:
            return False
        facts = self.list()
        if fact in facts:
            return False
        facts.insert(0, fact)
        self._write({"facts": facts})
        return True

    def remove(self, fact: str) -> bool:
        facts = self.list()
        if fact not in facts:
            return False
        facts.remove(fact)
        self._write({"facts": facts})
        return True

    def clear(self) -> None:
        self._write({"facts": []})
