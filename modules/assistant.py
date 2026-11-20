"""Assistant page backed by local storage and an Ollama provider."""

from __future__ import annotations

import urllib.error
import json
from pathlib import Path

import streamlit as st

from modules.ai_provider import OllamaProvider
from modules.storage import (
    JsonConversationStore,
    JsonMemoryStore,
    JsonPreferencesStore,
    JsonStorageError,
)


PROJECT_DIRECTORY = Path(__file__).resolve().parents[1]
DATA_DIRECTORY = PROJECT_DIRECTORY / "data"
CONVERSATIONS_FILE = "conversations.json"
MEMORY_FILE = "memory.json"


@st.cache_resource
def get_stores() -> tuple[
    JsonConversationStore,
    JsonMemoryStore,
    JsonPreferencesStore,
]:
    return (
        JsonConversationStore(DATA_DIRECTORY / CONVERSATIONS_FILE),
        JsonMemoryStore(DATA_DIRECTORY / MEMORY_FILE),
        JsonPreferencesStore(DATA_DIRECTORY / MEMORY_FILE),
    )


def conversation_title(prompt: str) -> str:
    """Create a concise local title for a new conversation."""
    prompt = " ".join(prompt.strip().split())
    if not prompt:
        return "Nouvelle conversation"
    return prompt[:60] + ("..." if len(prompt) > 60 else "")


def start_new_conversation() -> None:
    conversation_store, _, _ = get_stores()
    conversation = conversation_store.create()
    st.session_state.assistant_conversation_id = conversation.id
    st.session_state.selected_conversation_id = conversation.id


def delete_active_conversation() -> None:
    conversation_store, _, _ = get_stores()
    conversation_store.delete(st.session_state.assistant_conversation_id)
    remaining = conversation_store.list()
    replacement = remaining[0] if remaining else conversation_store.create()
    st.session_state.assistant_conversation_id = replacement.id
    st.session_state.selected_conversation_id = replacement.id


def delete_memory_fact(fact: str) -> None:
    _, memory_store, _ = get_stores()
    memory_store.remove(fact)


def render_assistant() -> None:
    try:
        _render_assistant()
    except JsonStorageError as exc:
        st.error(f"Erreur de stockage local : {exc}")


