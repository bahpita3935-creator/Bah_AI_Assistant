# BAH AI Assistant

Assistant IA personnel pour BAH TECH GROUP, développé avec Python et Streamlit.

## Modules

- **Assistant** : interface conversationnelle avec préparation pour Ollama.
- **Programmation** : création de consignes techniques.
- **Business** : synthèse de projet et proposition de valeur.
- **Réseaux sociaux** : brouillons de publications par plateforme.
- **Projets BAH TECH** : portefeuille des projets du groupe.

## Installation

```powershell
py -3.14 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Tests

```powershell
python -m pytest
```

## IA locale

L'intégration Ollama utilise l'API locale `http://localhost:11434`.
Installez Ollama puis un modèle, par exemple :

```powershell
ollama pull llama3.2
```

La feuille de route complète est disponible dans
[docs/ROADMAP.md](docs/ROADMAP.md).

Pour la prochaine architecture majeure, consulter :

- [Feuille de route V3](docs/ROADMAP_V3.md)
- [Backlog d'exécution V3](docs/V3_BACKLOG.md)

## Architecture

```text
app.py                  Point d'entrée Streamlit et navigation
modules/
  models.py             Modèles métier Conversation et Message
  storage.py            Persistance locale JSON
  ai_provider.py        Contrat et implémentation Ollama
  assistant.py          Interface conversationnelle
  programmation.py      Module d'aide à la programmation
  business.py           Module business
  social_media.py       Module réseaux sociaux
  projets.py            Module portefeuille de projets
data/
  conversations.json    Historique des conversations
  memory.json           Mémoire locale utilisateur
tests/
  test_modules.py       Tests unitaires et persistance
```

Les règles métier sont isolées de Streamlit. Le stockage JSON peut ensuite être
remplacé par SQLite ou une base distante sans modifier les modèles `app.py`.
