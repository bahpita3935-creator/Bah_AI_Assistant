# Backlog d'exécution — Bah AI Assistant V3

## Livrables prioritaires

| ID | Travail | Dépendances | Validation |
|---|---|---|---|
| V3-01 | Schémas de conversation, mémoire et projet | Aucun | Tests de validation |
| V3-02 | Migration JSON avec contrôles de version | V3-01 | Test avec fichiers actuels |
| V3-03 | Sauvegarde horodatée | V3-02 | Restauration réussie |
| V3-04 | Recherche et archivage | V3-01 | Tests de filtres |
| V3-05 | Mémoire typée | V3-01 | Mémoire activée/désactivée |
| V3-06 | Migration des projets statiques | V3-01 | Les cinq projets présents |
| V3-07 | CRUD des projets | V3-06 | Tests création/édition |
| V3-08 | Tableau de bord | V3-04, V3-06 | Métriques sans Ollama |
| V3-09 | Configuration Ollama | V3-01 | Modèle disponible ou erreur |
| V3-10 | Pipeline qualité | V3-07 | Lint, tests et typage |

## Règles d'ingénierie

- Préférer les fonctions sans effet sur les données.
- Garder les widgets Streamlit hors des services métier.
- Sauvegarder toutes les modifications par écriture atomique.
- Ne jamais écrire de données sensibles dans les sources.
- Ajouter un test avant chaque correction de stockage.
- Préserver les chemins de données indépendants du dossier courant.
- Ne pas faire de migration destructive sans sauvegarde préalable.

## Définition de terminé

Une tâche V3 est terminée lorsque :

1. son comportement est couvert par un test ;
2. son format JSON est documenté ;
3. l'utilisateur peut comprendre l'échec dans l'interface ;
4. les données sont persistées sans perte ;
5. le code passe le pipeline qualité ;
6. la documentation est mise à jour.
