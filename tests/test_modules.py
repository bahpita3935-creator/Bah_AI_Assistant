"""Tests for pure feature helpers."""

from modules.models import Conversation
from modules.business import build_business_brief
from modules.programmation import build_programming_prompt
from modules.social_media import build_social_post
from modules.storage import JsonConversationStore, JsonMemoryStore


def test_programming_prompt() -> None:
    prompt = build_programming_prompt("Python", "Créer une API REST")

    assert "Python" in prompt
    assert "API REST" in prompt
    assert "tests" in prompt


def test_programming_prompt_rejects_empty_objective() -> None:
    assert build_programming_prompt("Python", "  ") == ""


def test_business_brief() -> None:
    brief = build_business_brief(
        "Bahora Store",
        "Simplifier les ventes",
        "Petites entreprises",
    )

    assert "Bahora Store" in brief
    assert "Petites entreprises" in brief


def test_social_post() -> None:
    post = build_social_post("Lancement du produit", "LinkedIn", "Professionnel")

    assert "LinkedIn" in post
    assert "Call to action" in post


def test_conversation_persists_messages(tmp_path) -> None:
    store = JsonConversationStore(tmp_path / "conversations.json")
    conversation = store.create("Test")
    conversation.add_message("user", "Bonjour")
    conversation.add_message("assistant", "Salut")
    store.save(conversation)

    restored = store.get(conversation.id)

    assert restored is not None
    assert [message.role for message in restored.messages] == [
        "user",
        "assistant",
    ]


def test_json_memory_store(tmp_path) -> None:
    store = JsonMemoryStore(tmp_path / "memory.json")

    assert store.add("Préfère Python")
    assert not store.add("Préfère Python")
    assert store.list() == ["Préfère Python"]
    assert store.remove("Préfère Python")
    assert store.list() == []


def test_conversation_serialization_round_trip() -> None:
    conversation = Conversation.create("Architecture")
    conversation.add_message("user", "Explique le projet")

    restored = Conversation.from_dict(conversation.to_dict())

    assert restored.id == conversation.id
    assert restored.messages[0].content == "Explique le projet"
