# BAH AI ASSISTANT V2

BAH AI ASSISTANT est une application locale de conversation et d'assistance,
construite avec Python, Streamlit et Ollama. Le modèle Ollama par défaut est
`phi3` ; le modèle peut être changé dans les préférences et doit être installé
localement.

## Fonctionnalités V2

- **Assistant Général** et agents de conversation **Programmation**,
  **Affaires**, **Réseaux sociaux** et **BAH TECH**. Dans l'interface actuelle,
  l'agent Affaires porte le libellé « Business ».
- Identité commune BAH AI ASSISTANT et consignes spécialisées pour les agents.
- Conversations persistées localement en JSON et sélectionnées par identifiant,
  ce qui isole les historiques même si des conversations ont le même titre.
- Confirmation explicite avant de supprimer une conversation.
- Réponses Ollama en streaming. Le flux est rejeté s'il se termine sans
  `done=true`; un `done_reason` tel que `stop` ou `length` n'invalide pas à lui
  seul la fin du flux.
- Paramètres de génération actuels : `num_predict=256`, `temperature=0.7` et
  `keep_alive="10m"`.
- Mémoire et préférences conservées dans un fichier JSON local. Les faits libres
  de mémoire ne sont pas injectés automatiquement dans les prompts ; les
  préférences générales utiles peuvent l'être.
- Les fichiers JSON temporaires d'écriture sont ciblés par les règles Git
  d'exclusion.

Les pages Programmation, Business, Réseaux sociaux et Projets BAH TECH
fournissent aussi des outils de préparation et des informations statiques ;
elles ne sont pas des agents autonomes. Les projets présentés sont une liste
statique et ne disposent pas encore d'une gestion CRUD persistante.

## Prérequis Windows

- Windows et PowerShell.
- Git.
- Python 3.14 avec le lanceur Windows `py`. L'environnement V2 validé utilise
  Python 3.14.7.
- Ollama installé et démarré localement pour utiliser les réponses IA. C'est
  une dépendance externe, pas un package Python.

Streamlit 1.67.0, version utilisée dans l'environnement validé, déclare Python
3.11 comme minimum. Cela ne signifie pas que toute l'application a été validée
sous Python 3.11. Le projet ne fixe pas de version Python dans
`requirements.txt`.

La V2 a été validée avec Python 3.14.7, Streamlit 1.67.0 et pytest 9.2.0.
Les versions directes de Streamlit et pytest sont figées dans
`requirements.txt` pour stabiliser cet environnement de référence ; les
dépendances transitives ne sont pas toutes verrouillées et peuvent varier.

## Installation

Sous Windows, choisissez un dossier parent court et accessible en écriture.
Les chemins trop longs peuvent empêcher `pip` d'installer certaines
dépendances lorsque la prise en charge des chemins longs n'est pas activée.
Par exemple :

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\src" | Out-Null
Set-Location "$env:USERPROFILE\src"
git clone --branch main https://github.com/bahpita3935-creator/Bah_AI_Assistant.git
cd Bah_AI_Assistant
```

Si le chemin de votre profil est lui-même long, choisissez un emplacement plus
court où vous avez le droit d'écrire.

Créez l'environnement virtuel recommandé :

```powershell
py -3.14 -m venv .venv
```

Si `py -3.14` ne trouve pas Python alors que Python 3.14 est installé, listez
les interpréteurs avec `py --list` et utilisez le sélecteur affiché. Par exemple,
sur la machine de validation, les commandes suivantes ont fonctionné :

```powershell
py --list
py -V:Astral/CPython3.14.7 --version
py -V:Astral/CPython3.14.7 -m venv .venv
```

Ce sélecteur dépend de l'installation et peut être différent sur une autre
machine. Si nécessaire, utilisez le chemin complet de l'interpréteur Python
3.14 installé, vérifiez sa version avec `--version`, puis lancez cet
interpréteur avec `-m venv .venv`.

Activez l'environnement, puis installez et vérifiez les dépendances :

```powershell
.\.venv\Scripts\Activate.ps1
python --version
python -m pip install -r requirements.txt
python -m pip check
```

Le dossier `.venv` est propre à la machine et ne doit jamais être versionné.
L'activation est recommandée ; si PowerShell la bloque, utilisez directement
`.\.venv\Scripts\python.exe` à la place de `python` dans les commandes
ci-dessous et pour l'installation ci-dessus.

## Ollama

Installez et démarrez Ollama séparément, puis vérifiez-le et téléchargez Phi3,
le modèle par défaut :

```powershell
ollama --version
ollama pull phi3
ollama list
```

L'application utilise l'API Ollama locale à
`http://127.0.0.1:11434`. Un autre modèle peut être sélectionné dans les
préférences, s'il est installé dans Ollama.

