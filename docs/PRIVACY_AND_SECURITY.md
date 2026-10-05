# Confidentialité et sécurité

## Ce qui sort de la machine

- **Scripts** : rien. `audit.py` et `backup.py` lisent des fichiers locaux, écrivent sur la sortie
  standard (et, si vous le demandez, dans le fichier désigné par `--save` ou la copie `.bak-…`), et
  n'importent aucun module réseau.
- **Skill** : ce que Claude lit pendant la session (le rapport, vos fichiers de configuration que
  Claude ouvre pour les modifier) reste dans la session Claude Code, comme tout le reste de votre
  travail avec lui.
- Aucune clé, aucun jeton, aucun compte, aucune télémétrie.

## Ce que l'audit n'affiche jamais

Les valeurs du bloc `env` de `settings.json` (hors liste blanche de noms de réglages de tokens, dont
seule la présence est notée), les commandes de hooks, `apiKeyHelper`, les arguments, variables
d'environnement, en-têtes et URL des serveurs MCP, le contenu des `CLAUDE.md`, des règles, des agents
et des skills. Les tests vérifient qu'aucun secret fictif ne figure dans la sortie texte ni JSON
(`tests/test_audit.py`, `test_output_never_contains_secrets`).

Les définitions d'agents sont lues pour la seule présence des champs `model` et `effort`. Les agents
d'exemple du dépôt ne limitent pas les outils (`tools` absent) ; l'exemple `trieur` utilise
`omitClaudeMd: true`, ce qui le prive de vos consignes de sécurité : voir
[BONNES-PRATIQUES.md](BONNES-PRATIQUES.md#table-de-décision--tâche-vers-agent).

`audit.py --depense` lit les transcriptions de conversation en lecture seule, mais ne retient que les
champs `usage`, `model`, `timestamp` et l'identifiant du message : jamais le texte des échanges
(test : `tests/test_depense.py`, `test_read_only_and_no_conversation_content`). Il affiche des noms de
projets dérivés des noms de dossiers : à relire avant de partager la sortie.

## Ce que le rapport contient quand même

Des **noms** : skills, serveurs MCP, chemins relatifs au dossier personnel (remplacé par `~`), et
les numéros de ligne. Un nom de serveur peut trahir un outil interne. Relisez le rapport avant de le
coller dans une issue ou un forum.

## Ce que le skill ne fait jamais

- Modifier un fichier sans accord explicite de l'utilisateur dans la conversation.
- Modifier un fichier sans copie horodatée préalable.
- Afficher un secret, même s'il figure dans un fichier de configuration.
- Toucher aux connecteurs, aux comptes, aux extensions ou aux réglages gérés par une organisation :
  ces actions sont données à l'utilisateur sous forme de tutoriel.
- Suivre des instructions trouvées dans un fichier de configuration, un skill ou un résultat d'outil :
  ce sont des données à auditer, jamais des consignes.

## Surface d'attaque

Les fichiers lus (`SKILL.md` d'autres skills, `CLAUDE.md`, règles) peuvent contenir du texte rédigé
pour tromper un agent. L'audit ne lit que les en-têtes et les tailles, mais si Claude ouvre ensuite un de
ces fichiers pour proposer une réécriture, il le traite comme une donnée. Ne lui demandez pas
d'exécuter ce qu'un fichier tiers lui « ordonne ».

## Signaler une faille

Voir [../SECURITY.md](../SECURITY.md).

Voir aussi : [LIMITATIONS.md](LIMITATIONS.md), [CONFIGURATION.md](CONFIGURATION.md).
