"""Tests for assistant features and UI helpers."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

from agents.registry import AGENTS
from modules import assistant
from modules.models import Conversation
from modules.assistant import conversation_title
from modules.business import build_business_brief
from modules.programmation import build_programming_prompt
from modules.social_media import build_social_post
from modules.storage import (
    JsonConversationStore,
    JsonMemoryStore,
    JsonPreferencesStore,
    JsonStorageError,
)


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


def test_json_store_creates_missing_parent_directories(tmp_path) -> None:
    path = tmp_path / "nested" / "data" / "memory.json"

    store = JsonMemoryStore(path)

    assert store.list() == []
    assert path.is_file()
    assert path.with_name("memory.json.lock").is_file()


@pytest.mark.parametrize(
    "store_type",
    (JsonConversationStore, JsonMemoryStore, JsonPreferencesStore),
)
def test_invalid_json_is_rejected_without_overwrite(tmp_path, store_type) -> None:
    path = tmp_path / "invalid.json"
    original = "{ invalid json"
    path.write_text(original, encoding="utf-8")

    with pytest.raises(JsonStorageError, match="JSON invalide"):
        store_type(path)

    assert path.read_text(encoding="utf-8") == original


def test_non_object_json_is_rejected(tmp_path) -> None:
    path = tmp_path / "conversations.json"
    path.write_text("[]", encoding="utf-8")

    with pytest.raises(JsonStorageError, match="doit être un objet"):
        JsonConversationStore(path)


def test_invalid_conversation_schema_is_preserved(tmp_path) -> None:
    path = tmp_path / "conversations.json"
    original = (
        '{"conversations":[{"id":"test","title":"Test","messages":'
        '[{"role":"invalid","content":"text"}]}]}'
    )
    path.write_text(original, encoding="utf-8")

    with pytest.raises(JsonStorageError, match="role"):
        JsonConversationStore(path)

    assert path.read_text(encoding="utf-8") == original


def test_invalid_memory_schema_is_rejected(tmp_path) -> None:
    path = tmp_path / "memory.json"
    original = '{"facts":[1],"preferences":{}}'
    path.write_text(original, encoding="utf-8")

    with pytest.raises(JsonStorageError, match="facts"):
        JsonMemoryStore(path)

    assert path.read_text(encoding="utf-8") == original


def test_failed_atomic_write_preserves_original_file(tmp_path, monkeypatch) -> None:
    path = tmp_path / "conversations.json"
    store = JsonConversationStore(path)
    original = path.read_bytes()

    def fail_replace(source, destination) -> None:
        raise OSError("simulated replace failure")

    monkeypatch.setattr("modules.storage.os.replace", fail_replace)

    with pytest.raises(JsonStorageError, match="Impossible d'écrire"):
        store.create("Test")

    assert path.read_bytes() == original
    assert not any(
        item.name.startswith(f".{path.name}.") and item.suffix == ".tmp"
        for item in tmp_path.iterdir()
    )


def test_memory_updates_from_store_instances_are_serialized(tmp_path) -> None:
    path = tmp_path / "memory.json"
    stores = [JsonMemoryStore(path), JsonMemoryStore(path)]
    facts = [f"fact-{index}" for index in range(40)]

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(
            executor.map(
                lambda index: stores[index % len(stores)].add(facts[index]),
                range(len(facts)),
            )
        )

    assert all(results)
    assert set(JsonMemoryStore(path).list()) == set(facts)


def test_memory_updates_are_serialized_across_processes(tmp_path) -> None:
    path = tmp_path / "memory.json"
    JsonMemoryStore(path)
    script = (
        "import sys; from modules.storage import JsonMemoryStore; "
        "store = JsonMemoryStore(sys.argv[1]); "
        "[store.add(f'{sys.argv[2]}-{index}') for index in range(25)]"
    )

    def write_facts(prefix: str) -> None:
        subprocess.run(
            [sys.executable, "-c", script, str(path), prefix],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=Path(__file__).resolve().parents[1],
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        list(executor.map(write_facts, ("first", "second")))

    facts = JsonMemoryStore(path).list()
    assert len(facts) == 50
    assert len(set(facts)) == 50


def test_assistant_stores_persist_under_configured_data_directory(
    tmp_path, monkeypatch
) -> None:
    assistant.get_stores.clear()
    monkeypatch.setattr(assistant, "DATA_DIRECTORY", tmp_path)

    try:
        conversation_store, memory_store, preferences_store = (
            assistant.get_stores()
        )
        conversation = conversation_store.create("Chemin de données")
        memory_store.add("Préférence de test")
        preferences_store.save({"display_name": "Test"})

        assert conversation_store.path == tmp_path / "conversations.json"
        assert memory_store.path == tmp_path / "memory.json"
        assert preferences_store.path == tmp_path / "memory.json"
        assert (
            JsonConversationStore(conversation_store.path).get(conversation.id)
            is not None
        )
        assert JsonMemoryStore(memory_store.path).list() == [
            "Préférence de test"
        ]
        assert (
            JsonPreferencesStore(preferences_store.path).load()["display_name"]
            == "Test"
        )
    finally:
        assistant.get_stores.clear()


def test_assistant_reports_invalid_json_without_replacing_file(
    tmp_path, monkeypatch
) -> None:
    path = tmp_path / "conversations.json"
    original = "{ invalid json"
    path.write_text(original, encoding="utf-8")
    assistant.get_stores.clear()
    monkeypatch.setattr(assistant, "DATA_DIRECTORY", tmp_path)

    try:
        script = "from modules.assistant import render_assistant\nrender_assistant()"
        app = AppTest.from_string(script).run()
    finally:
        assistant.get_stores.clear()

    assert not app.exception
    assert app.error
    assert "JSON invalide" in app.error[0].value
    assert path.read_text(encoding="utf-8") == original


def test_conversation_serialization_round_trip() -> None:
    conversation = Conversation.create("Architecture")
    conversation.add_message("user", "Explique le projet")

    restored = Conversation.from_dict(conversation.to_dict())

    assert restored.id == conversation.id
    assert restored.messages[0].content == "Explique le projet"


def test_submitted_messages_stay_in_chat_history_container(tmp_path) -> None:
    conversation_store = JsonConversationStore(tmp_path / "conversations.json")
    memory_store = JsonMemoryStore(tmp_path / "memory.json")
    preferences_store = JsonPreferencesStore(tmp_path / "memory.json")
    conversation_store.create()

    class FakeProvider:
        def ensure_running(self):
            return True

        def list_models(self):
            return ["phi3:latest"]

        def model_is_available(self, model):
            return True

        def stream(self, messages, model="phi3"):
            yield "Réponse de test"

    stores = (conversation_store, memory_store, preferences_store)
    script = "from modules.assistant import render_assistant\nrender_assistant()"
    with patch("modules.assistant.get_stores", return_value=stores), patch(
        "modules.assistant.OllamaProvider", FakeProvider
    ):
        app = AppTest.from_string(script).run()
        app.text_area(key="assistant_user_message").set_value("Question de test")
        app.form_submit_button(key="send_assistant_message").click().run(timeout=15)

    assert not app.exception
    assert len(app.container(key="assistant_chat_history").chat_message) == 2
    persisted = conversation_store.list()[0]
    assert [(message.role, message.content) for message in persisted.messages] == [
        ("user", "Question de test"),
        ("assistant", "Réponse de test"),
    ]


@pytest.mark.parametrize("agent_id", ["general", "business"])
def test_new_conversation_isolated_with_duplicate_titles(tmp_path, agent_id) -> None:
    conversation_store = JsonConversationStore(tmp_path / "conversations.json")
    memory_store = JsonMemoryStore(tmp_path / "memory.json")
    preferences_store = JsonPreferencesStore(tmp_path / "memory.json")
    preferences_store.save({"context_messages": 5})
    memory_store.add("Ancien contexte marketing mémorisé")
    memory_before = (tmp_path / "memory.json").read_bytes()
    old_conversations = []
    for content in ("Ancienne campagne marketing", "Ancien produit marketing"):
        conversation = conversation_store.create()
        conversation.add_message("user", content)
        conversation_store.save(conversation)
        old_conversations.append(conversation)
    calls = []

    class FakeProvider:
        name = "test"

        def ensure_running(self):
            return True

        def is_available(self):
            return True

        def list_models(self):
            return ["phi3:latest"]

        def model_is_available(self, model):
            return True

        def stream(self, messages, model="phi3"):
            calls.append(messages)
            yield "Nouvelle réponse"

    stores = (conversation_store, memory_store, preferences_store)
    script = "from modules.assistant import render_assistant\nrender_assistant()"
    with patch("modules.assistant.get_stores", return_value=stores), patch(
        "modules.assistant.OllamaProvider", FakeProvider
    ):
        app = AppTest.from_string(script, default_timeout=15).run()
        app.selectbox(key="selected_conversation_id").select(
            old_conversations[0].id
        ).run()
        assert app.session_state["assistant_conversation_id"] == old_conversations[0].id
        app.selectbox(key="selected_conversation_id").select(
            old_conversations[1].id
        ).run()
        assert app.session_state["assistant_conversation_id"] == old_conversations[1].id

        next(
            button for button in app.button if button.label == "Nouvelle conversation"
        ).click().run()
        new_id = app.session_state["assistant_conversation_id"]
        assert new_id not in {conversation.id for conversation in old_conversations}
        assert app.selectbox(key="selected_conversation_id").value == new_id
        new_conversation = conversation_store.get(new_id)
        assert new_conversation is not None
        assert not new_conversation.messages

        app.run()
        assert app.session_state["assistant_conversation_id"] == new_id
        assert app.selectbox(key="selected_conversation_id").value == new_id
        app.selectbox(key="assistant_agent_id").select(agent_id).run()
        app.text_area(key="assistant_user_message").set_value("Question nouvelle")
        app.form_submit_button(key="send_assistant_message").click().run()

        assert not app.exception
        assert app.session_state["assistant_conversation_id"] == new_id
        assert app.selectbox(key="selected_conversation_id").value == new_id
        app.run()
        assert not app.exception
        assert app.session_state["assistant_conversation_id"] == new_id
        assert app.selectbox(key="selected_conversation_id").value == new_id

    assert len(calls) == 1
    assert [message["role"] for message in calls[0]] == ["system", "user"]
    assert calls[0][1]["content"] == "Question nouvelle"
    assert all("marketing" not in message["content"].lower() for message in calls[0])
    for old in old_conversations:
        restored = conversation_store.get(old.id)
        assert restored is not None
        assert restored.to_dict() == old.to_dict()
    new_conversation = conversation_store.get(new_id)
    assert new_conversation is not None
    assert [(message.role, message.content) for message in new_conversation.messages] == [
        ("user", "Question nouvelle"),
        ("assistant", "Nouvelle réponse"),
    ]
    assert (tmp_path / "memory.json").read_bytes() == memory_before
    assert memory_store.list() == ["Ancien contexte marketing mémorisé"]


@pytest.mark.parametrize("agent", AGENTS, ids=lambda agent: agent.id)
def test_agent_selection_streams_and_preserves_v1_data(tmp_path, agent) -> None:
    conversation_store = JsonConversationStore(tmp_path / "conversations.json")
    memory_store = JsonMemoryStore(tmp_path / "memory.json")
    preferences_store = JsonPreferencesStore(tmp_path / "memory.json")
    preferences_store.save(
        {"language": "Français", "response_tone": "Technique", "context_messages": 2}
    )
    memory_store.add("Préférence de test")
    memory_before = (tmp_path / "memory.json").read_bytes()
    conversation = conversation_store.create("Conversation V1")
    conversation.add_message("user", "Ancienne question")
    conversation.add_message("assistant", "Ancienne réponse")
    conversation_store.save(conversation)
    calls = []

    class FakeProvider:
        name = "test"

        def ensure_running(self):
            return True

        def is_available(self):
            return True

        def list_models(self):
            return ["phi3:latest"]

        def model_is_available(self, model):
            return True

        def stream(self, messages, model="phi3"):
            calls.append((messages, model))
            yield "Réponse "
            yield "spécialisée"

    stores = (conversation_store, memory_store, preferences_store)
    script = "from modules.assistant import render_assistant\nrender_assistant()"
    with patch("modules.assistant.get_stores", return_value=stores), patch(
        "modules.assistant.OllamaProvider", FakeProvider
    ):
        app = AppTest.from_string(script).run()
        assert app.selectbox(key="assistant_agent_id").value == "general"
        app.selectbox(key="assistant_agent_id").select(agent.id).run()
        app.text_input(key="ollama_model").set_value("modele-test")
        app.text_area(key="assistant_user_message").set_value("Nouvelle question")
        app.form_submit_button(key="send_assistant_message").click().run()
        assert not app.exception
        assert app.selectbox(key="assistant_agent_id").value == agent.id

        restored_app = AppTest.from_string(script).run()
        assert not restored_app.exception
        assert restored_app.selectbox(key="assistant_agent_id").value == "general"
        assert len(restored_app.container(key="assistant_chat_history").chat_message) == 4

    assert len(calls) == 1
    messages, model = calls[0]
    assert model == "modele-test"
    assert "BAH AI ASSISTANT" in messages[0]["content"]
    assert "modele-test" in messages[0]["content"]
    assert "via Ollama" in messages[0]["content"]
    assert agent.instructions in messages[0]["content"]
    assert "Préférence de test" not in messages[0]["content"]
    assert "Ton : Technique" in messages[0]["content"]
    assert messages[1:] == [
        {"role": "assistant", "content": "Ancienne réponse"},
        {"role": "user", "content": "Nouvelle question"},
    ]
    restored = JsonConversationStore(tmp_path / "conversations.json").get(
        conversation.id
    )
    assert restored is not None
    assert [(message.role, message.content) for message in restored.messages] == [
        ("user", "Ancienne question"),
        ("assistant", "Ancienne réponse"),
        ("user", "Nouvelle question"),
        ("assistant", "Réponse spécialisée"),
    ]
    assert (tmp_path / "memory.json").read_bytes() == memory_before


@pytest.mark.parametrize(
    ("model", "question"),
    [
        ("phi3", "Qui es-tu ?"),
        ("autre-modele", "Quel modèle utilises-tu ?"),
    ],
)
def test_general_assistant_excludes_saved_memory_from_system_message(
    tmp_path, model, question
) -> None:
    conversation_store = JsonConversationStore(tmp_path / "conversations.json")
    memory_store = JsonMemoryStore(tmp_path / "memory.json")
    preferences_store = JsonPreferencesStore(tmp_path / "memory.json")
    memory_store.add("Préférence V1")
    calls = []

    class FakeProvider:
        def ensure_running(self):
            return True

        def list_models(self):
            return ["phi3:latest"]

        def model_is_available(self, model):
            return True

        def stream(self, messages, model="phi3"):
            calls.append((messages, model))
            yield "Réponse V1"

    stores = (conversation_store, memory_store, preferences_store)
    script = "from modules.assistant import render_assistant\nrender_assistant()"
    with patch("modules.assistant.get_stores", return_value=stores), patch(
        "modules.assistant.OllamaProvider", FakeProvider
    ):
        app = AppTest.from_string(script).run()
        app.text_input(key="ollama_model").set_value(model)
        app.text_area(key="assistant_user_message").set_value(question)
        app.form_submit_button(key="send_assistant_message").click().run()

    assert not app.exception
    assert len(calls) == 1
    messages, selected_model = calls[0]
    assert selected_model == model
    assert "BAH AI ASSISTANT" in messages[0]["content"]
    assert model in messages[0]["content"]
    assert "via Ollama" in messages[0]["content"]
    assert (
        f"J'utilise le modèle {model}, exécuté localement via Ollama"
        in messages[0]["content"]
    )
    assert "Langue : Français. Ton : Professionnel." in messages[0]["content"]
    assert "Préférence V1" not in messages[0]["content"]
    assert messages[1:] == [{"role": "user", "content": question}]
    assert memory_store.list() == ["Préférence V1"]


def test_saving_context_preferences_updates_model_without_widget_error(tmp_path) -> None:
    conversation_store = JsonConversationStore(tmp_path / "conversations.json")
    memory_store = JsonMemoryStore(tmp_path / "memory.json")
    preferences_store = JsonPreferencesStore(tmp_path / "memory.json")
    conversation_store.create()

    class FakeProvider:
        def ensure_running(self):
            return False

    stores = (conversation_store, memory_store, preferences_store)
    script = "from modules.assistant import render_assistant\nrender_assistant()"
    with patch("modules.assistant.get_stores", return_value=stores), patch(
        "modules.assistant.OllamaProvider", FakeProvider
    ):
        app = AppTest.from_string(script, default_timeout=15).run()
        app.slider(key="pref_context_messages").set_value(5)
        app.text_input(key="pref_ollama_model").set_value("test-model")
        assert preferences_store.load()["context_messages"] == 20
        app.form_submit_button[0].click().run()

        assert not app.exception
        assert preferences_store.load()["context_messages"] == 5
        assert app.text_input(key="ollama_model").value == "test-model"
        assert app.slider(key="pref_context_messages").value == 5
        assert app.success

        with patch.object(
            preferences_store, "save", side_effect=JsonStorageError("test")
        ):
            app.slider(key="pref_context_messages").set_value(7)
            app.form_submit_button[0].click().run()
        assert not app.exception
        assert preferences_store.load()["context_messages"] == 5
        assert app.text_input(key="ollama_model").value == "test-model"
        assert any("Erreur de stockage local" in error.value for error in app.error)
        assert not app.success


def test_switching_agents_reuses_conversation_context(tmp_path) -> None:
    conversation_store = JsonConversationStore(tmp_path / "conversations.json")
    memory_store = JsonMemoryStore(tmp_path / "memory.json")
    preferences_store = JsonPreferencesStore(tmp_path / "memory.json")
    calls = []

    class FakeProvider:
        name = "test"

        def ensure_running(self):
            return True

        def is_available(self):
            return True

        def list_models(self):
            return ["phi3:latest"]

        def model_is_available(self, model):
            return True

        def stream(self, messages, model="phi3"):
            calls.append(messages)
            yield "Réponse de test"

    stores = (conversation_store, memory_store, preferences_store)
    script = "from modules.assistant import render_assistant\nrender_assistant()"
    with patch("modules.assistant.get_stores", return_value=stores), patch(
        "modules.assistant.OllamaProvider", FakeProvider
    ):
        app = AppTest.from_string(script).run()
        app.selectbox(key="assistant_agent_id").select("programmation").run()
        app.text_area(key="assistant_user_message").set_value("Question technique")
        app.form_submit_button(key="send_assistant_message").click().run()
        app.selectbox(key="assistant_agent_id").select("business").run()
        app.text_area(key="assistant_user_message").set_value("Question business")
        app.form_submit_button(key="send_assistant_message").click().run()

    assert not app.exception
    assert len(calls) == 2
    assert "agent Programmation" in calls[0][0]["content"]
    assert "agent Business" in calls[1][0]["content"]
    assert calls[1][1:] == [
        {"role": "user", "content": "Question technique"},
        {"role": "assistant", "content": "Réponse de test"},
        {"role": "user", "content": "Question business"},
    ]


def test_agent_reports_provider_failure(tmp_path) -> None:
    conversation_store = JsonConversationStore(tmp_path / "conversations.json")
    memory_store = JsonMemoryStore(tmp_path / "memory.json")
    preferences_store = JsonPreferencesStore(tmp_path / "memory.json")

    class FakeProvider:
        name = "test"

        def ensure_running(self):
            return True

        def is_available(self):
            return False

        def list_models(self):
            return ["phi3:latest"]

        def model_is_available(self, model):
            return True

        def stream(self, messages, model="phi3"):
            raise AssertionError("Un fournisseur indisponible ne doit pas être appelé.")

    stores = (conversation_store, memory_store, preferences_store)
    script = "from modules.assistant import render_assistant\nrender_assistant()"
    with patch("modules.assistant.get_stores", return_value=stores), patch(
        "modules.assistant.OllamaProvider", FakeProvider
    ):
        app = AppTest.from_string(script).run()
        app.selectbox(key="assistant_agent_id").select("business").run()
        app.text_area(key="assistant_user_message").set_value("Question")
        app.form_submit_button(key="send_assistant_message").click().run()

    assert not app.exception
    assert any("indisponible" in error.value for error in app.error)
    messages = conversation_store.list()[0].messages
    assert messages[0].content == "Question"
    assert "indisponible" in messages[1].content


def test_conversation_title() -> None:
    assert conversation_title("  Explique   Python  ") == "Explique Python"
    assert conversation_title("") == "Nouvelle conversation"


def test_preferences_save_and_reload(tmp_path) -> None:
    store = JsonPreferencesStore(tmp_path / "memory.json")

    saved = store.save(
        {
            "display_name": "Thierno",
            "language": "Français",
            "response_tone": "Technique",
            "ollama_model": "qwen2.5",
            "context_messages": 12,
        }
    )

    assert saved["display_name"] == "Thierno"
    assert JsonPreferencesStore(tmp_path / "memory.json").load() == saved


def test_memory_store_preserves_preferences(tmp_path) -> None:
    preferences_store = JsonPreferencesStore(tmp_path / "memory.json")
    preferences_store.save({"display_name": "Bah"})
    memory_store = JsonMemoryStore(tmp_path / "memory.json")

    memory_store.add("Préfère Python")

    assert memory_store.list() == ["Préfère Python"]
    assert (
        JsonPreferencesStore(tmp_path / "memory.json").load()["display_name"]
        == "Bah"
    )
