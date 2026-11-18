# Feuille de route — Bah AI Assistant V3

## 1. Diagnostic de la version actuelle

### Éléments déjà disponibles

- Navigation Streamlit modulaire dans `app.py`.
- Modules séparés pour l'assistant, la programmation, le business, les réseaux
  sociaux et les projets.
- Modèle `Conversation` et `Message` dans `modules/models.py`.
- Stockage atomique JSON pour les conversations et la mémoire locale.
- Abstraction `AIProvider` avec implémentation Ollama.
- Interface conversationnelle avec historique et mémoire locale.
- Configuration Streamlit centralisée dans `.streamlit/config.toml`.
- Tests pytest pour les fonctions métier et la persistance JSON.

### Lacunes à résoudre pour la V3

| Domaine | État actuel | Objectif V3 |
|---|---|---|
| Conversations | Historique JSON global | Contexte utilisateur, titres, recherche et archivage |
| Sauvegarde | JSON atomique | Sauvegarde, restauration, validation de schéma |
| Mémoire | Liste de chaînes locales | Mémoire typée, éditable, classée et limitée |
| Projets | Liste Python statique | Entités JSON typées et interface de gestion |
| Tableau de bord | Aucun KPI utilisateur | Synthèse globale avec métriques locales |
| Ollama | Détection et streaming simples | Statut modèle, tests, erreurs et configuration |
| Qualité | Tests unitaires limités | CI, lint, typage et tests Streamlit |

## 2. Objectif de la V3

Livrer une application locale stable offrant :

- des conversations persistantes, consultables et archivables ;
- une sauvegarde JSON exportable et restaurable ;
- une mémoire locale structurée et contrôlée par l'utilisateur ;
- une gestion complète des projets BAH TECH GROUP ;
- un tableau de bord des conversations, projets et activités ;
- une intégration Ollama fiable avec dégradation propre ;
- une base préparée pour une transition ultérieure vers SQLite.

La V3 reste locale par défaut : aucun contenu conversationnel ou fichier
personnel ne doit être envoyé à un service externe sans action explicite.

## 3. Architecture cible

```text
app.py
modules/
  models.py             Entités métiers
  repositories.py       Contrats de stockage
  storage_json.py       Implémentation JSON
  project_service.py    Règles métier des projets
  dashboard_service.py  Agrégation des indicateurs
  ai_provider.py        Contrat des fournisseurs IA
  assistant.py          UI conversationnelle
  projects.py           UI des projets
  dashboard.py          UI du tableau de bord
data/
  conversations.json
  memory.json
  projects.json
  backups/
tests/
  test_storage.py
  test_projects.py
  test_dashboard.py
  test_app.py
```

### Responsabilités

- `models.py` : structures de données sans dépendance Streamlit.
- `repositories.py` : interface stable pour conversations, mémoire et projets.
- `storage_json.py` : lecture, validation, écriture atomique et sauvegardes.
- `project_service.py` : création, modification, statut, échéances et filtres.
- `dashboard_service.py` : transformations et calcul des indicateurs.
- `ai_provider.py` : découverte des modèles, disponibilité et streaming.
- Les modules Streamlit : affichage et widgets uniquement.

## 4. Modèle de données V3

### Conversation

```json
{
  "id": "UUID",
  "title": "Titre",
  "project_id": "UUID ou null",
  "archived": false,
  "messages": [],
  "created_at": "ISO-8601 UTC",
  "updated_at": "ISO-8601 UTC"
}
```

### Mémoire

```json
{
  "id": "UUID",
  "category": "profile|preference|project|instruction",
  "fact": "Information mémorisée",
  "enabled": true,
  "created_at": "ISO-8601 UTC",
  "updated_at": "ISO-8601 UTC"
}
```

### Projet

```json
{
  "id": "UUID",
  "name": "Nom du projet",
  "description": "Description",
  "status": "idea|planned|active|paused|completed",
  "priority": "low|medium|high",
  "owner": "BAH TECH GROUP",
  "created_at": "ISO-8601 UTC",
  "updated_at": "ISO-8601 UTC"
}
```

## 5. Phases de réalisation

### V3.0 — Fondations données

1. Remplacer les structures libres par des dataclasses V3 validées.
2. Ajouter le protocole `ConversationRepository`, `MemoryRepository` et
   `ProjectRepository`.
3. Ajouter `JsonProjectStore` et migrer la liste statique `PROJECTS`.
4. Ajouter un numéro de version aux fichiers JSON.
5. Ajouter une migration automatique des fichiers V1/V2 vers V3.
6. Valider les fichiers après chargement et afficher les erreurs à l'utilisateur.

Critères :

- aucune perte de conversation lors d'une migration ;
- lecture et écriture compatibles avec les données actuelles ;
- sauvegarde atomique déjà utilisée ;
- fichiers invalides isolés, sans écraser les données existantes.

