"""Social media content features."""

from __future__ import annotations

import streamlit as st


PLATFORMS = ("LinkedIn", "Facebook", "Instagram", "TikTok")


def build_social_post(topic: str, platform: str, tone: str) -> str:
    """Build a platform-oriented publication draft."""
    topic = topic.strip()
    if not topic:
        return ""
    return (
        f"Plateforme : {platform}\n"
        f"Ton : {tone}\n"
        f"Sujet : {topic}\n\n"
        "Accroche : présentez une idée claire en une phrase.\n"
        "Développement : expliquez trois points utiles.\n"
        "Call to action : invitez l'audience à répondre ou à partager."
    )


def render_social_media() -> None:
    st.header("Réseaux sociaux")

    platform = st.selectbox("Plateforme", PLATFORMS, key="social_platform")
    tone = st.selectbox(
        "Ton",
        ["Professionnel", "Inspirant", "Éducatif", "Promotional"],
        key="social_tone",
    )
    topic = st.text_area(
        "Sujet",
        placeholder="Annonce, conseil, lancement ou actualité...",
        key="social_topic",
    )

    if st.button("Préparer la publication", type="primary"):
        post = build_social_post(topic, platform, tone)
        if post:
            st.subheader("Brouillon")
            st.markdown(post)
        else:
            st.warning("Ajoutez un sujet avant de générer la publication.")
