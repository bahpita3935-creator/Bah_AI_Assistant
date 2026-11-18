"""Business planning features."""

from __future__ import annotations

import streamlit as st


def build_business_brief(name: str, problem: str, audience: str) -> str:
    """Build a basic business brief."""
    name = name.strip()
    problem = problem.strip()
    audience = audience.strip()
    if not all((name, problem, audience)):
        return ""
    return (
        f"Projet : {name}\n"
        f"Problème : {problem}\n"
        f"Client cible : {audience}\n"
        "Prochaine étape : définir la proposition de valeur, "
        "le modèle économique, les coûts, les indicateurs et un pilote à 30 jours."
    )


def render_business() -> None:
    st.header("Business")

    name = st.text_input("Nom du projet", key="business_name")
    problem = st.text_area("Problème à résoudre", key="business_problem")
    audience = st.text_input("Client cible", key="business_audience")

    if st.button("Créer le brief", type="primary"):
        brief = build_business_brief(name, problem, audience)
        if brief:
            st.subheader("Synthèse")
            st.markdown(brief)
        else:
            st.warning("Complétez le nom, le problème et le client cible.")