### V3.1 — Gestion des conversations

1. Recherche par titre et contenu.
2. Renommage et archivage des conversations.
3. Association d'une conversation à un projet.
4. Export JSON et Markdown.
5. Limitation configurable du contexte envoyé à Ollama.
6. Préservation des messages utilisateur et assistant.

Critères :

- une conversation archivée reste consultable ;
- le contenu de conversation peut être exporté ;
- la recherche ne modifie pas les données ;
- le contexte envoyé reste limité aux N derniers messages.

### V3.2 — Mémoire locale

1. Remplacer les chaînes simples par des entrées typées.
2. Ajouter une catégorie, un statut actif/inactif et une date.
3. Permettre ajout, modification, désactivation et suppression.
4. Afficher clairement les mémoires transmises à Ollama.
5. Exporter ou effacer toute la mémoire.

Critères :

- aucune mémoire n'est envoyée si elle est désactivée ;
- l'utilisateur peut supprimer une mémoire individuelle ;
- `Effacer toute la mémoire` exige une confirmation ;
- les données restent locales.

### V3.3 — Gestion des projets

1. Migrer les projets vers `data/projects.json`.
2. Ajouter création, édition, archivage et suppression confirmée.
3. Ajouter statut, priorité, description et projet pilote.
4. Associer une conversation à un projet.
5. Filtrer les projets par statut ou priorité.

Critères :

- les cinq projets BAH TECH actuels sont migrés ;
- les modifications sont persistées ;
- un projet supprimé ne peut pas être restauré accidentellement ;
- les filtres ne modifient pas la source persistée.

### V3.4 — Tableau de bord utilisateur

1. Ajouter une page Dashboard.
2. Afficher le nombre de conversations actives et archivées.
3. Afficher le nombre de projets par statut.
4. Afficher les projets prioritaires.
5. Afficher les derniers échanges et les mémoires actives.
6. Ajouter une synthèse Ollama : disponible, indisponible, modèle configuré.

Critères :

- toutes les métriques sont calculées hors du rendu Streamlit ;
- les données absentes rendent des valeurs à zéro ;
- aucun appel IA n'est lancé pour afficher le tableau de bord ;
- un rafraîchissement normal ne modifie pas les fichiers JSON.

### V3.5 — Préparation Ollama avancée

1. Ajouter une configuration Ollama centralisée.
2. Lister les modèles disponibles.
3. Vérifier la disponibilité avant chaque nouvelle réponse.
4. Afficher les erreurs réseau sous forme utilisateur.
5. Empêcher l'envoi de secrets ou fichiers non autorisés.
6. Préparer une interface permettant plusieurs fournisseurs IA.

Critères :

- Ollama arrêté ne bloque pas l'application ;
- le modèle sélectionné existe ou affiche une erreur claire ;
- les conversations peuvent continuer hors ligne ;
- les paramètres Ollama sont isolés du reste de l'interface.

### V3.6 — Sauvegarde et qualité

1. Créer une sauvegarde horodatée des données JSON.
2. Restaurer une sauvegarde après validation.
3. Ajouter les tests unitaires des services et dépôts.
4. Ajouter des tests Streamlit pour les pages principales.
5. Ajouter les commandes lint, type-check et test.
6. Ajouter GitHub Actions sur chaque push et pull request.

Critères :

- une sauvegarde est toujours créée avant une restauration ;
- une sauvegarde corrompue est rejetée ;
- le pipeline échoue sur une erreur de type ou de test ;
- aucun fichier `data/*.json` sensible n'est publié.

## 6. Ordre d'exécution recommandé

1. Socle des données V3 et migrations.
2. Sauvegarde JSON et archives.
3. Gestion des conversations.
4. Mémoire locale typée.
5. Gestion des projets.
6. Tableau de bord utilisateur.
7. Préparation Ollama avancée.
8. Tests, sécurité des données et CI.

## 7. Critères de livraison V3

- conversations persistantes entre deux sessions ;
- mémoire locale visible et contrôlable ;
- projets BAH TECH persistés et filtrables ;
- tableau de bord utilisable sans Ollama ;
- Ollama optionnel avec état explicite ;
- restauration JSON validée ;
- tests unitaires et Streamlit reproductibles ;
- aucune donnée sensible en Git ;
- README et documentation d'exploitation à jour.

## 8. Évolution après la V3

Après stabilisation de la V3 :

- migrer vers SQLite avec les mêmes contrats de stockage ;
- ajouter RAG local sur documents ;
- ajouter des agents spécialisés ;
- ajouter l'authentification locale ou Streamlit ;
- préparer un conteneur Docker ;
- conserver Ollama comme fournisseur IA par défaut hors ligne.
