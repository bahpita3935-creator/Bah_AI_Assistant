"""Specialist roles available to the assistant."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Agent:
    id: str
    name: str
    instructions: str


AGENTS = (
    Agent(
        id="programmation",
        name="Programmation",
        instructions=(
            "Tu es l'agent Programmation. Aide à concevoir, expliquer et examiner "
            "du code. Propose des solutions et des tests adaptés, sans exécuter de code."
        ),
    ),
    Agent(
        id="business",
        name="Business",
        instructions=(
            "Tu es l'agent Business. Aide à analyser les idées, les marchés et les "
            "modèles économiques. Distingue les faits des hypothèses."
        ),
    ),
    Agent(
        id="reseaux_sociaux",
        name="Réseaux sociaux",
        instructions=(
            "Tu es l'agent Réseaux sociaux. Prépare des brouillons adaptés à la "
            "plateforme et au ton demandés, sans publier de contenu."
        ),
    ),
    Agent(
        id="bah_tech_group",
        name="BAH TECH GROUP",
        instructions=(
            "Tu es l'agent BAH TECH GROUP. Aide à organiser et analyser les projets "
            "à partir des informations fournies. Signale les informations manquantes "
            "et n'invente pas l'état des projets."
        ),
    ),
)


def get_agent(agent_id: str) -> Agent:
    """Return a registered agent or reject an unknown identifier."""
    for agent in AGENTS:
        if agent.id == agent_id:
            return agent
    raise ValueError(f"Agent inconnu : {agent_id}")
