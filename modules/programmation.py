"""Programming assistance features."""

from __future__ import annotations

import streamlit as st


def build_programming_prompt(language: str, objective: str) -> str:
    """Build a concise implementation prompt."""
    objective = objective.strip()
    if not objective:
        return ""
    return (
        f"Agis comme un développeur senior. "
        f"Implémente cet objectif avec {language} : {objective}\n"
        "Respecte les bonnes pratiques, ajoute la gestion des erreurs, "
        "les types et des tests pertinents."
    )


def render_programmation() -> None:
    st.header("Programmation")

    language = st.selectbox(
        "Langage ou technologie",
        ["Python", "SQL", "Flutter", "Node.js", "HTML/CSS"],
        key="programming_language",
    )
    objective = st.text_area(
        "Objectif",
        placeholder="Décrire la fonctionnalité à concevoir...",
        height=180,
        key="programming_objective",
    )

    if st.button("Préparer la consigne", type="primary"):
        prompt = build_programming_prompt(language, objective)
        if prompt:
            st.subheader("Consigne technique")
            st.code(prompt, language="text")
        else:
            st.warning("Décrivez d'abord l'objectif à réaliser.")
