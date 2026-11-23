"""Build specialist context and stream responses through an AI provider."""

from collections.abc import Iterator, Sequence

from agents.registry import get_agent
from modules.ai_provider import AIProvider
from modules.models import Message


def identity_instruction(model: str) -> str:
    """Describe the product identity and its selected local model."""
    return (
        "Tu es BAH AI ASSISTANT, le nom du produit. Ton identité n'est ni le "
        "modèle ni Ollama. "
        f"Le modèle sélectionné est {model.strip()}, exécuté localement via Ollama. "
        "Si on demande qui tu es, réponds : Je suis BAH AI ASSISTANT. "
        "Si on demande ton modèle ou ton moteur, réponds : "
        f"J'utilise le modèle {model.strip()}, exécuté localement via Ollama. "
        "Ne prétends pas être un autre assistant ou modèle. "
        "Réponds brièvement par défaut."
    )


def build_messages(
    agent_id: str,
    history: Sequence[Message],
    *,
    facts: Sequence[str],
    language: str,
    response_tone: str,
    context_messages: int,
    model: str,
) -> list[dict[str, str]]:
    """Build the system instruction and bounded conversation context."""
    agent = get_agent(agent_id)
    if not 1 <= context_messages <= 100:
        raise ValueError("La limite de contexte doit être comprise entre 1 et 100.")

    system = f"{identity_instruction(model)} {agent.instructions}"
    if facts:
        system += " Mémoire locale de l'utilisateur : " + " ".join(facts) + "."
    system += f" Langue : {language}. Ton : {response_tone}."
    return [
        {"role": "system", "content": system},
        *(
            {"role": message.role, "content": message.content}
            for message in history[-context_messages:]
        ),
    ]


def stream_response(
    provider: AIProvider,
    agent_id: str,
    history: Sequence[Message],
    *,
    facts: Sequence[str],
    language: str,
    response_tone: str,
    context_messages: int,
    model: str = "phi3",
) -> Iterator[str]:
    """Stream a response without changing the conversation or memory."""
    if not model.strip():
        raise ValueError("Le nom du modèle ne peut pas être vide.")
    messages = build_messages(
        agent_id,
        history,
        facts=facts,
        language=language,
        response_tone=response_tone,
        context_messages=context_messages,
        model=model.strip(),
    )
    if not provider.is_available():
        raise RuntimeError(f"Le fournisseur IA '{provider.name}' est indisponible.")
    return provider.stream(messages, model=model.strip())
