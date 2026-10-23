# Organiser le travail : conversation pilote, file de fond, délestage, sorties courtes

Quatre pratiques d'organisation qui visent à économiser du quota sans toucher à la qualité. Elles complètent les
réglages de [BONNES-PRATIQUES.md](BONNES-PRATIQUES.md) : ici, on agit sur la façon de répartir le travail,
pas sur un fichier de configuration. Version 1.4.0, rédigée le **2026-10-23**.

## Étiquettes

Les mêmes que dans [BONNES-PRATIQUES.md](BONNES-PRATIQUES.md#légende-des-étiquettes) : **[officiel]**,
**[rapporté]**, **[à vérifier]**. Tout ce qui est écrit ici sans source est une **convention de l'auteur,
non mesurée [à vérifier]** : une façon de travailler qui a servi, pas un résultat démontré. Aucun gain
chiffré n'est promis.

## 1. Une conversation pilote et des sessions rattachées

### Le principe

La conversation principale reste sur le modèle fort : c'est le point d'entrée, celle où l'on décide. Chaque
tâche qui mérite sa propre session part dans une **session rattachée** (une session lancée depuis la
conversation pilote, que l'application de bureau affiche sous elle [officiel :
[desktop](https://code.claude.com/docs/en/desktop#start-a-task-that-claude-suggests), consulté le
2026-10-23] ; le modèle se choisit dans **Options** avant le démarrage). Le rapport de la session revient à
la conversation pilote, par message entre sessions [à vérifier].

| Tâche | Modèle et effort de la session rattachée |
|---|---|
| Gros volume simple (tri, comptage, reformatage) | Haiku |
| Travail courant (code, tests, documentation) | Sonnet, `medium` |
| Texte publié, extraction ou analyse de documents | Sonnet, `high` |
| Architecture, sécurité, vérification des faits | Opus |
| Tâche que le modèle de la conversation pilote traite déjà bien | aucune session : on reste dans la conversation pilote |

La table est une **convention de l'auteur, non mesurée [à vérifier]**. Elle suit celle des types
d'agents ([BONNES-PRATIQUES.md](BONNES-PRATIQUES.md#table-de-décision--tâche-vers-agent)) ; la différence
est qu'une session rattachée est une conversation complète, que l'on peut ouvrir et suivre [à vérifier],
alors qu'un sous-agent travaille dans l'ombre et ne rend qu'un résumé.

### Ce que ça apporte

- Un **contexte court par tâche** : chaque session repart d'un contexte neuf, sans l'historique des tâches
  précédentes que la conversation pilote porte.
- Des **rapports qui reviennent à un seul endroit**, la conversation pilote, au lieu de conversations
  éparpillées que l'on doit rouvrir une à une.
- Le **bon modèle sans changer de modèle en cours de tâche** : changer de modèle dans une conversation fait
  relire tout le contexte sans cache ([le cache](BONNES-PRATIQUES.md#le-cache--ce-qui-le-casse-ce-qui-le-garde)).

### Ce que ça coûte

Chaque session recharge le prompt système, les `CLAUDE.md`, la liste des skills et les noms d'outils des
serveurs MCP : environ 75 000 tokens avant tout travail pour une session de bureau
([mesure de l'auteur du 2026-10-05](BONNES-PRATIQUES.md#exemple-mesuré-sur-un-usage-réel--où-part-largent),
[rapporté]). Pour une action de deux minutes, une session coûte plus que l'action : on la fait dans la
conversation pilote. Une session rattachée se justifie quand la tâche est longue, volumineuse, ou demande
un autre modèle que celui de la conversation pilote.

### Limite constatée : pas de modèle plus fort que celui de la session qui lance

Sur Claude Code Desktop, l'auteur a constaté le 2026-10-23 qu'une session lancée par une autre ne peut pas
utiliser un modèle plus fort que celui de la session qui la lance (exemple : Fable depuis une session sur
Opus est impossible). **Constatée, à vérifier** : la page de l'application de bureau
([desktop](https://code.claude.com/docs/en/desktop), consultée le 2026-10-23, sections « Start a task that
Claude suggests » et « Work across sessions ») décrit un choix du modèle avant le démarrage, dans
**Options**, et ne mentionne aucune règle de ce genre dans les parties lues (la page fait environ 170 000 caractères, seule une partie a été lue). Absence de mention n'est pas
preuve d'absence : testez avant de vous y fier. Conséquence pratique, si la limite se confirme : gardez la
conversation pilote sur le modèle le plus fort dont vous aurez besoin, puisque les sessions rattachées ne
pourront qu'égaler ou baisser.

## 2. Une file de fond sur un serveur, cadencée par une ligne régulière

### Le principe

Les travaux longs et autonomes (tâches planifiées lançant `claude -p`) tournent sur un serveur, de façon à
continuer PC éteint. Pour qu'ils ne vident pas la semaine, on leur donne un **budget qui suit une ligne
régulière** :

> usage hebdomadaire autorisé à l'instant *t* = part de la fenêtre hebdomadaire déjà écoulée, plafonnée.

Exemple, avec un plafond à 90 % : à la moitié de la fenêtre de sept jours, la file de fond ne lance rien de
nouveau si l'usage hebdomadaire dépasse 50 %. À la fin de la fenêtre, la limite monte jusqu'au plafond. La
file consomme donc en continu au lieu de tout dépenser le premier jour, et la file de fond ne vide pas la semaine à
elle seule. Ajoutez le plafond de la fenêtre de cinq heures (par exemple 85 %), qui protège vos sessions
interactives.

Règles à respecter :

1. **La décision se prend dans le script, avant de lancer le modèle**, jamais dans le prompt : un lancement
   refusé ne coûte rien, alors qu'un lancement qui « décide de ne rien faire » repaie tout le contexte
   ([point 3 de l'exemple mesuré](BONNES-PRATIQUES.md#exemple-mesuré-sur-un-usage-réel--où-part-largent)).
2. **L'usage lu est l'usage total du compte**, interactif compris : la ligne régulière protège aussi
   vos propres sessions.
3. **Un travail refusé est reporté, pas perdu** : la file le garde avec sa date de reprise.
4. **Distillation progressive** : quelques tâches par jour, deux ou trois chantiers en parallèle au plus,
   Sonnet par défaut, plutôt que tout d'un coup.

La formule est une **convention de l'auteur, non mesurée [à vérifier]**. Où lire l'usage hebdomadaire
depuis un script : aucune interface n'a été trouvée dans la documentation consultée [à vérifier] ;
`/usage` l'affiche dans Claude Code [officiel :
[costs#plan-usage-breakdown](https://code.claude.com/docs/en/costs#plan-usage-breakdown)].

### Le skill public claude-lot

[claude-lot](https://github.com/RAAAAAGEEEEE/claude-lot) (même auteur, consulté le 2026-10-23, version
1.0.0) est un skill public qui fait cette passerelle : plafond commun à plusieurs projets, refus au lancement (code de
sortie 75) au-delà de 85 % de la fenêtre de cinq heures ou de 90 % de la semaine, choix du modèle et de
l'effort par type de tâche. L'usage y est lu par une sonde (script fourni, ou tout programme qui
imprime la même ligne). Cette version applique des **seuils constants (réglables)** ; la ligne régulière ci-dessus est
une règle de pilotage à ajouter par-dessus. Ce dépôt ne recopie pas claude-lot : installez-le et lisez sa
documentation.

## 3. Délester vers un autre fournisseur le travail sur données publiques

### Le principe

Une partie du travail ne demande pas Claude : premiers jets, résolution à l'aveugle (un second modèle qui
essaie de résoudre sans voir la réponse, pour mesurer l'ambiguïté), étiquetage, tri. Le confier à un autre
fournisseur (par exemple un autre modèle accessible par un crédit tiers) épargne le quota Claude.

Garde-fous, tous obligatoires :

1. **Données publiques seulement.** Le travail délesté ne contient que des données déjà publiques ou
   produites pour être publiées.
2. **Jamais de code source, de clé, de jeton ni de donnée d'utilisateur vers un tiers.** Une donnée
   d'utilisateur reste chez Claude ou chez vous.
3. **Un test qui vérifie ce qui part.** Avant l'envoi, un contrôle automatique compare le contenu sortant à
   une liste de champs autorisés et refuse tout ce qui ressemble à un secret, à une adresse e-mail ou à du code. L'exemple
   [examples/delestage_garde.py](../examples/delestage_garde.py) fait ce contrôle ; il est testé dans
   [tests/test_delestage_garde.py](../tests/test_delestage_garde.py). C'est un filet minimal, pas une
   garantie : adaptez la liste de champs à votre cas.
4. **Claude garde la vérification des faits sur 100 % de ce qui est publié.** Le tiers produit, Claude (de
   préférence le modèle fort) vérifie chaque fait avant publication. Un premier jet d'un autre fournisseur
   n'est jamais publié tel quel.

Le travail délesté a un coût (le crédit tiers) : signalez-le avant un gros lot, comme pour toute API payante.

## 4. Des sorties sans répétition

Chaque token écrit coûte, et la réponse est relue à chaque requête suivante, au tarif réduit de la
lecture de cache, jusqu'à la compaction. Une réponse plus courte coûte donc moins à l'écriture, et un peu
moins à chaque relecture du contexte.

Deux règles pour les réponses de l'agent :

1. **Une information n'apparaît qu'à un seul endroit** de la réponse. Pas de récapitulatif qui redit le
   corps, pas de conclusion qui répète l'introduction, pas de liste des options écartées.
2. **Les actions et décisions demandées à l'utilisateur sont regroupées en haut**, avant le détail : il
   voit tout de suite ce qu'on attend de lui, sans avoir à lire le reste.

Un paragraphe prêt à coller dans votre `CLAUDE.md` est dans
[examples/CLAUDE.md.example](../examples/CLAUDE.md.example). L'effet sur le quota n'est pas mesuré
[à vérifier] ; le principe (une sortie plus courte pèse moins dans le contexte relu) découle du
fonctionnement décrit dans [BONNES-PRATIQUES.md](BONNES-PRATIQUES.md#où-partent-les-tokens).

## Sécurité et confidentialité

Le skill n'envoie rien : ces pratiques sont des consignes, pas du code qui s'exécute. Le seul code fourni,
`examples/delestage_garde.py`, n'importe aucun module réseau. Détail :
[PRIVACY_AND_SECURITY.md](PRIVACY_AND_SECURITY.md).

Voir aussi : [BONNES-PRATIQUES.md](BONNES-PRATIQUES.md), [LIMITATIONS.md](LIMITATIONS.md),
[USAGE.md](USAGE.md).
