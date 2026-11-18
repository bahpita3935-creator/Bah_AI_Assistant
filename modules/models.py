"""Domain models used by BAH AI Assistant."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4


MessageRole = Literal["user", "assistant", "system"]


def utc_now() -> str:
    """Return an ISO 8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(slots=True)
class Message:
    role: MessageRole
    content: str
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(slots=True)
class Conversation:
    id: str
    title: str
    messages: list[Message] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    @classmethod
    def create(cls, title: str = "Nouvelle conversation") -> "Conversation":
        now = utc_now()
        return cls(
            id=str(uuid4()),
            title=title,
            created_at=now,
            updated_at=now,
        )

    def add_message(self, role: MessageRole, content: str) -> Message:
        message = Message(role=role, content=content)
        self.messages.append(message)
        self.updated_at = utc_now()
        return message

    @classmethod
    def from_dict(cls, data: dict) -> "Conversation":
        messages = [
            Message(
                role=message["role"],
                content=message["content"],
                created_at=message.get("created_at", utc_now()),
            )
            for message in data.get("messages", [])
        ]
        return cls(
            id=data["id"],
            title=data["title"],
            messages=messages,
            created_at=data.get("created_at", utc_now()),
            updated_at=data.get("updated_at", utc_now()),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "messages": [message.to_dict() for message in self.messages],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
