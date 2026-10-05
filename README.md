# claude-code-token-saver

**In English.** A Claude Code skill that cuts token and quota usage **without losing quality**. It
runs a read-only audit of your Claude Code setup (`settings.json`, `CLAUDE.md`, skills, MCP servers,
subagents, hooks), ranks what to fix, applies changes only with your approval and a timestamped
backup, then measures before and after. It also ships four generic subagent definitions and a
decision table that proposes the agent, model and effort per task (an unmeasured convention). Every lever is labelled *official*, *reported* or *to verify*
with a dated source (official docs checked on 2026-10-01, prices and measurements on 2026-10-05). Python standard library only, no network
access, no secret ever printed. Documentation is in French.

Skill Claude Code qui réduit la consommation de tokens et de quota **sans perte de qualité** : audit
en lecture seule de la configuration, rapport priorisé, application avec sauvegarde horodatée et
accord de l'utilisateur, mesure avant et après, et choix du bon sous-agent, modèle et effort selon la
tâche.

## Comment ça marche

Pour un débutant, trois gestes, et aucun copier-coller du dépôt dans la conversation :

1. **Installer le skill une fois** : `git clone https://github.com/RAAAAAGEEEEE/claude-code-token-saver ~/.claude/skills/claude-code-token-saver`
   (disponible dans tous vos projets), ou le même clone dans `.claude/skills/claude-code-token-saver` du
   dépôt d'un projet (disponible dans ce projet seulement). Détail : [docs/INSTALLATION.md](docs/INSTALLATION.md).
2. **Le demander** : dans n'importe quelle session Claude Code, écrivez simplement « audite ma
   consommation de tokens », ou tapez `/claude-code-token-saver`.
3. **Se laisser guider** : Claude charge le skill tout seul d'après sa description, vous pose d'abord
   quelques questions de cadrage (votre accès à Claude, votre priorité, votre usage, ce que vous refusez de
   sacrifier), puis suit pas à pas l'audit, le rapport, l'application avec votre accord et la mesure.