## Tests

```powershell
python -m pytest
```

Dernière validation de référence pour la V2 : **59 tests réussis, 0 échec**.
Un timeout intermittent d'AppTest a été observé pour
`test_submitted_messages_stay_in_chat_history_container` pendant la validation.
Il n'a pas été reproduit lors de **15 exécutions ciblées réussies** ; sa cause
reste inconnue.

## Lancement

Depuis la racine du dépôt :

```powershell
python -m streamlit run app.py
```

Ouvrez l'adresse locale affichée par Streamlit. Le port `8501` est le port
habituel, pas une contrainte de l'application. Pour utiliser explicitement
une adresse locale et un autre port, ajoutez par exemple
`--server.address=127.0.0.1 --server.port=8502`.

## Données locales et limites

Au premier lancement, `data/conversations.json` et `data/memory.json` peuvent
être absents : l'application les crée lorsqu'ils sont nécessaires. Ces fichiers
contiennent l'historique, les faits de mémoire et les préférences ; ce sont des
données locales générées par l'application,
ignorées par Git et non destinées à être versionnées. Les fichiers de
verrouillage et temporaires JSON ciblés sont également exclus. La V2 ne fournit
pas de sauvegarde ou de restauration automatique.

Les données sont stockées sur la machine. Ollama est appelé localement ; ne
considérez toutefois pas le stockage local comme une sauvegarde ou une
protection contre l'accès à votre compte ou appareil.

Limites connues de la V2 :

- Phi3 peut occasionnellement ne pas suivre parfaitement une consigne ; une
  instruction système ne garantit pas une réponse déterminée.
- BAH TECH s'appuie sur une liste statique de projets et les informations
  fournies dans la conversation ; il n'y a pas de RAG ni de recherche dans des
  documents de projet.
- Les agents ne sont pas autonomes et n'exécutent pas de commandes.
- Aucune authentification multi-utilisateur n'est fournie.
- Les brouillons de réseaux sociaux ne sont pas publiés automatiquement.
- Une suppression confirmée est définitive ; aucune restauration intégrée n'est
  disponible.

## Documentation

- [Feuille de route et périmètre V2/V3](docs/ROADMAP.md)
- [Détail des objectifs V3](docs/ROADMAP_V3.md)
- [Backlog V3](docs/V3_BACKLOG.md)

## Structure du projet

```text
app.py                       Entrée Streamlit et navigation
agents/
  registry.py                Définition des agents spécialisés
  service.py                 Construction du contexte et consigne d'identité
modules/
  ai_provider.py             Fournisseur Ollama et streaming
  assistant.py               Interface conversationnelle et historique
  models.py                  Modèles Conversation et Message
  storage.py                 Stockage local JSON
  business.py                Outil de préparation Affaires (Business)
  programmation.py           Outil de préparation technique
  social_media.py            Génération de brouillons de publication
  projets.py                 Présentation statique des projets
.streamlit/
  config.toml                Thème Streamlit
data/
  README.md                  Notice sur les données locales
  conversations.json         Généré localement, non versionné
  memory.json                Généré localement, non versionné
tests/
  test_ai_provider.py        Tests du fournisseur Ollama
  test_modules.py            Tests des modules, stockage et interface
```

Le stockage actuel repose sur des fichiers JSON. Une éventuelle migration vers
SQLite ou un autre stockage nécessitera une conception et des changements
adaptés ; elle n'est pas garantie sans modification de l'application.
