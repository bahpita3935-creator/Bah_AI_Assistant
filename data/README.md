# Données locales

Ce dossier contient les données applicatives générées au démarrage :

- `conversations.json` : historique des conversations.
- `memory.json` : mémoire locale de faits retenus par l'utilisateur.

Ces fichiers sont ignorés par Git. Ils ne doivent pas être commités avec des
informations personnelles ou sensibles.

Le stockage valide les fichiers avant utilisation et écrit les changements par
remplacement atomique. Si un fichier est invalide ou inaccessible, l'application
affiche une erreur et conserve le fichier d'origine; ne le supprimez pas avant
d'avoir créé une copie de sauvegarde. Des fichiers `.json.lock` locaux
synchronisent les accès et sont également ignorés par Git.
