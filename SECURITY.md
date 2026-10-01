# Sécurité

## Surface

Le skill n'a aucun accès réseau et ne stocke rien : `scripts/audit.py` lit des fichiers de
configuration locaux et écrit sur la sortie standard ; `scripts/backup.py` copie un fichier à côté de
l'original. La surface concerne surtout la confidentialité de la configuration auditée (voir
[docs/PRIVACY_AND_SECURITY.md](docs/PRIVACY_AND_SECURITY.md)).

## Signaler un problème

Le signalement privé de GitHub (« Report a vulnerability ») n'est pas activé sur ce dépôt. Ouvrez une
[issue](https://github.com/RAAAAAGEEEEE/claude-code-token-saver/issues/new) intitulée « Sécurité »
**sans détail exploitable** ni donnée personnelle ; le mainteneur répondra pour convenir d'un canal
privé.

Cas typique à signaler : une sortie de l'audit qui affiche une valeur issue d'un champ sensible
(`env`, commande de hook, argument de serveur MCP).

## Versions concernées

Seule la dernière version publiée (voir [CHANGELOG.md](CHANGELOG.md)) reçoit des correctifs.
