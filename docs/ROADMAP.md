# Feuille de route — BAH AI ASSISTANT

Ce document distingue les capacités effectivement livrées en V2 des objectifs
encore à réaliser en V3. Les objectifs V3 ne sont pas des fonctionnalités
disponibles dans la version actuelle.

## V2 livrée

- Application locale Streamlit avec navigation entre l'accueil, l'assistant,
  les outils Programmation, Business, Réseaux sociaux et la liste des projets
  BAH TECH.
- Assistant Général et agents de conversation Programmation, Affaires
  (libellé « Business » dans l'interface actuelle), Réseaux sociaux et BAH TECH.
- Appels à Ollama local ; modèle par défaut `phi3`, configurable dans
  l'application ; réponses en streaming.
- Paramètres de génération actuels : `num_predict=256`,
  `temperature=0.7`, `keep_alive="10m"`.
- Historique des conversations et mémoire/préférences stockés localement en
  JSON. Les conversations sont sélectionnées et isolées par identifiant ;
  les faits libres de mémoire ne sont pas injectés automatiquement aux prompts.
- Confirmation avant suppression d'une conversation.
- Détection des flux Ollama incomplets : une fin sans `done=true` est signalée
  comme erreur et n'est pas acceptée comme réponse complète.
- Fichiers JSON de données et fichiers temporaires ciblés exclus de Git.
- Tests unitaires et tests Streamlit `AppTest`. Dernière référence de livraison :
  **59 tests réussis, 0 échec**.

## Limites de la V2

- Phi3 peut ne pas respecter parfaitement certaines consignes.
- Les données utilisateur restent locales et ne disposent pas de sauvegarde ou
  de restauration intégrée.
- La liste de projets BAH TECH est statique ; elle n'est pas un gestionnaire de
  projets persistant.
- Il n'y a ni RAG, ni recherche documentaire par projet, ni agent exécutant des
  commandes, ni authentification multi-utilisateur.
- Les agents Réseaux sociaux préparent des brouillons sans les publier.
- Une conversation supprimée après confirmation ne peut pas être restaurée par
  l'application.

## À réaliser en V3

- Recherche, renommage, archivage et association des conversations aux projets.
- Sauvegarde, export et restauration validée des données JSON.
- Mémoire structurée et contrôlée plus finement par l'utilisateur.
- Gestion persistante des projets (création, consultation, modification,
  archivage et suppression).
- Recherche documentaire/RAG local et, si nécessaire, base vectorielle.
- Tableau de bord local pour les conversations et les projets.
- Améliorations de diagnostic Ollama et configuration plus complète.
- Authentification et rôles, si un usage multi-utilisateur est retenu.
- Exécution d'outils seulement après conception de contrôles et autorisations.
- Distribution Docker et pipeline CI GitHub Actions.

Le détail des objectifs est dans [ROADMAP_V3.md](ROADMAP_V3.md) et leur ordre
proposé dans [V3_BACKLOG.md](V3_BACKLOG.md).
