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
| Niveau d'effort | `/effort`, sélecteur de modèle, `CLAUDE_CODE_EFFORT_LEVEL` | Les niveaux élevés raisonnent plus longtemps (tokens de sortie). Opus 5.5 et Sonnet 5.5 démarrent en `medium`. Sur Opus 5.5, Sonnet 5.5 et Fable 5.1, changer d'effort ne casse pas le cache (abonnement ou clé API ; pas sur Amazon Bedrock, Google Cloud, une passerelle Claude apps, ni avec `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS` ou une configuration HIPAA). | Faible en `medium` pour les tâches courantes ; montez à `high` ou `xhigh` pour les tâches difficiles. | [officiel] [model-config#adjust-effort-level](https://code.claude.com/docs/en/model-config#adjust-effort-level), [prompt-caching#changing-effort-level](https://code.claude.com/docs/en/prompt-caching#changing-effort-level) |
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

Attention à une erreur courante : sur Opus 5.5 et les modèles suivants, la clé `effortLevel` placée
au premier niveau du `settings.json` **utilisateur** n'est pas prise en compte (elle correspond à
l'ancienne forme). Choisissez l'effort avec `/effort` ou le sélecteur de modèle, qui écrivent
`modelSettings`, ou avec `CLAUDE_CODE_EFFORT_LEVEL`. [officiel :
[model-config#adjust-effort-level](https://code.claude.com/docs/en/model-config#adjust-effort-level)]

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
9. **Un modèle par tâche, choisi au début.** Sonnet pour l'exécution courante, un modèle plus fort
   pour architecture et raisonnement multi-étapes ; la doc le recommande ainsi. Évitez de changer de
   modèle au milieu d'une tâche : le contexte est relu sans cache. [officiel : [costs#choose-the-right-model](https://code.claude.com/docs/en/costs#choose-the-right-model),
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
Retours tiers [rapporté] : [codersera](https://codersera.com/blog/how-to-stretch-claude-code-usage-limits-2026/)
(publiée le 2026-06-26, mise à jour le 2026-08-13) ; [thepromptshelf](https://thepromptshelf.dev/blog/claude-code-usage-limits-explained-2026)
(consultée le 2026-10-01, reprend pour l'essentiel la doc officielle).

Voir aussi : [CONFIGURATION.md](CONFIGURATION.md), [USAGE.md](USAGE.md), [LIMITATIONS.md](LIMITATIONS.md).
