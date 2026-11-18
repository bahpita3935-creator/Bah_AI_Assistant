import streamlit as st

st.set_page_config(
    page_title="BAH AI ASSISTANT",
    page_icon="🤖",
    layout="centered"
)

st.markdown(
    """
    <style>
    [data-testid="stMain"] h1 {
        font-size: clamp(1.8rem, 5vw, 2.75rem);
        line-height: 1.15;
        overflow-wrap: anywhere;
    }

    [data-testid="stMain"] h2,
    [data-testid="stMain"] h3,
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] {
        max-width: 100%;
        overflow-wrap: anywhere;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🤖 ASSISTANT IA BAH")

st.subheader(
    "Assistant Personnel de Thierno Souleymane Bah"
)

menu = st.sidebar.selectbox(
    "Choisir un module",
    [
        "Accueil",
        "Programmation",
        "Business",
        "Réseaux Sociaux",
        "Projets BAH TECH"
    ]
)

if menu == "Accueil":
    st.write("Bienvenue dans BAH AI ASSISTANT")

elif menu == "Programmation":
    st.header("💻 Programmation")
    st.write("Python, Flutter, Node.js, SQL")

elif menu == "Business":
    st.header("💼 Business")
    st.write("Gestion des entreprises")

elif menu == "Réseaux Sociaux":
    st.header("📱 Réseaux Sociaux")
    st.write("Création de contenu")

elif menu == "Projets BAH TECH":
    st.header("🚀 Projets BAH TECH GROUP")

    projets = [
        "Bah Immo Gestion",
        "Bahora Store",
        "BhantalHub SaaS",
        "Agro Transit Hub",
        "Bah Studio AI"
    ]

    for projet in projets:
        st.write("✅", projet)