# Feuille de route — BAH AI ASSISTANT V3

La V3 est une feuille de route : les éléments ci-dessous ne sont pas annoncés
comme livrés. Le périmètre V2 actuel et ses limites sont décrits dans
[ROADMAP.md](ROADMAP.md).

## Socle disponible en V2

La V2 comprend une application Streamlit locale, une intégration Ollama avec
Phi3 par défaut, des agents spécialisés, un historique et une mémoire JSON,
ainsi que des tests pytest et Streamlit `AppTest`. Les conversations sont
isolées par identifiant, leur suppression demande confirmation et les fins de
flux sans `done=true` sont rejetées.

Certaines capacités de base ne sont donc pas des tâches V3 à créer de nouveau :

- le nombre de messages de contexte est configurable ;
- l'application peut lister les modèles Ollama installés et vérifier le modèle
  sélectionné ;
- les erreurs de disponibilité et de réponse sont présentées dans l'interface ;
- des tests `AppTest` vérifient les principaux parcours conversationnels.

La V3 pourra enrichir ces capacités (diagnostics, couverture et options), sans
les présenter comme absentes.

## Objectifs V3

### V3.0 — Évolution et migration des données

- Définir les formats et versions de schéma avant toute évolution de JSON.
- Concevoir une migration réversible et testée des conversations et préférences.
- Évaluer SQLite comme option de stockage ; une migration n'est pas garantie
  sans changements dans l'application.

### V3.1 — Conversations et sauvegarde

- Recherche dans les titres et contenus, renommage et archivage.
- Association facultative d'une conversation à un projet.
- Export et restauration après validation, avec sauvegarde préalable.
- Préserver les données existantes et documenter les suppressions.

### V3.2 — Mémoire locale

- Évaluer des entrées typées et catégorisées plutôt que des faits libres.
- Donner à l'utilisateur un contrôle explicite sur activation, modification,
  suppression et éventuelle utilisation dans les prompts.
- Expliquer clairement quelles données sont envoyées à Ollama local.

### V3.3 — Gestion des projets

- Remplacer, si validé, la liste statique actuelle par des projets persistés.
- Ajouter création, modification, archivage, filtres et suppression confirmée.
- Associer les conversations aux projets sans intégrer de recherche documentaire
  par défaut.

### V3.4 — Connaissances locales

- Étudier la recherche dans des documents locaux et un RAG local.
- Évaluer une base vectorielle uniquement si les besoins et les tests le
  justifient.
- Définir les formats pris en charge, les limites, la suppression des index et
  les garanties de confidentialité avant implémentation.

### V3.5 — Tableau de bord

- Ajouter une synthèse locale des conversations, projets et état du modèle.
- Calculer les indicateurs sans déclencher d'appel IA.

### V3.6 — Fiabilité et distribution

- Renforcer les diagnostics Ollama, notamment la distinction entre fin
  protocolaire et sortie arrêtée sur une limite de génération.
- Étudier la configuration des paramètres de génération ; la V2 utilise
  actuellement `num_predict=256`, `temperature=0.7` et `keep_alive="10m"`.
- Améliorer la reproductibilité des dépendances, le typage, le lint et la
  couverture des tests.
- Évaluer Docker et GitHub Actions pour la distribution et l'intégration
  continue.

## Principes de réalisation

- Toute migration ou restauration doit être testée avec des copies et ne pas
  écraser une source invalide.
- Les données restent locales par défaut ; tout transfert externe éventuel doit
  être explicite et documenté.
- Les actions destructives demandent une confirmation.
- Chaque nouvelle capacité doit avoir des critères de validation et une
  documentation cohérente.

Le [backlog V3](V3_BACKLOG.md) donne une décomposition indicative. Son ordre
peut être ajusté après validation des besoins.
