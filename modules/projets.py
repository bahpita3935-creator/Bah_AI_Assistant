"""BAH TECH GROUP project portfolio."""

from __future__ import annotations

import streamlit as st


PROJECTS = (
    {"name": "Bah Immo Gestion", "status": "En développement"},
    {"name": "Bahora Store", "status": "En conception"},
    {"name": "BhantalHub SaaS", "status": "En développement"},
    {"name": "Agro Transit Hub", "status": "En étude"},
    {"name": "Bah Studio AI", "status": "En construction"},
)


def render_projets() -> None:
    st.header("Projets BAH TECH")

    for project in PROJECTS:
        with st.container(border=True):
            left, right = st.columns([3, 1])
            left.subheader(project["name"])
            right.badge(project["status"], color="blue")
