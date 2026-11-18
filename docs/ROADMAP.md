# Feuille de route — BAH AI Assistant

## Version 1.0 — Fondation

- Interface Streamlit avec navigation et modules
- Architecture modulaire dans `modules/`
- Briefs programmation, business et réseaux sociaux
- Portefeuille de projets BAH TECH GROUP
- Tests unitaires des fonctions métier

## Version 1.1 — Données et observabilité

- Persistance locale SQLite
- Journalisation des conversations
- Gestion des paramètres utilisateur
- Export des résultats en Markdown et PDF
- Métriques d'utilisation anonymisées

## Version 1.2 — Connecteurs IA

- Abstraction d'un fournisseur IA commun
- Ollama en fournisseur local
- Choix du modèle dans l'interface
- Streaming des réponses
- Historique des conversations par session
- Limite des contextes et gestion des erreurs

## Version 1.3 — Qualité produit

- Authentification native Streamlit
- Contrôle des droits par rôle
- Validation Pydantic des entrées et sorties
- Tests Streamlit `AppTest`
- Pipeline GitHub Actions : lint, tests et compilation
- Déploiement reproductible avec Python 3.12

## Version 2.0 — IA locale complète avec Ollama

- RAG sur documents locaux
- Base vectorielle locale
- Recherche des connaissances par projet
- Agents spécialisés programmation, business, social media et projets
- Exécution d'outils limitée et validée
- Exécution locale par défaut, sans données sensibles envoyées à un service externe

## Version 2.1 — Distribution

- Conteneur Docker
- Sauvegarde et restauration des données
- Gestion des modèles Ollama
- Téléchargement hors ligne des modèles
- Monitoring santé Ollama et métriques
- Procédure de mise à jour automatique

## Cible technique

- Python 3.12+
- Streamlit 1.67+
- Ollama avec modèles tels que `llama3.2`
- SQLite pour les données locales
- GitHub Actions pour CI/CD

## Version 3.0 — Produit local complet

La feuille de route détaillée vers la V3 est disponible dans
[ROADMAP_V3.md](ROADMAP_V3.md).
