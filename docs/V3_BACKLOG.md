# Backlog prévisionnel — BAH AI ASSISTANT V3

Ce backlog décrit des travaux futurs, pas des fonctions disponibles dans la
V2. Le périmètre et les limites actuellement livrés sont recensés dans
[ROADMAP.md](ROADMAP.md).

## Capacités déjà acquises en V2

Ces fonctions ne sont pas à re-développer comme tâches de backlog :

- limite du contexte configurable ;
- liste des modèles Ollama installés et vérification du modèle sélectionné ;
- affichage des erreurs Ollama dans l'interface ;
- tests `AppTest` des parcours de l'application.

Le backlog peut proposer d'en améliorer les options, diagnostics ou couverture.

## Travaux proposés

| ID | Travail futur | Dépendances indicatives | Validation attendue |
|---|---|---|---|
| V3-01 | Définir les versions de schéma et les migrations de données | Aucun | Migration testée sur copies, données d'origine préservées |
| V3-02 | Sauvegarde, export et restauration JSON | V3-01 | Restauration validée, sauvegarde préalable, rejet d'une sauvegarde invalide |
| V3-03 | Recherche, renommage, archivage et association des conversations | V3-01 | Tests sur plusieurs conversations, aucune mutation par la recherche |
| V3-04 | Mémoire typée avec contrôle utilisateur explicite | V3-01 | Tests d'activation, modification, suppression et injection explicite |
| V3-05 | Persistance et interface CRUD des projets | V3-01 | Création, modification, filtres et suppression confirmée testés |
| V3-06 | Recherche documentaire locale / étude RAG | V3-01 | Formats, limites, confidentialité et suppression d'index documentés |
| V3-07 | Tableau de bord local | V3-03, V3-05 | Indicateurs reproductibles sans appel au modèle |
| V3-08 | Diagnostics et configuration Ollama plus riches | Aucun | Fin de flux, limite de génération et erreurs distinguées dans les tests |
| V3-09 | Reproductibilité et distribution (dépendances, lint, typage, CI, Docker) | Périmètre V3 stabilisé | Environnement documenté et contrôles automatisés vérifiés |

Les dépendances sont indicatives : elles devront être confirmées lors de la
planification. L'évaluation d'une migration vers SQLite ne préjuge ni de sa
nécessité ni de sa faisabilité sans modification de l'application.

## Règles d'ingénierie

- Tester les changements de stockage avec des données temporaires ou des copies.
- Ne pas modifier des données utilisateur pendant une migration non validée.
- Garder les données locales par défaut et documenter tout échange externe.
- Ne pas effectuer de suppression ou migration destructive sans confirmation et
  stratégie de sauvegarde.
- Maintenir cohérents le README, la feuille de route et les critères de livraison.

## Définition de terminé

Un élément du backlog est terminé lorsque son comportement est testé, ses
formats et erreurs sont documentés, les données existantes sont préservées et
la suite de validation convenue passe.
