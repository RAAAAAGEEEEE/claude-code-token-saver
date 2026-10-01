# claude-code-token-saver

**In English.** A Claude Code skill that cuts token and quota usage **without losing quality**. It
runs a read-only audit of your Claude Code setup (`settings.json`, `CLAUDE.md`, skills, MCP servers,
subagents, hooks), ranks what to fix, applies changes only with your approval and a timestamped
backup, then measures before and after. Every lever is labelled *official*, *reported* or *to verify*
with a dated source (official docs checked on 2026-10-01). Python standard library only, no network
access, no secret ever printed. Documentation is in French.

Skill Claude Code qui réduit la consommation de tokens et de quota **sans perte de qualité** : audit
en lecture seule de la configuration, rapport priorisé, application avec sauvegarde horodatée et
accord de l'utilisateur, mesure avant et après.

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
- Un **déroulé** que Claude suit : audit, rapport priorisé, application avec accord, mesure.
- Des **leviers sourcés** ([docs/BONNES-PRATIQUES.md](docs/BONNES-PRATIQUES.md)), chacun avec son
  risque pour la qualité et son étiquette de preuve ; ce qui est écarté, et pourquoi.
- Des **exemples** génériques de `settings.json` et de paragraphe `CLAUDE.md`
  ([examples/](examples/)).

## Statut

**Bêta, version 1.0.0** (2026-10-01). Les deux scripts sont couverts par des tests hors ligne
(`python -m unittest discover -s tests`). Le comportement de Claude avec le skill n'a pas
d'évaluation automatique, et **aucun gain chiffré n'est promis** : Anthropic ne publie pas la
pondération du quota ; seule votre mesure fait foi. Voir [docs/LIMITATIONS.md](docs/LIMITATIONS.md).

## Exemple de sortie

Extrait réel sur une configuration **fictive** (58 skills d'exemple, 10 serveurs MCP) :

```
Audit de consommation Claude Code (audit.py 1.0.0, doc du 2026-10-01)

Mesures (estimations : environ 4 caractères par token, à confirmer avec /context)
  Skills : 58 au total, 58 visibles pour Claude, 58 avec description complète
  Listing des skills : environ 3509 tokens (sans skillOverrides : environ 3509)
  Serveurs MCP actifs : 10 (configurés : 10)
  Seuil de compaction : non réglé (défaut du modèle)

Constats (6), du plus utile au moins utile
1. [P1] Seuil de compaction automatique non réglé
   Action   : Dans une session : /autocompact 400k (valeur d'exemple, entre 100k et 1M). ...
   Source   : code.claude.com/docs/en/model-config#set-the-auto-compact-window, ...
2. [P1] Un hook PreCompact est configuré
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

## Architecture

`SKILL.md` porte le déroulé et les règles dures ; `scripts/audit.py` mesure et signale ;
`scripts/backup.py` sauvegarde avant toute modification ; `docs/` porte le détail. Rien n'est écrit
sans accord. Détail : [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Configuration

Aucune variable obligatoire, aucune clé. Options de l'audit et réglages recommandés, clé par clé :
[docs/CONFIGURATION.md](docs/CONFIGURATION.md).

## Sécurité et confidentialité

Aucun accès réseau, aucune valeur de secret affichée (ni `env`, ni commandes de hooks, ni arguments de
serveurs MCP). Les rapports peuvent contenir des noms de skills et de serveurs : à relire avant de les
partager. Détail : [docs/PRIVACY_AND_SECURITY.md](docs/PRIVACY_AND_SECURITY.md).

## Limites

- Les tailles sont des **estimations** (environ 4 caractères par token) ; `/context` fait foi.
- Le script ne voit pas les connecteurs claude.ai, les serveurs intégrés à l'application, les skills
  de plugins ni les réglages gérés par une organisation.
- Il ne lit pas les commandes de hooks : il signale un hook `PreCompact`, il ne peut pas dire s'il bloque.
- Les réglages et seuils de Claude Code changent d'une version à l'autre : les leviers sont datés du
  2026-10-01.
- Testé à la main sous Windows 11 avec Python 3.11 ; le workflow GitHub Actions du dépôt exécute les
  tests sous Linux, macOS et Windows (résultat dans l'onglet Actions).

Liste complète : [docs/LIMITATIONS.md](docs/LIMITATIONS.md).

## Feuille de route (non contractuelle)

- Compter les skills et serveurs MCP fournis par des plugins installés.
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