C'est le fonctionnement de tous les skills Claude Code : un dossier avec un `SKILL.md` placé dans
`~/.claude/skills/<nom>/` (personnel) ou `.claude/skills/<nom>/` (projet) ; Claude le charge
automatiquement quand votre demande correspond à sa `description`, et `/<nom>` le lance à la main.
[officiel : [skills](https://code.claude.com/docs/en/skills#where-skills-live), page consultée le
2026-10-05]

## Le problème

Claude Code renvoie toute la conversation à chaque requête. Une session ouverte toute la journée, des
dizaines de skills dont la description est envoyée à chaque session et à chaque sous-agent, des
serveurs MCP en double, un hook qui bloque la compaction : le quota part vite, et rien ne le dit
clairement. Les conseils qui circulent mélangent des leviers officiels, des réglages qui n'existent
plus et des astuces qui dégradent le résultat.

## Pour qui

Les utilisateurs de Claude Code (terminal ou application de bureau) dont le quota ou la facture
monte, en particulier avec beaucoup de skills, de serveurs MCP et de sous-agents.

## Ce qu'il apporte

- Un **script d'audit** portable (`scripts/audit.py`) : nombre de skills et taille de leurs
  descriptions, serveurs MCP, réglages présents ou absents, taille des `CLAUDE.md`, sous-agents sans
  modèle, hooks qui peuvent bloquer la compaction. Il n'affiche jamais de secret.
- Une **mesure de la dépense réelle** (`audit.py --depense --jours N`, lecture seule) : coût estimé en
  équivalent API par projet, par modèle et pour les sous-agents, lu dans les transcriptions
  ([docs/USAGE.md](docs/USAGE.md#mesurer-la-dépense-réelle)), et un exemple mesuré sur un usage réel
  ([docs/BONNES-PRATIQUES.md](docs/BONNES-PRATIQUES.md#exemple-mesuré-sur-un-usage-réel--où-part-largent)).
- Un **déroulé** que Claude suit : audit, rapport priorisé, application avec accord, mesure.
- Des **leviers sourcés** ([docs/BONNES-PRATIQUES.md](docs/BONNES-PRATIQUES.md)), chacun avec son
  risque pour la qualité et son étiquette de preuve ; ce qui est écarté, et pourquoi.
- Un **choix par tâche du sous-agent, du modèle et de l'effort** : la documentation ne décrit qu'un
  paramètre `model` à l'appel de l'outil Agent, donc des types d'agents sont le moyen documenté de
  fixer l'effort d'un sous-agent. Quatre définitions génériques (`executant`, `analyste`, `expert`, `trieur`) dans
  [examples/agents/](examples/agents/), une table de décision tâche vers agent
  ([docs/BONNES-PRATIQUES.md](docs/BONNES-PRATIQUES.md#choisir-le-sous-agent-le-modèle-et-leffort)), et
  un constat d'audit si aucune définition ne fixe l'effort.
- Des **exemples** génériques de `settings.json` et de paragraphe `CLAUDE.md`
  ([examples/](examples/)).

## Statut

**Bêta, version 1.3.0** (2026-10-05). Les deux scripts et les définitions d'agents d'exemple sont couverts
par des tests hors ligne (`python -m unittest discover -s tests`). Le comportement de Claude avec le skill n'a pas
d'évaluation automatique, et **aucun gain chiffré n'est promis** : Anthropic ne publie pas la
pondération du quota ; seule votre mesure fait foi. Voir [docs/LIMITATIONS.md](docs/LIMITATIONS.md).

## Exemple de sortie

Extrait réel (abrégé) de `audit.py 1.2.0` sur une configuration **fictive** : 58 skills dont la
description fait 233 caractères, 10 serveurs MCP, aucun agent.

```
Audit de consommation Claude Code (audit.py 1.2.0, doc du 2026-10-01)

Mesures (estimations : environ 4 caractères par token, à confirmer avec /context)
  Skills : 58 au total, 58 visibles pour Claude, 58 avec description complète
  Listing des skills : environ 3494 tokens (sans skillOverrides : environ 3494)
  Serveurs MCP actifs : 10 (configurés : 10)
  Sous-agents personnalisés : 0 dont 0 sans modèle déclaré, 0 avec effort déclaré
  Seuil de compaction : non réglé (défaut du modèle)

Constats (4), du plus utile au moins utile
1. [P1] Seuil de compaction automatique non réglé
   Action   : Dans une session : /autocompact 400k (valeur d'exemple, entre 100k et 1M). ...
2. [P2] Aucun sous-agent personnalisé : modèle et effort ne se règlent pas par tâche
   Pourquoi : La doc ne décrit qu'un paramètre model à l'appel de l'outil Agent, pas d'effort : ...
   Action   : Copier les quatre définitions de examples/agents/ du skill (executant, analyste, ...
   Source   : https://code.claude.com/docs/en/sub-agents#supported-frontmatter-fields, ...
3. [P2] 10 serveurs MCP actifs dans les fichiers de configuration
   ...
```

## Prérequis

- Claude Code (skills personnels dans `~/.claude/skills/`).
- Python 3.9 ou plus récent pour les scripts, bibliothèque standard seulement. Sans Python, le skill
  fonctionne en lecture manuelle ([docs/USAGE.md](docs/USAGE.md#sans-python)).
- Git, pour installer par `git clone`.

## Démarrage

```bash
git clone https://github.com/RAAAAAGEEEEE/claude-code-token-saver ~/.claude/skills/claude-code-token-saver
python ~/.claude/skills/claude-code-token-saver/scripts/audit.py --save avant.json
```

Puis, dans Claude Code : « Mon quota part vite, fais un audit de consommation. » Le skill se charge
seul et déroule les quatre modes ([SKILL.md](SKILL.md)).

Vérifier l'installation :

```bash
cd ~/.claude/skills/claude-code-token-saver && python -m unittest discover -s tests
```

## Exemple minimal

Mesurer, appliquer un changement, comparer :

```bash
python scripts/audit.py --save avant.json
python scripts/backup.py ~/.claude/settings.json
# ... modifier settings.json (voir examples/settings.example.json), ouvrir une NOUVELLE session ...
python scripts/audit.py --compare avant.json
```

Dans Claude Code, relevez aussi `/context` et `/usage` avant et après.

Installer les quatre types d'agents (sans écraser les vôtres, variante PowerShell dans
[docs/INSTALLATION.md](docs/INSTALLATION.md#installer-les-types-dagents-facultatif)), puis vérifier
qu'ils sont comptés :

```bash
mkdir -p ~/.claude/agents
for f in ~/.claude/skills/claude-code-token-saver/examples/agents/*.md; do
  [ -e ~/.claude/agents/"$(basename "$f")" ] && echo "existe déjà, ignoré : $(basename "$f")" || cp "$f" ~/.claude/agents/
done
python ~/.claude/skills/claude-code-token-saver/scripts/audit.py --top 0 | grep "Sous-agents"
```

## Architecture

`SKILL.md` porte le déroulé et les règles dures ; `scripts/audit.py` mesure et signale ;
`scripts/backup.py` sauvegarde avant toute modification ; `examples/agents/` fournit les types d'agents ;
`docs/` porte le détail. Rien n'est écrit
sans accord. Détail : [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Configuration

Aucune variable obligatoire, aucune clé. Options de l'audit et réglages recommandés, clé par clé :
[docs/CONFIGURATION.md](docs/CONFIGURATION.md).

## Sécurité et confidentialité

Aucun accès réseau, aucune valeur de secret affichée (ni `env`, ni commandes de hooks, ni arguments de
serveurs MCP). Les rapports peuvent contenir des noms de skills et de serveurs : à relire avant de les
partager. Détail : [docs/PRIVACY_AND_SECURITY.md](docs/PRIVACY_AND_SECURITY.md).

## Limites

- Les tailles sont des **estimations** (environ 4 caractères par token) ; `/context` fait foi. Les
  montants de `--depense` sont des équivalents API, pas une facture.
- Le script ne voit pas les connecteurs claude.ai, les serveurs intégrés à l'application, les skills
  de plugins ni les réglages gérés par une organisation.
- La table de décision tâche vers agent est une convention proposée, non mesurée ; Haiku 4.5 a une date de
  retrait provisoire au plus tôt le 2026-10-15 (voir
  [docs/BONNES-PRATIQUES.md](docs/BONNES-PRATIQUES.md#haiku-et-son-retrait)).
- Il ne lit pas les commandes de hooks : il signale un hook `PreCompact`, il ne peut pas dire s'il bloque.
- Les réglages et seuils de Claude Code changent d'une version à l'autre : les leviers sont datés du
  2026-10-01.
- Testé à la main sous Windows 11 avec Python 3.11 ; le workflow GitHub Actions du dépôt exécute les
  tests sous Linux, macOS et Windows (résultat dans l'onglet Actions).

Liste complète : [docs/LIMITATIONS.md](docs/LIMITATIONS.md).

## Feuille de route (non contractuelle)

- Compter les skills, serveurs MCP et agents fournis par des plugins installés.
- Évaluations de déclenchement du skill (quelles demandes le chargent).
- Revérification des leviers à chaque version majeure de Claude Code.

## Contribuer

Voir [CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

MIT, voir [LICENSE](LICENSE). Sources et attributions :
[docs/LEGAL_AND_ATTRIBUTION.md](docs/LEGAL_AND_ATTRIBUTION.md). Projet indépendant, non affilié à
Anthropic.

## Documentation

- [SKILL.md](SKILL.md) : le déroulé lu par Claude
- [docs/BONNES-PRATIQUES.md](docs/BONNES-PRATIQUES.md) : pour aller plus loin (leviers, actions manuelles, écartés)
- [docs/INSTALLATION.md](docs/INSTALLATION.md)
- [docs/USAGE.md](docs/USAGE.md)
- [docs/CONFIGURATION.md](docs/CONFIGURATION.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- [docs/LIMITATIONS.md](docs/LIMITATIONS.md)
- [docs/PRIVACY_AND_SECURITY.md](docs/PRIVACY_AND_SECURITY.md)
- [docs/LEGAL_AND_ATTRIBUTION.md](docs/LEGAL_AND_ATTRIBUTION.md)
- [SECURITY.md](SECURITY.md), [CHANGELOG.md](CHANGELOG.md)