def _render_assistant() -> None:
    st.header("Assistant")
    conversation_store, memory_store, preferences_store = get_stores()
    provider = OllamaProvider()
    ollama_available = provider.ensure_running()

    if "assistant_preferences_loaded" not in st.session_state:
        st.session_state.user_preferences = preferences_store.load()
        st.session_state.assistant_preferences_loaded = True

    preferences = st.session_state.user_preferences
    welcome_name = preferences["display_name"]
    if welcome_name:
        st.caption(f"Préférences chargées pour {welcome_name}")

    if "assistant_conversation_id" not in st.session_state:
        conversations = conversation_store.list()
        active = conversations[0] if conversations else conversation_store.create()
        st.session_state.assistant_conversation_id = active.id

    conversations = conversation_store.list()
    if conversations:
        selected_id = st.selectbox(
            "Conversation",
            [item.id for item in conversations],
            index=next(
                (
                    index
                    for index, item in enumerate(conversations)
                    if item.id == st.session_state.assistant_conversation_id
                ),
                0,
            ),
            format_func=lambda conversation_id: next(
                (
                    item.title
                    for item in conversations
                    if item.id == conversation_id
                ),
                "Conversation",
            ),
            key="selected_conversation_id",
            help="Reprendre une conversation enregistrée localement.",
        )
        st.session_state.assistant_conversation_id = selected_id

    conversation = conversation_store.get(
        st.session_state.assistant_conversation_id
    )
    if conversation is None:
        conversation = conversation_store.create()
        st.session_state.assistant_conversation_id = conversation.id

    left, right = st.columns([3, 1])
    with left:
        model = st.text_input(
            "Modèle Ollama",
            value=preferences["ollama_model"],
            key="ollama_model",
            help="Nom du modèle installé sur votre machine Ollama.",
        )
    with right:
        st.caption("Statut IA")
        if ollama_available:
            st.success("✅ Ollama connecté")
        else:
            st.error("❌ Ollama déconnecté")

    if ollama_available:
        available_models = provider.list_models()
        if available_models:
            st.caption("Modèles disponibles : " + ", ".join(available_models))
    else:
        st.warning(
            "Ollama n'est pas lancé sur cette machine. "
            "Démarrez Ollama, puis utilisez le bouton Actualiser."
        )
        st.button(
            "Actualiser le statut",
            icon=":material/refresh:",
            key="refresh_ollama_status",
        )

    with st.expander("Préférences utilisateur"):
        with st.form("assistant_preferences_form"):
            display_name = st.text_input(
                "Nom affiché",
                value=preferences["display_name"],
                key="pref_display_name",
            )
            language = st.selectbox(
                "Langue",
                ("Français", "English"),
                index=0 if preferences["language"] == "Français" else 1,
                key="pref_language",
            )
            response_tone = st.selectbox(
                "Ton des réponses",
                ("Professionnel", "Simple", "Technique"),
                index=("Professionnel", "Simple", "Technique").index(
                    preferences["response_tone"]
                ),
                key="pref_response_tone",
            )
            preference_model = st.text_input(
                "Modèle Ollama préféré",
                value=preferences["ollama_model"],
                key="pref_ollama_model",
            )
            context_messages = st.slider(
                "Messages récents envoyés au modèle",
                min_value=1,
                max_value=100,
                value=int(preferences["context_messages"]),
                key="pref_context_messages",
            )
            save_preferences = st.form_submit_button(
                "Sauvegarder les préférences",
                icon=":material/save:",
                width="stretch",
            )

        if save_preferences:
            saved_preferences = preferences_store.save(
                {
                    "display_name": display_name,
                    "language": language,
                    "response_tone": response_tone,
                    "ollama_model": preference_model,
                    "context_messages": context_messages,
                }
            )
            st.session_state.user_preferences = saved_preferences
            st.session_state.ollama_model = saved_preferences["ollama_model"]
            st.success("Préférences sauvegardées.")

    toolbar_left, toolbar_right = st.columns([1, 1])
    with toolbar_left:
        st.button(
            "Nouvelle conversation",
            icon=":material/add:",
            width="stretch",
            on_click=start_new_conversation,
        )
    with toolbar_right:
        st.button(
            "Supprimer la conversation",
            icon=":material/delete:",
            width="stretch",
            on_click=delete_active_conversation,
        )

    chat_history = st.container(key="assistant_chat_history")
    with chat_history:
        for message in conversation.messages:
            with st.chat_message(message.role):
                st.markdown(message.content)

    with st.form("assistant_message_form", clear_on_submit=True):
        prompt = st.text_area(
            "Votre message",
            key="assistant_user_message",
            height=120,
            placeholder="Posez une question ou décrivez votre demande...",
        )
        sent = st.form_submit_button(
            "Envoyer",
            icon=":material/send:",
            type="primary",
            key="send_assistant_message",
            width="stretch",
        )

    if sent:
        prompt = prompt.strip()

    if sent and prompt:
        conversation.add_message("user", prompt)
        if conversation.title == "Nouvelle conversation":
            conversation.title = conversation_title(prompt)
        conversation_store.save(conversation)
        with chat_history:
            with st.chat_message("user"):
                st.markdown(prompt)

        if ollama_available:
            with chat_history:
                assistant_message = st.chat_message("assistant")
            with assistant_message:
                try:
                    if not provider.model_is_available(model):
                        response = (
                            f"Le modèle '{model}' n'est pas installé dans Ollama. "
                            f"Installez-le avec : ollama pull {model}"
                        )
                        st.error(response)
                        conversation.add_message("assistant", response)
                        conversation_store.save(conversation)
                        st.stop()

                    facts = memory_store.list()
                    messages = []
                    if facts:
                        messages.append(
                            {
                                "role": "system",
                                "content": "Mémoire locale de l'utilisateur : "
                                + " ".join(facts)
                                + f". Langue : {preferences['language']}."
                                + f" Ton : {preferences['response_tone']}.",
                            }
                        )
                    else:
                        messages.append(
                            {
                                "role": "system",
                                "content": (
                                    f"Langue : {preferences['language']}."
                                    f" Ton : {preferences['response_tone']}."
                                ),
                            }
                        )
                    messages.extend(
                        {
                            "role": message.role,
                            "content": message.content,
                        }
                        for message in conversation.messages[
                            -int(preferences["context_messages"]):
                        ]
                    )
                    response = st.write_stream(
                        provider.stream(messages, model=model)
                    )
                    conversation.add_message("assistant", response)
                    conversation_store.save(conversation)
                except (
                    urllib.error.URLError,
                    TimeoutError,
                    json.JSONDecodeError,
                    RuntimeError,
                ) as exc:
                    response = f"Impossible de contacter Ollama : {exc}"
                    st.error(response)
                    conversation.add_message("assistant", response)
                    conversation_store.save(conversation)
        else:
            with chat_history:
                assistant_message = st.chat_message("assistant")
            with assistant_message:
                response = (
                    "Ollama n'est pas disponible sur cette machine. "
                    "Installez-le, démarrez-le, puis installez un modèle "
                    "avec `ollama pull phi3`."
                )
                st.warning(response)
                conversation.add_message("assistant", response)
                conversation_store.save(conversation)

    with st.expander("Mémoire locale"):
        fact = st.text_input(
            "Ajouter une information retenue",
            key="assistant_memory_fact",
        )
        if st.button("Enregistrer", icon=":material/save:", key="save_memory"):
            if memory_store.add(fact):
                st.success("Information enregistrée.")
            else:
                st.info("Ajoutez une information nouvelle.")

        for stored_fact in memory_store.list():
            columns = st.columns([5, 1])
            columns[0].write(stored_fact)
            columns[1].button(
                "Supprimer",
                key=f"delete_memory_{stored_fact}",
                width="stretch",
                on_click=delete_memory_fact,
                args=(stored_fact,),
            )
