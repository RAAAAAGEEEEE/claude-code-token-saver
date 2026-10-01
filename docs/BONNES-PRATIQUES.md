# Bonnes pratiques : pour aller plus loin

Leviers pour faire dépenser moins de tokens à Claude Code sans perdre en qualité, vérifiés dans la
documentation officielle le **2026-10-01** (Claude Code en version récente ; les versions minimales
sont indiquées quand la doc les donne). Le skill applique une partie de ces leviers
([SKILL.md](../SKILL.md)) ; ce document sert de référence et de guide manuel.

## Légende des étiquettes

- **[officiel]** : page de documentation Anthropic, citée avec son ancre. Toutes les pages ont été
  consultées le 2026-10-01 sur `code.claude.com/docs/en/` (liste en bas).
- **[rapporté]** : retour d'un tiers (blog, forum), non mesuré ici. Jamais érigé en règle.
- **[à vérifier]** : non confirmé par une source. À tester avant de s'y fier.

Aucun chiffre d'économie n'est promis : Anthropic ne publie pas la pondération du quota d'un
abonnement. Mesurez chez vous ([Mesurer](#mesurer)).

## Où partent les tokens

Claude Code renvoie toute la conversation à chaque requête, et chaque appel d'outil déclenche une
requête de plus. Le cache de prompt relit cet historique à un tarif réduit, mais une session ouverte
toute la journée pèse sur le quota même pour une question d'une ligne. [officiel :
[costs#why-usage-climbs-in-a-long-session](https://code.claude.com/docs/en/costs#why-usage-climbs-in-a-long-session)]

Les causes que la doc liste : contexte long, cache perdu après une pause, tâches planifiées, messages
entre sessions, sous-agents et workflows, équipes d'agents (environ 7 fois plus de tokens qu'une
session standard quand les équipiers sont en mode plan), compaction d'un gros contexte, points de contrôle d'objectif en veille. [officiel,
même page et [costs#manage-agent-team-costs](https://code.claude.com/docs/en/costs#manage-agent-team-costs)]

## Leviers dans les réglages

| Levier | Où | Effet | Risque pour la qualité | Preuve |
|---|---|---|---|---|
| Plafonner la fenêtre de compaction | `autoCompactWindow` (100 000 à 1 000 000) ou `/autocompact 400k` | Sans réglage, la compaction attend environ 967 000 tokens sur les modèles à fenêtre de 1 million. Un plafond plus bas évite que chaque requête relise un contexte énorme. | Faible à moyen : une compaction résume et perd du détail. Gardez un fichier de reprise pour les travaux longs. | [officiel] [model-config#set-the-auto-compact-window](https://code.claude.com/docs/en/model-config#set-the-auto-compact-window), [settings-reference#autocompactwindow](https://code.claude.com/docs/en/settings-reference#autocompactwindow) |
| Modèle des sous-agents | `CLAUDE_CODE_SUBAGENT_MODEL` dans le bloc `env` | Un sous-agent sans modèle déclaré hérite de la session ; cette variable fixe un défaut moins cher (par exemple `sonnet`). Sans `_FORCE`, un modèle passé à l'appel ou déclaré dans l'agent reste prioritaire, et les agents intégrés Explore et Plan ne sont pas concernés (ils héritent du modèle de la session). | Faible à moyen selon la tâche. La doc indique que Sonnet convient à la plupart des tâches de code et coûte moins cher qu'Opus ; gardez un modèle plus fort pour revue et architecture. | [officiel] [sub-agents#choose-a-model](https://code.claude.com/docs/en/sub-agents#choose-a-model), [env-vars](https://code.claude.com/docs/en/env-vars), [costs#choose-the-right-model](https://code.claude.com/docs/en/costs#choose-the-right-model) |
| Niveau d'effort | `/effort`, sélecteur de modèle, `CLAUDE_CODE_EFFORT_LEVEL` ; champ `effort` d'un agent ou d'un skill | Les niveaux élevés raisonnent plus longtemps (tokens de sortie). Opus 5.5 et Sonnet 5.5 démarrent en `medium`. Sur Opus 5.5, Sonnet 5.5 et Fable 5.1, changer d'effort ne casse pas le cache (abonnement ou clé API ; pas sur Amazon Bedrock, Google Cloud, une passerelle Claude apps, ni avec `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS` ou une configuration HIPAA). | Faible en `medium` pour les tâches courantes ; montez à `high` ou `xhigh` pour les tâches difficiles. | [officiel] [model-config#adjust-effort-level](https://code.claude.com/docs/en/model-config#adjust-effort-level), [prompt-caching#changing-effort-level](https://code.claude.com/docs/en/prompt-caching#changing-effort-level) |
| Alléger la liste des skills | `skillOverrides` : `name-only`, `user-invocable-only`, `off` | La description de chaque skill visible est envoyée à chaque session et à chaque sous-agent. `name-only` ne garde que le nom ; `user-invocable-only` cache le skill à Claude mais `/nom` reste possible. | Nul pour les skills conservés. Léger pour ceux passés en `name-only` : Claude les choisit moins bien sans description. | [officiel] [skills#override-skill-visibility-from-settings](https://code.claude.com/docs/en/skills#override-skill-visibility-from-settings) |
| Repérer les skills inutiles | `/skill-doctor` (v2.1.252 ou plus), `/skills` (touche `t` pour trier par taille) | Montre le coût de chaque skill et s'il a déjà servi. | Aucun, lecture seule. | [officiel] [skills#find-unused-skills](https://code.claude.com/docs/en/skills#find-unused-skills), [commands](https://code.claude.com/docs/en/commands) |
| Garder les skills utiles lisibles | budget du listing : 1 % de la fenêtre ; plafond de 1 536 caractères par skill (`description` plus `when_to_use`) | Au-delà du budget, les descriptions des skills les moins utilisés sautent en premier. Mettez le cas d'usage principal au début de la description. | Évite une perte de qualité (skills non déclenchés). | [officiel] [skills#skill-descriptions-are-cut-short](https://code.claude.com/docs/en/skills#skill-descriptions-are-cut-short) |
| Couper les serveurs MCP inutiles | `/mcp`, puis désactiver | Les définitions d'outils sont différées par défaut (seuls les noms et les instructions des serveurs entrent dans le contexte), mais chaque serveur ajoute encore du texte à chaque session et à chaque sous-agent. | Faible. | [officiel] [costs#reduce-mcp-server-overhead](https://code.claude.com/docs/en/costs#reduce-mcp-server-overhead), [mcp#scale-with-mcp-tool-search](https://code.claude.com/docs/en/mcp#scale-with-mcp-tool-search) |
| Préférer un CLI à un serveur MCP | `gh`, `aws`, `gcloud`, `sentry-cli`… | Un CLI n'ajoute aucun listing d'outils. | Nul quand le CLI fait le même travail. | [officiel] [costs#reduce-mcp-server-overhead](https://code.claude.com/docs/en/costs#reduce-mcp-server-overhead) |
| Hook qui filtre les sorties | hook `PreToolUse` sur Bash | Réduit un journal de milliers de lignes à quelques lignes d'erreurs avant que Claude le lise. | Moyen si le filtre cache une erreur utile : testez-le. | [officiel] [costs#offload-processing-to-hooks-and-skills](https://code.claude.com/docs/en/costs#offload-processing-to-hooks-and-skills) |
| Laisser `ultracode` désactivé par défaut | `ultracode` à `false` (ou absent) | `ultracode` planifie un workflow pour chaque tâche substantielle ; chaque agent du workflow envoie ses propres requêtes. Activez-le par session quand une tâche le justifie. | Aucun. | [officiel] [settings-reference#ultracode](https://code.claude.com/docs/en/settings-reference#ultracode) |

Un exemple de `settings.json` : [examples/settings.example.json](../examples/settings.example.json),
expliqué clé par clé dans [CONFIGURATION.md](CONFIGURATION.md). Les réglages s'appliquent aux
nouvelles sessions.

Attention à une erreur courante : sur Opus 5.5 et les modèles publiés après lui, la clé `effortLevel`
placée au premier niveau du `settings.json` **utilisateur** n'est pas prise en compte (elle correspond
à l'ancienne forme, qui s'applique encore à Opus 5, Fable 5.1 et avant). Choisissez l'effort avec
`/effort` ou le sélecteur de modèle, qui écrivent `modelSettings`, avec `CLAUDE_CODE_EFFORT_LEVEL`, ou,
pour un sous-agent, avec le champ `effort` de sa définition (la variable `CLAUDE_CODE_EFFORT_LEVEL`
l'emporte alors sur ce champ ; voir
[choisir le sous-agent, le modèle et l'effort](#choisir-le-sous-agent-le-modèle-et-leffort)). [officiel :
[model-config#adjust-effort-level](https://code.claude.com/docs/en/model-config#adjust-effort-level)]

## Choisir le sous-agent, le modèle et l'effort

La documentation recommande de faire correspondre le modèle à la tâche : Sonnet pour la plupart des
tâches de code, un modèle plus fort pour l'architecture, un modèle léger pour les tâches simples
[officiel : [costs#choose-the-right-model](https://code.claude.com/docs/en/costs#choose-the-right-model)].
Les types d'agents appliquent ce choix, et celui de l'effort, tâche par tâche. Voici ce que la
documentation établit, puis une table de décision.

### Ce que la documentation établit

Faits [officiel], pages consultées le 2026-10-01 :
[sub-agents](https://code.claude.com/docs/en/sub-agents#supported-frontmatter-fields),
[model-config](https://code.claude.com/docs/en/model-config#adjust-effort-level).

- Le front-matter d'un fichier d'agent (`~/.claude/agents/*.md` ou `.claude/agents/*.md`) accepte
  `model` (`sonnet`, `opus`, `haiku`, `fable`, un identifiant complet comme `claude-opus-5-5`, ou
  `inherit`) et `effort` (`low`, `medium`, `high`, `xhigh`, `max`, selon ce que le modèle accepte).
  `effort` remplace l'effort de la session et le niveau enregistré dans les réglages pendant que cet
  agent travaille, **mais pas la variable `CLAUDE_CODE_EFFORT_LEVEL`**, qui l'emporte. Le réglage géré
  `maxEffortLevel` et les plafonds d'organisation limitent les deux
  [officiel : [model-config#set-the-effort-level](https://code.claude.com/docs/en/model-config#set-the-effort-level)].
- **La documentation ne décrit qu'un paramètre `model` à l'appel de l'outil Agent, aucun paramètre
  d'effort.** Déduction de l'auteur [à vérifier] : l'effort d'un sous-agent vient donc de sa définition
  ou de la session, et définir des types d'agents est le moyen documenté de le fixer **pour un
  sous-agent** (le champ `effort` d'un skill et `/effort` en session restent les leviers hors
  sous-agent). Ordre de résolution du modèle depuis la v2.1.251 : paramètre `model` de l'appel, puis
  `model` de la définition, puis `CLAUDE_CODE_SUBAGENT_MODEL`, puis le modèle de la conversation. Avant
  la v2.1.251, `CLAUDE_CODE_SUBAGENT_MODEL` passait en premier et écrasait le `model` des définitions,
  donc le `opus` d'`expert`.
- Les niveaux d'effort existent sur Opus 5.5, Sonnet 5.5, Opus 5, Sonnet 5, Fable 5.1 et 5, Opus 4.8 et
  4.7 (de `low` à `max`), et sur Opus 4.6 et Sonnet 4.6 (sans `xhigh`). La page ne liste pas Haiku : les
  modèles absents de la liste ne gèrent pas l'effort, d'où l'absence de champ `effort` dans l'exemple
  Haiku. Opus 5.5 et Sonnet 5.5 sont en `medium` par défaut.
- Autres champs utiles : `tools` (liste des outils permis, tous par défaut), `maxTurns` (arrête
  l'agent après ce nombre de tours ; sa sortie est alors marquée partielle, v2.1.246 ou plus) et
  `omitClaudeMd: true` (lance l'agent sans les `CLAUDE.md` utilisateur, projet et local ; v2.1.271 ou
  plus). Par défaut un agent reçoit les `CLAUDE.md` de la session, sauf Explore et Plan.
- Claude choisit l'agent d'après son champ `description` : une description claire (cas d'emploi, modèle,
  effort) est ce qui déclenche la bonne délégation. On peut aussi le nommer dans la demande ou écrire
  `@agent-<nom>`.
- Priorité des emplacements : réglages gérés, option `--agents`, `.claude/agents/` (projet),
  `~/.claude/agents/` (utilisateur), puis les agents fournis par des plugins. Un fichier ajouté ou
  modifié est pris en compte en quelques secondes ; il faut redémarrer après la **création du premier
  fichier** dans un dossier `agents` qui n'existait pas au lancement de la session, après une
  modification dans un dossier ajouté avec `--add-dir`, et dans une session lancée avec
  `--disable-slash-commands` (qui ne surveille pas ces dossiers).
- Un `effortLevel` de premier niveau dans le `settings.json` utilisateur ne compte pas pour Opus 5.5 et
  les modèles publiés après lui (la page parle d'Opus 5.5 ; pour Sonnet 5.5, vérifiez avec `/effort`).
  Il s'applique encore à Opus 5, Fable 5.1 et avant. Dans les réglages de projet, locaux ou gérés, ou
  passé avec `--settings`, il s'applique à tous les modèles. Claude Code enregistre le niveau par modèle
  dans `modelSettings` quand vous le choisissez avec `/effort` ou le sélecteur de modèle.

### Table de décision : tâche vers agent

Cette table est **une convention proposée, non mesurée [à vérifier]**. La doc recommande Sonnet pour la
plupart des tâches de code, Opus pour l'architecture et le raisonnement en plusieurs étapes, et Haiku pour
les tâches simples
([costs#choose-the-right-model](https://code.claude.com/docs/en/costs#choose-the-right-model)) ;
l'affectation fine ci-dessous, et les niveaux d'effort retenus, sont des choix à ajuster sur vos
tâches. Les définitions sont dans [examples/agents/](../examples/agents/).

| Tâche | Agent | Modèle et effort | Pourquoi, et risque |
|---|---|---|---|
| Code du quotidien, modification mécanique, tests, documentation, rédaction, recherche web simple, reprise d'un travail déjà cadré | `executant` (choix par défaut) | Sonnet 5.5, `medium` | La doc juge Sonnet adapté à la plupart des tâches de code. Fixe `medium` quand la session tourne plus haut (sauf si `CLAUDE_CODE_EFFORT_LEVEL` est posée). Risque faible. |
| Extraction ou analyse de documents, journaux, tableaux ; recherche approfondie avec sources | `analyste` | Sonnet 5.5, `high` | L'exactitude prime sur la vitesse ; l'effort monté coûte plus de tokens de sortie. À réserver aux cas où l'extraction doit être fiable. |
| Architecture, logique centrale, sécurité et réseau, refactor entre fichiers, contre-revue, vérification factuelle | `expert` | Opus 5.5, `medium` | La doc réserve Opus à l'architecture et au raisonnement en plusieurs étapes. Opus 5.5 démarre en `medium` ; montez à `high` ou `xhigh` seulement si un gain est mesuré. Réservé à ces cas. |
| Gros volume simple et répétitif : tri, classement, filtrage, comptage, reformatage | `trieur` | Haiku 4.5 (pas d'effort) | La doc le propose pour les tâches simples. Une erreur isolée doit être sans gravité ; l'agent signale les cas ambigus. Outils limités à la lecture. Voir le retrait de Haiku plus bas. |
| Lecture ou recherche pure dans le code | agent intégré Explore | modèle de la session (plafonné à Opus sur l'API Claude) | Ne charge ni `CLAUDE.md` ni l'état git [officiel : [sub-agents#what-loads-at-startup](https://code.claude.com/docs/en/sub-agents#what-loads-at-startup)]. |
| Un travail court que la session peut faire directement | aucun sous-agent | modèle de la session | Un sous-agent repart avec son propre prompt, les `CLAUDE.md` et la même configuration de skills et de serveurs MCP, et ses requêtes comptent sur votre quota [officiel : [sub-agents#what-loads-at-startup](https://code.claude.com/docs/en/sub-agents#what-loads-at-startup), [costs#delegate-verbose-operations-to-subagents](https://code.claude.com/docs/en/costs#delegate-verbose-operations-to-subagents)]. |

Règles de conduite associées :

1. **Défaut : `executant`.** Monter d'un cran (`analyste`, puis `expert`) quand la tâche est difficile ou
   quand un premier essai échoue, pas par précaution.
2. **Baisser l'effort avant de changer de modèle**, et ne monter à `xhigh` ou `max` que si un gain est
   mesuré sur vos tâches [à vérifier : règle de l'auteur].
3. **Un modèle unique imposé à tous les sous-agents** par `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` **ignore le
   champ `model` de toutes vos définitions** (pas leur `effort`) et empêche Claude de passer un modèle à
   l'appel : à éviter si vous utilisez ces types
   ([sub-agents#run-every-subagent-on-one-model](https://code.claude.com/docs/en/sub-agents#run-every-subagent-on-one-model)).
4. **Ne changez pas le modèle de la session en cours de tâche** : déléguez à un type d'agent à la place
   (le cache du parent reste intact, voir [le cache](#le-cache--ce-qui-le-casse-ce-qui-le-garde)).
5. **`omitClaudeMd: true`** (exemple `trieur`) allège le prompt de départ, mais l'agent ne reçoit plus
   vos consignes de sécurité ni de confidentialité : à réserver à des lots sans donnée sensible, dont
   le brief contient tout ce qui est nécessaire.
6. **Variable d'effort et définitions** : si `CLAUDE_CODE_EFFORT_LEVEL` est posée, elle l'emporte sur le
   champ `effort` de tous vos agents. L'audit le signale (`effort-env-overrides-agents`). Retirez la
   variable, ou renoncez à l'effort par type d'agent.
7. **Mesurer** : sur les forfaits Pro, Max, Team et Enterprise, `/usage` attribue la consommation aux
   sous-agents [officiel :
   [costs#plan-usage-breakdown](https://code.claude.com/docs/en/costs#plan-usage-breakdown)]. Aucun gain
   chiffré n'est promis ici.

### Haiku et son retrait

La page des dépréciations
([platform.claude.com/docs/en/about-claude/model-deprecations](https://platform.claude.com/docs/en/about-claude/model-deprecations),
consultée le 2026-10-01) donne pour `claude-haiku-4-5-20251001` l'état « Active » et une date de retrait
**provisoire, au plus tôt le 2026-10-15** [officiel]. Quand Haiku sera retiré, remplacez
l'en-tête de `trieur.md` par :

```yaml
model: claude-sonnet-5-5
effort: low
```

(Sonnet 5.5 accepte `low`, voir la liste ci-dessus ; ce remplacement est une proposition de l'auteur
[à vérifier].)

### Installer les définitions

```bash
mkdir -p ~/.claude/agents
for f in ~/.claude/skills/claude-code-token-saver/examples/agents/*.md; do
  [ -e ~/.claude/agents/"$(basename "$f")" ] && echo "existe déjà, ignoré : $(basename "$f")" || cp "$f" ~/.claude/agents/
done
python ~/.claude/skills/claude-code-token-saver/scripts/audit.py --top 0 | grep "Sous-agents"
```

La boucle n'écrase aucun agent existant du même nom (comparez à la main en cas de doublon). Variante
PowerShell : [INSTALLATION.md](INSTALLATION.md#installer-les-types-dagents-facultatif). Si
`~/.claude/agents/` n'existait pas, redémarrez Claude Code. Ensuite, demandez par exemple : « Utilise
l'agent analyste pour extraire les montants de ce PDF. » La ligne affichée doit indiquer 3 sous-agents
avec effort déclaré (executant, analyste, expert), en plus de ceux que vous aviez déjà. Le paragraphe
[examples/CLAUDE.md.example](../examples/CLAUDE.md.example) explique à Claude quand choisir chacun.

## Leviers dans les fichiers d'instructions

- **CLAUDE.md** est chargé à chaque session ; visez moins de 200 lignes par fichier. Les imports
  `@fichier` organisent le texte mais ne réduisent rien : les fichiers importés sont chargés au
  lancement. [officiel : [memory](https://code.claude.com/docs/en/memory)]
- **Procédures longues** : mettez-les dans un skill (chargé à la demande) plutôt que dans CLAUDE.md.
  [officiel : [costs#move-instructions-from-claudemd-to-skills](https://code.claude.com/docs/en/costs#move-instructions-from-claudemd-to-skills)]
- **Règles par zone du code** : `.claude/rules/` avec un champ `paths:` ne se charge que quand un
  fichier correspondant est lu ; une règle sans `paths` est chargée à chaque session. [officiel :
  [memory](https://code.claude.com/docs/en/memory)]
- **Instructions de compaction** : un bloc `# Compact instructions` dans CLAUDE.md dit quoi garder
  quand Claude résume la conversation. [officiel : [costs#manage-context-proactively](https://code.claude.com/docs/en/costs#manage-context-proactively)]
  Modèle : [examples/CLAUDE.md.example](../examples/CLAUDE.md.example).
- **Modifier CLAUDE.md en cours de session** ne casse pas le cache mais ne s'applique qu'après
  `/clear`, `/compact` ou un redémarrage. [officiel : [prompt-caching#editing-claudemd-mid-session](https://code.claude.com/docs/en/prompt-caching#editing-claudemd-mid-session)]
- **Audit des instructions** : `/doctor prompt-audit` (v2.1.283 ou plus) signale consignes périmées,
  références à des fichiers absents et contradictions, sans rien modifier tant que vous ne le demandez
  pas. [officiel : [memory](https://code.claude.com/docs/en/memory)]

## Le cache : ce qui le casse, ce qui le garde

Le cache de prompt réduit automatiquement le coût du contenu répété. Sur un abonnement, dans le quota inclus,
la conversation principale a un cache d'une heure ; les sous-agents, la compaction et les workflows
ont cinq minutes. Si vous passez sur des crédits d'usage, la conversation principale tombe aussi à
cinq minutes. [officiel : [prompt-caching#cache-lifetime](https://code.claude.com/docs/en/prompt-caching#cache-lifetime)]

| Casse le cache (la requête suivante relit tout au tarif plein) | Garde le cache |
|---|---|
| Changer de modèle (aussi un skill dont l'en-tête fixe `model:`) | Modifier CLAUDE.md |
| Activer le mode rapide | Changer de mode de permission ou de style de sortie |
| Compacter (par conception) | Appeler un skill |
| Accumuler beaucoup d'images | `/rewind`, `/recap` |
| Mettre à jour Claude Code | Lancer un sous-agent (son cache est à part, celui du parent est intact) |
| Connecter ou retirer un serveur MCP, ou activer un plugin qui en fournit, en cours de session (sans recherche d'outils) | Changer d'effort sur Opus 5.5, Sonnet 5.5 et Fable 5.1, sous conditions (voir plus haut) |
| Changer d'effort sur les autres modèles | Retirer un outil ou un serveur MCP quand la recherche d'outils est active |

[officiel : [prompt-caching](https://code.claude.com/docs/en/prompt-caching), sections
« Actions that invalidate the cache » et « Actions that keep the cache »]. Conséquence pratique :
choisissez modèle et effort **au début** de la session, et ne laissez pas une grosse session
inactive plus longtemps que la durée du cache. Sur les forfaits Pro et Max, Claude Code propose de
reprendre une grosse session à partir d'un résumé après une longue pause. [officiel :
[costs#why-usage-climbs-in-a-long-session](https://code.claude.com/docs/en/costs#why-usage-climbs-in-a-long-session)]

## Actions manuelles dans l'application

Ces actions ne se font pas dans un fichier. Libellés tels qu'ils sont décrits dans la doc de
l'application de bureau ([desktop](https://code.claude.com/docs/en/desktop)) ; si un libellé a
changé dans votre version, cherchez le mot en gras.

**Couper un connecteur inutile**

1. Ouvrez une session **locale ou SSH** dans l'application de bureau (le bouton **+** n'existe pas en session cloud ni WSL).
2. Cliquez sur le bouton **+** à côté de la zone de saisie, puis sur **Connectors**.
3. Choisissez **Manage connectors** (ou allez dans **Settings** puis **Connectors**).
4. Déconnectez les connecteurs que vous n'utilisez pas.
5. Vérification : demandez à Claude quels connecteurs sont configurés dans la session, ou rouvrez
   **+** puis **Connectors** ; le connecteur ne doit plus être listé. Les connecteurs du compte se
   gèrent aussi sur [claude.ai/customize/connectors](https://claude.ai/customize/connectors), page
   que la doc MCP cite pour ajouter ou reconnecter un connecteur.

**Désactiver des skills et plugins du compte claude.ai**

1. Cliquez sur **Customize** dans la barre latérale.
2. Désactivez les skills et plugins dont vous ne vous servez pas.
3. Attention : cette configuration est partagée avec l'onglet **Cowork** de l'application, qui y
   puise ses skills, plugins et connecteurs. Désactivez seulement ce qui ne sert nulle part.
4. Vérification : au bout d'environ dix minutes (ou dans une nouvelle session), `/skills` ne doit plus
   lister le skill ; Claude Code resynchronise les skills du compte environ toutes les dix minutes.
   Les skills synchronisés se trouvent dans `~/.claude/skills/synced/` (`syncClaudeAiSkills: false`
   arrête cette synchro, au prix de perdre ces skills).

Les skills **de plugins** ne se règlent pas avec `skillOverrides` : passez par `/plugin`.
[officiel : [skills](https://code.claude.com/docs/en/skills),
[settings-reference#skilloverrides](https://code.claude.com/docs/en/settings-reference#skilloverrides)]

**Choisir modèle et effort pour la session**

1. Dans l'application de bureau, ouvrez le sélecteur de modèle (raccourci **Cmd+Maj+I** sur macOS ;
   voir le tableau des raccourcis de la page desktop pour Windows) et choisissez le modèle de la
   session.
2. Ouvrez le menu d'effort (**Cmd+Maj+E** sur macOS) et choisissez le niveau.
3. Faites-le au début de la session (voir [le cache](#le-cache--ce-qui-le-casse-ce-qui-le-garde)).

Dans le terminal, `/effort` et `/model` proposent un curseur d'effort : `Entrée` enregistre le niveau
comme défaut du modèle, `s` ne l'applique qu'à la session (v2.1.257 ou plus). [officiel :
[model-config#adjust-effort-level](https://code.claude.com/docs/en/model-config#adjust-effort-level)]

**Voir où vous en êtes**

- L'anneau d'usage à côté du sélecteur de modèle montre le contexte de la session et l'usage du
  forfait. [officiel : [desktop](https://code.claude.com/docs/en/desktop)]

**Poser une question annexe sans alourdir la session**

- Ouvrez un side chat avec `Ctrl+;` (Windows) ou `Cmd+;` (macOS), ou tapez `/btw`. Il lit la session
  mais n'ajoute rien à la conversation principale, et il coûte peu tant que le cache est chaud. Il n'a
  pas accès aux outils. [officiel : [desktop](https://code.claude.com/docs/en/desktop),
  [interactive-mode#side-questions-with-btw](https://code.claude.com/docs/en/interactive-mode#side-questions-with-btw)]

**Abandonner une piste**

- `/rewind` (ou deux fois Échap) revient à un point précédent de la conversation et du code ;
  il garde le cache (voir tableau). Après une exploration qui a mal tourné, c'est plus propre qu'un
  `/compact`. [officiel : [costs#work-efficiently-on-complex-tasks](https://code.claude.com/docs/en/costs#work-efficiently-on-complex-tasks),
  [prompt-caching#rewinding-the-conversation](https://code.claude.com/docs/en/prompt-caching#rewinding-the-conversation)]

## Workflow de session

1. **Sessions courtes et ciblées.** `/clear` entre deux tâches sans lien : il ne coûte rien, alors
   qu'un historique périmé alourdit chaque message suivant. Faites `/rename` avant pour retrouver la
   session avec `/resume`. [officiel : [costs#manage-context-proactively](https://code.claude.com/docs/en/costs#manage-context-proactively)]
2. **`/compact` avec consigne** quand il faut continuer : `/compact Focus on ...`. Compacter un
   gros contexte est une grosse requête : lancez-le à une pause naturelle entre deux tâches plutôt
   qu'en plein milieu d'une tâche. [officiel :
   [prompt-caching#compacting-the-conversation](https://code.claude.com/docs/en/prompt-caching#compacting-the-conversation)]
3. **Prompts précis.** « Ajoute la validation d'entrée dans la fonction de connexion de auth.ts »
   déclenche moins de lectures que « améliore ce dépôt ». [officiel : [costs#write-specific-prompts](https://code.claude.com/docs/en/costs#write-specific-prompts)]
4. **Mode plan avant un gros chantier** (`Maj+Tab`) : évite de refaire le travail si la direction était
   mauvaise. [officiel : [costs#work-efficiently-on-complex-tasks](https://code.claude.com/docs/en/costs#work-efficiently-on-complex-tasks)]
5. **Sous-agents seulement pour les gros volumes** : tests verbeux, journaux, lecture de nombreux
   fichiers. Le volume reste dans le contexte du sous-agent et seul un résumé revient, mais chaque
   sous-agent part avec son propre prompt, les CLAUDE.md (sauf Explore et Plan) et la même
   configuration de skills et de serveurs MCP, et ses requêtes comptent sur votre quota. [officiel :
   [sub-agents#what-loads-at-startup](https://code.claude.com/docs/en/sub-agents#what-loads-at-startup),
   [context-window](https://code.claude.com/docs/en/context-window),
   [costs#delegate-verbose-operations-to-subagents](https://code.claude.com/docs/en/costs#delegate-verbose-operations-to-subagents)]
6. **Agent Explore pour la recherche pure** : lui et l'agent Plan ne chargent ni les CLAUDE.md ni
   l'instantané git. Explore hérite du modèle de la session (plafonné à Opus sur l'API Claude).
   [officiel : [sub-agents](https://code.claude.com/docs/en/sub-agents)]
7. **Rendus condensés.** Demandez au sous-agent un résumé (conclusions, chemins, extraits utiles) et
   non la copie des fichiers ou des journaux. Un brief court évite aussi de gonfler son contexte de
   départ. [officiel : [costs#delegate-verbose-operations-to-subagents](https://code.claude.com/docs/en/costs#delegate-verbose-operations-to-subagents)
   (seul un résumé revient dans la conversation principale) ; pour le brief court,
   [costs#agent-team-token-costs](https://code.claude.com/docs/en/costs#agent-team-token-costs), qui le dit des équipiers
   d'agents : tout le prompt de lancement s'ajoute à leur contexte]
8. **Sorties filtrées, lectures ciblées.** Pour les sorties volumineuses, un hook qui filtre est le
   levier documenté (voir le tableau des réglages). Le reste est du bon sens : filtrer avant de lire
   (`grep`, `head`, `tail`), lire un gros fichier par plage quand la zone est connue, ne pas relire
   un fichier inchangé [à vérifier : non documenté comme levier]. Un article tiers va dans le même
   sens, en recommandant de viser la fonction utile plutôt qu'un fichier de 2 000 lignes entier
   [rapporté : [codersera](https://codersera.com/blog/how-to-stretch-claude-code-usage-limits-2026/),
   publiée le 2026-06-26, mise à jour le 2026-08-13].
9. **Un modèle et un effort par tâche, choisis au début.** Sonnet pour l'exécution courante, un modèle
   plus fort pour architecture et raisonnement multi-étapes ; la doc le recommande ainsi. Évitez de
   changer de modèle au milieu d'une tâche : le contexte est relu sans cache. Pour varier par tâche sans
   toucher à la session, déléguez à un type d'agent défini avec `model` et `effort`
   ([table de décision](#table-de-décision--tâche-vers-agent)). [officiel : [costs#choose-the-right-model](https://code.claude.com/docs/en/costs#choose-the-right-model),
   [prompt-caching#switching-models](https://code.claude.com/docs/en/prompt-caching#switching-models)]
10. **Planifiées et équipes : surveiller.** Une tâche planifiée renvoie tout le contexte à chaque
    échéance ; un équipier d'agent consomme tant qu'il n'est pas arrêté. [officiel : [costs](https://code.claude.com/docs/en/costs)]

## Ce qui est écarté et pourquoi

| Piste | Pourquoi elle est écartée par défaut |
|---|---|
| Baisser `BASH_MAX_OUTPUT_LENGTH` (défaut 30 000 caractères) ou `MAX_MCP_OUTPUT_TOKENS` | Une sortie tronquée peut cacher l'erreur qu'on cherche : risque de qualité pour un gain mal défini. Préférez un hook qui filtre. [officiel : [env-vars](https://code.claude.com/docs/en/env-vars)] |
| `MAX_THINKING_TOKENS` ou couper la réflexion | Impossible de couper la réflexion sur Opus 5.5, Sonnet 5.5 et les modèles Fable ; sur les modèles à raisonnement adaptatif, les budgets non nuls sont ignorés : utilisez l'effort. [officiel : [costs#adjust-extended-thinking](https://code.claude.com/docs/en/costs#adjust-extended-thinking)] |
| `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` | Impose un modèle même aux agents qui déclarent le leur (contre-revue sur un modèle plus fort, par exemple) : perte de qualité possible. [officiel : [sub-agents#run-every-subagent-on-one-model](https://code.claude.com/docs/en/sub-agents#run-every-subagent-on-one-model)] |
| Haiku comme défaut des sous-agents | Perte de qualité sur les tâches non triviales ; la doc ne le suggère que pour les tâches simples. [officiel : [costs#choose-the-right-model](https://code.claude.com/docs/en/costs#choose-the-right-model)] |
| `subagentPromptCacheTtl: 1h` | L'écriture d'un cache d'une heure coûte plus cher qu'un cache de cinq minutes : rentable seulement si le sous-agent reste souvent inactif entre deux appels. [officiel : [prompt-caching#choose-the-ttl-yourself](https://code.claude.com/docs/en/prompt-caching#choose-the-ttl-yourself)] |
| `FORCE_PROMPT_CACHING_5M` ou `DISABLE_PROMPT_CACHING` | Font perdre le cache d'une heure de la conversation principale, ou tout cache. Outils de diagnostic, pas d'économie. [officiel : [prompt-caching](https://code.claude.com/docs/en/prompt-caching)] |
| `disableBundledSkills` | Retire les skills intégrés (dont `/verify` et `/claude-api`) pour un gain faible. [officiel : [skills](https://code.claude.com/docs/en/skills)] |
| `CLAUDE_CODE_DISABLE_1M_CONTEXT` | `autoCompactWindow` donne un effet proche en gardant la marge de la grande fenêtre pour les tâches qui en ont besoin. [officiel : [model-config](https://code.claude.com/docs/en/model-config)] |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` | La doc ne le présente pas comme un levier de tokens ; il désactive en revanche plusieurs fonctions, dont la synchronisation des skills du compte et les artefacts. [officiel : [skills](https://code.claude.com/docs/en/skills), [env-vars](https://code.claude.com/docs/en/env-vars)] |
| Hook `PreCompact` qui bloque la compaction automatique | Le contexte grossit jusqu'à la limite du modèle, puis la requête échoue. Pour sauvegarder avant compaction, gardez le hook mais faites-le sortir avec le code 0 ; `PostCompact` tourne après coup (utile pour exporter le résumé) et ne peut pas bloquer. [officiel : [hooks#precompact](https://code.claude.com/docs/en/hooks#precompact)] |
| Réécrire d'office les CLAUDE.md et les skills pour les raccourcir | Risque de supprimer une consigne utile ; à faire seulement sur demande, avec relecture. |

## À vérifier

- Comment le quota d'un abonnement pondère les tokens d'entrée, de sortie et de cache selon le
  modèle : non documenté. [à vérifier] Servez-vous de `/usage` (touche `w`) pour voir la part des
  skills, sous-agents, MCP et boucles sur sept jours, et les comportements qui pèsent 10 % ou plus.
- Le gain réel de chaque levier sur **votre** quota : seule une mesure comparée, sur des tâches
  comparables, le dit. [à vérifier]

- Les gains annoncés par des blogs tiers (pourcentages de tokens économisés) : [rapporté], non
  repris ici.

## Mesurer

| Quoi | Commande dans Claude Code | Ce que vous voyez |
|---|---|---|
| Contexte de la session | `/context` | Grille d'usage, taille du listing des skills (budget appliqué), des serveurs MCP et des fichiers mémoire |
| Quota et coût | `/usage`, puis `w` pour sept jours | Jauges d'usage du forfait, répartition par skills, sous-agents, MCP, boucles ; comportements à 10 % ou plus |
| Coût des skills | `/skill-doctor`, `/doctor` | Coût en contexte de chaque skill et usage ; estimation du listing |
| Configuration | `python scripts/audit.py --save avant.json`, puis `--compare avant.json` | Nombre de skills, taille du listing, serveurs MCP, réglages présents ou absents, et les deltas |

[officiel : [costs#track-your-costs](https://code.claude.com/docs/en/costs#track-your-costs),
[commands](https://code.claude.com/docs/en/commands)]. Comparez dans une **nouvelle** session et
sur des tâches comparables : un seul essai ne prouve rien.

## Sources consultées le 2026-10-01

Pages officielles (`https://code.claude.com/docs/en/<page>.md`) : `costs`, `prompt-caching`,
`context-window`, `memory`, `model-config`, `sub-agents`, `skills`, `mcp`, `env-vars`,
`settings-reference`, `hooks`, `commands`, `interactive-mode`, `desktop`.
Tarifs : [platform.claude.com/docs/en/about-claude/pricing](https://platform.claude.com/docs/en/about-claude/pricing)
(consultée, aucun prix repris ici).
Dépréciations de modèles : [platform.claude.com/docs/en/about-claude/model-deprecations](https://platform.claude.com/docs/en/about-claude/model-deprecations)
(consultée, date de retrait provisoire de Haiku 4.5 reprise).
Retours tiers [rapporté] : [codersera](https://codersera.com/blog/how-to-stretch-claude-code-usage-limits-2026/)
(publiée le 2026-06-26, mise à jour le 2026-08-13) ; [thepromptshelf](https://thepromptshelf.dev/blog/claude-code-usage-limits-explained-2026)
(consultée le 2026-10-01, reprend pour l'essentiel la doc officielle).

Voir aussi : [CONFIGURATION.md](CONFIGURATION.md), [USAGE.md](USAGE.md), [LIMITATIONS.md](LIMITATIONS.md).
