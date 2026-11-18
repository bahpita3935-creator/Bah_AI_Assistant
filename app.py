import streamlit as st

from modules.assistant import render_assistant
from modules.business import render_business
from modules.programmation import render_programmation
from modules.projets import render_projets
from modules.social_media import render_social_media

st.set_page_config(
    page_title="BAH AI ASSISTANT",
    page_icon=":material/smart_toy:",
    layout="wide",
)


def render_home() -> None:
    st.header("Bienvenue")
    st.write(
        "Assistant IA personnel de BAH TECH GROUP pour la programmation, "
        "les activités business, les réseaux sociaux et la gestion de projets."
    )

    columns = st.columns(4)
    cards = (
        (pages[1], "chat"),
        (pages[2], "code"),
        (pages[3], "store"),
        (pages[5], "rocket_launch"),
    )
    for column, (target_page, icon) in zip(columns, cards):
        column.page_link(
            target_page,
            label=target_page.title,
            icon=f":material/{icon}:",
        )


pages = [
    st.Page(
        render_home,
        title="Accueil",
        icon=":material/home:",
        url_path="accueil",
        help="Présentation générale de BAH AI Assistant.",
    ),
    st.Page(
        render_assistant,
        title="Assistant",
        icon=":material/smart_toy:",
        url_path="assistant",
        help="Discuter avec un assistant disponible et préparer une connexion Ollama locale.",
    ),
    st.Page(
        render_programmation,
        title="Programmation",
        icon=":material/code:",
        url_path="programmation",
        help="Générer des consignes techniques structurées pour Python, SQL, Flutter et plus.",
    ),
    st.Page(
        render_business,
        title="Business",
        icon=":material/store:",
        url_path="business",
        help="Construire une synthèse business, une proposition de valeur et un plan d'action.",
    ),
    st.Page(
        render_social_media,
        title="Réseaux sociaux",
        icon=":material/campaign:",
        url_path="reseaux-sociaux",
        help="Préparer des publications adaptées à plusieurs plateformes.",
    ),
    st.Page(
        render_projets,
        title="Projets BAH TECH",
        icon=":material/rocket_launch:",
        url_path="projets-bah-tech",
        help="Consulter et suivre le portefeuille de projets de BAH TECH GROUP.",
    ),
]

page = st.navigation(pages, position="sidebar")
page.run()