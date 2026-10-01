# Usage

## Dans Claude Code

Demandez en langage courant ; le skill se charge sur des phrases comme :

- « Mon quota Claude Code part vite, fais un audit de consommation. »
- « Audit de consommation puis applique les changements sûrs. »
- « J'ai appliqué les réglages hier, ça a servi à quelque chose ? »
- « Quel sous-agent, quel modèle et quel effort pour cette tâche ? » : le skill s'appuie sur la
  [table de décision](BONNES-PRATIQUES.md#table-de-décision--tâche-vers-agent) et propose d'installer
  les définitions de `examples/agents/` (avec votre accord).
- « How do I reduce Claude Code token usage without losing quality? »

Le déroulé complet (audit, rapport, application avec accord, mesure) est décrit dans
[../SKILL.md](../SKILL.md).

## Le script d'audit

```bash
python scripts/audit.py [--config-dir DIR] [--project-dir DIR] [--json] [--save FICHIER] [--compare FICHIER] [--top N]
```

| Option | Rôle |
|---|---|
| `--config-dir DIR` | Dossier de configuration. Défaut : `$CLAUDE_CONFIG_DIR`, sinon `~/.claude`. |
| `--project-dir DIR` | Projet à auditer (`.claude/`, `CLAUDE.md`, `.mcp.json`). Défaut : dossier courant. |
| `--json` | Rapport au format JSON sur la sortie standard. |
| `--save FICHIER` | Écrit le rapport JSON dans ce fichier, pour une comparaison ultérieure. |
| `--compare FICHIER` | Après le rapport, affiche les écarts avec un fichier écrit par `--save`. |
| `--top N` | Nombre de skills les plus lourds à lister (défaut 10, 0 pour aucun). |

Codes de sortie : 0 si l'audit s'est déroulé (même avec des constats), 2 si le dossier de
configuration est introuvable ou si `--save` ne peut pas écrire.

### Lire le rapport

- **Mesures** : nombres et tailles estimées (environ 4 caractères par token). Elles ne remplacent pas
  `/context`.
- **Constats** : classés P1 (levier le plus utile), P2, P3 (information ou point mineur). Chaque
  constat donne ce qui est observé, pourquoi c'est coûteux, l'action et la page officielle.
- Identifiants de constats : `compact-window`, `precompact-hook`, `tool-search-off`,
  `prompt-cache-off`, `subagent-model`, `subagent-force`, `effort-heavy`, `effort-toplevel-ignored`,
  `agents-no-effort`, `effort-env-overrides-agents`, `ultracode`, `skills-many`, `skills-still-many`, `skills-truncated`, `mcp-many`,
  `mcp-browser-duplicates`, `memory-long`, `rules-unconditional`, `config-unreadable`.

### Exemple avant et après

```bash
python scripts/audit.py --save avant.json
python scripts/backup.py ~/.claude/settings.json
# modifier settings.json, puis ouvrir une NOUVELLE session
python scripts/audit.py --compare avant.json
```

La section « Comparaison » liste chaque mesure (avant, après, écart) et les constats résolus ou
nouveaux. Un écart négatif est une économie de contexte ; ce n'est pas une économie de quota
démontrée (voir [LIMITATIONS.md](LIMITATIONS.md)).

## Le script de sauvegarde

```bash
python scripts/backup.py ~/.claude/settings.json
```

Crée `settings.json.bak-AAAA-MM-JJTHH-MM-SS` à côté de l'original (tirets à la place des deux-points
pour Windows), affiche le chemin, ne modifie jamais l'original et n'écrase jamais une sauvegarde.
Code de sortie 1 si une copie échoue.

## Mesurer dans Claude Code

Les commandes à relever avant et après (`/context`, `/usage`, `/doctor`, `/skill-doctor`) sont
décrites dans [BONNES-PRATIQUES.md](BONNES-PRATIQUES.md#mesurer).

## Sans Python

Lisez à la main, dans l'ordre :

1. `~/.claude/settings.json` : présence de `autoCompactWindow`, de `skillOverrides`, d'un bloc
   `hooks.PreCompact`, de `env.CLAUDE_CODE_SUBAGENT_MODEL`, de `env.CLAUDE_CODE_EFFORT_LEVEL`.
2. Dans Claude Code : `/skills` (touche `t` pour trier par taille), `/skill-doctor`, `/mcp`,
   `/context`, `/doctor`.
3. Les `CLAUDE.md` : nombre de lignes (moins de 200 recommandé).
4. `~/.claude/agents/` et `.claude/agents/` : les fichiers sans champ `model`, et l'absence de tout
   fichier avec un champ `effort` (voir
   [BONNES-PRATIQUES.md](BONNES-PRATIQUES.md#choisir-le-sous-agent-le-modèle-et-leffort)).

Puis suivez les modes 2 à 4 de [../SKILL.md](../SKILL.md) en signalant dans le rapport que l'audit
a été manuel.

Voir aussi : [CONFIGURATION.md](CONFIGURATION.md), [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
