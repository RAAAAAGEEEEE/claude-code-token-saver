# Configuration

Le skill n'a aucune configuration propre : pas de clé, pas de fichier `.env`. Ce document décrit
(1) les réglages de Claude Code qu'il recommande et (2) ce que l'audit lit.

## Réglages recommandés

Fichier d'exemple : [../examples/settings.example.json](../examples/settings.example.json). À
fusionner dans votre `~/.claude/settings.json` **sans écraser vos clés existantes**, après une
sauvegarde ([USAGE.md](USAGE.md#le-script-de-sauvegarde)). Les noms de skills de l'exemple sont
fictifs. Les réglages s'appliquent aux nouvelles sessions.

| Clé | Valeur d'exemple | Effet | Pour qui | Source |
|---|---|---|---|---|
| `autoCompactWindow` | `400000` | Compacte à ce nombre de tokens au lieu d'attendre la limite du modèle (environ 967 000 sur les modèles à fenêtre de 1 million). Plage 100 000 à 1 000 000. Équivalent : `/autocompact 400k`. | Sessions longues. Choisissez la valeur selon vos tâches : plus bas, plus de compactions. | [model-config](https://code.claude.com/docs/en/model-config), [settings-reference](https://code.claude.com/docs/en/settings-reference) |
| `env.CLAUDE_CODE_SUBAGENT_MODEL` | `"sonnet"` | Modèle par défaut des sous-agents qui n'en déclarent pas. Un modèle passé à l'appel ou déclaré dans l'agent reste prioritaire. | Si vos sous-agents font de la lecture, de la recherche, des tests. | [sub-agents](https://code.claude.com/docs/en/sub-agents), [env-vars](https://code.claude.com/docs/en/env-vars) |
| `skillOverrides` | `{"nom": "name-only"}` | `name-only` : Claude voit le nom sans description. `user-invocable-only` : caché de Claude, `/nom` possible. `off` : caché partout. Ne s'applique pas aux skills de plugins. | Skills rarement utiles ; repérez-les avec `/skill-doctor`. | [skills](https://code.claude.com/docs/en/skills), [settings-reference](https://code.claude.com/docs/en/settings-reference) |

Réglages qui existent mais ne sont **pas** dans l'exemple, par prudence : voir
[BONNES-PRATIQUES.md](BONNES-PRATIQUES.md#ce-qui-est-écarté-et-pourquoi).

### Effort : ne pas passer par `effortLevel` sur Opus 5.5

Sur Opus 5.5 et les modèles suivants, un `effortLevel` de premier niveau dans le `settings.json`
**utilisateur** est ignoré ; dans les réglages de projet, locaux ou gérés, il s'applique à tous les
modèles. Le détail et la marche à suivre sont dans
[BONNES-PRATIQUES.md](BONNES-PRATIQUES.md#leviers-dans-les-réglages).

### Effort et modèle par type de sous-agent

La documentation ne décrit qu'un paramètre `model` à l'appel de l'outil Agent : l'effort d'un
sous-agent se fixe dans sa définition (champ `effort`), sauf si `CLAUDE_CODE_EFFORT_LEVEL` est posée
(elle l'emporte). Quatre définitions génériques sont fournies dans
[../examples/agents/](../examples/agents/) (`executant`, `analyste`, `expert`, `trieur`). À copier dans
`~/.claude/agents/` ; la table de décision et la procédure d'installation sont dans
[BONNES-PRATIQUES.md](BONNES-PRATIQUES.md#choisir-le-sous-agent-le-modèle-et-leffort).

### Paragraphe CLAUDE.md

Modèle : [../examples/CLAUDE.md.example](../examples/CLAUDE.md.example) (économie de tokens, choix
du sous-agent, instructions de compaction). Ajoutez-le à votre
`CLAUDE.md` (global ou de projet) ; il ne s'applique qu'après `/clear`, `/compact` ou un redémarrage.

## Ce que l'audit lit

| Fichier | Lu pour | Jamais affiché |
|---|---|---|
| `<config>/settings.json`, `.claude/settings.json`, `.claude/settings.local.json` | clés de la liste blanche (ci-dessous) | commandes de hooks, valeurs du bloc `env` hors liste blanche, `apiKeyHelper`, tout autre champ |
| `<config>/skills/*/SKILL.md`, `.claude/skills/*/SKILL.md`, `skills/synced/*/SKILL.md` | nom, description, `when_to_use`, `disable-model-invocation` | le corps des skills |
| `<config>/CLAUDE.md`, `CLAUDE.md`, `.claude/CLAUDE.md`, `CLAUDE.local.md` | nombre de lignes, de caractères, d'imports | le contenu |
| `<config>/rules/`, `.claude/rules/` | présence d'un champ `paths` | le contenu |
| `<config>/agents/*.md`, `.claude/agents/*.md` | présence d'un champ `model` et d'un champ `effort` (jamais leur valeur) | le contenu |
| `<config>/.claude.json` ou `~/.claude.json`, `.mcp.json` | noms des serveurs MCP, liste des serveurs désactivés du projet | commandes, arguments, `env`, en-têtes, URL |

Clés de `settings.json` lues : `autoCompactWindow`, `skillOverrides`, `skillListingMaxDescChars`,
`effortLevel`, `modelSettings` (niveaux seulement), `ultracode`, `hooks` (noms d'événements et nombre
de hooks), et dans `env` seulement : `CLAUDE_CODE_AUTO_COMPACT_WINDOW`, `CLAUDE_CODE_SUBAGENT_MODEL`,
`CLAUDE_CODE_SUBAGENT_MODEL_FORCE`, `CLAUDE_CODE_EFFORT_LEVEL`, `ENABLE_TOOL_SEARCH`,
`CLAUDE_CODE_DISABLE_1M_CONTEXT`, `DISABLE_PROMPT_CACHING` (et variantes `_HAIKU`, `_SONNET`,
`_OPUS`, `_FABLE`), `FORCE_PROMPT_CACHING_5M`, `SLASH_COMMAND_TOOL_CHAR_BUDGET`. Les mêmes noms sont
aussi cherchés dans l'environnement du shell qui lance le script.

Priorité appliquée : `settings.local.json`, puis `.claude/settings.json`, puis `settings.json`
utilisateur ; pour une variable présente à la fois dans un bloc `env` et dans l'environnement du
shell, la valeur du fichier l'emporte (comme la plupart du temps dans Claude Code, d'après la page
[env-vars](https://code.claude.com/docs/en/env-vars#precedence)). Les réglages gérés par une organisation et les options de ligne de commande ne sont pas
lus.

Voir aussi : [LIMITATIONS.md](LIMITATIONS.md), [PRIVACY_AND_SECURITY.md](PRIVACY_AND_SECURITY.md).
